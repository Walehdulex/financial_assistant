import json

import unittest
from unittest.mock import patch

from app import db, create_app
from app.models.portfolio import Portfolio, Holding
from app.models.user import User


class PerformanceTestCase(unittest.TestCase):
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
        })

        # Create test portfolio
        self.portfolio = Portfolio(user_id=self.user.id, name="Test Portfolio")
        db.session.add(self.portfolio)
        db.session.commit()

        # Add holdings
        holding = Holding(portfolio_id=self.portfolio.id, symbol='AAPL', quantity=10, purchase_price=145.0)
        db.session.add(holding)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_get_performance(self, mock_get_stock_data):
        """Test getting portfolio performance"""
        mock_get_stock_data.return_value = {
            'current_price': 160.0,
            'daily_change': 2.5,
            'daily_change_percent': 1.59
        }

        response = self.client.get('/portfolio/performance')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('holdings' in data)
        self.assertTrue('total_value' in data)
        self.assertTrue('total_cost' in data)
        self.assertTrue('total_return' in data)
        self.assertTrue('total_return_percentage' in data)

        # AAPL: 10 shares purchased at $145, now worth $160
        self.assertEqual(float(data['total_value']), 1600.0)
        self.assertEqual(float(data['total_cost']), 1450.0)
        self.assertEqual(float(data['total_return']), 150.0)
        self.assertAlmostEqual(float(data['total_return_percentage']), 10.34, places=1)

    @patch('app.services.history_service.HistoryService.get_portfolio_history')
    @patch('app.services.history_service.HistoryService.record_portfolio_value')
    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_get_historical_performance(self, mock_get_stock_data, mock_record, mock_get_history):
        """Test getting historical portfolio performance"""
        from app.models.portfolio import PortfolioHistory
        from datetime import datetime, timedelta

        # Mock current stock data
        mock_get_stock_data.return_value = {
            'current_price': 160.0,
            'daily_change': 2.5,
            'daily_change_percent': 1.59
        }

        # Mock recording current value
        mock_record.return_value = 1600.0

        # Create historical data
        today = datetime.now().date()
        history = [
            PortfolioHistory(portfolio_id=self.portfolio.id, date=today - timedelta(days=3), total_value=1450.0),
            PortfolioHistory(portfolio_id=self.portfolio.id, date=today - timedelta(days=2), total_value=1500.0),
            PortfolioHistory(portfolio_id=self.portfolio.id, date=today - timedelta(days=1), total_value=1550.0),
            PortfolioHistory(portfolio_id=self.portfolio.id, date=today, total_value=1600.0)
        ]
        mock_get_history.return_value = history

        response = self.client.get('/portfolio/historical_performance')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('dates' in data)
        self.assertTrue('values' in data)
        self.assertTrue('returns' in data)
        self.assertEqual(len(data['dates']), 4)
        self.assertEqual(len(data['values']), 4)
        self.assertEqual(len(data['returns']), 4)
        self.assertEqual(data['values'][0], 1450.0)
        self.assertEqual(data['values'][-1], 1600.0)
        self.assertEqual(data['current_value'], 1600.0)
        self.assertEqual(data['initial_value'], 1450.0)
        self.assertAlmostEqual(data['total_return'], 10.34, places=1)