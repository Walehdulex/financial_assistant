# app/routes/market_routes.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.services.market_service import MarketService
import requests
import time
from datetime import datetime, timedelta
import os
from functools import lru_cache
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('market', __name__)
market_service = MarketService()

# Cache configuration
CACHE_TIMEOUT = 300  # 5 minutes


@bp.route('/overview')
@login_required
def market_overview():
    """Render the market overview page"""
    return render_template('market/overview.html')


@bp.route('/stock/<symbol>')
@login_required
def stock_details(symbol):
    """Render detailed view for a specific stock"""
    # Get stock data
    stock_data = market_service.get_stock_data(symbol)

    if not stock_data:
        logger.warning(f"Failed to get stock data for {symbol}")
        return render_template('error.html', message=f"Could not find data for {symbol}")

    # Get additional company info
    company_info = get_company_info(symbol)

    return render_template('market/details.html',
                           symbol=symbol,
                           company_name=company_info.get('name', 'Unknown Company'),
                           current_price=stock_data['current_price'],
                           price_change=stock_data.get('daily_change', 0),
                           price_change_percent=stock_data.get('daily_change_percent', 0),
                           company_description=company_info.get('description', 'No description available.'),
                           sector=company_info.get('sector', 'Unknown'),
                           industry=company_info.get('industry', 'Unknown'),
                           market_cap=format_market_cap(company_info.get('market_cap', 0)),
                           pe_ratio=company_info.get('pe_ratio', 'N/A'),
                           dividend_yield=company_info.get('dividend_yield', 'N/A'),
                           fifty_two_week_high=company_info.get('52_week_high', 'N/A'),
                           fifty_two_week_low=company_info.get('52_week_low', 'N/A'))


@bp.route('/indices')
@login_required
@lru_cache(maxsize=1)
def get_indices():
    """Get current values for major market indices"""
    try:
        indices = {}
        # Using ETFs that track the major indices
        symbols = ['SPY', 'QQQ', 'DIA']  # S&P 500, NASDAQ, Dow Jones

        for symbol in symbols:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': market_service.api_key
            }

            response = requests.get(market_service.base_url, params=params)
            data = response.json()

            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                price = float(quote.get('05. price', 0))
                change = float(quote.get('09. change', 0))

                index_data = {
                    'price': format_price(price),
                    'change': format_price(change),
                    'changePercent': quote.get('10. change percent', '0%').rstrip('%')
                }

                if symbol == 'SPY':
                    indices['sp500'] = index_data
                elif symbol == 'QQQ':
                    indices['nasdaq'] = index_data
                elif symbol == 'DIA':
                    indices['dow'] = index_data

            # Add delay to avoid API rate limiting
            time.sleep(1)

        # If any index is missing, add placeholder
        if 'sp500' not in indices:
            indices['sp500'] = {'price': 'N/A', 'change': '0', 'changePercent': '0'}
        if 'nasdaq' not in indices:
            indices['nasdaq'] = {'price': 'N/A', 'change': '0', 'changePercent': '0'}
        if 'dow' not in indices:
            indices['dow'] = {'price': 'N/A', 'change': '0', 'changePercent': '0'}

        return jsonify(indices)
    except Exception as e:
        logger.error(f"Error fetching indices: {e}")
        return jsonify({
            'sp500': {'price': 'N/A', 'change': 'N/A', 'changePercent': 'N/A'},
            'nasdaq': {'price': 'N/A', 'change': 'N/A', 'changePercent': 'N/A'},
            'dow': {'price': 'N/A', 'change': 'N/A', 'changePercent': 'N/A'}
        })


