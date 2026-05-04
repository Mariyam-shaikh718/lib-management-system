from app import db
from app.models.borrow import BorrowRecord
from app.models.fine import Fine
from datetime import datetime
from config import Config

def calculate_and_apply_fines():
    """Run this daily via scheduler to auto-generate fines."""
    overdue = BorrowRecord.query.filter(
        BorrowRecord.status == 'borrowed',
        BorrowRecord.due_date < datetime.utcnow()
    ).all()
    
    for record in records_to_update(overdue):
        record.status = 'overdue'
        existing_fine = Fine.query.filter_by(borrow_id=record.id, paid=False).first()
        fine_amount = record.days_overdue() * Config.FINE_PER_DAY
        if existing_fine:
            existing_fine.amount = fine_amount
        else:
            fine = Fine(
                user_id=record.user_id,
                borrow_id=record.id,
                amount=fine_amount,
                reason=f'Overdue: {record.days_overdue()} days'
            )
            db.session.add(fine)
    db.session.commit()

def records_to_update(records):
    return records