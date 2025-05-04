from app import db
from datetime import datetime


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), default='info')  # info, alert, warning, success
    is_read = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(50))  # market, portfolio, security, system
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with User model
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'source': self.source,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }