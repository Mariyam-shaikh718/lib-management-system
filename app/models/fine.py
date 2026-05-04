from app import db
from datetime import datetime

class Fine(db.Model):
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    borrow_id = db.Column(db.Integer, db.ForeignKey('borrow_records.id'))
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(200))
    paid = db.Column(db.Boolean, default=False)
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    paid_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    
    borrow = db.relationship('BorrowRecord', backref='fine')