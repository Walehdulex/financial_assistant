import unittest
from unittest.mock import patch

from app import create_app, db
from app.models.user import User


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        self.assertTrue('Registration successful' in response.get_data(as_text=True))

    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        # Create a user first
        user = User(username='existinguser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Attempt to register with the same email
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'newpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Email already registered' in response.get_data(as_text=True))

    def test_register_duplicate_username(self):
        """Test registration with existing username"""
        # Create a user first
        user = User(username='testuser', email='existing@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Attempt to register with the same username
        response = self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'new@example.com',
            'password': 'newpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Username already registered' in response.get_data(as_text=True))

    def test_login_success(self):
        """Test successful login"""
        # Create a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Login
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        # Check if we are redirected to dashboard
        self.assertTrue('/portfolio/dashboard' in response.request.url)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Login with wrong password
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Invalid email or password' in response.get_data(as_text=True))

    def test_login_nonexistent_user(self):
        """Test login with email that doesn't exist"""
        response = self.client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Invalid email or password' in response.get_data(as_text=True))

    def test_logout(self):
        """Test user logout"""
        # Create and login a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })

        # Logout
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check we are redirected to login page
        self.assertTrue('/auth/login' in response.request.url)

    @patch('app.routes.auth_routes.mail.send')
    def test_forgot_password(self, mock_send):
        """Test forgot password functionality"""
        # Create a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Send forgot password request

        response = self.client.post('/auth/forgot', data={
            'email': 'test@example.com'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('A password reset link has been sent' in response.get_data(as_text=True))
        self.assertTrue(mock_send.called)

    def test_forgot_password_invalid_email(self):
        """Test forgot password with invalid email"""
        response = self.client.post('/auth/forgot', data={
            'email': 'nonexistent@example.com'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('No account with that email exists' in response.get_data(as_text=True))

    #testing token validation
    def test_reset_password(self):
        """Test password reset functionality"""

        from app.utils import generate_reset_token

        # Create a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('oldpassword')
        db.session.add(user)
        db.session.commit()

        # Generate token
        token = generate_reset_token(user.email)

        # Reset password
        response = self.client.post(f'/auth/reset/{token}', data={
            'password': 'newpassword',
            'confirm_password': 'newpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your password has been updated' in response.get_data(as_text=True))

        # Verify new password works
        user = User.query.filter_by(email='test@example.com').first()
        self.assertTrue(user.check_password('newpassword'))

    def test_protected_route_redirect(self):
        """Test that protected routes redirect to login when not authenticated"""
        # Try to access a protected route
        response = self.client.get('/portfolio/dashboard', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('/auth/login' in response.request.url)
        self.assertTrue('Please log in to access this page' in response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()