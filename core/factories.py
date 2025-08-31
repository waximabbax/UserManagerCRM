"""
Factory classes for creating test data across all apps
"""

import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image
import io

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    bio = Faker('paragraph')
    location = Faker('city')
    website = Faker('url')
    github = factory.LazyAttribute(lambda obj: f"https://github.com/{obj.username}")
    linkedin = factory.LazyAttribute(lambda obj: f"https://linkedin.com/in/{obj.username}")
    twitter = factory.LazyAttribute(lambda obj: f"https://twitter.com/{obj.username}")
    is_verified = False
    is_active = True

    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        """Set a default password for the user"""
        if create:
            obj.set_password('testpass123')
            obj.save()


class StaffUserFactory(UserFactory):
    """Factory for creating staff users"""
    is_staff = True


class SuperUserFactory(UserFactory):
    """Factory for creating superusers"""
    is_staff = True
    is_superuser = True


class ProfileFactory(DjangoModelFactory):
    """Factory for creating Profile instances"""
    
    class Meta:
        model = 'users.Profile'
    
    user = SubFactory(UserFactory)
    phone = Faker('phone_number')
    date_of_birth = Faker('date_of_birth', minimum_age=18, maximum_age=65)
    company = Faker('company')
    position = Faker('job')
    skills = "Python, Django, JavaScript, React, PostgreSQL"
    is_available_for_hire = True
    hourly_rate = Faker('pydecimal', left_digits=3, right_digits=2, positive=True, min_value=25, max_value=200)