@bp.route('/movers')
@login_required
def get_market_movers():
    """Get top gainers, losers, and most active stocks"""
    try:
        # Alpha Vantage doesn't have a direct endpoint for market movers
        # This would typically require a premium API or calculation from a larger dataset
        # Here we're using the TOP_GAINERS_LOSERS endpoint which is available in some plans

        params = {
            'function': 'TOP_GAINERS_LOSERS',
            'apikey': market_service.api_key
        }

        response = requests.get(market_service.base_url, params=params)
        data = response.json()

        gainers = []
        losers = []
        most_active = []

        if 'top_gainers' in data:
            for stock in data['top_gainers'][:5]:  # Top 5 gainers
                gainers.append({
                    'symbol': stock.get('ticker', ''),
                    'price': stock.get('price', '0'),
                    'change': stock.get('change_amount', '0'),
                    'changePercent': stock.get('change_percentage', '0%').rstrip('%'),
                    'volume': int(stock.get('volume', '0').replace(',', ''))
                })

        if 'top_losers' in data:
            for stock in data['top_losers'][:5]:  # Top 5 losers
                losers.append({
                    'symbol': stock.get('ticker', ''),
                    'price': stock.get('price', '0'),
                    'change': stock.get('change_amount', '0'),
                    'changePercent': stock.get('change_percentage', '0%').rstrip('%'),
                    'volume': int(stock.get('volume', '0').replace(',', ''))
                })

        if 'most_actively_traded' in data:
            for stock in data['most_actively_traded'][:5]:  # Top 5 most active
                most_active.append({
                    'symbol': stock.get('ticker', ''),
                    'price': stock.get('price', '0'),
                    'change': stock.get('change_amount', '0'),
                    'changePercent': stock.get('change_percentage', '0%').rstrip('%'),
                    'volume': int(stock.get('volume', '0').replace(',', ''))
                })

        # If any list is empty (e.g., if the endpoint is not available in your plan),
        # fill with placeholder data for demonstration
        if not gainers:
            # Use top stocks as placeholders
            top_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
            gainers = generate_placeholder_stocks(top_stocks, is_gainer=True)

        if not losers:
            # Use different stocks for losers
            loser_stocks = ['META', 'NFLX', 'TSLA', 'JPM', 'BAC']
            losers = generate_placeholder_stocks(loser_stocks, is_gainer=False)

        if not most_active:
            # Use combination for most active
            active_stocks = ['TSLA', 'AAPL', 'AMD', 'INTC', 'PFE']
            most_active = generate_placeholder_stocks(active_stocks, is_gainer=None)

        return jsonify({
            'gainers': gainers,
            'losers': losers,
            'mostActive': most_active
        })
    except Exception as e:
        logger.error(f"Error fetching market movers: {e}")
        return jsonify({'error': 'Failed to fetch market movers'}), 500


@bp.route('/news')
@login_required
def get_market_news():
    """Get latest market news"""
    try:
        params = {
            'function': 'NEWS_SENTIMENT',
            'topics': 'financial_markets,economy_macro',
            'apikey': market_service.api_key,
            'limit': 10
        }

        # Add target stock for more relevant news if provided
        symbol = request.args.get('symbol')
        if symbol:
            params['tickers'] = symbol

        response = requests.get(market_service.base_url, params=params)
        data = response.json()

        news_items = []
        if 'feed' in data:
            for item in data['feed'][:6]:  # Limit to 6 news items
                # Format date
                date_str = item.get('time_published', '')
                try:
                    date_obj = datetime.strptime(date_str, '%Y%m%dT%H%M%S')
                    formatted_date = date_obj.strftime('%b %d, %Y')
                except:
                    formatted_date = date_str

                news_items.append({
                    'title': item.get('title', 'No title'),
                    'summary': item.get('summary', 'No summary available')[:150] + '...',
                    'source': item.get('source', 'Unknown'),
                    'url': item.get('url', '#'),
                    'published_at': formatted_date,
                    'sentiment': item.get('overall_sentiment_label', 'neutral')
                })

        return jsonify({'news': news_items})
    except Exception as e:
        logger.error(f"Error fetching market news: {e}")
        return jsonify({'error': 'Failed to fetch market news'}), 500


