import unittest
from app import create_app, db


class MainTestCase(unittest.TestCase):
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

    def test_basic_access(self):
        """Test that we can access a basic route"""
        # Try to access the root route
        response = self.client.get('/')
        # Just check that it returns some response, don't check content yet
        self.assertIn(response.status_code, [200, 302])

    def test_auth_page_access(self):
        """Test that we can access the login page"""
        response = self.client.get('/auth/login')
        self.assertIn(response.status_code, [200, 302])

