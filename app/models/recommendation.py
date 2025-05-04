from app import db
from datetime import datetime

class RecommendationFeedback(db.Model):
    __tablename__ = 'recommendation_feedback'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommendation_type = db.Column(db.String(50), nullable=False)
    recommendation_action = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 scale
    was_followed = db.Column(db.Boolean, default=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='recommendation_feedback')


