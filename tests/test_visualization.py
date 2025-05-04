# tests/test_visualization.py

import unittest
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio, Holding
from unittest.mock import patch, MagicMock
import json


class VisualizationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()

        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

        # Login user
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        # Create test portfolio with holdings
        self.portfolio = Portfolio(user_id=self.user.id, name="Test Portfolio")
        db.session.add(self.portfolio)
        db.session.commit()

        # Add diverse holdings
        holdings = [
            Holding(portfolio_id=self.portfolio.id, symbol='AAPL', quantity=10, purchase_price=145.0),
            Holding(portfolio_id=self.portfolio.id, symbol='MSFT', quantity=5, purchase_price=290.0),
            Holding(portfolio_id=self.portfolio.id, symbol='AMZN', quantity=3, purchase_price=130.0),
            Holding(portfolio_id=self.portfolio.id, symbol='GOOGL', quantity=8, purchase_price=140.0)
        ]
        db.session.add_all(holdings)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_portfolio_allocation_chart(self, mock_get_stock_data):
        """Test generating portfolio allocation charts"""

        # Mock stock data with current prices
        def get_stock_mock(symbol):
            stock_data = {
                'AAPL': {'current_price': 160.0, 'company_name': 'Apple Inc.'},
                'MSFT': {'current_price': 310.0, 'company_name': 'Microsoft Corporation'},
                'AMZN': {'current_price': 145.0, 'company_name': 'Amazon.com Inc.'},
                'GOOGL': {'current_price': 150.0, 'company_name': 'Alphabet Inc.'}
            }
            return stock_data.get(symbol, {})

        mock_get_stock_data.side_effect = get_stock_mock

        # Get portfolio allocation chart data
        response = self.client.get('/portfolio/charts/allocation')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify chart data structure
        self.assertIn('chart_data', data)
        self.assertIn('labels', data['chart_data'])
        self.assertIn('values', data['chart_data'])

        # Check that all holdings are represented
        for symbol in ['AAPL', 'MSFT', 'AMZN', 'GOOGL']:
            self.assertIn(symbol, data['chart_data']['labels'])

        # Check that values add up to 100%
        self.assertAlmostEqual(sum(data['chart_data']['values']), 100.0, places=1)

    @patch('app.services.history_service.HistoryService.get_portfolio_history')
    def test_performance_chart(self, mock_get_history):
        """Test generating performance history chart"""
        from datetime import datetime, timedelta
        from app.models.portfolio import PortfolioHistory

        # Create historical data for last 30 days
        today = datetime.now().date()
        history_data = []

        base_value = 5000.0
        for i in range(30, 0, -1):
            # Generate some random-looking but trending data
            day_value = base_value * (1 + (30 - i) * 0.01)  # 1% growth per day
            history_data.append(
                PortfolioHistory(
                    portfolio_id=self.portfolio.id,
                    date=today - timedelta(days=i),
                    total_value=day_value
                )
            )

        mock_get_history.return_value = history_data

        # Get performance chart data
        response = self.client.get('/portfolio/charts/performance?period=1m')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify chart data structure
        self.assertIn('chart_data', data)
        self.assertIn('dates', data['chart_data'])
        self.assertIn('values', data['chart_data'])

        # Check number of data points
        self.assertEqual(len(data['chart_data']['dates']), 30)
        self.assertEqual(len(data['chart_data']['values']), 30)

        # Verify data shows growth trend
        self.assertGreater(data['chart_data']['values'][-1], data['chart_data']['values'][0])

    @patch('app.services.market_service.MarketService.get_stock_history')
    def test_stock_price_chart(self, mock_get_history):
        """Test generating stock price history chart"""
        # Mock historical price data
        mock_data = {
            'dates': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)],
            'prices': [150 + i for i in range(30)]  # Simple uptrend
        }
        mock_get_history.return_value = mock_data

        # Get stock price chart data
        response = self.client.get('/market/charts/stock/AAPL?period=1m')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify chart data structure
        self.assertIn('chart_data', data)
        self.assertIn('dates', data['chart_data'])
        self.assertIn('prices', data['chart_data'])

        # Check number of data points
        self.assertEqual(len(data['chart_data']['dates']), 30)
        self.assertEqual(len(data['chart_data']['prices']), 30)

        # Verify we're getting the mockup data
        self.assertEqual(data['chart_data']['prices'][-1], 150 + 29)

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_sector_allocation_chart(self, mock_get_stock_data):
        """Test generating sector allocation chart"""

        # Mock stock data with sector information
        def get_stock_with_sector(symbol):
            stock_data = {
                'AAPL': {'current_price': 160.0, 'sector': 'Technology'},
                'MSFT': {'current_price': 310.0, 'sector': 'Technology'},
                'AMZN': {'current_price': 145.0, 'sector': 'Consumer Cyclical'},
                'GOOGL': {'current_price': 150.0, 'sector': 'Communication Services'}
            }
            return stock_data.get(symbol, {})

        mock_get_stock_data.side_effect = get_stock_with_sector

        # Get sector allocation chart data
        response = self.client.get('/portfolio/charts/sector-allocation')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify chart data structure
        self.assertIn('chart_data', data)
        self.assertIn('sectors', data['chart_data'])
        self.assertIn('values', data['chart_data'])

        # Check that all sectors are represented
        expected_sectors = ['Technology', 'Consumer Cyclical', 'Communication Services']
        for sector in expected_sectors:
            self.assertIn(sector, data['chart_data']['sectors'])

        # Technology should be the largest sector due to AAPL and MSFT
        tech_index = data['chart_data']['sectors'].index('Technology')
        self.assertEqual(max(data['chart_data']['values']), data['chart_data']['values'][tech_index])