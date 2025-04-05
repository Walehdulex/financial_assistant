from datetime import datetime

from app import db
from app.models.portfolio import Portfolio, PortfolioHistory
from app.services.market_service import MarketService


# from financial_assistant.app.models.portfolio import Portfolio, PortfolioHistory
# from financial_assistant.app.routes.portfolio_routes import market_service
# from financial_assistant.app.services.market_service import MarketService


#Recording Daily Portfolio Values
def record_portfolio_values():
    market_service = MarketService()
    today = datetime.now().date()

    #Getting all Portfolios
    portfolios = Portfolio.query.all()

    for portfolio in portfolios:
        total_value = 0

        #Calculating Portfolio Value
        for holding in portfolio.holdings:
            stock_data = market_service.get_stock_data(holding.symbol)
            if stock_data:
                total_value += stock_data['current_price'] * holding.quantity

        #Creating new History Record
        history_entry = PortfolioHistory(
            portfolio_id=portfolio.id,
            date=today,
            total_value=total_value,
        )

        db.session.add(history_entry)

    db.session.commit()
