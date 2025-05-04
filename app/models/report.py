from app import db
from datetime import datetime


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    report_type = db.Column(db.String(50), nullable=False)  # performance, allocation, tax, risk
    file_path = db.Column(db.String(255))
    format = db.Column(db.String(20))  # pdf, csv, xlsx
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)

    # Relationship with User model
    user = db.relationship('User', backref=db.backref('reports', lazy='dynamic'))

    def __repr__(self):
        return f'<Report {self.id} - {self.report_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'format': self.format,
            'generated_at': self.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_archived': self.is_archived
        }