def create_test_image(width=100, height=100, color='RGB', format_name='PNG'):
    """Create a test image for upload fields"""
    image = Image.new(color, (width, height), color='red')
    image_io = io.BytesIO()
    image.save(image_io, format=format_name)
    image_io.seek(0)
    return ContentFile(image_io.getvalue(), name=f'test_image.{format_name.lower()}')


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances"""
    
    class Meta:
        model = 'portfolio.Category'
    
    name = Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())
    description = Faker('paragraph')
    icon = "fas fa-code"
    color = "#007bff"


class ProjectFactory(DjangoModelFactory):
    """Factory for creating Project instances"""
    
    class Meta:
        model = 'portfolio.Project'
    
    title = Faker('sentence', nb_words=4)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    description = Faker('paragraph', nb_sentences=10)
    short_description = Faker('sentence', nb_words=15)
    category = SubFactory(CategoryFactory)
    user = SubFactory(UserFactory)
    status = 'completed'
    start_date = Faker('date_between', start_date='-2y', end_date='-6m')
    end_date = Faker('date_between', start_date='-6m', end_date='today')
    client = Faker('company')
    budget = Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    demo_url = Faker('url')
    source_url = factory.LazyAttribute(lambda obj: f"https://github.com/{obj.user.username}/{obj.slug}")
    technologies = "Python, Django, HTML, CSS, JavaScript"
    is_featured = False
    is_published = True
    views = Faker('pyint', min_value=0, max_value=1000)

    @factory.post_generation
    def featured_image(obj, create, extracted, **kwargs):
        if create:
            obj.featured_image = create_test_image()
            obj.save()


class SkillFactory(DjangoModelFactory):
    """Factory for creating Skill instances"""
    
    class Meta:
        model = 'portfolio.Skill'
    
    name = Faker('word')
    proficiency = factory.Iterator(['beginner', 'intermediate', 'advanced', 'expert'])
    percentage = factory.LazyAttribute(lambda obj: {
        'beginner': 25,
        'intermediate': 50,
        'advanced': 75,
        'expert': 90
    }[obj.proficiency])
    icon = "fab fa-python"
    category = "Programming"
    user = SubFactory(UserFactory)


class ExperienceFactory(DjangoModelFactory):
    """Factory for creating Experience instances"""
    
    class Meta:
        model = 'portfolio.Experience'
    
    user = SubFactory(UserFactory)
    company = Faker('company')
    position = Faker('job')
    description = Faker('paragraph', nb_sentences=5)
    location = Faker('city')
    start_date = Faker('date_between', start_date='-3y', end_date='-1y')
    end_date = Faker('date_between', start_date='-1y', end_date='today')
    is_current = False
    company_url = Faker('url')
    skills_used = "Python, Django, PostgreSQL, AWS"


class EducationFactory(DjangoModelFactory):
    """Factory for creating Education instances"""
    
    class Meta:
        model = 'portfolio.Education'
    
    user = SubFactory(UserFactory)
    institution = Faker('company')
    degree = factory.Iterator(['bachelor', 'master', 'phd', 'certificate'])
    field_of_study = Faker('sentence', nb_words=3)
    description = Faker('paragraph')
    start_date = Faker('date_between', start_date='-6y', end_date='-2y')
    end_date = Faker('date_between', start_date='-4y', end_date='today')
    is_current = False
    grade = "3.8/4.0"
    institution_url = Faker('url')


class AchievementFactory(DjangoModelFactory):
    """Factory for creating Achievement instances"""
    
    class Meta:
        model = 'portfolio.Achievement'
    
    user = SubFactory(UserFactory)
    title = Faker('sentence', nb_words=6)
    description = Faker('paragraph')
    issuer = Faker('company')
    date_received = Faker('date_between', start_date='-2y', end_date='today')
    credential_id = Faker('uuid4')
    credential_url = Faker('url')

    @factory.post_generation
    def image(obj, create, extracted, **kwargs):
        if create:
            obj.image = create_test_image()
            obj.save()


class TestimonialFactory(DjangoModelFactory):
    """Factory for creating Testimonial instances"""
    
    class Meta:
        model = 'portfolio.Testimonial'
    
    user = SubFactory(UserFactory)
    client_name = Faker('name')
    client_position = Faker('job')
    client_company = Faker('company')
    testimonial = Faker('paragraph', nb_sentences=8)
    rating = Faker('pyint', min_value=1, max_value=5)
    project = SubFactory(ProjectFactory)
    is_featured = False

    @factory.post_generation
    def client_image(obj, create, extracted, **kwargs):
        if create:
            obj.client_image = create_test_image()
            obj.save()


class BlogCategoryFactory(DjangoModelFactory):
    """Factory for creating BlogCategory instances"""
    
    class Meta:
        model = 'blog.BlogCategory'
    
    name = Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())
    description = Faker('paragraph')
    color = "#007bff"


class BlogSeriesFactory(DjangoModelFactory):
    """Factory for creating BlogSeries instances"""
    
    class Meta:
        model = 'blog.BlogSeries'
    
    title = Faker('sentence', nb_words=5)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    description = Faker('paragraph')
    author = SubFactory(UserFactory)
    is_completed = False

    @factory.post_generation
    def image(obj, create, extracted, **kwargs):
        if create:
            obj.image = create_test_image()
            obj.save()


class PostFactory(DjangoModelFactory):
    """Factory for creating Post instances"""
    
    class Meta:
        model = 'blog.Post'
    
    title = Faker('sentence', nb_words=8)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    author = SubFactory(UserFactory)
    category = SubFactory(BlogCategoryFactory)
    excerpt = Faker('sentence', nb_words=20)
    content = Faker('paragraph', nb_sentences=20)
    status = 'published'
    is_featured = False
    reading_time = Faker('pyint', min_value=1, max_value=15)
    meta_title = factory.LazyAttribute(lambda obj: obj.title[:60])
    meta_description = factory.LazyAttribute(lambda obj: obj.excerpt[:160])
    views = Faker('pyint', min_value=0, max_value=1000)
    published_at = Faker('date_time_between', start_date='-1y', end_date='now')

    @factory.post_generation
    def featured_image(obj, create, extracted, **kwargs):
        if create:
            obj.featured_image = create_test_image()
            obj.save()


class CommentFactory(DjangoModelFactory):
    """Factory for creating Comment instances"""
    
    class Meta:
        model = 'blog.Comment'
    
    post = SubFactory(PostFactory)
    author = SubFactory(UserFactory)
    content = Faker('paragraph')
    is_approved = True


class NewsletterFactory(DjangoModelFactory):
    """Factory for creating Newsletter instances"""
    
    class Meta:
        model = 'blog.Newsletter'
    
    email = Faker('email')
    name = Faker('name')
    is_active = True


class ContactMessageFactory(DjangoModelFactory):
    """Factory for creating ContactMessage instances"""
    
    class Meta:
        model = 'contact.ContactMessage'
    
    name = Faker('name')
    email = Faker('email')
    phone = Faker('phone_number')
    company = Faker('company')
    website = Faker('url')
    subject = factory.Iterator(['general', 'project', 'freelance', 'support', 'partnership'])
    message = Faker('paragraph', nb_sentences=10)
    project_budget = "5000-10000"
    project_timeline = "2-3 months"
    status = 'new'
    priority = 'medium'
    ip_address = Faker('ipv4')
    user_agent = "Mozilla/5.0 (Test Browser)"


class FAQFactory(DjangoModelFactory):
    """Factory for creating FAQ instances"""
    
    class Meta:
        model = 'contact.FAQ'
    
    question = Faker('sentence', nb_words=10)
    answer = Faker('paragraph', nb_sentences=5)
    category = factory.Iterator(['general', 'services', 'pricing', 'technical', 'support'])
    is_featured = False
    order = Faker('pyint', min_value=1, max_value=100)


class ContactInfoFactory(DjangoModelFactory):
    """Factory for creating ContactInfo instances"""
    
    class Meta:
        model = 'contact.ContactInfo'
    
    business_name = "Portfolio Platform"
    tagline = "Showcase your work professionally"
    description = Faker('paragraph')
    email = "contact@portfolioplatform.com"
    phone = Faker('phone_number')
    address = Faker('address')
    website = "https://portfolioplatform.com"
    linkedin = "https://linkedin.com/company/portfolio-platform"
    twitter = "https://twitter.com/portfolioplatform"
    facebook = "https://facebook.com/portfolioplatform"
    github = "https://github.com/portfolio-platform"
    business_hours = "Monday - Friday: 9:00 AM - 6:00 PM"
    is_active = True
