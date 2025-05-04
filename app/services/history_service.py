from app import db
from app.models.portfolio import PortfolioHistory
from datetime import datetime

class HistoryService:
    def __init__(self, market_service):
        self.market_service = market_service

    def record_portfolio_value(self, portfolio):
        #Recording current value of portfolio
        today = datetime.now().date()

        #Check if entry already exist
        existing_entry = PortfolioHistory.query.filter_by(
            portfolio_id=portfolio.id,
            date=today
        ).first()

        #Calculating current portfolio value
        total_value = 0
        for holding in portfolio.holdings:
            stock_data = self.market_service.get_stock_data(holding.symbol)
            if stock_data:
                total_value += stock_data['current_price'] * holding.quantity


        if existing_entry:
            # Updating existing entry
            existing_entry.total_value = total_value
        else:
            #Create new Entry
            history_entry = PortfolioHistory(
                portfolio_id=portfolio.id,
                date=today,
                total_value=total_value,
            )
            db.session.add(history_entry)

        db.session.commit()
        return total_value

    def get_portfolio_history(self, portfolio, days=30):

        portfolio_id = portfolio.id if hasattr(portfolio, 'id') else portfolio

        history = (PortfolioHistory.query
                   .filter_by(portfolio_id=portfolio_id)
                   .order_by(PortfolioHistory.date.asc())
                   .limit(days)
                   .all())

        # #Debugging Message
        # print(f"Retrieved {len(history)} history records for portfolio {portfolio_id}")

        return history
