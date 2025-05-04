from datetime import datetime

from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    risk_tolerance = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    settings = db.relationship('UserSettings', backref='user', uselist=False)
    portfolios = db.relationship('Portfolio', backref='user', lazy='dynamic')



    def __repr__(self):
        return f'<User {self.username}>'

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    risk_tolerance = db.Column(db.String(20), default='Moderate')
    default_chart_period = db.Column(db.String(10), default='1y')
    enable_notifications = db.Column(db.Boolean, default=False)


    # New personalization fields based on USer goals
    investment_goal = db.Column(db.String(50), default='Growth')  # Growth, Income, Preservation, Speculation
    time_horizon = db.Column(db.String(20), default='Long-term')  # Short-term, Medium-term, Long-term
    preferred_sectors = db.Column(db.String(255))  # Comma-separated list of preferred sectors
    preferred_assets = db.Column(db.String(255))  # Comma-separated list of preferred asset types
    tax_consideration = db.Column(db.Boolean, default=False)  # Whether to consider tax implications

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserSettings for User ID {self.user_id}>'






