import unittest
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio, Holding
from app.services.risk_service import RiskService
from app.services.market_service import MarketService
from unittest.mock import patch, MagicMock
import json


class RiskServiceTestCase(unittest.TestCase):
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

        # Create test portfolio with diverse holdings
        self.portfolio = Portfolio(user_id=self.user.id, name="Test Portfolio")
        db.session.add(self.portfolio)
        db.session.commit()

        # Add holdings from different sectors
        holdings = [
            Holding(portfolio_id=self.portfolio.id, symbol='AAPL', quantity=10, purchase_price=145.0),  # Tech
            Holding(portfolio_id=self.portfolio.id, symbol='JPM', quantity=5, purchase_price=140.0),  # Financial
            Holding(portfolio_id=self.portfolio.id, symbol='PFE', quantity=15, purchase_price=45.0),  # Healthcare
            Holding(portfolio_id=self.portfolio.id, symbol='XOM', quantity=12, purchase_price=60.0)  # Energy
        ]
        db.session.add_all(holdings)
        db.session.commit()

        # Initialize the market service (without api_key)
        self.market_service = MarketService()

        # Initialize the risk service with the market service
        self.risk_service = RiskService(market_service=self.market_service)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_calculate_portfolio_risk(self, mock_get_stock_data):
        """Test calculating portfolio risk with diversified portfolio"""

        # Mock stock data with different volatilities
        def get_stock_mock(symbol):
            stock_data = {
                'AAPL': {'current_price': 160.0, 'volatility': 0.25},
                'JPM': {'current_price': 150.0, 'volatility': 0.20},
                'PFE': {'current_price': 50.0, 'volatility': 0.15},
                'XOM': {'current_price': 65.0, 'volatility': 0.22}
            }
            return stock_data.get(symbol, {})

        mock_get_stock_data.side_effect = get_stock_mock

        # Calculate risk
        risk_data = self.risk_service.calculate_portfolio_risk(self.portfolio)

        # Verify risk data structure
        self.assertIn('volatility', risk_data)
        self.assertIn('diversification_score', risk_data)
        self.assertIn('risk_level', risk_data)
        self.assertIn('individual_stock_risks', risk_data)

        # Check that we have risk data for each stock
        for symbol in ['AAPL', 'JPM', 'PFE', 'XOM']:
            self.assertIn(symbol, risk_data['individual_stock_risks'])

        # Ensure diversification score is reasonable (diversified portfolio)
        self.assertGreater(risk_data['diversification_score'], 0.5)

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_calculate_single_stock_risk(self, mock_get_stock_data):
        """Test calculating portfolio risk with only one stock (no diversification)"""
        # Clear existing holdings
        db.session.query(Holding).delete()
        db.session.commit()

        # Add only one holding
        holding = Holding(portfolio_id=self.portfolio.id, symbol='TSLA', quantity=5, purchase_price=220.0)
        db.session.add(holding)
        db.session.commit()

        # Mock stock data
        mock_get_stock_data.return_value = {
            'current_price': 250.0,
            'volatility': 0.35  # High volatility
        }

        # Calculate risk
        risk_data = self.risk_service.calculate_portfolio_risk(self.portfolio)

        # A single-stock portfolio should have poor diversification
        self.assertLess(risk_data['diversification_score'], 0.3)

        # Risk level should be high for a volatile stock
        self.assertEqual(risk_data['risk_level'], 'High')

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_calculate_empty_portfolio_risk(self, mock_get_stock_data):
        """Test calculating risk for an empty portfolio"""
        # Clear existing holdings
        db.session.query(Holding).delete()
        db.session.commit()

        # Calculate risk for empty portfolio
        risk_data = self.risk_service.calculate_portfolio_risk(self.portfolio)

        # Check default values for empty portfolio
        self.assertEqual(risk_data['volatility'], 0)
        self.assertEqual(risk_data['diversification_score'], 0)
        self.assertEqual(risk_data['risk_level'], 'N/A')
        self.assertEqual(risk_data['individual_stock_risks'], {})