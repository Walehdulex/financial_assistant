import pandas as pd
from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from app.models.portfolio import Portfolio, Holding
from app.services import market_service
from app.services.portfolio_service import PortfolioService
from app.services.performance_service import PerformanceService
from app.services.market_service import MarketService
from app.services.risk_service import RiskService
from app.services.recommendation_service import RecommendationService
from app.services.news_service import NewsService
from app.services.history_service import HistoryService
from app.services.ml_service import MLService
from app.services.enhanced_recommendation_service import EnhancedRecommendationService
from datetime import datetime, timedelta
from app import db


import random

from pyexpat import features

bp = Blueprint('portfolio', __name__)
market_service = MarketService()
history_service = HistoryService(market_service)
portfolio_service = PortfolioService()
performance_service = PerformanceService(market_service)
risk_service = RiskService(market_service)
recommendation_service = RecommendationService(market_service, risk_service)
news_service = NewsService(market_service)
ml_service = MLService(market_service)
enhanced_recommendation_service = EnhancedRecommendationService(market_service, risk_service, ml_service)



@bp.route('/dashboard')
@login_required
def dashboard():
    portfolio = current_user.portfolios.first()
    if portfolio:
        history_service.record_portfolio_value(portfolio)

    today_date = datetime.now().strftime('%B-%d-%Y')
    return render_template('portfolio/dashboard.html', today_date=today_date)

@bp.route('/holdings')
@login_required
def get_holdings():
    holdings = []
    total_value = 0
    total_change = 0

    for holding in current_user.portfolios.first().holdings.all():
        stock_data = market_service.get_stock_data(holding.symbol)
        if stock_data:
            current_price = stock_data['current_price']
            value = current_price * holding.quantity
            holdings.append({
                'symbol': holding.symbol,
                'quantity': holding.quantity,
                'current_price': current_price,
                'total_value': current_price * holding.quantity,
                'daily_change': stock_data.get('daily_change', 0),
            })
            total_value += value
            total_change += stock_data.get('total_change', 0) * value / 100

    return jsonify({
        'holdings': holdings,
        'total_value': f"{total_value:.2f}",
        'daily_change': f"{total_change:.2f}",
        'daily_change_percent': f"{(total_change/total_value*100 if total_value else 0):.2f}"
    })

# Adding  Stock
@bp.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    try:
        data = request.json
        symbol = data.get('symbol').upper()
        quantity = int(data.get('quantity', 0))

        if not symbol or quantity <= 0:
            return jsonify({'error': 'Invalid input data'}), 400

        # Getting the  stock data
        stock_data = market_service.get_stock_data(symbol)
        if not stock_data:
            return jsonify({'error': f'Could not fetch data for {symbol}. Please check the symbol and try again.'}), 400

        # Getting / creating portfolio
        portfolio = current_user.portfolios.first()
        if not portfolio:
            portfolio = Portfolio(user_id=current_user.id, name="Default Portfolio")
            db.session.add(portfolio)
            db.session.commit()

        # Adding / updating holding
        holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
        if holding:
            holding.quantity += quantity
        else:
            holding = Holding(
                portfolio_id=portfolio.id,
                symbol=symbol,
                quantity=quantity,
                purchase_price=stock_data['current_price']
            )
            db.session.add(holding)

        db.session.commit()
        history_service.record_portfolio_value(portfolio)
        return jsonify({
            'message': 'Stock added successfully',
            'stock_data': stock_data
        })

    except Exception as e:
        print(f"Error adding stock: {e}")
        return jsonify({'error': 'An error occurred while adding the stock'}), 500

# Removing Stock
@bp.route('/remove_stock/<symbol>', methods=['DELETE'])
@login_required
def remove_stock(symbol):
    portfolio = current_user.portfolios.first()
    if portfolio:
        holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
        if holding:
            db.session.delete(holding)
            db.session.commit()
            history_service.record_portfolio_value(portfolio)
            return jsonify({'message': 'Stock removed successfully'})
    return jsonify({'error': 'Stock not found'}), 404


