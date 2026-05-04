from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.book import Book, Category
from app.models.user import User
from app.models.borrow import BorrowRecord
from app.models.reservation import Reservation
from app.models.fine import Fine
from app.models.audit import AuditLog
from app.utils.decorators import admin_required
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_books = Book.query.count()
    total_members = User.query.filter_by(role='student').count()
    active_borrows = BorrowRecord.query.filter_by(status='borrowed').count()
    overdue_count = len([b for b in BorrowRecord.query.filter_by(status='borrowed').all() if b.is_overdue()])
    total_fines = db.session.query(db.func.sum(Fine.amount)).filter_by(paid=False).scalar() or 0
    popular_books = Book.query.order_by(Book.borrow_count.desc()).limit(5).all()
    recent_activity = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    # Monthly borrow stats (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        d = datetime.utcnow() - timedelta(days=30*i)
        count = BorrowRecord.query.filter(
            db.extract('month', BorrowRecord.borrow_date) == d.month,
            db.extract('year', BorrowRecord.borrow_date) == d.year
        ).count()
        monthly_data.append({'month': d.strftime('%b'), 'count': count})
    return render_template('admin/dashboard.html',
        total_books=total_books, total_members=total_members,
        active_borrows=active_borrows, overdue_count=overdue_count,
        total_fines=total_fines, popular_books=popular_books,
        recent_activity=recent_activity, monthly_data=monthly_data)

@admin_bp.route('/books', methods=['GET', 'POST'])
@login_required
@admin_required
def books():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            book = Book(
                title=request.form['title'], author=request.form['author'],
                isbn=request.form['isbn'], genre=request.form['genre'],
                description=request.form.get('description'),
                publisher=request.form.get('publisher'),
                publication_year=request.form.get('year', type=int),
                total_copies=request.form.get('copies', 1, type=int),
                available_copies=request.form.get('copies', 1, type=int),
                is_ebook=bool(request.form.get('is_ebook')),
                ebook_url=request.form.get('ebook_url')
            )
            db.session.add(book)
            db.session.commit()
            AuditLog.log(current_user.id, 'ADD_BOOK', 'book', book.id, f'Added: {book.title}')
            flash(f'Book "{book.title}" added!', 'success')
        elif action == 'delete':
            book = Book.query.get_or_404(request.form['book_id'])
            db.session.delete(book)
            db.session.commit()
            flash('Book deleted.', 'success')
        return redirect(url_for('admin.books'))
    q = request.args.get('q', '')
    query = Book.query
    if q:
        query = query.filter(db.or_(Book.title.ilike(f'%{q}%'), Book.author.ilike(f'%{q}%')))
    books = query.order_by(Book.added_date.desc()).paginate(page=request.args.get('page', 1, type=int), per_page=15)
    categories = Category.query.all()
    return render_template('admin/books.html', books=books, categories=categories, q=q)

@admin_bp.route('/members')
@login_required
@admin_required
def members():
    q = request.args.get('q', '')
    query = User.query.filter(User.role != 'admin')
    if q:
        query = query.filter(db.or_(User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%')))
    members = query.paginate(page=request.args.get('page', 1, type=int), per_page=20)
    return render_template('admin/members.html', members=members, q=q)

@admin_bp.route('/toggle-member/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_member(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'Member {user.name} {status}.', 'info')
    return redirect(url_for('admin.members'))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    overdue_records = [b for b in BorrowRecord.query.filter_by(status='borrowed').all() if b.is_overdue()]
    pending_fines = Fine.query.filter_by(paid=False).all()
    all_fines = Fine.query.order_by(Fine.issued_date.desc()).limit(50).all()
    return render_template('admin/reports.html',
        overdue_records=overdue_records, pending_fines=pending_fines, all_fines=all_fines)

@admin_bp.route('/issue-book', methods=['POST'])
@login_required
@admin_required
def issue_book():
    member_id = request.form.get('member_id')
    book_id = request.form.get('book_id', type=int)
    user = User.query.filter_by(member_id=member_id).first()
    book = Book.query.get(book_id)
    if not user or not book:
        flash('Invalid member or book.', 'danger')
        return redirect(url_for('admin.dashboard'))
    record = BorrowRecord(user_id=user.id, book_id=book.id)
    book.available_copies -= 1
    book.borrow_count += 1
    db.session.add(record)
    db.session.commit()
    AuditLog.log(current_user.id, 'ISSUE_BOOK', 'book', book.id, f'Issued to {user.name}')
    flash(f'Book issued to {user.name}!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/audit')
@login_required
@admin_required
def audit():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=request.args.get('page', 1, type=int), per_page=30)
    return render_template('admin/audit.html', logs=logs)

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    genre_stats = db.session.query(Book.genre, db.func.count(Book.id)).group_by(Book.genre).all()
    return jsonify({'genres': [{'name': g, 'count': c} for g, c in genre_stats]})