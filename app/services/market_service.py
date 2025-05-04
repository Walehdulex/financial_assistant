import requests
from datetime import datetime, timedelta
from time import sleep
import time
from flask import current_app
from config import Config

from app.monitoring.metrics import (
    track_api_call,
    track_cache_access,
    track_response_with_cache_status
)


from app import db


class MarketService:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.base_url = 'https://www.alphavantage.co/query'
        self.api_key = Config.ALPHA_VANTAGE_API_KEY  # Store API key here

    def get_stock_data(self, symbol):
        """Getting current stock data with caching and metrics."""
        cache_key = f"stock_data_{symbol}"
        try:
            # Check cache
            if symbol in self.cache:
                last_update = self.cache[symbol]['last_update']
                if datetime.now() - last_update < timedelta(seconds=self.cache_timeout):
                    track_cache_access(cache_key, True)  # Cache hit
                    start_time = time.time()
                    result = self.cache[symbol]['data']
                    duration = time.time() - start_time
                    # print(f"CACHED RESPONSE: Symbol={symbol}, Duration={duration}s, Duration in ms={duration * 1000}ms")
                    track_response_with_cache_status('get_stock_data', duration, True)
                    return result

            track_cache_access(cache_key, False)  # Cache miss

            # API parameters for getting quote data
            start_time = time.time()
            try:
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.api_key
                }

                response = requests.get(self.base_url, params=params, timeout=10)
                quote_data = response.json()

                if 'Global Quote' in quote_data and quote_data['Global Quote']:
                    quote = quote_data['Global Quote']

                    data = {
                        'current_price': float(quote.get('05. price', 0)),
                        'company_name': symbol,
                        'daily_change': float(quote.get('09. change', 0)),
                        'daily_change_percent': float(quote.get('10. change percent', '0').rstrip('%')),
                        'volume': int(quote.get('06. volume', 0)),
                        'high': float(quote.get('03. high', 0)),
                        'low': float(quote.get('04. low', 0))
                    }

                    # Update cache
                    self.cache[symbol] = {
                        'data': data,
                        'last_update': datetime.now()
                    }

                    # Add these two lines to track fresh API responses
                    duration = time.time() - start_time
                    track_response_with_cache_status('get_stock_data', duration, False)
                    track_api_call('alpha_vantage', 'GLOBAL_QUOTE', True)

                    return data
                else:
                    print(f"No quote data found for {symbol}")
                    track_api_call('alpha_vantage', 'GLOBAL_QUOTE', False)
                    return None

            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")
                track_api_call('alpha_vantage', 'GLOBAL_QUOTE', False)
                return None
        except Exception as e:
            print(f"Unexpected error in get_stock_data: {str(e)}")
            return None


    def get_historical_data(self, symbol, period='1y'):
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full'
        }

        response = requests.get(self.base_url, params=params)
        return response.json()

    def check_price_alerts(self, user_id):
        """Checking price alerts for a user and generating notifications if needed"""
        from app.models.alert import PriceAlert
        from app.services.notification_service import NotificationService

        notification_service = NotificationService()
        alerts = PriceAlert.query.filter_by(user_id=user_id, is_active=True).all()

        triggered_alerts = []
        for alert in alerts:
            stock_data = self.get_stock_data(alert.symbol)
            current_price = stock_data.get('current_price', 0)

            if (alert.alert_type == 'above' and current_price >= alert.price_threshold) or \
                    (alert.alert_type == 'below' and current_price <= alert.price_threshold):
                # Alert triggered, create notification
                notification = notification_service.create_price_alert_notification(
                    user_id=user_id,
                    symbol=alert.symbol,
                    price=current_price,
                    threshold=alert.price_threshold,
                    alert_type=alert.alert_type
                )

                # marking the alert as inactive or deleting it
                if alert.one_time:
                    alert.is_active = False
                    db.session.commit()

                triggered_alerts.append({
                    'alert_id': alert.id,
                    'symbol': alert.symbol,
                    'price': current_price,
                    'threshold': alert.price_threshold,
                    'alert_type': alert.alert_type
                })

        return triggered_alerts

