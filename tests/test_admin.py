import unittest
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio, Holding
from datetime import datetime, timedelta
import json


class AdminTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()

        # Creating admin user
        self.admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        self.admin.set_password('admin123')

        # Creating regular user
        self.user = User(
            username='testuser',
            email='test@example.com',
            is_admin=False
        )
        self.user.set_password('password123')

        db.session.add_all([self.admin, self.user])
        db.session.commit()

        # Login as admin
        self.client.post('/auth/login', data={
            'email': 'admin@example.com',
            'password': 'admin123'
        })

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()



    def test_user_list(self):
        """Testing viewing user list"""
        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'admin@example.com' in response.data)
        self.assertTrue(b'test@example.com' in response.data)

    def test_add_user(self):
        """Testing adding a new user through admin panel"""
        new_user = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword',
            'is_admin': False
        }

        response = self.client.post('/admin/users/add',
                                    json=new_user)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verifying user was added
        user = User.query.filter_by(email='new@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newuser')

    def test_edit_user(self):
        """Testing editing a user through admin panel"""
        response = self.client.post(f'/admin/users/edit/{self.user.id}', data={
            'username': 'updateduser',
            'email': 'updated@example.com',
            'is_admin': 'true'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Verifying user was updated
        user = User.query.get(self.user.id)
        self.assertEqual(user.username, 'updateduser')
        self.assertEqual(user.email, 'updated@example.com')
        self.assertTrue(user.is_admin)

    def test_delete_user(self):
        """Test deleting a user through admin panel"""
        response = self.client.post(f'/admin/users/delete/{self.user.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verifying user was deleted
        user = User.query.get(self.user.id)
        self.assertIsNone(user)

    def test_non_admin_access_denied(self):
        """Test non-admin cannot access admin area"""
        # Logout admin
        self.client.get('/auth/logout')

        # trying to Login  as regular user
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })

        # Trying to access admin area
        response = self.client.get('/admin/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'You do not have permission to access this page' in response.data)

    def test_make_admin(self):
        """Test making a user an admin"""
        response = self.client.get(f'/admin/make-admin/{self.user.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check if user is now an admin
        user = User.query.get(self.user.id)
        self.assertTrue(user.is_admin)



    def test_recommendation_stats(self):
        """Test recommendation statistics page"""
        # Add some recommendation feedback
        from app.models.recommendation import RecommendationFeedback
        feedbacks = [
            RecommendationFeedback(
                user_id=self.user.id,
                recommendation_type='Buy',
                recommendation_action='Buy AAPL',
                rating=4,
                was_followed=True
            ),
            RecommendationFeedback(
                user_id=self.user.id,
                recommendation_type='Sell',
                recommendation_action='Sell MSFT',
                rating=3,
                was_followed=False
            )
        ]
        db.session.add_all(feedbacks)
        db.session.commit()

        response = self.client.get('/admin/recommendation-stats')
        self.assertEqual(response.status_code, 200)
        # Check for content that would be on the recommendation stats page
        self.assertTrue(b'Recommendation' in response.data)

    def test_fix_dates(self):
        """Test fixing user dates"""
        # Create a user with a null created_at date
        user = User(username='nulldate', email='null@example.com')
        user.set_password('password')
        user.created_at = None
        db.session.add(user)
        db.session.commit()

        response = self.client.get('/admin/fix-dates')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Fixed' in response.data)

        # Check if date was fixed
        user = User.query.filter_by(email='null@example.com').first()
        self.assertIsNotNone(user.created_at)

    def test_admin_status(self):
        """Test admin status check page"""
        response = self.client.get('/admin/admin-status')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Admin Status Check' in response.data)
        self.assertTrue(b'Is Admin: True' in response.data)