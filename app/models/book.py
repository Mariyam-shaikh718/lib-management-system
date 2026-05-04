from app import db
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    books = db.relationship('Book', backref='category_obj', lazy='dynamic')

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    genre = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    description = db.Column(db.Text)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    cover_image = db.Column(db.String(200))
    is_ebook = db.Column(db.Boolean, default=False)
    ebook_url = db.Column(db.String(300))
    borrow_count = db.Column(db.Integer, default=0)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    borrows = db.relationship('BorrowRecord', backref='book', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='book', lazy='dynamic')

    def is_available(self):
        return self.available_copies > 0

    def __repr__(self):
        return f'<Book {self.title}>'