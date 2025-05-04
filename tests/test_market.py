import unittest
from app import create_app, db
from app.models.user import User
from unittest.mock import patch, MagicMock
import json


class MarketDataTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()

        # Create and login test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.market_service.MarketService.get_stock_data')
    @patch('app.routes.market_routes.get_company_info')
    def test_stock_details(self, mock_company_info, mock_get_stock_data):
        """Test stock details page"""
        mock_get_stock_data.return_value = {
            'current_price': 150.0,
            'daily_change': 2.5,
            'daily_change_percent': 1.7
        }

        mock_company_info.return_value = {
            'name': 'Apple Inc.',
            'description': 'Apple Inc. is an American multinational technology company.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'market_cap': 2500000000000,
            'pe_ratio': '30.5',
            'dividend_yield': '0.6%',
            '52_week_high': '$182.94',
            '52_week_low': '$124.17'
        }

        response = self.client.get('/market/stock/AAPL')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Apple Inc.' in response.data)
        self.assertTrue(b'Technology' in response.data)

    @patch('app.routes.market_routes.requests.get')
    def test_search_stock(self, mock_get):
        """Test stock search functionality"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Global Quote': {
                '05. price': '150.25',
                '09. change': '2.50',
                '10. change percent': '1.7%'
            }
        }
        mock_get.return_value = mock_response

        response = self.client.get('/market/search?symbol=AAPL')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['symbol'], 'AAPL')
        self.assertEqual(data['price'], '150.25')
        self.assertEqual(data['change'], '2.50')

    @patch('app.routes.market_routes.requests.get')
    def test_get_market_news(self, mock_get):
        """Test fetching market news"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'feed': [
                {
                    'title': 'Market rallies on tech earnings',
                    'summary': 'Stock market surges after positive tech earnings reports.',
                    'source': 'Financial News',
                    'url': 'https://example.com/news/1',
                    'time_published': '20210820T120000',
                    'overall_sentiment_label': 'positive'
                },
                {
                    'title': 'Fed signals rate hikes',
                    'summary': 'Federal Reserve hints at upcoming interest rate increases.',
                    'source': 'Economic Times',
                    'url': 'https://example.com/news/2',
                    'time_published': '20210820T110000',
                    'overall_sentiment_label': 'neutral'
                }
            ]
        }
        mock_get.return_value = mock_response

        response = self.client.get('/market/news')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('news' in data)
        self.assertEqual(len(data['news']), 2)
        self.assertEqual(data['news'][0]['title'], 'Market rallies on tech earnings')

    @patch('app.routes.market_routes.requests.get')
    def test_get_stock_history(self, mock_get):
        """Test getting stock price history"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Time Series (Daily)': {
                '2023-04-01': {
                    '1. open': '145.00',
                    '2. high': '147.50',
                    '3. low': '144.00',
                    '4. close': '146.75',
                    '5. volume': '10000000'
                },
                '2023-04-02': {
                    '1. open': '146.75',
                    '2. high': '148.50',
                    '3. low': '146.00',
                    '4. close': '148.25',
                    '5. volume': '11000000'
                }
            }
        }
        mock_get.return_value = mock_response

        response = self.client.get('/market/stock_history/AAPL?period=1m')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('dates' in data)
        self.assertTrue('prices' in data)
        self.assertEqual(len(data['dates']), 2)
        self.assertEqual(len(data['prices']), 2)

    @patch('app.routes.market_routes.requests.get')
    def test_get_market_movers(self, mock_get):
        """Test getting market movers (top gainers, losers)"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'top_gainers': [
                {
                    'ticker': 'AAPL',
                    'price': '150.00',
                    'change_amount': '5.00',
                    'change_percentage': '3.45%',
                    'volume': '15,000,000'
                }
            ],
            'top_losers': [
                {
                    'ticker': 'MSFT',
                    'price': '250.00',
                    'change_amount': '-7.50',
                    'change_percentage': '-2.91%',
                    'volume': '12,000,000'
                }
            ],
            'most_actively_traded': [
                {
                    'ticker': 'TSLA',
                    'price': '180.00',
                    'change_amount': '2.50',
                    'change_percentage': '1.41%',
                    'volume': '25,000,000'
                }
            ]
        }
        mock_get.return_value = mock_response

        response = self.client.get('/market/movers')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('gainers' in data)
        self.assertTrue('losers' in data)
        self.assertTrue('mostActive' in data)
        self.assertEqual(len(data['gainers']), 1)
        self.assertEqual(data['gainers'][0]['symbol'], 'AAPL')
        self.assertEqual(data['losers'][0]['symbol'], 'MSFT')
        self.assertEqual(data['mostActive'][0]['symbol'], 'TSLA')

    @patch('app.routes.market_routes.requests.get')
    def test_get_indices(self, mock_get):
        """Test getting market indices"""

        def side_effect(url, params):
            response = MagicMock()
            symbol = params.get('symbol')
            if symbol == 'SPY':
                response.json.return_value = {
                    'Global Quote': {'05. price': '450.00', '09. change': '3.50', '10. change percent': '0.78%'}}
            elif symbol == 'QQQ':
                response.json.return_value = {
                    'Global Quote': {'05. price': '380.00', '09. change': '4.20', '10. change percent': '1.12%'}}
            elif symbol == 'DIA':
                response.json.return_value = {
                    'Global Quote': {'05. price': '350.00', '09. change': '2.10', '10. change percent': '0.60%'}}
            return response

        mock_get.side_effect = side_effect

        response = self.client.get('/market/indices')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('sp500' in data)
        self.assertTrue('nasdaq' in data)
        self.assertTrue('dow' in data)
        self.assertEqual(data['sp500']['price'], '450.00')
        self.assertEqual(data['nasdaq']['price'], '380.00')
        self.assertEqual(data['dow']['price'], '350.00')



    def test_basic_market_access(self):
        """Test that we can access a basic route"""
        # Try to access the root route
        response = self.client.get('/')
        # Just check that it returns some response, don't check content yet
        self.assertIn(response.status_code, [200, 302])