# app/services/market_service.py
import requests
from datetime import datetime, timedelta
from time import sleep
from flask import current_app
from config import Config  # Add this import


class MarketService:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.base_url = 'https://www.alphavantage.co/query'
        self.api_key = Config.ALPHA_VANTAGE_API_KEY  # Store API key here

    def get_stock_data(self, symbol):
        """Get current stock data with caching"""
        try:
            # Check cache
            if symbol in self.cache:
                last_update = self.cache[symbol]['last_update']
                if datetime.now() - last_update < timedelta(seconds=self.cache_timeout):
                    return self.cache[symbol]['data']

            # API parameters for getting quote data
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

                return data
            else:
                print(f"No quote data found for {symbol}")
                return None

        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None

    # def get_stock_data(self, symbol):
    #     try:
    #         # Check cache
    #         if symbol in self.cache:
    #             last_update = self.cache[symbol]['last_update']
    #             if datetime.now() - last_update < timedelta(seconds=self.cache_timeout):
    #                 return self.cache[symbol]['data']
    #
    #         # API parameters for getting quote data
    #         params = {
    #             'function': 'GLOBAL_QUOTE',
    #             'symbol': symbol,
    #             'apikey': self.api_key  # Use the stored API key
    #         }
    #
    #         print(f"Fetching data for {symbol}...")  # Debug print
    #         response = requests.get(self.base_url, params=params)
    #         quote_data = response.json()
    #
    #         print(f"Response: {quote_data}")  # Debug print
    #
    #         if 'Global Quote' in quote_data and quote_data['Global Quote']:
    #             quote = quote_data['Global Quote']
    #
    #             data = {
    #                 'current_price': float(quote.get('05. price', 0)),
    #                 'company_name': symbol,
    #                 'daily_change': float(quote.get('10. change percent', '0').rstrip('%')),
    #                 'volume': int(quote.get('06. volume', 0)),
    #                 'high': float(quote.get('03. high', 0)),
    #                 'low': float(quote.get('04. low', 0))
    #             }
    #
    #             # Update cache
    #             self.cache[symbol] = {
    #                 'data': data,
    #                 'last_update': datetime.now()
    #             }
    #
    #             return data
    #         else:
    #             print(f"No data found for {symbol} in response: {quote_data}")
    #             return None
    #
    #     except Exception as e:
    #         print(f"Error fetching data for {symbol}: {e}")
    #         return None

    def get_historical_data(self, symbol, period='1y'):
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full'
        }

        response = requests.get(self.base_url, params=params)
        return response.json()

