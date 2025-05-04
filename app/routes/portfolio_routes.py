import app
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, url_for, send_file, flash, redirect
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
from app.models.recommendation import RecommendationFeedback
from app.services.report_service import ReportService
from app.routes import track_request_time


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
@track_request_time
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
        'daily_change_percent': f"{(total_change / total_value * 100 if total_value else 0):.2f}"
    })


# Adding  Stock
@bp.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    try:
        data = request.json
        symbol = data.get('symbol').upper()
        quantity = float(data.get('quantity', 0))

        if not symbol or quantity <= 0 or quantity < 0.001:
            return jsonify({'error': 'Invalid input data. Quantity must be at least 0.001.'}), 400

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
        quantity_to_sell = float(data['quantity'])
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
        if holding.quantity < 0.0001:
            db.session.delete(holding)
        else:
            db.session.flush()


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
@track_request_time
def get_historical_performance():
    portfolio = current_user.portfolios.first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    # Recording current value
    history_service.record_portfolio_value(portfolio)

    # Getting Historical data from database
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

    # Preparing data for charts
    dates = [entry.date.strftime('%Y-%m-%d') for entry in history]
    values = [entry.total_value for entry in history]

    # Calculating returns based on the first value
    initial_value = values[0] if values else 0
    returns = [((value / initial_value) - 1) * 100 for value in values] if initial_value else []
    current_value = values[-1] if values else 0

    # print(f"Historical data: {len(dates)} data points")
    # print(f"First few dates: {dates[:3]}")
    # print(f"First few values: {values[:3]}")

    return jsonify({
        'dates': dates,
        'values': values,
        'returns': returns,
        'current_value': current_value,
        'initial_value': initial_value,
        'total_return': ((current_value / initial_value) - 1) * 100 if initial_value else 0
    })


@bp.route('/risk_analysis')
@track_request_time
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
@track_request_time
def get_enhanced_recommendations():
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
            # Getting Historical Data
            historical_data = ml_service._get_historical_data(symbol)

            if historical_data is None or len(historical_data) < 30:
                print(f"Insufficient historical data for {symbol}, skipping")
                continue

            # Generating Features
            features = ml_service._generate_features(historical_data)

            if features is None or len(features) == 0:
                print(f"could not generate features for {symbol}, skipping")

            # Making Predictions
            predicted_return, target_price, confidence = ml_service._predict_return(symbol, features)

            # Preparing data for Chart
            dates = []
            historical_prices = []

            # Last 30 Days
            lookback_days = min(30, len(features))
            for i in range(lookback_days):
                idx = len(features) - lookback_days + i
                # Ensuring index is Valid
                if 0 <= idx < len(features):
                    date_val = features['date'].iloc[idx]
                    # Converting date to string if it's a datetime object
                    if isinstance(date_val, (datetime, pd.Timestamp)):
                        date_str = date_val.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date_val)
                    dates.append(date_str)
                    historical_prices.append(float(features['close'].iloc[idx]))

            # Skipping it if there is no data
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

            # Parsing the last date from historical data
            last_date = datetime.strptime(dates[-1], '%Y-%m-%d') if dates else datetime.now()

            # Generating forecast prices and dates
            for i in range(30):
                next_date = (last_date + timedelta(days=i + 1)).strftime('%Y-%m-%d')
                forecast_dates.append(next_date)

                # Simple linear projection
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


