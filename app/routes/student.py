from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.book import Book, Category
from app.models.borrow import BorrowRecord
from app.models.reservation import Reservation
from app.models.fine import Fine
from app.models.audit import AuditLog
from datetime import datetime, timedelta
from config import Config

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    active_borrows = BorrowRecord.query.filter_by(user_id=current_user.id, status='borrowed').all()
    overdue = [b for b in active_borrows if b.is_overdue()]
    reservations = Reservation.query.filter_by(user_id=current_user.id, status='pending').all()
    unpaid_fines = Fine.query.filter_by(user_id=current_user.id, paid=False).all()
    recent_books = Book.query.order_by(Book.added_date.desc()).limit(6).all()
    popular_books = Book.query.order_by(Book.borrow_count.desc()).limit(6).all()
    return render_template('student/dashboard.html',
        active_borrows=active_borrows, overdue=overdue,
        reservations=reservations, unpaid_fines=unpaid_fines,
        recent_books=recent_books, popular_books=popular_books,
        total_fines=sum(f.amount for f in unpaid_fines))

@student_bp.route('/books')
@login_required
def books():
    q = request.args.get('q', '')
    genre = request.args.get('genre', '')
    page = request.args.get('page', 1, type=int)
    query = Book.query
    if q:
        query = query.filter(
            db.or_(Book.title.ilike(f'%{q}%'),
                   Book.author.ilike(f'%{q}%'),
                   Book.isbn.ilike(f'%{q}%'))
        )
    if genre:
        query = query.filter_by(genre=genre)
    books = query.paginate(page=page, per_page=Config.BOOKS_PER_PAGE)
    categories = Category.query.all()
    return render_template('student/books.html', books=books, categories=categories, q=q, genre=genre)

@student_bp.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    active_count = BorrowRecord.query.filter_by(user_id=current_user.id, status='borrowed').count()
    if active_count >= current_user.max_books:
        flash(f'You can only borrow up to {current_user.max_books} books at a time.', 'warning')
        return redirect(url_for('student.books'))
    if not book.is_available():
        flash('No copies available right now.', 'warning')
        return redirect(url_for('student.books'))
    already = BorrowRecord.query.filter_by(user_id=current_user.id, book_id=book_id, status='borrowed').first()
    if already:
        flash('You already have this book borrowed.', 'info')
        return redirect(url_for('student.my_books'))
    record = BorrowRecord(user_id=current_user.id, book_id=book_id)
    book.available_copies -= 1
    book.borrow_count += 1
    db.session.add(record)
    db.session.commit()
    AuditLog.log(current_user.id, 'BORROW_BOOK', 'book', book_id, f'Borrowed: {book.title}')
    flash(f'Successfully borrowed "{book.title}". Due: {record.due_date.strftime("%b %d, %Y")}', 'success')
    return redirect(url_for('student.my_books'))

@student_bp.route('/return/<int:record_id>', methods=['POST'])
@login_required
def return_book(record_id):
    record = BorrowRecord.query.filter_by(id=record_id, user_id=current_user.id).first_or_404()
    record.return_date = datetime.utcnow()
    record.status = 'returned'
    record.book.available_copies += 1
    if record.is_overdue():
        fine_amt = record.calculated_fine()
        fine = Fine(user_id=current_user.id, borrow_id=record.id,
                    amount=fine_amt, reason=f'Late return: {record.days_overdue()} days overdue')
        db.session.add(fine)
        flash(f'Book returned. Fine applied: PKR {fine_amt:.2f}', 'warning')
    else:
        flash('Book returned successfully!', 'success')
    # Check reservations queue
    next_res = Reservation.query.filter_by(book_id=record.book_id, status='pending').order_by(Reservation.reserved_date).first()
    if next_res:
        next_res.status = 'ready'
    db.session.commit()
    AuditLog.log(current_user.id, 'RETURN_BOOK', 'book', record.book_id, f'Returned: {record.book.title}')
    return redirect(url_for('student.my_books'))

@student_bp.route('/renew/<int:record_id>', methods=['POST'])
@login_required
def renew_book(record_id):
    record = BorrowRecord.query.filter_by(id=record_id, user_id=current_user.id).first_or_404()
    if not record.can_renew():
        flash('This book cannot be renewed (max renewals reached or overdue).', 'danger')
        return redirect(url_for('student.my_books'))
    record.due_date += timedelta(days=Config.MAX_BORROW_DAYS)
    record.renewals += 1
    db.session.commit()
    flash(f'Renewed! New due date: {record.due_date.strftime("%b %d, %Y")}', 'success')
    return redirect(url_for('student.my_books'))

@student_bp.route('/reserve/<int:book_id>', methods=['POST'])
@login_required
def reserve_book(book_id):
    book = Book.query.get_or_404(book_id)
    existing = Reservation.query.filter_by(user_id=current_user.id, book_id=book_id, status='pending').first()
    if existing:
        flash('You already have a reservation for this book.', 'info')
        return redirect(url_for('student.books'))
    queue_pos = Reservation.query.filter_by(book_id=book_id, status='pending').count() + 1
    reservation = Reservation(user_id=current_user.id, book_id=book_id, queue_position=queue_pos)
    db.session.add(reservation)
    db.session.commit()
    flash(f'Reserved! Queue position: #{queue_pos}', 'success')
    return redirect(url_for('student.my_books'))

@student_bp.route('/my-books')
@login_required
def my_books():
    borrows = BorrowRecord.query.filter_by(user_id=current_user.id).order_by(BorrowRecord.borrow_date.desc()).all()
    reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.reserved_date.desc()).all()
    return render_template('student/my_books.html', borrows=borrows, reservations=reservations)

@student_bp.route('/fines')
@login_required
def fines():
    all_fines = Fine.query.filter_by(user_id=current_user.id).order_by(Fine.issued_date.desc()).all()
    return render_template('student/fines.html', fines=all_fines)

@student_bp.route('/pay-fine/<int:fine_id>', methods=['POST'])
@login_required
def pay_fine(fine_id):
    fine = Fine.query.filter_by(id=fine_id, user_id=current_user.id).first_or_404()
    fine.paid = True
    fine.paid_date = datetime.utcnow()
    fine.payment_method = request.form.get('method', 'cash')
    db.session.commit()
    flash(f'Fine of PKR {fine.amount:.2f} paid successfully!', 'success')
    return redirect(url_for('student.fines'))