# Add this route to your Flask app - right after the remove_stock route
@bp.route('/sell_shares', methods=['POST'])
@login_required
def sell_shares():
    try:
        data = request.json

        if not data or 'symbol' not in data or 'quantity' not in data:
            return jsonify({'status': 'error', 'message': 'Missing required data'}), 400

        symbol = data['symbol'].upper()
        quantity_to_sell = int(data['quantity'])
        sell_price = data.get('sell_price')
        sell_date = data.get('sell_date')

        # Get the current portfolio
        portfolio = current_user.portfolios.first()
        if not portfolio:
            return jsonify({'status': 'error', 'message': 'No portfolio found'}), 404

        # Get the holding
        holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
        if not holding:
            return jsonify({'status': 'error', 'message': f'Stock {symbol} not found in portfolio'}), 404

        # Validate the quantity to sell
        if quantity_to_sell <= 0:
            return jsonify({'status': 'error', 'message': 'Quantity to sell must be positive'}), 400

        if quantity_to_sell > holding.quantity:
            return jsonify({'status': 'error',
                            'message': f'Cannot sell more than current holdings ({holding.quantity} shares)'}), 400

        # Update the holding quantity
        holding.quantity -= quantity_to_sell

        # If all shares are sold, remove the holding
        if holding.quantity == 0:
            db.session.delete(holding)

        # You may want to record this transaction in a transaction history table
        # if you have one. Here's a sample of how you might do that:
        # transaction = Transaction(
        #     user_id=current_user.id,
        #     portfolio_id=portfolio.id,
        #     symbol=symbol,
        #     transaction_type='SELL',
        #     quantity=quantity_to_sell,
        #     price=sell_price or market_service.get_stock_data(symbol)['current_price'],
        #     transaction_date=datetime.strptime(sell_date, '%Y-%m-%d').date() if sell_date else datetime.now().date()
        # )
        # db.session.add(transaction)

        # Commit changes to the database
        db.session.commit()

        # Record the new portfolio value
        history_service.record_portfolio_value(portfolio)

        return jsonify({
            'status': 'success',
            'message': f'Successfully sold {quantity_to_sell} shares of {symbol}'
        }), 200

    except Exception as e:
        print(f"Error selling shares: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500



@bp.route('/performance')
@login_required
def get_performance():
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    performance_data = performance_service.calculate_portfolio_performance(portfolio)
    return jsonify(performance_data)

@bp.route('/historical_performance')
@login_required
def get_historical_performance():
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    #Recording current value
    history_service.record_portfolio_value(portfolio)

    #Getting Historical data from database
    history = history_service.get_portfolio_history(portfolio)

    if not history:
        return jsonify({
            'dates': [],
            'values': [],
            'returns': [],
            'current_value': 0,
            'initial_value': 0,
            'total_return': 0
        })

    #Preparing data for charts
    dates = [entry.date.strftime('%Y-%m-%d') for entry in history]
    values = [entry.total_value for entry in history]

    #Calculating returns based on the first value
    initial_value = values[0] if values else 0
    returns = [((value / initial_value) - 1) * 100 for value in values] if initial_value else []
    current_value = values[-1] if values else 0

    print(f"Historical data: {len(dates)} data points")
    print(f"First few dates: {dates[:3]}")
    print(f"First few values: {values[:3]}")

    return jsonify({
        'dates': dates,
        'values': values,
        'returns': returns,
        'current_value': current_value,
        'initial_value': initial_value,
        'total_return': ((current_value / initial_value) - 1) * 100 if initial_value else 0
    })

@bp.route('/risk_analysis')
@login_required
def get_risk_analysis():
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    risk_data = risk_service.calculate_portfolio_risk(portfolio)
    return jsonify(risk_data)



@bp.route('/recommendations')
@login_required
def get_recommendations():
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    recommendations = recommendation_service.generate_recommendations(portfolio)
    return jsonify({'recommendations': recommendations})

@bp.route('/news')
@login_required
def get_portfolio_news():
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    holdings = list(portfolio.holdings)
    news = news_service.get_news_for_portfolio(holdings)

    return jsonify({'news': news})

@bp.route('/enhanced-recommendations')
@login_required
def get_enhanced_recommendations():
    # recommendations = [
    #     {
    #         'type': 'diversification',
    #         'action': 'Add more stocks to improve diversification',
    #         'reasoning': 'Your portfolio currently has few stocks which increases risk',
    #         'priority': 'high'
    #     }
    # ]
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    recommendations = enhanced_recommendation_service.generate_enhanced_recommendations(portfolio, current_user)
    return jsonify({'recommendations': recommendations})

@bp.route('/analysis')
@login_required
def portfolio_analysis():
    return render_template('portfolio/analysis.html')

@bp.route('/forecasts')
@login_required
def get_forecasts():
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    holdings = list(portfolio.holdings)
    symbols = [holding.symbol for holding in holdings]

    forecasts = {}
    for symbol in symbols:
        try:
            #Getting Historical Data
            historical_data = ml_service._get_historical_data(symbol)

            if historical_data is None or len(historical_data) < 30:
                print(f"Insufficient historical data for {symbol}, skipping")
                continue

            #Generating Features
            features = ml_service._generate_features(historical_data)

            if features is None or len(features) == 0:
                print(f"could not generate features for {symbol}, skipping")

            #Making Predictions
            predicted_return, target_price, confidence = ml_service._predict_return(symbol, features)

            #Preparing data for Chart
            dates = []
            historical_prices = []

            #Last 30 Days
            lookback_days = min(30, len(features))
            for i in range (lookback_days):
                idx = len(features) - lookback_days + i
                #Ensuring index is Valid
                if 0 <= idx < len(features):
                    date_val = features['date'].iloc[idx]
                    #Converting date to string if it's a datetime object
                    if isinstance(date_val, (datetime, pd.Timestamp)):
                        date_str = date_val.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date_val)
                    dates.append(date_str)
                    historical_prices.append(float(features['close'].iloc[idx]))

            #Skipping it if there is no data
            if not historical_prices:
                print(f"could not extarct histtorical prices for {symbol}, skipping")
                continue

            # Next 30 Days
            forecast_dates = []
            forecast_prices = []

            last_price = historical_prices[-1] if historical_prices else None
            if last_price is None:
                print(f"No last price available for {symbol}, skipping")
                continue

            #Parsing the last date from historical data
            last_date = datetime.strptime(dates[-1], '%Y-%m-%d') if dates else datetime.now()

            #Generating forecast prices and dates
            for i in range(30):
                next_date = (last_date + timedelta(days=i + 1)).strftime('%Y-%m-%d')
                forecast_dates.append(next_date)


                #Simple linear projection
                forecast_price = last_price * (1 + (predicted_return * (i + 1) / 30))
                forecast_prices.append(float(forecast_price))

            forecasts[symbol] = {
                'current_price': last_price,
                'target_price': target_price,
                'predicted_return': predicted_return,
                'confidence': confidence,
                'dates': dates,
                'historical_prices': historical_prices,
                'forecast_dates': forecast_dates,
                'forecast_prices': forecast_prices
            }
        except Exception as e:
            print(f"Error generating forecasts for {symbol}: {str(e)}")
    return jsonify({'forecasts': forecasts})




