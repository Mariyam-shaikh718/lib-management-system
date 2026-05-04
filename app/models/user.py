from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # student, staff, admin
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    joined_date = db.Column(db.DateTime, default=datetime.utcnow)
    max_books = db.Column(db.Integer, default=5)
    
    borrows = db.relationship('BorrowRecord', backref='user', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')
    fines = db.relationship('Fine', backref='user', lazy='dynamic')

    def get_active_borrows(self):
        from app.models.borrow import BorrowRecord
        return self.borrows.filter_by(status='borrowed').count()

    def get_total_fines(self):
        from app.models.fine import Fine
        unpaid = Fine.query.filter_by(user_id=self.id, paid=False).all()
        return sum(f.amount for f in unpaid)

    def __repr__(self):
        return f'<User {self.email}>'