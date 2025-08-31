"""
Tests for Users app views
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from unittest.mock import patch, Mock

from core.test_utils import BaseTestCase, EmailTestMixin, FileTestMixin, IntegrationTestCase
from core.factories import UserFactory, ProfileFactory

User = get_user_model()


class RegisterViewTests(BaseTestCase):
    """Test cases for user registration view"""

    def setUp(self):
        super().setUp()
        self.register_url = reverse('users:register')

    def test_register_view_get(self):
        """Test GET request to registration page"""
        response = self.client.get(self.register_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'register')  # Assuming template contains 'register'
        self.assertIn('form', response.context)

    def test_register_view_post_valid_data(self):
        """Test POST request with valid registration data"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        response = self.client.post(self.register_url, data=form_data)
        
        # Should redirect to login after successful registration
        self.assertRedirects(response, reverse('users:login'))
        
        # User should be created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        
        # Success message should be displayed
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.username, 'newuser')

    def test_register_view_post_invalid_data(self):
        """Test POST request with invalid registration data"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',  # Invalid email
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'differentpassword123'  # Mismatched password
        }
        
        response = self.client.post(self.register_url, data=form_data)
        
        # Should not redirect, should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'Enter a valid email address.')

    def test_register_view_authenticated_user_redirect(self):
        """Test that authenticated users are redirected away from registration"""
        user = self.login_user()
        
        response = self.client.get(self.register_url)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('portfolio:home'))

    def test_register_view_creates_profile(self):
        """Test that registration creates associated profile"""
        form_data = {
            'username': 'profileuser',
            'email': 'profile@example.com',
            'first_name': 'Profile',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        response = self.client.post(self.register_url, data=form_data)
        
        user = User.objects.get(email='profile@example.com')
        self.assertTrue(hasattr(user, 'profile'))


class LoginViewTests(BaseTestCase):
    """Test cases for user login view"""

    def setUp(self):
        super().setUp()
        self.login_url = reverse('users:login')
        self.test_user = UserFactory(email='login@example.com')

    def test_login_view_get(self):
        """Test GET request to login page"""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_login_view_post_valid_credentials(self):
        """Test POST request with valid login credentials"""
        form_data = {
            'email': 'login@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data=form_data)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('portfolio:home'))
        
        # User should be logged in
        user = User.objects.get(email='login@example.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_login_view_post_invalid_credentials(self):
        """Test POST request with invalid login credentials"""
        form_data = {
            'email': 'login@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, data=form_data)
        
        # Should not redirect, should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'Invalid email or password.')

    def test_login_view_with_next_parameter(self):
        """Test login redirect with next parameter"""
        next_url = reverse('users:dashboard')
        login_url = f"{self.login_url}?next={next_url}"
        
        form_data = {
            'email': 'login@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(login_url, data=form_data)
        
        # Should redirect to next URL
        self.assertRedirects(response, next_url)

    def test_login_view_authenticated_user_redirect(self):
        """Test that authenticated users are redirected away from login"""
        self.login_user(self.test_user)
        
        response = self.client.get(self.login_url)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('portfolio:home'))


class LogoutViewTests(BaseTestCase):
    """Test cases for user logout view"""

    def setUp(self):
        super().setUp()
        self.logout_url = reverse('users:logout')

    def test_logout_view(self):
        """Test user logout"""
        # Login user first
        user = self.login_user()
        
        # Verify user is logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        
        response = self.client.get(self.logout_url)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('portfolio:home'))
        
        # User should be logged out
        self.assertNotIn('_auth_user_id', self.client.session)


class ProfileViewTests(BaseTestCase):
    """Test cases for profile view"""

    def setUp(self):
        super().setUp()
        self.profile_url = reverse('users:profile')

    def test_profile_view_own_profile(self):
        """Test viewing own profile"""
        user = self.login_user()
        profile = ProfileFactory(user=user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_user', response.context)
        self.assertIn('profile', response.context)
        self.assertTrue(response.context['is_own_profile'])

    def test_profile_view_other_user_profile(self):
        """Test viewing another user's profile"""
        other_user = UserFactory()
        ProfileFactory(user=other_user)
        self.login_user()  # Login different user
        
        profile_url = reverse('users:profile_detail', kwargs={'username': other_user.username})
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile_user'], other_user)
        self.assertFalse(response.context['is_own_profile'])

    def test_profile_view_nonexistent_user(self):
        """Test viewing profile of nonexistent user"""
        self.login_user()
        
        profile_url = reverse('users:profile_detail', kwargs={'username': 'nonexistent'})
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, 404)

    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(self.profile_url)
        
        self.assertRedirectsToLogin(response, self.profile_url)

    def test_profile_view_creates_profile_if_not_exists(self):
        """Test that profile is created if it doesn't exist"""
        user = self.login_user()
        
        # Ensure profile doesn't exist
        if hasattr(user, 'profile'):
            user.profile.delete()
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        # Profile should be created
        user.refresh_from_db()
        self.assertTrue(hasattr(user, 'profile'))