@bp.route('/recommendation-feedback', methods=['POST'])
@login_required
def submit_recommendation_feedback():
    try:
        data = request.json

        if not data or 'recommendation_type' not in data or 'recommendation_action' not in data or 'rating' not in data:
            return jsonify({'status': 'error', 'message': 'Missing required data'}), 400

        feedback = RecommendationFeedback(
            user_id=current_user.id,
            recommendation_type=data['recommendation_type'],
            recommendation_action=data['recommendation_action'],
            rating=data['rating'],
            was_followed=data.get('was_followed', False),
            comment=data.get('comment', '')
        )

        db.session.add(feedback)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Feedback submitted successfully'}), 200

    except Exception as e:
        print(f"Error submitting recommendation feedback: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred while submitting feedback'}), 500


@bp.route('/impact-analysis')
@login_required
def get_impact_analysis():
    try:
        action_type = request.args.get('type')
        symbol = request.args.get('symbol')

        if not action_type or not symbol:
            return jsonify({'error': 'Missing parameters'}), 400

        # Getting the current portfolio
        portfolio = current_user.portfolios.first()
        if not portfolio:
            return jsonify({'error': 'No portfolio found'}), 404

        # Get current portfolio value and risk metrics
        current_holdings = list(portfolio.holdings)
        total_value = 0
        current_allocation = []

        for holding in current_holdings:
            stock_data = market_service.get_stock_data(holding.symbol)
            if stock_data:
                price = stock_data['current_price']
                value = price * holding.quantity
                total_value += value
                current_allocation.append({
                    'symbol': holding.symbol,
                    'value': value,
                    'weight': 0  # This will be calculated after total is known
                })

        # Updating Weights - FIXED INDENTATION
        for item in current_allocation:
            item['weight'] = item['value'] / total_value if total_value > 0 else 0

        # Getting the current risk metrics
        risk_data = risk_service.calculate_portfolio_risk(portfolio)

        # Calculating projected changes based on action type
        projected_holdings = current_holdings.copy()
        projected_allocation = []
        stock_data = market_service.get_stock_data(symbol)

        if not stock_data:
            return jsonify({'error': f'Could not get data for {symbol}'}), 400

        current_price = stock_data['current_price']
        projected_total = total_value  # Default initialization
        quantity_to_add = 5  # Default for buy action

        if action_type == 'buy':
            # Simulating adding 5 shares
            projected_total = total_value + (current_price * quantity_to_add)

            # Updating projected allocation
            symbol_exists = False
            for holding in projected_holdings:
                stock_data_for_holding = market_service.get_stock_data(holding.symbol)
                if stock_data_for_holding:
                    price = stock_data_for_holding['current_price']

                    if holding.symbol == symbol:
                        symbol_exists = True
                        projected_quantity = holding.quantity + quantity_to_add
                        projected_allocation.append({
                            'symbol': symbol,
                            'value': projected_quantity * price,
                            'weight': 0  # Will update after calculating total
                        })
                    else:
                        # Existing holdings keep the same quantity
                        projected_allocation.append({
                            'symbol': holding.symbol,
                            'value': price * holding.quantity,
                            'weight': 0  # Will update after calculating total
                        })

            # adding symbol If it doesn't exist in current holdings
            if not symbol_exists:
                projected_allocation.append({
                    'symbol': symbol,
                    'value': current_price * quantity_to_add,
                    'weight': 0  # Will update after calculating total
                })

        elif action_type == 'sell':
            # Finding the holding
            target_holding = None
            for holding in projected_holdings:
                if holding.symbol == symbol:
                    target_holding = holding
                    break
            if not target_holding:
                return jsonify({'error': f'You don\'t own any {symbol} shares'}), 400

            # Simulating selling half the position (or at least 1 share)
            quantity_to_sell = max(1, target_holding.quantity / 2)

            # Calculating new values
            remaining_quantity = target_holding.quantity - quantity_to_sell
            projected_total = total_value - (current_price * quantity_to_sell)

            # Updating projected allocation
            for holding in projected_holdings:
                stock_data_for_holding = market_service.get_stock_data(holding.symbol)
                if stock_data_for_holding:
                    price = stock_data_for_holding['current_price']
                    if holding.symbol == symbol:
                        value = price * remaining_quantity
                    else:
                        value = price * holding.quantity

                    projected_allocation.append({
                        'symbol': holding.symbol,
                        'value': value,
                        'weight': 0  # Will update after calculating total
                    })
        else:
            return jsonify({'error': 'Invalid action type'}), 400

        # Calculating projected total and update weights
        projected_total = sum(item['value'] for item in projected_allocation)
        for item in projected_allocation:
            item['weight'] = item['value'] / projected_total if projected_total > 0 else 0

        # Simulating the projected portfolio risk
        current_volatility = risk_data['volatility']
        current_diversification = risk_data['diversification_score']

        # Initialize projected values
        projected_volatility = current_volatility
        projected_diversification = current_diversification

        # Simple projection based on number of holdings and allocation
        symbol_exists = any(holding.symbol == symbol for holding in current_holdings)

        if action_type == 'buy' and not symbol_exists:
            projected_diversification = min(1.0, current_diversification + 0.05)

            # Volatility impact depends on the stock's volatility
            stock_volatility = 0.25  # Default assumption
            if symbol in risk_data['individual_stock_risks']:
                stock_volatility = risk_data['individual_stock_risks'][symbol]['volatility']

            # Blending based on new weight
            new_weight = (current_price * quantity_to_add) / projected_total
            projected_volatility = ((1 - new_weight) * current_volatility) + (new_weight * stock_volatility)
        elif action_type == 'sell':
            # Removing a stock might reduce diversification
            if len(projected_allocation) < len(current_allocation):
                projected_diversification = max(0, current_diversification - 0.05)
            else:
                projected_diversification = current_diversification

            # Volatility impact depends on the stock's volatility
            stock_volatility = 0.25  # Default assumption
            if symbol in risk_data['individual_stock_risks']:
                stock_volatility = risk_data['individual_stock_risks'][symbol]['volatility']

            # When a user is selling a high-volatility stock, overall volatility might decrease
            if stock_volatility > current_volatility:
                projected_volatility = max(0, current_volatility - 0.02)
            else:
                projected_volatility = min(1.0, current_volatility + 0.01)

        return jsonify({
            'current_value': total_value,
            'projected_value': projected_total,
            'current_allocation': current_allocation,
            'projected_allocation': projected_allocation,
            'current_risk': {
                'volatility': current_volatility,
                'diversification': current_diversification
            },
            'projected_risk': {
                'volatility': projected_volatility,
                'diversification': projected_diversification
            }
        })
    except Exception as e:
        print(f"Error calculating impact analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to calculate impact analysis'}), 500

@bp.route('/holding/<symbol>')
@login_required
def get_holding_info(symbol):
    try:
        portfolio = current_user.portfolios.first()
        if not portfolio:
            return jsonify({'error': 'No portfolio found'}), 404

        holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()

        if not holding:
            return jsonify({'error': f'No holding found for {symbol}'}), 404

        stock_data = market_service.get_stock_data(symbol)
        current_price = stock_data['current_price'] if stock_data else 0

        return jsonify({
            'holding': {
                'symbol': holding.symbol,
                'quantity': holding.quantity,
                'purchase_price': holding.purchase_price,
                'current_price': current_price,
                'current_value': holding.quantity * current_price
            }
        })
    except Exception as e:
        print(f"Error fetching holding info: {e}")
        return jsonify({'error': 'Failed to fetch holding information'}), 500

@bp.route('/export/csv', methods=['GET'])
@login_required
def export_csv():
    try:
        report_service = ReportService()
        report = report_service.generate_portfolio_summary_report(user_id=current_user.id)
        if not report:
            flash('No portfolio data available for export', 'warning')
            return redirect(url_for('portfolio.dashboard'))

        return send_file(report.file_path, as_attachment=True, download_name=f"portfolio_summary_{datetime.now().strftime('%Y%m%d')}.csv")
    except Exception as e:
        # Log the error and show a user-friendly message
        from flask import current_app
        current_app.logger.error(f"CSV generation error: {str(e)}")
        flash(f"Error generating CSV report: {str(e)}", "danger")
        return redirect(url_for('portfolio.dashboard'))

@bp.route('/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    try:
        report_service = ReportService()
        report = report_service.generate_portfolio_summary_pdf_report(user_id=current_user.id)
        if not report:
            flash('No portfolio data available for PDF export', 'warning')
            return redirect(url_for('portfolio.dashboard'))

        return send_file(report.file_path, as_attachment=True, download_name=f"portfolio_summary_{datetime.now().strftime('%Y%m%d')}.pdf")
    except Exception as e:
        # Log the error and show a user-friendly message
        from flask import current_app
        current_app.logger.error(f"PDF generation error: {str(e)}")
        flash(f"Error generating PDF report: {str(e)}", "danger")
        return redirect(url_for('portfolio.dashboard'))

