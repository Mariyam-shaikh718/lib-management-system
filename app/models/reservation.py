from app import db
from datetime import datetime, timedelta

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    reserved_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, ready, fulfilled, cancelled
    queue_position = db.Column(db.Integer, default=1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expiry_date:
            self.expiry_date = datetime.utcnow() + timedelta(days=7)