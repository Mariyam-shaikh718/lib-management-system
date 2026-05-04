from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')

    @staticmethod
    def log(user_id, action, target_type=None, target_id=None, description=None, ip=None):
        log = AuditLog(
            user_id=user_id, action=action,
            target_type=target_type, target_id=target_id,
            description=description, ip_address=ip
        )
        db.session.add(log)
        db.session.commit()