@bp.route('/search')
@login_required
def search_stock():
    """Search for a specific stock symbol"""
    symbol = request.args.get('symbol', '').upper()

    if not symbol:
        return jsonify({'error': 'No symbol provided'})

    try:
        # First, try to get current data for the symbol
        stock_data = market_service.get_stock_data(symbol)

        if not stock_data:
            # If not found, try symbol search endpoint to see if it exists
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': symbol,
                'apikey': market_service.api_key
            }

            response = requests.get(market_service.base_url, params=params)
            search_data = response.json()

            if 'bestMatches' in search_data and search_data['bestMatches']:
                best_match = search_data['bestMatches'][0]
                return jsonify({
                    'symbol': best_match.get('1. symbol', symbol),
                    'name': best_match.get('2. name', 'Unknown Company'),
                    'price': 'N/A',
                    'change': '0',
                    'changePercent': '0',
                    'lastUpdated': datetime.now().isoformat()
                })
            else:
                return jsonify({'error': f'Could not find data for {symbol}'})

        return jsonify({
            'symbol': symbol,
            'name': stock_data.get('company_name', 'Unknown Company'),
            'price': format_price(stock_data['current_price']),
            'change': format_price(stock_data.get('daily_change', 0)),
            'changePercent': format_percent(stock_data.get('daily_change_percent', 0)),
            'lastUpdated': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error searching for stock {symbol}: {e}")
        return jsonify({'error': f'Error searching for {symbol}'}), 500


@bp.route('/stock_history/<symbol>')
@login_required
def get_stock_history(symbol):
    """Get historical price data for a stock"""
    try:
        period = request.args.get('period', '1m')

        # Map period to appropriate Alpha Vantage function and outputsize
        if period in ['1d', '5d']:
            function = 'TIME_SERIES_INTRADAY'
            interval = '60min'
            outputsize = 'full'
        elif period in ['1m', '6m']:
            function = 'TIME_SERIES_DAILY'
            outputsize = 'compact'
        else:  # 1y, 5y
            function = 'TIME_SERIES_DAILY'
            outputsize = 'full'

        params = {
            'function': function,
            'symbol': symbol,
            'apikey': market_service.api_key,
            'outputsize': outputsize
        }

        if function == 'TIME_SERIES_INTRADAY':
            params['interval'] = interval

        response = requests.get(market_service.base_url, params=params)
        data = response.json()

        # Process historical data
        dates = []
        prices = []

        if function == 'TIME_SERIES_INTRADAY' and 'Time Series (60min)' in data:
            time_series = data['Time Series (60min)']
            # Limit data points based on period
            limit = 24 if period == '1d' else 120  # 24 hours or 5 days

            for date_str, values in list(time_series.items())[:limit]:
                dates.append(date_str)
                prices.append(float(values['4. close']))

        elif function == 'TIME_SERIES_DAILY' and 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            # Limit data points based on period
            limit = 30 if period == '1m' else 180 if period == '6m' else 365 if period == '1y' else 1825  # 1m, 6m, 1y, 5y

            for date_str, values in list(time_series.items())[:limit]:
                dates.append(date_str)
                prices.append(float(values['4. close']))

        # Reverse to get chronological order
        dates.reverse()
        prices.reverse()

        return jsonify({
            'dates': dates,
            'prices': prices
        })
    except Exception as e:
        logger.error(f"Error fetching stock history for {symbol}: {e}")
        return jsonify({'error': f'Failed to fetch history for {symbol}'}), 500


def get_company_info(symbol):
    """Get detailed company information"""
    try:
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': market_service.api_key
        }

        response = requests.get(market_service.base_url, params=params)
        data = response.json()

        if not data or 'Symbol' not in data:
            logger.warning(f"No company info found for {symbol}")
            return {}

        # Format numbers appropriately
        market_cap = int(float(data.get('MarketCapitalization', 0)))
        pe_ratio = float(data.get('PERatio', 0)) if data.get('PERatio') else None
        dividend_yield = float(data.get('DividendYield', 0)) * 100 if data.get('DividendYield') else None
        week_high = float(data.get('52WeekHigh', 0)) if data.get('52WeekHigh') else None
        week_low = float(data.get('52WeekLow', 0)) if data.get('52WeekLow') else None

        return {
            'name': data.get('Name', f'{symbol} Corp'),
            'description': data.get('Description', 'No description available.'),
            'sector': data.get('Sector', 'Unknown'),
            'industry': data.get('Industry', 'Unknown'),
            'market_cap': market_cap,
            'pe_ratio': format_number(pe_ratio) if pe_ratio else 'N/A',
            'dividend_yield': f"{format_number(dividend_yield)}%" if dividend_yield else 'N/A',
            '52_week_high': f"${format_number(week_high)}" if week_high else 'N/A',
            '52_week_low': f"${format_number(week_low)}" if week_low else 'N/A',
            'exchange': data.get('Exchange', 'Unknown'),
            'currency': data.get('Currency', 'USD')
        }
    except Exception as e:
        logger.error(f"Error getting company info for {symbol}: {e}")
        return {}


def generate_placeholder_stocks(symbols, is_gainer=None):
    """Generate placeholder stock data for demo purposes"""
    results = []
    for symbol in symbols:
        stock_data = market_service.get_stock_data(symbol)
        if stock_data:
            # Use actual data with modified change values based on gainer/loser
            price = stock_data['current_price']
            if is_gainer is True:
                change = abs(price * 0.02)  # 2% gain
                change_percent = 2.0
            elif is_gainer is False:
                change = -abs(price * 0.02)  # 2% loss
                change_percent = -2.0
            else:
                # Random change for most active
                change = price * 0.01  # 1% change
                change_percent = 1.0

            results.append({
                'symbol': symbol,
                'price': format_price(price),
                'change': format_price(change),
                'changePercent': format_percent(change_percent),
                'volume': 5000000 + (symbols.index(symbol) * 1000000)  # Dummy volume
            })
        else:
            # Completely fake data
            results.append({
                'symbol': symbol,
                'price': '100.00',
                'change': '1.00' if is_gainer else '-1.00',
                'changePercent': '1.00' if is_gainer else '-1.00',
                'volume': 5000000 + (symbols.index(symbol) * 1000000)
            })

    return results


def format_price(price):
    """Format price value"""
    try:
        return f"{float(price):.2f}"
    except:
        return str(price)


def format_percent(percent):
    """Format percentage value"""
    try:
        return f"{float(percent):.2f}"
    except:
        return str(percent)


def format_number(number):
    """Format numeric value"""
    try:
        return f"{float(number):.2f}"
    except:
        return 'N/A'


def format_market_cap(market_cap):
    """Format market cap in B/M format"""
    try:
        market_cap = float(market_cap)
        if market_cap >= 1_000_000_000:
            return f"${market_cap / 1_000_000_000:.2f}B"
        elif market_cap >= 1_000_000:
            return f"${market_cap / 1_000_000:.2f}M"
        else:
            return f"${market_cap:,.0f}"
    except:
        return 'N/A'