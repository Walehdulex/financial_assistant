import unittest
from app import create_app, db
from app.models.user import User, UserSettings
import json


class SettingsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()

        # Creating and login test user
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

    def test_get_user_preferences(self):
        """Test getting user preferences"""
        # Adding test settings
        settings = UserSettings(
            user_id=self.user.id,
            risk_tolerance='Moderate',
            default_chart_period='1y',
            enable_notifications=False,
            investment_goal='Growth',
            time_horizon='Long-term',
            preferred_sectors='Technology,Healthcare',
            tax_consideration=True
        )
        db.session.add(settings)
        db.session.commit()

        response = self.client.get('/settings/preferences')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['risk_tolerance'], 'Moderate')
        self.assertEqual(data['default_chart_period'], '1y')
        self.assertEqual(data['investment_goal'], 'Growth')
        self.assertEqual(data['time_horizon'], 'Long-term')
        self.assertEqual(data['preferred_sectors'], 'Technology,Healthcare')
        self.assertTrue(data['tax_consideration'])

    def test_update_user_preferences(self):
        """Testing the  updating user preferences"""
        new_settings = {
            'risk_tolerance': 'Aggressive',
            'default_chart_period': '6m',
            'enable_notifications': True,
            'investment_goal': 'Income',
            'time_horizon': 'Medium-term',
            'preferred_sectors': 'Financials,Energy',
            'preferred_assets': 'Stocks,ETFs',
            'tax_consideration': True
        }

        response = self.client.post('/settings/preferences',
                                    json=new_settings)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verifying settings were updated in database
        settings = UserSettings.query.filter_by(user_id=self.user.id).first()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.risk_tolerance, 'Aggressive')
        self.assertEqual(settings.default_chart_period, '6m')
        self.assertTrue(settings.enable_notifications)
        self.assertEqual(settings.investment_goal, 'Income')
        self.assertEqual(settings.time_horizon, 'Medium-term')
        self.assertEqual(settings.preferred_sectors, 'Financials,Energy')




