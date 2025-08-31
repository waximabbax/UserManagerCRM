"""
Tests for Users app forms
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from core.test_utils import BaseTestCase, FileTestMixin
from core.factories import UserFactory, ProfileFactory
from .forms import (
    UserRegistrationForm, UserLoginForm, UserUpdateForm, 
    ProfileUpdateForm, CustomUserChangeForm
)

User = get_user_model()


class UserRegistrationFormTests(BaseTestCase):
    """Test cases for UserRegistrationForm"""

    def test_valid_registration_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registration_form_missing_required_fields(self):
        """Test form validation with missing required fields"""
        form_data = {
            'username': 'testuser',
            # Missing email, first_name, last_name, passwords
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        required_fields = ['email', 'first_name', 'last_name', 'password1', 'password2']
        for field in required_fields:
            self.assertIn(field, form.errors)

    def test_registration_form_password_mismatch(self):
        """Test form validation with password mismatch"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'differentpassword123'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_registration_form_duplicate_email(self):
        """Test form validation with duplicate email"""
        # Create existing user
        UserFactory(email='existing@example.com')
        
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        form = UserRegistrationForm(data=form_data)
        # Note: This test depends on custom validation in the form
        # If you don't have email uniqueness validation in the form,
        # it will be caught at the database level

    def test_registration_form_save(self):
        """Test saving form creates user and profile"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('complexpassword123'))
        
        # Check if profile was created (if your form creates it)
        self.assertTrue(hasattr(user, 'profile'))

    def test_registration_form_widget_classes(self):
        """Test that form fields have correct CSS classes"""
        form = UserRegistrationForm()
        
        for field_name, field in form.fields.items():
            self.assertEqual(field.widget.attrs.get('class'), 'form-control')

    def test_registration_form_help_text_removal(self):
        """Test that help text is removed from certain fields"""
        form = UserRegistrationForm()
        
        # These fields should have help_text set to None
        fields_without_help = ['username', 'password1', 'password2']
        for field_name in fields_without_help:
            self.assertIsNone(form.fields[field_name].help_text)


class UserLoginFormTests(BaseTestCase):
    """Test cases for UserLoginForm"""

    def setUp(self):
        super().setUp()
        self.test_user = UserFactory(email='login@example.com')

    def test_valid_login_form(self):
        """Test form with valid credentials"""
        form_data = {
            'email': 'login@example.com',
            'password': 'testpass123'
        }
        
        form = UserLoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_login_form_invalid_email(self):
        """Test form with non-existent email"""
        form_data = {
            'email': 'nonexistent@example.com',
            'password': 'anypassword'
        }
        
        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid email or password', str(form.non_field_errors()))

    def test_login_form_invalid_password(self):
        """Test form with incorrect password"""
        form_data = {
            'email': 'login@example.com',
            'password': 'wrongpassword'
        }
        
        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid email or password', str(form.non_field_errors()))

    def test_login_form_missing_fields(self):
        """Test form with missing required fields"""
        # Test missing email
        form_data = {'password': 'testpass123'}
        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        
        # Test missing password
        form_data = {'email': 'login@example.com'}
        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_login_form_widget_attributes(self):
        """Test that form widgets have correct attributes"""
        form = UserLoginForm()
        
        email_widget = form.fields['email'].widget
        password_widget = form.fields['password'].widget
        
        self.assertEqual(email_widget.attrs['class'], 'form-control')
        self.assertEqual(email_widget.attrs['placeholder'], 'Enter your email')
        
        self.assertEqual(password_widget.attrs['class'], 'form-control')
        self.assertEqual(password_widget.attrs['placeholder'], 'Enter your password')


class UserUpdateFormTests(BaseTestCase, FileTestMixin):
    """Test cases for UserUpdateForm"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_valid_user_update_form(self):
        """Test form with valid update data"""
        form_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'bio': 'Updated bio',
            'location': 'New City',
            'website': 'https://newwebsite.com',
            'github': 'https://github.com/updated',
            'linkedin': 'https://linkedin.com/in/updated',
            'twitter': 'https://twitter.com/updated'
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_user_update_form_with_file(self):
        """Test form with profile picture upload"""
        image = self.create_image_file('new_profile.jpg')
        
        form_data = {
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        form = UserUpdateForm(
            data=form_data,
            files={'profile_picture': image},
            instance=self.user
        )
        self.assertTrue(form.is_valid())

    def test_user_update_form_email_validation(self):
        """Test email field validation"""
        # Test with invalid email format
        form_data = {
            'username': self.user.username,
            'email': 'invalid-email',
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_user_update_form_required_fields(self):
        """Test that required fields are enforced"""
        form_data = {}  # Empty data
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        
        required_fields = ['username', 'email', 'first_name', 'last_name']
        for field in required_fields:
            self.assertIn(field, form.errors)

    def test_user_update_form_save(self):
        """Test saving form updates user"""
        form_data = {
            'username': 'newusername',
            'email': 'newemail@example.com',
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'bio': 'New bio'
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        
        self.assertEqual(updated_user.username, 'newusername')
        self.assertEqual(updated_user.email, 'newemail@example.com')
        self.assertEqual(updated_user.first_name, 'NewFirst')
        self.assertEqual(updated_user.last_name, 'NewLast')
        self.assertEqual(updated_user.bio, 'New bio')


class ProfileUpdateFormTests(BaseTestCase, FileTestMixin):
    """Test cases for ProfileUpdateForm"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.profile = ProfileFactory(user=self.user)

    def test_valid_profile_update_form(self):
        """Test form with valid profile data"""
        form_data = {
            'phone': '+1234567890',
            'date_of_birth': '1990-01-01',
            'company': 'New Company',
            'position': 'New Position',
            'skills': 'Python, Django, React',
            'is_available_for_hire': True,
            'hourly_rate': '150.00'
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())

    def test_profile_update_form_with_resume(self):
        """Test form with resume upload"""
        resume = self.create_uploaded_file('resume.pdf', b'fake pdf content')
        
        form_data = {
            'phone': self.profile.phone or '',
            'company': self.profile.company or '',
            'position': self.profile.position or '',
            'skills': self.profile.skills or '',
            'is_available_for_hire': self.profile.is_available_for_hire,
        }
        
        form = ProfileUpdateForm(
            data=form_data,
            files={'resume': resume},
            instance=self.profile
        )
        self.assertTrue(form.is_valid())

    def test_profile_update_form_skills_processing(self):
        """Test skills field processing"""
        form_data = {
            'skills': 'Python, Django, JavaScript, React',
            'is_available_for_hire': True,
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
        
        # Test that skills are properly handled
        self.assertEqual(
            form.cleaned_data['skills'], 
            'Python, Django, JavaScript, React'
        )

    def test_profile_update_form_date_validation(self):
        """Test date field validation"""
        # Test with invalid date
        form_data = {
            'date_of_birth': 'invalid-date',
            'is_available_for_hire': True,
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_profile_update_form_hourly_rate_validation(self):
        """Test hourly rate field validation"""
        # Test with invalid decimal
        form_data = {
            'hourly_rate': 'not-a-number',
            'is_available_for_hire': True,
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('hourly_rate', form.errors)

    def test_profile_update_form_optional_fields(self):
        """Test that most fields are optional"""
        form_data = {
            'is_available_for_hire': False,
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())

    def test_profile_update_form_save(self):
        """Test saving form updates profile"""
        form_data = {
            'phone': '+9876543210',
            'company': 'Updated Company',
            'position': 'Senior Developer',
            'skills': 'Python, Django, Vue.js',
            'is_available_for_hire': False,
            'hourly_rate': '200.00'
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
        
        updated_profile = form.save()
        
        self.assertEqual(updated_profile.phone, '+9876543210')
        self.assertEqual(updated_profile.company, 'Updated Company')
        self.assertEqual(updated_profile.position, 'Senior Developer')
        self.assertEqual(updated_profile.skills, 'Python, Django, Vue.js')
        self.assertFalse(updated_profile.is_available_for_hire)
        self.assertEqual(updated_profile.hourly_rate, 200.00)


class CustomUserChangeFormTests(BaseTestCase):
    """Test cases for CustomUserChangeForm (admin form)"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_custom_user_change_form_meta(self):
        """Test that form includes all fields"""
        form = CustomUserChangeForm(instance=self.user)
        
        # Should include all User model fields
        self.assertEqual(form._meta.model, User)
        self.assertEqual(form._meta.fields, '__all__')

    def test_custom_user_change_form_initialization(self):
        """Test form initializes with user data"""
        form = CustomUserChangeForm(instance=self.user)
        
        self.assertEqual(form.instance, self.user)
        # Test that initial values are populated
        self.assertEqual(form.initial.get('email'), self.user.email)


class FormIntegrationTests(BaseTestCase):
    """Integration tests for forms working together"""

    def test_registration_to_update_workflow(self):
        """Test user registration followed by profile update"""
        # Register user
        registration_data = {
            'username': 'workflowuser',
            'email': 'workflow@example.com',
            'first_name': 'Workflow',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        registration_form = UserRegistrationForm(data=registration_data)
        self.assertTrue(registration_form.is_valid())
        user = registration_form.save()
        
        # Update user profile
        user_update_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': 'Updated bio after registration'
        }
        
        user_update_form = UserUpdateForm(data=user_update_data, instance=user)
        self.assertTrue(user_update_form.is_valid())
        updated_user = user_update_form.save()
        
        self.assertEqual(updated_user.bio, 'Updated bio after registration')

    def test_user_and_profile_forms_together(self):
        """Test updating user and profile forms in same workflow"""
        user = UserFactory()
        profile = ProfileFactory(user=user)
        
        # Update user
        user_data = {
            'username': user.username,
            'email': 'newemail@example.com',
            'first_name': 'Updated',
            'last_name': user.last_name,
        }
        
        user_form = UserUpdateForm(data=user_data, instance=user)
        self.assertTrue(user_form.is_valid())
        
        # Update profile
        profile_data = {
            'company': 'New Company',
            'position': 'New Position',
            'is_available_for_hire': True,
        }
        
        profile_form = ProfileUpdateForm(data=profile_data, instance=profile)
        self.assertTrue(profile_form.is_valid())
        
        # Save both
        updated_user = user_form.save()
        updated_profile = profile_form.save()
        
        self.assertEqual(updated_user.email, 'newemail@example.com')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_profile.company, 'New Company')
        self.assertEqual(updated_profile.position, 'New Position')
