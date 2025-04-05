from app.models.user import User
from app import db
from datetime import datetime

#Portfolio class
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    holdings = db.relationship('Holding', backref='portfolio', lazy='dynamic')
    history = db.relationship('PortfolioHistory', backref='portfolio', lazy='dynamic')


    def __repr__(self):
        return f'<Portfolio {self.name}>'

#Holding class
class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_return = db.Column(db.Float,)
    return_percentage = db.Column(db.Float)

#Portfolio History Class
class PortfolioHistory(db.Model):
    __tablename__ = 'portfolio_history'

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_value = db.Column(db.Float, nullable=False)
    cash_value = db.Column(db.Float, default=0.0)


    def __repr__(self):
        return f'<Holding {self.symbol}>'