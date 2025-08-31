"""
Base test classes and utility functions for all test suites
"""

from django.test import TestCase, TransactionTestCase, Client
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.messages import get_messages
from unittest.mock import patch, Mock
import tempfile
import shutil
import os
from PIL import Image
import io

from .factories import (
    UserFactory, StaffUserFactory, SuperUserFactory,
    ProfileFactory, create_test_image
)

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test class with common setup and utility methods"""
    
    def setUp(self):
        """Set up common test data"""
        self.client = Client()
        self.user = UserFactory()
        self.staff_user = StaffUserFactory()
        self.superuser = SuperUserFactory()
        
        # Create test media directory
        self.media_root = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test data"""
        # Remove test media directory
        if hasattr(self, 'media_root') and os.path.exists(self.media_root):
            shutil.rmtree(self.media_root)
    
    def login_user(self, user=None):
        """Login a user for testing"""
        if user is None:
            user = self.user
        
        login_successful = self.client.login(
            username=user.username, 
            password='testpass123'
        )
        self.assertTrue(login_successful)
        return user
    
    def login_staff_user(self):
        """Login a staff user for testing"""
        return self.login_user(self.staff_user)
    
    def login_superuser(self):
        """Login a superuser for testing"""
        return self.login_user(self.superuser)
    
    def logout_user(self):
        """Logout current user"""
        self.client.logout()
    
    def get_test_image_file(self, name='test_image.jpg', size=(100, 100)):
        """Create a test image file for upload testing"""
        image = Image.new('RGB', size, color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        return SimpleUploadedFile(
            name=name,
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    def assertContainsMessage(self, response, message_text, level=None):
        """Assert that response contains a specific message"""
        messages = list(get_messages(response.wsgi_request))
        message_contents = [str(m) for m in messages]
        
        if level:
            level_messages = [str(m) for m in messages if m.level == level]
            self.assertIn(message_text, level_messages)
        else:
            self.assertIn(message_text, message_contents)
    
    def assertRedirectsToLogin(self, response, next_url=None):
        """Assert that response redirects to login page"""
        if next_url:
            expected_url = f"{reverse('users:login')}?next={next_url}"
        else:
            expected_url = reverse('users:login')
        
        self.assertRedirects(response, expected_url)
    
    def assertFormHasError(self, response, form_name, field_name, error_message=None):
        """Assert that form has specific field error"""
        form = response.context.get(form_name)
        self.assertIsNotNone(form, f"Form '{form_name}' not found in context")
        self.assertIn(field_name, form.errors)
        
        if error_message:
            field_errors = form.errors[field_name]
            self.assertIn(error_message, field_errors)
    
    def create_user_with_profile(self, **kwargs):
        """Create a user with associated profile"""
        user = UserFactory(**kwargs)
        profile = ProfileFactory(user=user)
        return user, profile


class APITestCase(BaseTestCase):
    """Base class for API testing"""
    
    def setUp(self):
        super().setUp()
        self.api_client = Client()
        # Set up API authentication if needed
    
    def api_login(self, user=None):
        """Login user for API access"""
        if user is None:
            user = self.user
        
        # Add API authentication logic here if using DRF tokens
        return self.login_user(user)
    
    def assertJSONResponse(self, response, expected_status=200):
        """Assert that response is valid JSON with expected status"""
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def assertJSONContains(self, response, key, value=None):
        """Assert that JSON response contains specific key/value"""
        self.assertJSONResponse(response)
        data = response.json()
        
        if '.' in key:
            # Handle nested keys like 'user.name'
            keys = key.split('.')
            current = data
            for k in keys:
                self.assertIn(k, current)
                current = current[k]
            
            if value is not None:
                self.assertEqual(current, value)
        else:
            self.assertIn(key, data)
            if value is not None:
                self.assertEqual(data[key], value)


class EmailTestMixin:
    """Mixin for testing email functionality"""
    
    def setUp(self):
        super().setUp()
        # Use in-memory email backend for testing
        self.email_backend = 'django.core.mail.backends.locmem.EmailBackend'
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def assertEmailSent(self, subject=None, to=None, count=None):
        """Assert that email was sent with optional filters"""
        from django.core import mail
        
        if count is not None:
            self.assertEqual(len(mail.outbox), count)
        else:
            self.assertGreater(len(mail.outbox), 0)
        
        if subject or to:
            matching_emails = []
            for email in mail.outbox:
                if subject and subject not in email.subject:
                    continue
                if to and to not in email.to:
                    continue
                matching_emails.append(email)
            
            self.assertGreater(len(matching_emails), 0)
            return matching_emails[0]
        
        return mail.outbox[-1]


class FileTestMixin:
    """Mixin for testing file upload functionality"""
    
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def create_uploaded_file(self, name='test_file.txt', content=b'test content'):
        """Create a simple uploaded file for testing"""
        return SimpleUploadedFile(name, content)
    
    def create_image_file(self, name='test_image.jpg', size=(100, 100), format='JPEG'):
        """Create an image file for testing"""
        image = Image.new('RGB', size, color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        
        return SimpleUploadedFile(
            name=name,
            content=image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def assertFileExists(self, file_path):
        """Assert that file exists"""
        self.assertTrue(os.path.exists(file_path))
    
    def assertFileDoesNotExist(self, file_path):
        """Assert that file does not exist"""
        self.assertFalse(os.path.exists(file_path))


class MockTestMixin:
    """Mixin for mocking external services"""
    
    def mock_external_api(self, return_value=None, side_effect=None):
        """Mock external API calls"""
        mock_response = Mock()
        if return_value is not None:
            mock_response.json.return_value = return_value
        if side_effect is not None:
            mock_response.side_effect = side_effect
        
        return mock_response
    
    def mock_email_send(self):
        """Mock email sending"""
        return patch('django.core.mail.send_mail')
    
    def mock_file_storage(self):
        """Mock file storage operations"""
        return patch('django.core.files.storage.default_storage')


class PerformanceTestMixin:
    """Mixin for performance testing"""
    
    def assertQueryCountEqual(self, count):
        """Assert that a specific number of database queries are executed"""
        from django.test.utils import override_settings
        from django.db import connection
        
        @override_settings(DEBUG=True)
        def test_with_query_count():
            initial_queries = len(connection.queries)
            yield
            final_queries = len(connection.queries)
            query_count = final_queries - initial_queries
            self.assertEqual(query_count, count)
        
        return test_with_query_count()
    
    def assertMaxQueryCount(self, max_count):
        """Assert that no more than max_count queries are executed"""
        from django.test.utils import override_settings
        from django.db import connection
        
        @override_settings(DEBUG=True)
        def test_with_max_query_count():
            initial_queries = len(connection.queries)
            yield
            final_queries = len(connection.queries)
            query_count = final_queries - initial_queries
            self.assertLessEqual(query_count, max_count)
        
        return test_with_max_query_count()


class IntegrationTestCase(BaseTestCase, EmailTestMixin, FileTestMixin):
    """
    Base class for integration tests that test multiple components together
    """
    
    def setUp(self):
        super().setUp()
        # Set up integration test specific data
        self.setup_test_data()
    
    def setup_test_data(self):
        """Set up comprehensive test data for integration tests"""
        # Create users with profiles
        self.regular_user, self.regular_profile = self.create_user_with_profile()
        self.author_user, self.author_profile = self.create_user_with_profile()
        
        # Login regular user by default
        self.login_user(self.regular_user)
    
    def simulate_user_workflow(self, steps):
        """
        Simulate a complete user workflow
        steps should be a list of (method, url, data) tuples
        """
        responses = []
        for method, url, data in steps:
            if method.upper() == 'GET':
                response = self.client.get(url)
            elif method.upper() == 'POST':
                response = self.client.post(url, data)
            elif method.upper() == 'PUT':
                response = self.client.put(url, data)
            elif method.upper() == 'DELETE':
                response = self.client.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            responses.append(response)
        
        return responses


# Test data fixtures
TEST_USER_DATA = {
    'username': 'testuser',
    'email': 'test@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    'password': 'testpass123'
}

TEST_PROJECT_DATA = {
    'title': 'Test Project',
    'short_description': 'A test project for testing',
    'description': 'This is a comprehensive test project description.',
    'technologies': 'Python, Django, HTML, CSS',
    'status': 'completed',
    'is_published': True
}

TEST_BLOG_POST_DATA = {
    'title': 'Test Blog Post',
    'excerpt': 'This is a test blog post excerpt.',
    'content': 'This is the full content of the test blog post.',
    'status': 'published'
}

TEST_CONTACT_DATA = {
    'name': 'Test Contact',
    'email': 'contact@example.com',
    'subject': 'general',
    'message': 'This is a test contact message.'
}


def skip_if_no_db(test_func):
    """Decorator to skip tests if database is not available"""
    def wrapper(*args, **kwargs):
        from django.db import connection
        try:
            connection.ensure_connection()
            return test_func(*args, **kwargs)
        except Exception:
            import unittest
            raise unittest.SkipTest("Database not available")
    return wrapper


def override_media_root(test_func):
    """Decorator to override MEDIA_ROOT for tests"""
    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                return test_func(*args, **kwargs)
    return wrapper