class EditProfileViewTests(BaseTestCase, FileTestMixin):
    """Test cases for edit profile view"""

    def setUp(self):
        super().setUp()
        self.edit_profile_url = reverse('users:edit_profile')

    def test_edit_profile_view_get(self):
        """Test GET request to edit profile page"""
        user = self.login_user()
        profile = ProfileFactory(user=user)
        
        response = self.client.get(self.edit_profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)

    def test_edit_profile_view_post_valid_data(self):
        """Test POST request with valid profile data"""
        user = self.login_user()
        profile = ProfileFactory(user=user)
        
        form_data = {
            'username': user.username,
            'email': user.email,
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio',
            'phone': '+1234567890',
            'company': 'New Company',
            'position': 'New Position',
            'skills': 'Python, Django',
            'is_available_for_hire': True,
            'hourly_rate': '150.00'
        }
        
        response = self.client.post(self.edit_profile_url, data=form_data)
        
        # Should redirect to profile page
        self.assertRedirects(response, reverse('users:profile'))
        
        # Data should be updated
        user.refresh_from_db()
        profile.refresh_from_db()
        
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
        self.assertEqual(user.bio, 'Updated bio')
        self.assertEqual(profile.phone, '+1234567890')
        self.assertEqual(profile.company, 'New Company')

    def test_edit_profile_view_post_invalid_data(self):
        """Test POST request with invalid profile data"""
        user = self.login_user()
        ProfileFactory(user=user)
        
        form_data = {
            'username': '',  # Invalid: empty username
            'email': 'invalid-email',  # Invalid email
            'first_name': '',  # Invalid: empty first name
            'last_name': '',  # Invalid: empty last name
        }
        
        response = self.client.post(self.edit_profile_url, data=form_data)
        
        # Should not redirect, should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormHasError(response, 'user_form', 'username')
        self.assertFormHasError(response, 'user_form', 'email')

    def test_edit_profile_view_with_file_upload(self):
        """Test editing profile with file uploads"""
        user = self.login_user()
        profile = ProfileFactory(user=user)
        
        profile_image = self.create_image_file('new_profile.jpg')
        resume_file = self.create_uploaded_file('new_resume.pdf', b'resume content')
        
        form_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_available_for_hire': True,
        }
        
        file_data = {
            'profile_picture': profile_image,
            'resume': resume_file
        }
        
        response = self.client.post(
            self.edit_profile_url, 
            data=form_data, 
            files=file_data
        )
        
        self.assertRedirects(response, reverse('users:profile'))

    def test_edit_profile_view_requires_login(self):
        """Test that edit profile view requires authentication"""
        response = self.client.get(self.edit_profile_url)
        
        self.assertRedirectsToLogin(response, self.edit_profile_url)

    def test_edit_profile_view_creates_profile_if_not_exists(self):
        """Test that profile is created if it doesn't exist"""
        user = self.login_user()
        
        # Ensure profile doesn't exist
        if hasattr(user, 'profile'):
            user.profile.delete()
        
        response = self.client.get(self.edit_profile_url)
        
        self.assertEqual(response.status_code, 200)
        # Profile should be created
        user.refresh_from_db()
        self.assertTrue(hasattr(user, 'profile'))


class DashboardViewTests(BaseTestCase):
    """Test cases for user dashboard view"""

    def setUp(self):
        super().setUp()
        self.dashboard_url = reverse('users:dashboard')

    def test_dashboard_view_get(self):
        """Test GET request to dashboard page"""
        user = self.login_user()
        profile = ProfileFactory(user=user)
        
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile', response.context)
        self.assertIn('recent_projects', response.context)
        self.assertIn('recent_posts', response.context)

    def test_dashboard_view_requires_login(self):
        """Test that dashboard view requires authentication"""
        response = self.client.get(self.dashboard_url)
        
        self.assertRedirectsToLogin(response, self.dashboard_url)

    def test_dashboard_view_with_projects_and_posts(self):
        """Test dashboard view when user has projects and posts"""
        user = self.login_user()
        ProfileFactory(user=user)
        
        # Create some projects and posts for the user
        # This depends on your models - adjust as needed
        from core.factories import ProjectFactory, PostFactory
        
        projects = [ProjectFactory(user=user) for _ in range(3)]
        posts = [PostFactory(author=user) for _ in range(3)]
        
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        # Should show recent projects and posts
        self.assertTrue(len(response.context['recent_projects']) <= 5)
        self.assertTrue(len(response.context['recent_posts']) <= 5)


