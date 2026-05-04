from app import db
from datetime import datetime, timedelta
from config import Config

class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='borrowed')  # borrowed, returned, overdue
    renewals = db.Column(db.Integer, default=0)
    max_renewals = db.Column(db.Integer, default=2)
    notes = db.Column(db.Text)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.due_date:
            self.due_date = datetime.utcnow() + timedelta(days=Config.MAX_BORROW_DAYS)

    def is_overdue(self):
        return self.status == 'borrowed' and datetime.utcnow() > self.due_date

    def days_overdue(self):
        if self.is_overdue():
            return (datetime.utcnow() - self.due_date).days
        return 0

    def can_renew(self):
        return self.renewals < self.max_renewals and not self.is_overdue()

    def calculated_fine(self):
        return self.days_overdue() * Config.FINE_PER_DAY