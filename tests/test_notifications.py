import unittest
from app import create_app, db
from app.models.user import User
from app.models.notification import Notification  # Assuming you have this model
from app.services.notification_service import NotificationService  # Assuming you have this service
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta


class NotificationTestCase(unittest.TestCase):
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

        # Initialize notification service
        self.notification_service = NotificationService()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_notification(self):
        """Test creating a notification"""
        # Create a notification for the user
        notification = Notification(
            user_id=self.user.id,
            title="Test Notification",
            message="This is a test notification",
            notification_type="info",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()

        # Verify notification was created
        notifications = Notification.query.filter_by(user_id=self.user.id).all()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].title, "Test Notification")
        self.assertEqual(notifications[0].message, "This is a test notification")
        self.assertEqual(notifications[0].notification_type, "info")
        self.assertFalse(notifications[0].is_read)

    def test_get_user_notifications(self):
        """Test getting a user's notifications"""
        # Create multiple notifications
        notifications = [
            Notification(
                user_id=self.user.id,
                title="Notification 1",
                message="First notification",
                notification_type="info",
                is_read=False
            ),
            Notification(
                user_id=self.user.id,
                title="Notification 2",
                message="Second notification",
                notification_type="alert",
                is_read=False
            )
        ]
        db.session.add_all(notifications)
        db.session.commit()

        # Get user notifications via API
        response = self.client.get('/notifications')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify returned data
        self.assertTrue('notifications' in data)
        self.assertEqual(len(data['notifications']), 2)
        self.assertEqual(data['notifications'][0]['title'], "Notification 1")
        self.assertEqual(data['notifications'][1]['title'], "Notification 2")

    def test_mark_notification_as_read(self):
        """Test marking a notification as read"""
        # Create a notification
        notification = Notification(
            user_id=self.user.id,
            title="Test Notification",
            message="This is a test notification",
            notification_type="info",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()

        # Mark notification as read
        response = self.client.post(f'/notifications/mark_read/{notification.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify notification is marked as read
        updated_notification = Notification.query.get(notification.id)
        self.assertTrue(updated_notification.is_read)

    @patch('app.services.notification_service.NotificationService.send_email_notification')
    def test_send_email_notification(self, mock_send_email):
        """Test sending email notifications"""
        # Mock email sending
        mock_send_email.return_value = True

        # Call notification service to send email
        result = self.notification_service.send_email_notification(
            user_id=self.user.id,
            subject="Important Alert",
            body="Your portfolio has increased by 5%"
        )

        # Verify email was sent
        self.assertTrue(result)
        mock_send_email.assert_called_once()

    @patch('app.services.market_service.MarketService.get_stock_data')
    def test_price_alert_notification(self, mock_get_stock_data):
        """Test price alert notifications"""
        # Mock price data
        mock_get_stock_data.return_value = {
            'current_price': 175.0,  # Price above threshold
            'company_name': 'Apple Inc.'
        }

        # Set up a price alert (assuming you have this functionality)
        response = self.client.post('/alerts/add', json={
            'symbol': 'AAPL',
            'price_threshold': 170.0,
            'alert_type': 'above'
        })
        self.assertEqual(response.status_code, 200)

        # Trigger alert check (this would typically be a background job)
        response = self.client.get('/alerts/check')
        self.assertEqual(response.status_code, 200)

        # Verify notification was created
        notifications = Notification.query.filter_by(user_id=self.user.id).all()
        self.assertGreaterEqual(len(notifications), 1)
        self.assertIn('AAPL', notifications[0].message)
        self.assertIn('above', notifications[0].message)