class UserListViewTests(BaseTestCase):
    """Test cases for user list view"""

    def setUp(self):
        super().setUp()
        self.user_list_url = reverse('users:user_list')

    def test_user_list_view_get(self):
        """Test GET request to user list page"""
        # Create some users
        users = [UserFactory() for _ in range(5)]
        
        response = self.client.get(self.user_list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertTrue(len(response.context['page_obj']) <= 12)  # Paginated

    def test_user_list_view_search(self):
        """Test user list with search query"""
        # Create users with specific names
        user1 = UserFactory(first_name='John', last_name='Doe')
        user2 = UserFactory(first_name='Jane', last_name='Smith')
        user3 = UserFactory(first_name='Bob', last_name='Johnson')
        
        # Search for 'John'
        response = self.client.get(self.user_list_url, {'q': 'John'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('query', response.context)
        self.assertEqual(response.context['query'], 'John')
        
        # Should contain users matching 'John'
        page_obj = response.context['page_obj']
        user_names = [f"{u.first_name} {u.last_name}" for u in page_obj]
        self.assertIn('John Doe', user_names)
        self.assertIn('Bob Johnson', user_names)  # Contains 'John' in last name

    def test_user_list_view_pagination(self):
        """Test user list pagination"""
        # Create more users than page size (12)
        users = [UserFactory() for _ in range(15)]
        
        response = self.client.get(self.user_list_url)
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should show first page with 12 users
        self.assertEqual(len(page_obj), 12)
        self.assertTrue(page_obj.has_next())
        
        # Test second page
        response = self.client.get(self.user_list_url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 3)  # Remaining users


class UserViewIntegrationTests(IntegrationTestCase):
    """Integration tests for user views working together"""

    def test_complete_user_registration_and_profile_setup(self):
        """Test complete workflow from registration to profile setup"""
        # Step 1: Register new user
        registration_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'first_name': 'Integration',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        response = self.client.post(reverse('users:register'), data=registration_data)
        self.assertRedirects(response, reverse('users:login'))
        
        # Step 2: Login
        login_data = {
            'email': 'integration@example.com',
            'password': 'complexpassword123'
        }
        
        response = self.client.post(reverse('users:login'), data=login_data)
        self.assertRedirects(response, reverse('portfolio:home'))
        
        # Step 3: Access dashboard
        response = self.client.get(reverse('users:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Edit profile
        profile_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'first_name': 'Integration',
            'last_name': 'User',
            'bio': 'This is my bio',
            'company': 'Test Company',
            'position': 'Developer',
            'skills': 'Python, Django, JavaScript',
            'is_available_for_hire': True
        }
        
        response = self.client.post(reverse('users:edit_profile'), data=profile_data)
        self.assertRedirects(response, reverse('users:profile'))
        
        # Step 5: View updated profile
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This is my bio')
        self.assertContains(response, 'Test Company')

    def test_user_profile_visibility_workflow(self):
        """Test user profile visibility for different users"""
        # Create two users
        user1 = UserFactory(username='user1')
        user2 = UserFactory(username='user2')
        ProfileFactory(user=user1, company='Company 1')
        ProfileFactory(user=user2, company='Company 2')
        
        # Login as user1
        self.login_user(user1)
        
        # View own profile
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Company 1')
        self.assertTrue(response.context['is_own_profile'])
        
        # View other user's profile
        response = self.client.get(
            reverse('users:profile_detail', kwargs={'username': 'user2'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Company 2')
        self.assertFalse(response.context['is_own_profile'])

    def test_authentication_flow_with_redirects(self):
        """Test authentication flow with proper redirects"""
        # Try to access protected page without login
        dashboard_url = reverse('users:dashboard')
        response = self.client.get(dashboard_url)
        
        # Should redirect to login with next parameter
        login_url = reverse('users:login')
        expected_redirect = f"{login_url}?next={dashboard_url}"
        self.assertRedirects(response, expected_redirect)
        
        # Login with next parameter
        user = UserFactory()
        login_data = {
            'email': user.email,
            'password': 'testpass123'
        }
        
        response = self.client.post(expected_redirect, data=login_data)
        
        # Should redirect to originally requested page
        self.assertRedirects(response, dashboard_url)
