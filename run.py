from app import create_app, db
from app.models.user import User
from app.models.book import Book, Category
from app.models.borrow import BorrowRecord
from app.models.reservation import Reservation
from app.models.fine import Fine
from app.models.audit import AuditLog
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Book=Book)

@app.cli.command("init-db")
def init_db():
    """Initialize the database with sample data."""
    db.create_all()
    
    # Create admin user
    if not User.query.filter_by(email='admin@lms.com').first():
        admin = User(
            name='Super Admin',
            email='admin@lms.com',
            password=generate_password_hash('admin123'),
            role='admin',
            is_active=True,
            member_id='ADM001',
            joined_date=datetime.utcnow()
        )
        db.session.add(admin)

    # Create categories
    categories = ['Fiction', 'Science', 'History', 'Technology', 'Philosophy', 'Arts', 'Mathematics', 'Literature']
    for cat_name in categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))

    # Sample books
    sample_books = [
        {'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'isbn': '9780743273565', 'genre': 'Fiction', 'total_copies': 5, 'description': 'A story of the fabulously wealthy Jay Gatsby.', 'publisher': 'Scribner', 'year': 1925},
        {'title': 'Clean Code', 'author': 'Robert C. Martin', 'isbn': '9780132350884', 'genre': 'Technology', 'total_copies': 4, 'description': 'A Handbook of Agile Software Craftsmanship.', 'publisher': 'Prentice Hall', 'year': 2008},
        {'title': 'A Brief History of Time', 'author': 'Stephen Hawking', 'isbn': '9780553380163', 'genre': 'Science', 'total_copies': 3, 'description': 'From the Big Bang to Black Holes.', 'publisher': 'Bantam', 'year': 1988},
        {'title': 'Sapiens', 'author': 'Yuval Noah Harari', 'isbn': '9780062316097', 'genre': 'History', 'total_copies': 6, 'description': 'A Brief History of Humankind.', 'publisher': 'Harper', 'year': 2011},
        {'title': '1984', 'author': 'George Orwell', 'isbn': '9780451524935', 'genre': 'Fiction', 'total_copies': 4, 'description': 'A dystopian social science fiction novel.', 'publisher': 'Signet Classic', 'year': 1949},
        {'title': 'The Pragmatic Programmer', 'author': 'Andrew Hunt', 'isbn': '9780201616224', 'genre': 'Technology', 'total_copies': 3, 'description': 'Your Journey to Mastery.', 'publisher': 'Addison-Wesley', 'year': 1999},
    ]

    for book_data in sample_books:
        if not Book.query.filter_by(isbn=book_data['isbn']).first():
            category = Category.query.filter_by(name=book_data['genre']).first()
            book = Book(
                title=book_data['title'],
                author=book_data['author'],
                isbn=book_data['isbn'],
                genre=book_data['genre'],
                category_id=category.id if category else None,
                total_copies=book_data['total_copies'],
                available_copies=book_data['total_copies'],
                description=book_data['description'],
                publisher=book_data['publisher'],
                publication_year=book_data['year']
            )
            db.session.add(book)

    db.session.commit()
    print("✅ Database initialized with sample data!")
    print("👤 Admin: admin@lms.com / admin123")

if __name__ == '__main__':
    app.run(debug=True)