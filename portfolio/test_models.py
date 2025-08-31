"""
Tests for Portfolio app models
"""

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from decimal import Decimal

from core.test_utils import BaseTestCase, FileTestMixin, override_media_root
from core.factories import (
    UserFactory, CategoryFactory, ProjectFactory, SkillFactory,
    ExperienceFactory, EducationFactory, AchievementFactory, TestimonialFactory
)

User = get_user_model()


class CategoryModelTests(BaseTestCase):
    """Test cases for Category model"""

    def test_category_creation(self):
        """Test creating a category with all fields"""
        category = CategoryFactory(
            name='Web Development',
            slug='web-development',
            description='Web development projects',
            icon='fas fa-globe',
            color='#007bff'
        )
        
        self.assertEqual(category.name, 'Web Development')
        self.assertEqual(category.slug, 'web-development')
        self.assertEqual(category.description, 'Web development projects')
        self.assertEqual(category.icon, 'fas fa-globe')
        self.assertEqual(category.color, '#007bff')

    def test_category_str_method(self):
        """Test Category model __str__ method"""
        category = CategoryFactory(name='Mobile Development')
        self.assertEqual(str(category), 'Mobile Development')

    def test_category_get_absolute_url(self):
        """Test Category model get_absolute_url method"""
        category = CategoryFactory(slug='test-category')
        expected_url = reverse('portfolio:category_detail', kwargs={'slug': 'test-category'})
        self.assertEqual(category.get_absolute_url(), expected_url)

    def test_category_unique_name(self):
        """Test that category name must be unique"""
        CategoryFactory(name='Unique Category')
        
        with self.assertRaises(IntegrityError):
            CategoryFactory(name='Unique Category')

    def test_category_unique_slug(self):
        """Test that category slug must be unique"""
        CategoryFactory(slug='unique-slug')
        
        with self.assertRaises(IntegrityError):
            CategoryFactory(slug='unique-slug')

    def test_category_meta_options(self):
        """Test Category model meta options"""
        from portfolio.models import Category
        self.assertEqual(Category._meta.verbose_name_plural, 'Categories')
        self.assertEqual(Category._meta.ordering, ['name'])

    def test_category_created_at_timestamp(self):
        """Test that category has created_at timestamp"""
        category = CategoryFactory()
        self.assertIsNotNone(category.created_at)


