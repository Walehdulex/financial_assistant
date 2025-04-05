from datetime import datetime

from app import db
from app.models.portfolio import Portfolio, Holding
from app.services.market_service import MarketService



class PortfolioService:
    def __init__(self):
        self.market_service = MarketService()

    def create_portfolio(self, user_id, name):
        portfolio = Portfolio(user_id=user_id, name=name)
        db.session.add(portfolio)
        db.session.commit()
        return portfolio

    def add_holding(self, portfolio_id, symbol, quantity, purchase_price=None):
        holding = Holding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            purchase_price=purchase_price
        )
        db.session.add(holding)
        db.session.commit()
        return holding

    def get_portfolio_value(self, portfolio_id):
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return 0

        total_value = 0
        for holding in portfolio.holdings:
            stock_data = self.market_service.get_stock_data(holding.symbol)
            if stock_data:
                total_value += stock_data['current_price'] * holding.quantity
        return total_value

    def record_portfolio_history(self, user_id, total_value, total_cost):
        today = datetime.now().date()

        #Creating or Updating the porfolio entry for the Day
        existing_entry = PortfolioHistory.query.filter_by(
            user_id=user_id,
            date=today
        ).first()

        if existing_entry:
            existing_entry.total_value = total_value
            existing_entry.total_cost = total_cost
        else:
            new_entry = PortfolioHistory(
                user_id=user_id,
                date=today,
                total_value=total_value,
                total_cost=total_cost
            )
            db.session.add(new_entry)
        db.session.commit()



