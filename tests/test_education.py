import unittest
from unittest.mock import patch

from app import create_app, db
from app.models.user import User


class EducationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

        # Log in the user (if needed)
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_education_resources_page(self):
        """Test that education resources page loads correctly"""
        response = self.client.get('/education/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Learning Resources', response.data)
        self.assertIn(b'Welcome to the Education Center', response.data)

    def test_glossary_page(self):
        """Test that glossary page loads correctly"""
        response = self.client.get('/education/glossary')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Financial Glossary', response.data)
        self.assertIn(b'Search terms', response.data)

    def test_stocks_guide_page(self):
        """Test that stocks guide page loads correctly"""
        response = self.client.get('/education/guides/stocks')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Stocks Basics', response.data)
        self.assertIn(b'What is a Stock?', response.data)

    def test_investing_basics_guide_page(self):
        """Test that investing basics guide page loads correctly"""
        response = self.client.get('/education/guides/investing-basics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Investing Basics', response.data)
        self.assertIn(b'What is Investing?', response.data)


    def test_api_guides_endpoint(self):
        """Test the API endpoint for guides"""
        response = self.client.get('/education/api/guides')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'stocks', response.data)
        self.assertIn(b'Beginner', response.data)

    def test_api_guides_filtering(self):
        """Test filtering guides by level through API"""
        response = self.client.get('/education/api/guides?level=Intermediate')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'technical-analysis', response.data)
        self.assertIn(b'Intermediate', response.data)
        # Beginner guides should not be in filtered results
        self.assertNotIn(b'"level": "Beginner"', response.data)

    def test_guide_not_found_page(self):
        """Test that non-existent guide shows guide not found page"""
        response = self.client.get('/education/guides/nonexistent-guide')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Guide Not Found', response.data)
        self.assertIn(b'not currently available', response.data)

    def test_guide_list_rendering(self):
        """Test that all guides are properly listed on resources page"""
        response = self.client.get('/education/')
        self.assertEqual(response.status_code, 200)

        # Check for links to guides - adjust these to match what's actually in your HTML
        self.assertIn(b'Investing Basics', response.data)
        self.assertIn(b'Stock', response.data)  # More generic to match any mention of stocks
        self.assertIn(b'Bonds', response.data)
        self.assertIn(b'Diversification', response.data)

    def test_guide_content_structure(self):
        """Test that guide content has proper structure"""
        response = self.client.get('/education/guides/stocks')
        self.assertEqual(response.status_code, 200)

        # Check for expected sections
        self.assertIn(b'What is a Stock?', response.data)
        self.assertIn(b'How Stock Markets Work', response.data)
        self.assertIn(b'Types of Stocks', response.data)

