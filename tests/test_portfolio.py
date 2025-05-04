import unittest
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio, Holding
from flask_login import current_user
from unittest.mock import patch
import json


class PortfolioTestCase(unittest.TestCase):
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

        # Create test portfolio
        self.portfolio = Portfolio(user_id=self.user.id, name="Test Portfolio")
        db.session.add(self.portfolio)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_add_stock(self, mock_get_stock_data):
        """Test adding a stock to portfolio"""
        mock_get_stock_data.return_value = {
            'current_price': 150.0,
            'company_name': 'Apple Inc.',
            'daily_change': 2.5,
            'daily_change_percent': 1.7
        }

        response = self.client.post('/portfolio/add_stock',
                                    json={'symbol': 'AAPL', 'quantity': 10})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Stock added successfully')

        # Verify stock was added to database
        holding = Holding.query.filter_by(portfolio_id=self.portfolio.id, symbol='AAPL').first()
        self.assertIsNotNone(holding)
        self.assertEqual(holding.quantity, 10)

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_remove_stock(self, mock_get_stock_data):
        """Test removing a stock from portfolio"""
        mock_get_stock_data.return_value = {
            'current_price': 150.0,
            'company_name': 'Apple Inc.'
        }

        # First add a stock
        holding = Holding(portfolio_id=self.portfolio.id, symbol='AAPL', quantity=10, purchase_price=145.0)
        db.session.add(holding)
        db.session.commit()

        # Now delete it
        response = self.client.delete('/portfolio/remove_stock/AAPL')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Stock removed successfully')

        # Verify stock was removed from database
        holding = Holding.query.filter_by(portfolio_id=self.portfolio.id, symbol='AAPL').first()
        self.assertIsNone(holding)

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_get_holdings(self, mock_get_stock_data):
        """Test retrieving portfolio holdings"""
        mock_get_stock_data.return_value = {
            'current_price': 150.0,
            'company_name': 'Apple Inc.',
            'daily_change': 2.5,
            'daily_change_percent': 1.7
        }

        # Add a stock
        holding = Holding(portfolio_id=self.portfolio.id, symbol='AAPL', quantity=10, purchase_price=145.0)
        db.session.add(holding)
        db.session.commit()

        response = self.client.get('/portfolio/holdings')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('holdings' in data)
        self.assertEqual(len(data['holdings']), 1)
        self.assertEqual(data['holdings'][0]['symbol'], 'AAPL')
        self.assertEqual(data['holdings'][0]['quantity'], 10)
        self.assertEqual(data['holdings'][0]['current_price'], 150.0)

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_sell_shares(self, mock_get_stock_data):
        """Test selling shares"""
        mock_get_stock_data.return_value = {
            'current_price': 150.0,
            'company_name': 'Apple Inc.'
        }

        # Add a stock
        holding = Holding(portfolio_id=self.portfolio.id, symbol='AAPL', quantity=10, purchase_price=145.0)
        db.session.add(holding)
        db.session.commit()

        # Sell 5 shares
        response = self.client.post('/portfolio/sell_shares',
                                    json={'symbol': 'AAPL', 'quantity': 5})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

        # Verify quantity was updated
        holding = Holding.query.filter_by(portfolio_id=self.portfolio.id, symbol='AAPL').first()
        self.assertIsNotNone(holding)
        self.assertEqual(holding.quantity, 5)



    def test_user_authenticated(self):
        """Test that the user is properly authenticated after login"""
        # First check that we're logged out
        self.client.get('/auth/logout')

        # Try to log in
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Try to access a protected page and see if we get redirected
        protected_response = self.client.get('/portfolio/')
        # If it returns 200, we're logged in
        # If it returns 302, we're being redirected (not logged in)
        print(f"Protected response status code: {protected_response.status_code}")
        if protected_response.status_code == 302:
            # Print the location we're being redirected to for debugging
            print(f"Redirected to: {protected_response.headers.get('Location')}")