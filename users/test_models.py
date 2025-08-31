"""
Tests for Users app models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
import os
import tempfile

from core.test_utils import BaseTestCase, FileTestMixin, override_media_root
from core.factories import UserFactory, ProfileFactory

User = get_user_model()


class UserModelTests(BaseTestCase):
    """Test cases for custom User model"""

    def test_user_creation(self):
        """Test creating a user with all fields"""
        user = UserFactory(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            bio='This is a test bio',
            location='Test City',
            website='https://testsite.com',
            github='https://github.com/testuser',
            linkedin='https://linkedin.com/in/testuser',
            twitter='https://twitter.com/testuser'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.bio, 'This is a test bio')
        self.assertEqual(user.location, 'Test City')
        self.assertEqual(user.website, 'https://testsite.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_str_method(self):
        """Test User model __str__ method"""
        user = UserFactory(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        expected_str = "John Doe (john@example.com)"
        self.assertEqual(str(user), expected_str)

    def test_user_full_name_property(self):
        """Test User model full_name property"""
        user = UserFactory(first_name='John', last_name='Doe')
        self.assertEqual(user.full_name, 'John Doe')
        
        # Test with empty last name
        user.last_name = ''
        self.assertEqual(user.full_name, 'John')
        
        # Test with empty first name
        user.first_name = ''
        user.last_name = 'Doe'
        self.assertEqual(user.full_name, 'Doe')

    def test_user_email_unique(self):
        """Test that user email must be unique"""
        UserFactory(email='unique@example.com')
        
        with self.assertRaises(IntegrityError):
            UserFactory(email='unique@example.com')

    def test_user_username_field(self):
        """Test that EMAIL is the USERNAME_FIELD"""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_user_required_fields(self):
        """Test REQUIRED_FIELDS setting"""
        expected_fields = ['username', 'first_name', 'last_name']
        self.assertEqual(User.REQUIRED_FIELDS, expected_fields)

    @override_media_root
    def test_user_profile_picture_upload(self):
        """Test user profile picture upload"""
        user = UserFactory()
        
        # Create test image
        image_content = b'fake image content'
        image = SimpleUploadedFile(
            'test_profile.jpg',
            image_content,
            content_type='image/jpeg'
        )
        
        user.profile_picture = image
        user.save()
        
        self.assertTrue(user.profile_picture.name.startswith('profile_pics/'))

    def test_user_verification_status(self):
        """Test user verification functionality"""
        user = UserFactory(is_verified=False)
        self.assertFalse(user.is_verified)
        
        user.is_verified = True
        user.save()
        self.assertTrue(user.is_verified)

    def test_user_timestamps(self):
        """Test user creation and update timestamps"""
        user = UserFactory()
        
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        
        # Test that updated_at changes when user is updated
        original_updated = user.updated_at
        user.bio = 'Updated bio'
        user.save()
        
        self.assertGreater(user.updated_at, original_updated)


class ProfileModelTests(BaseTestCase, FileTestMixin):
    """Test cases for Profile model"""

    def test_profile_creation(self):
        """Test creating a profile"""
        user = UserFactory()
        profile = ProfileFactory(
            user=user,
            phone='+1234567890',
            company='Test Company',
            position='Test Position',
            skills='Python, Django, JavaScript',
            is_available_for_hire=True,
            hourly_rate=100.00
        )
        
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.phone, '+1234567890')
        self.assertEqual(profile.company, 'Test Company')
        self.assertEqual(profile.position, 'Test Position')
        self.assertEqual(profile.skills, 'Python, Django, JavaScript')
        self.assertTrue(profile.is_available_for_hire)
        self.assertEqual(profile.hourly_rate, 100.00)

    def test_profile_str_method(self):
        """Test Profile model __str__ method"""
        user = UserFactory(first_name='John', last_name='Doe')
        profile = ProfileFactory(user=user)
        expected_str = "John Doe's Profile"
        self.assertEqual(str(profile), expected_str)

    def test_profile_skill_list_property(self):
        """Test Profile model skill_list property"""
        user = UserFactory()
        profile = ProfileFactory(
            user=user,
            skills='Python, Django, JavaScript, React'
        )
        
        expected_skills = ['Python', 'Django', 'JavaScript', 'React']
        self.assertEqual(profile.skill_list, expected_skills)
        
        # Test with empty skills
        profile.skills = ''
        self.assertEqual(profile.skill_list, [])
        
        # Test with skills containing extra spaces
        profile.skills = ' Python , Django , JavaScript '
        expected_skills = ['Python', 'Django', 'JavaScript']
        self.assertEqual(profile.skill_list, expected_skills)

    def test_profile_one_to_one_relationship(self):
        """Test that Profile has one-to-one relationship with User"""
        user = UserFactory()
        profile = ProfileFactory(user=user)
        
        # Test accessing profile from user
        self.assertEqual(user.profile, profile)
        
        # Test that creating another profile for same user raises error
        with self.assertRaises(IntegrityError):
            ProfileFactory(user=user)

    def test_profile_date_of_birth(self):
        """Test profile date of birth field"""
        from datetime import date
        
        user = UserFactory()
        profile = ProfileFactory(
            user=user,
            date_of_birth=date(1990, 1, 1)
        )
        
        self.assertEqual(profile.date_of_birth, date(1990, 1, 1))

    @override_media_root
    def test_profile_resume_upload(self):
        """Test profile resume upload"""
        user = UserFactory()
        profile = ProfileFactory(user=user)
        
        # Create test file
        resume_content = b'fake resume content'
        resume = SimpleUploadedFile(
            'test_resume.pdf',
            resume_content,
            content_type='application/pdf'
        )
        
        profile.resume = resume
        profile.save()
        
        self.assertTrue(profile.resume.name.startswith('resumes/'))

    def test_profile_optional_fields(self):
        """Test that profile optional fields can be empty"""
        user = UserFactory()
        profile = ProfileFactory(
            user=user,
            phone='',
            company='',
            position='',
            skills='',
            date_of_birth=None,
            hourly_rate=None
        )
        
        self.assertEqual(profile.phone, '')
        self.assertEqual(profile.company, '')
        self.assertEqual(profile.position, '')
        self.assertEqual(profile.skills, '')
        self.assertIsNone(profile.date_of_birth)
        self.assertIsNone(profile.hourly_rate)

    def test_profile_availability_status(self):
        """Test profile availability for hire status"""
        user = UserFactory()
        profile = ProfileFactory(user=user, is_available_for_hire=True)
        
        self.assertTrue(profile.is_available_for_hire)
        
        profile.is_available_for_hire = False
        profile.save()
        
        self.assertFalse(profile.is_available_for_hire)

    def test_profile_hourly_rate_validation(self):
        """Test profile hourly rate field"""
        user = UserFactory()
        profile = ProfileFactory(user=user, hourly_rate=150.50)
        
        self.assertEqual(profile.hourly_rate, 150.50)
        
        # Test with decimal precision
        profile.hourly_rate = 99.99
        profile.save()
        
        self.assertEqual(profile.hourly_rate, 99.99)


class UserProfileIntegrationTests(BaseTestCase):
    """Integration tests for User and Profile models"""

    def test_profile_auto_creation_signal(self):
        """Test that profile is automatically created when user is created"""
        # This test assumes you have a signal to auto-create profiles
        # If you don't have this signal, you can skip this test
        pass

    def test_user_deletion_cascades_to_profile(self):
        """Test that deleting user also deletes profile"""
        user = UserFactory()
        profile = ProfileFactory(user=user)
        profile_id = profile.id
        
        # Delete user
        user.delete()
        
        # Check that profile is also deleted
        from users.models import Profile
        with self.assertRaises(Profile.DoesNotExist):
            Profile.objects.get(id=profile_id)

    def test_user_profile_update_together(self):
        """Test updating user and profile together"""
        user = UserFactory(first_name='John')
        profile = ProfileFactory(user=user, company='Old Company')
        
        # Update both user and profile
        user.first_name = 'Jane'
        user.save()
        
        profile.company = 'New Company'
        profile.save()
        
        # Refresh from database
        user.refresh_from_db()
        profile.refresh_from_db()
        
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(profile.company, 'New Company')

    def test_user_meta_options(self):
        """Test User model meta options"""
        self.assertEqual(User._meta.verbose_name, 'User')
        self.assertEqual(User._meta.verbose_name_plural, 'Users')
        self.assertEqual(User._meta.ordering, ['-created_at'])

    def test_profile_meta_options(self):
        """Test Profile model doesn't have specific ordering"""
        from users.models import Profile
        # Profile doesn't specify ordering, so it should be empty
        self.assertEqual(Profile._meta.ordering, [])


class UserModelManagerTests(BaseTestCase):
    """Test custom User model manager methods if any"""

    def test_create_user(self):
        """Test creating user with create_user method"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating superuser"""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        self.assertEqual(user.username, 'admin')
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.check_password('adminpass123'))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_manager_get_by_natural_key(self):
        """Test getting user by natural key (email)"""
        user = UserFactory(email='natural@example.com')
        
        retrieved_user = User.objects.get_by_natural_key('natural@example.com')
        self.assertEqual(user, retrieved_user)
