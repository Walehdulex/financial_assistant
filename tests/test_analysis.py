import unittest
from app import create_app, db
from app.models.user import User, UserSettings
from app.models.portfolio import Portfolio, Holding
from unittest.mock import patch
import json
import pandas as pd
import numpy as np


class AnalysisTestCase(unittest.TestCase):
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

        # Adding user settings
        user_settings = UserSettings(
            user_id=1,
            risk_tolerance='Moderate',
            investment_goal='Growth',
            time_horizon='Long-term'
        )
        db.session.add(user_settings)
        db.session.commit()

        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })

        # Creating test portfolio with holdings
        self.portfolio = Portfolio(user_id=self.user.id, name="Test Portfolio")
        db.session.add(self.portfolio)
        db.session.commit()

        # Adding test holdings
        holdings = [
            Holding(portfolio_id=self.portfolio.id, symbol='AAPL', quantity=10, purchase_price=145.0),
            Holding(portfolio_id=self.portfolio.id, symbol='MSFT', quantity=8, purchase_price=250.0)
        ]
        db.session.add_all(holdings)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.risk_service.RiskService.calculate_portfolio_risk')
    def test_risk_analysis(self, mock_calculate_risk):
        """Testing portfolio risk analysis"""
        mock_calculate_risk.return_value = {
            'volatility': 0.18,
            'sharpe_ratio': 0.75,
            'diversification_score': 0.65,
            'risk_level': 'Medium',
            'individual_stock_risks': {
                'AAPL': {'volatility': 0.2, 'risk_level': 'Medium'},
                'MSFT': {'volatility': 0.15, 'risk_level': 'Low'}
            }
        }

        response = self.client.get('/portfolio/risk_analysis')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['volatility'], 0.18)
        self.assertEqual(data['sharpe_ratio'], 0.75)
        self.assertEqual(data['diversification_score'], 0.65)
        self.assertEqual(data['risk_level'], 'Medium')

    @patch(
        'app.services.enhanced_recommendation_service.EnhancedRecommendationService.generate_enhanced_recommendations')
    def test_enhanced_recommendations(self, mock_recommendations):
        """Testing enhanced recommendation generation"""
        mock_recommendations.return_value = [
            {
                'type': 'diversification',
                'action': 'Increase Portfolio Diversification',
                'reasoning': 'Current diversification score is low',
                'priority': 'high'
            },
            {
                'type': 'sector',
                'action': 'Consider adding healthcare exposure',
                'reasoning': 'Healthcare sector is underrepresented in your portfolio',
                'priority': 'medium'
            }
        ]

        response = self.client.get('/portfolio/enhanced-recommendations')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('recommendations' in data)
        self.assertEqual(len(data['recommendations']), 2)
        self.assertEqual(data['recommendations'][0]['type'], 'diversification')
        self.assertEqual(data['recommendations'][1]['type'], 'sector')

    @patch('app.services.ml_service.MLService._get_historical_data')
    @patch('app.services.ml_service.MLService._generate_features')
    @patch('app.services.ml_service.MLService._predict_return')
    def test_forecasts(self, mock_predict, mock_features, mock_historical):
        """Testing stock price forecast generation"""
        # Mocking historical data
        mock_historical.return_value = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=100),
            'close': np.linspace(140, 160, 100)
        })

        # Mock features
        features_df = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=100),
            'close': np.linspace(140, 160, 100),
            'sma_5': np.linspace(142, 158, 100),
            'sma_20': np.linspace(145, 155, 100),
            'return_1d': np.random.normal(0.001, 0.02, 100),
            'return_5d': np.random.normal(0.005, 0.03, 100),
            'volatility': np.random.uniform(0.1, 0.2, 100),
            'rsi_14': np.random.uniform(30, 70, 100)
        })
        mock_features.return_value = features_df

        # Mocking the  prediction
        mock_predict.return_value = (0.05, 168.0, 0.7)  # (expected_return, target_price, confidence)

        response = self.client.get('/portfolio/forecasts')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('forecasts' in data)
        self.assertTrue('AAPL' in data['forecasts'])
        self.assertTrue('MSFT' in data['forecasts'])
        self.assertEqual(data['forecasts']['AAPL']['predicted_return'], 0.05)
        self.assertEqual(data['forecasts']['AAPL']['target_price'], 168.0)
        self.assertEqual(data['forecasts']['AAPL']['confidence'], 0.7)

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_get_holding_info(self, mock_get_stock_data):
        """Test getting holding info"""
        # Mock stock data
        mock_get_stock_data.return_value = {
            'current_price': 160.0,
            'company_name': 'Apple Inc.'
        }

        response = self.client.get('/portfolio/holding/AAPL')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('holding' in data)
        self.assertEqual(data['holding']['symbol'], 'AAPL')
        self.assertEqual(data['holding']['quantity'], 10)
        self.assertEqual(data['holding']['purchase_price'], 145.0)
        self.assertEqual(data['holding']['current_price'], 160.0)
        self.assertEqual(data['holding']['current_value'], 1600.0)