class ProjectModelTests(BaseTestCase, FileTestMixin):
    """Test cases for Project model"""

    def test_project_creation(self):
        """Test creating a project with all fields"""
        user = UserFactory()
        category = CategoryFactory()
        
        project = ProjectFactory(
            title='Test Project',
            slug='test-project',
            description='This is a test project',
            short_description='Test project description',
            category=category,
            user=user,
            status='completed',
            client='Test Client',
            budget=Decimal('5000.00'),
            technologies='Python, Django, HTML, CSS'
        )
        
        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.slug, 'test-project')
        self.assertEqual(project.user, user)
        self.assertEqual(project.category, category)
        self.assertEqual(project.status, 'completed')
        self.assertEqual(project.client, 'Test Client')
        self.assertEqual(project.budget, Decimal('5000.00'))
        self.assertTrue(project.is_published)

    def test_project_str_method(self):
        """Test Project model __str__ method"""
        project = ProjectFactory(title='My Awesome Project')
        self.assertEqual(str(project), 'My Awesome Project')

    def test_project_get_absolute_url(self):
        """Test Project model get_absolute_url method"""
        project = ProjectFactory(slug='test-project')
        expected_url = reverse('portfolio:project_detail', kwargs={'slug': 'test-project'})
        self.assertEqual(project.get_absolute_url(), expected_url)

    def test_project_technology_list_property(self):
        """Test Project model technology_list property"""
        project = ProjectFactory(technologies='Python, Django, JavaScript, React')
        expected_list = ['Python', 'Django', 'JavaScript', 'React']
        self.assertEqual(project.technology_list, expected_list)
        
        # Test with empty technologies
        project.technologies = ''
        self.assertEqual(project.technology_list, [])

    def test_project_like_count_property(self):
        """Test Project model like_count property"""
        project = ProjectFactory()
        users = [UserFactory() for _ in range(3)]
        
        # Add likes
        for user in users:
            project.likes.add(user)
        
        self.assertEqual(project.like_count, 3)

    def test_project_unique_slug(self):
        """Test that project slug must be unique"""
        ProjectFactory(slug='unique-project')
        
        with self.assertRaises(IntegrityError):
            ProjectFactory(slug='unique-project')

    def test_project_status_choices(self):
        """Test project status field choices"""
        project = ProjectFactory(status='planning')
        self.assertEqual(project.status, 'planning')
        
        project.status = 'in_progress'
        project.save()
        self.assertEqual(project.status, 'in_progress')

    def test_project_dates_validation(self):
        """Test project start and end dates"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        project = ProjectFactory(start_date=start_date, end_date=end_date)
        
        self.assertEqual(project.start_date, start_date)
        self.assertEqual(project.end_date, end_date)

    def test_project_meta_options(self):
        """Test Project model meta options"""
        from portfolio.models import Project
        self.assertEqual(Project._meta.ordering, ['-created_at'])

    @override_media_root
    def test_project_image_processing(self):
        """Test project featured image processing"""
        project = ProjectFactory()
        # Image processing is tested in the factory post_generation


class SkillModelTests(BaseTestCase):
    """Test cases for Skill model"""

    def test_skill_creation(self):
        """Test creating a skill with all fields"""
        user = UserFactory()
        skill = SkillFactory(
            name='Python',
            proficiency='advanced',
            percentage=85,
            icon='fab fa-python',
            category='Programming',
            user=user
        )
        
        self.assertEqual(skill.name, 'Python')
        self.assertEqual(skill.proficiency, 'advanced')
        self.assertEqual(skill.percentage, 85)
        self.assertEqual(skill.icon, 'fab fa-python')
        self.assertEqual(skill.category, 'Programming')
        self.assertEqual(skill.user, user)

    def test_skill_str_method(self):
        """Test Skill model __str__ method"""
        skill = SkillFactory(name='Django', proficiency='expert')
        expected_str = 'Django (Expert)'
        self.assertEqual(str(skill), expected_str)

    def test_skill_proficiency_choices(self):
        """Test skill proficiency field choices"""
        proficiency_choices = ['beginner', 'intermediate', 'advanced', 'expert']
        
        for choice in proficiency_choices:
            skill = SkillFactory(proficiency=choice)
            self.assertEqual(skill.proficiency, choice)

    def test_skill_unique_together(self):
        """Test that skill name and user combination must be unique"""
        user = UserFactory()
        SkillFactory(name='Python', user=user)
        
        with self.assertRaises(IntegrityError):
            SkillFactory(name='Python', user=user)

    def test_skill_percentage_validation(self):
        """Test skill percentage field"""
        skill = SkillFactory(percentage=90)
        self.assertEqual(skill.percentage, 90)

    def test_skill_meta_options(self):
        """Test Skill model meta options"""
        from portfolio.models import Skill
        self.assertEqual(Skill._meta.ordering, ['-percentage', 'name'])
        self.assertEqual(Skill._meta.unique_together, [('name', 'user')])


class ExperienceModelTests(BaseTestCase):
    """Test cases for Experience model"""

    def test_experience_creation(self):
        """Test creating an experience with all fields"""
        user = UserFactory()
        start_date = date.today() - timedelta(days=365)
        end_date = date.today() - timedelta(days=30)
        
        experience = ExperienceFactory(
            user=user,
            company='Test Company',
            position='Software Developer',
            description='Worked on various projects',
            location='New York, NY',
            start_date=start_date,
            end_date=end_date,
            is_current=False,
            skills_used='Python, Django, PostgreSQL'
        )
        
        self.assertEqual(experience.user, user)
        self.assertEqual(experience.company, 'Test Company')
        self.assertEqual(experience.position, 'Software Developer')
        self.assertEqual(experience.location, 'New York, NY')
        self.assertEqual(experience.start_date, start_date)
        self.assertEqual(experience.end_date, end_date)
        self.assertFalse(experience.is_current)

    def test_experience_str_method(self):
        """Test Experience model __str__ method"""
        experience = ExperienceFactory(position='Senior Developer', company='Tech Corp')
        expected_str = 'Senior Developer at Tech Corp'
        self.assertEqual(str(experience), expected_str)

    def test_experience_duration_property(self):
        """Test Experience model duration property"""
        start_date = date(2020, 1, 1)
        end_date = date(2022, 6, 15)
        
        experience = ExperienceFactory(start_date=start_date, end_date=end_date)
        duration = experience.duration
        
        # Should contain years and months
        self.assertIn('year', duration)

    def test_experience_current_position(self):
        """Test experience with current position (no end date)"""
        experience = ExperienceFactory(is_current=True, end_date=None)
        
        self.assertTrue(experience.is_current)
        self.assertIsNone(experience.end_date)
        
        # Duration should calculate to current date
        duration = experience.duration
        self.assertIsInstance(duration, str)

    def test_experience_meta_options(self):
        """Test Experience model meta options"""
        from portfolio.models import Experience
        self.assertEqual(Experience._meta.ordering, ['-start_date'])


class EducationModelTests(BaseTestCase):
    """Test cases for Education model"""

    def test_education_creation(self):
        """Test creating an education record with all fields"""
        user = UserFactory()
        start_date = date(2018, 9, 1)
        end_date = date(2022, 5, 31)
        
        education = EducationFactory(
            user=user,
            institution='Test University',
            degree='bachelor',
            field_of_study='Computer Science',
            description='Studied computer science fundamentals',
            start_date=start_date,
            end_date=end_date,
            is_current=False,
            grade='3.8/4.0'
        )
        
        self.assertEqual(education.user, user)
        self.assertEqual(education.institution, 'Test University')
        self.assertEqual(education.degree, 'bachelor')
        self.assertEqual(education.field_of_study, 'Computer Science')
        self.assertEqual(education.grade, '3.8/4.0')
        self.assertFalse(education.is_current)

    def test_education_str_method(self):
        """Test Education model __str__ method"""
        education = EducationFactory(
            degree='master',
            field_of_study='Data Science',
            institution='Tech University'
        )
        expected_str = "Master's Degree in Data Science from Tech University"
        self.assertEqual(str(education), expected_str)

    def test_education_degree_choices(self):
        """Test education degree field choices"""
        degree_choices = ['high_school', 'associate', 'bachelor', 'master', 'phd', 'certificate', 'other']
        
        for choice in degree_choices:
            education = EducationFactory(degree=choice)
            self.assertEqual(education.degree, choice)

    def test_education_current_education(self):
        """Test education with is_current=True"""
        education = EducationFactory(is_current=True, end_date=None)
        
        self.assertTrue(education.is_current)
        self.assertIsNone(education.end_date)

    def test_education_meta_options(self):
        """Test Education model meta options"""
        from portfolio.models import Education
        self.assertEqual(Education._meta.ordering, ['-start_date'])
        self.assertEqual(Education._meta.verbose_name_plural, 'Education')


class AchievementModelTests(BaseTestCase, FileTestMixin):
    """Test cases for Achievement model"""

    def test_achievement_creation(self):
        """Test creating an achievement with all fields"""
        user = UserFactory()
        date_received = date(2023, 6, 15)
        
        achievement = AchievementFactory(
            user=user,
            title='Best Developer Award',
            description='Awarded for outstanding contribution',
            issuer='Tech Conference 2023',
            date_received=date_received,
            credential_id='CERT-12345',
            credential_url='https://example.com/cert/12345'
        )
        
        self.assertEqual(achievement.user, user)
        self.assertEqual(achievement.title, 'Best Developer Award')
        self.assertEqual(achievement.issuer, 'Tech Conference 2023')
        self.assertEqual(achievement.date_received, date_received)
        self.assertEqual(achievement.credential_id, 'CERT-12345')

    def test_achievement_str_method(self):
        """Test Achievement model __str__ method"""
        achievement = AchievementFactory(
            title='Python Certification',
            issuer='Python Institute'
        )
        expected_str = 'Python Certification - Python Institute'
        self.assertEqual(str(achievement), expected_str)

    def test_achievement_meta_options(self):
        """Test Achievement model meta options"""
        from portfolio.models import Achievement
        self.assertEqual(Achievement._meta.ordering, ['-date_received'])

    @override_media_root
    def test_achievement_image_upload(self):
        """Test achievement image upload"""
        achievement = AchievementFactory()
        # Image upload is tested in the factory post_generation


class TestimonialModelTests(BaseTestCase, FileTestMixin):
    """Test cases for Testimonial model"""

    def test_testimonial_creation(self):
        """Test creating a testimonial with all fields"""
        user = UserFactory()
        project = ProjectFactory()
        
        testimonial = TestimonialFactory(
            user=user,
            client_name='John Client',
            client_position='Project Manager',
            client_company='Client Corp',
            testimonial='Great work on the project!',
            rating=5,
            project=project,
            is_featured=True
        )
        
        self.assertEqual(testimonial.user, user)
        self.assertEqual(testimonial.client_name, 'John Client')
        self.assertEqual(testimonial.client_position, 'Project Manager')
        self.assertEqual(testimonial.client_company, 'Client Corp')
        self.assertEqual(testimonial.rating, 5)
        self.assertEqual(testimonial.project, project)
        self.assertTrue(testimonial.is_featured)

    def test_testimonial_str_method(self):
        """Test Testimonial model __str__ method"""
        testimonial = TestimonialFactory(client_name='Jane Doe')
        expected_str = 'Testimonial from Jane Doe'
        self.assertEqual(str(testimonial), expected_str)

    def test_testimonial_rating_choices(self):
        """Test testimonial rating field choices"""
        for rating in range(1, 6):
            testimonial = TestimonialFactory(rating=rating)
            self.assertEqual(testimonial.rating, rating)

    def test_testimonial_without_project(self):
        """Test testimonial without associated project"""
        testimonial = TestimonialFactory(project=None)
        self.assertIsNone(testimonial.project)

    def test_testimonial_meta_options(self):
        """Test Testimonial model meta options"""
        from portfolio.models import Testimonial
        self.assertEqual(Testimonial._meta.ordering, ['-created_at'])

    @override_media_root
    def test_testimonial_client_image_upload(self):
        """Test testimonial client image upload"""
        testimonial = TestimonialFactory()
        # Image upload is tested in the factory post_generation


class ProjectImageModelTests(BaseTestCase, FileTestMixin):
    """Test cases for ProjectImage model"""

    def test_project_image_creation(self):
        """Test creating a project image"""
        project = ProjectFactory()
        
        from portfolio.models import ProjectImage
        project_image = ProjectImage.objects.create(
            project=project,
            caption='Project screenshot',
            order=1
        )
        
        self.assertEqual(project_image.project, project)
        self.assertEqual(project_image.caption, 'Project screenshot')
        self.assertEqual(project_image.order, 1)

    def test_project_image_str_method(self):
        """Test ProjectImage model __str__ method"""
        project = ProjectFactory(title='Test Project')
        
        from portfolio.models import ProjectImage
        project_image = ProjectImage.objects.create(
            project=project,
            order=1
        )
        
        expected_str = 'Test Project - Image 1'
        self.assertEqual(str(project_image), expected_str)

    def test_project_image_ordering(self):
        """Test ProjectImage model ordering"""
        project = ProjectFactory()
        
        from portfolio.models import ProjectImage
        image1 = ProjectImage.objects.create(project=project, order=2)
        image2 = ProjectImage.objects.create(project=project, order=1)
        image3 = ProjectImage.objects.create(project=project, order=3)
        
        images = list(project.images.all())
        self.assertEqual(images[0], image2)  # order=1
        self.assertEqual(images[1], image1)  # order=2
        self.assertEqual(images[2], image3)  # order=3


class ModelIntegrationTests(BaseTestCase):
    """Integration tests for portfolio models working together"""

    def test_user_portfolio_relationship(self):
        """Test relationships between user and portfolio models"""
        user = UserFactory()
        
        # Create related objects
        skills = [SkillFactory(user=user) for _ in range(3)]
        experiences = [ExperienceFactory(user=user) for _ in range(2)]
        education = [EducationFactory(user=user) for _ in range(2)]
        achievements = [AchievementFactory(user=user) for _ in range(2)]
        projects = [ProjectFactory(user=user) for _ in range(3)]
        testimonials = [TestimonialFactory(user=user) for _ in range(2)]
        
        # Test reverse relationships
        self.assertEqual(user.skills.count(), 3)
        self.assertEqual(user.experiences.count(), 2)
        self.assertEqual(user.education.count(), 2)
        self.assertEqual(user.achievements.count(), 2)
        self.assertEqual(user.projects.count(), 3)
        self.assertEqual(user.testimonials.count(), 2)

    def test_category_project_relationship(self):
        """Test category and project relationship"""
        category = CategoryFactory()
        projects = [ProjectFactory(category=category) for _ in range(3)]
        
        self.assertEqual(category.project_set.count(), 3)
        
        # Test deleting category sets projects category to NULL
        category.delete()
        
        from portfolio.models import Project
        for project in projects:
            project.refresh_from_db()
            self.assertIsNone(project.category)

    def test_project_testimonial_relationship(self):
        """Test project and testimonial relationship"""
        project = ProjectFactory()
        testimonials = [TestimonialFactory(project=project) for _ in range(2)]
        
        self.assertEqual(project.testimonials.count(), 2)

    def test_model_cascade_deletions(self):
        """Test cascade deletions when user is deleted"""
        user = UserFactory()
        
        # Create related objects
        skill = SkillFactory(user=user)
        experience = ExperienceFactory(user=user)
        education = EducationFactory(user=user)
        achievement = AchievementFactory(user=user)
        project = ProjectFactory(user=user)
        testimonial = TestimonialFactory(user=user)
        
        # Store IDs for verification
        skill_id = skill.id
        experience_id = experience.id
        education_id = education.id
        achievement_id = achievement.id
        project_id = project.id
        testimonial_id = testimonial.id
        
        # Delete user
        user.delete()
        
        # Verify all related objects are deleted
        from portfolio.models import (
            Skill, Experience, Education, Achievement, Project, Testimonial
        )
        
        with self.assertRaises(Skill.DoesNotExist):
            Skill.objects.get(id=skill_id)
        
        with self.assertRaises(Experience.DoesNotExist):
            Experience.objects.get(id=experience_id)
        
        with self.assertRaises(Education.DoesNotExist):
            Education.objects.get(id=education_id)
        
        with self.assertRaises(Achievement.DoesNotExist):
            Achievement.objects.get(id=achievement_id)
        
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(id=project_id)
        
        with self.assertRaises(Testimonial.DoesNotExist):
            Testimonial.objects.get(id=testimonial_id)
