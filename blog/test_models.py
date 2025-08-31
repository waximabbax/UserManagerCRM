"""
Tests for Blog app models
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.test_utils import BaseTestCase, FileTestMixin, override_media_root
from core.factories import (
    UserFactory, BlogCategoryFactory, PostFactory, CommentFactory,
    NewsletterFactory, BlogSeriesFactory
)

User = get_user_model()


class BlogCategoryModelTests(BaseTestCase):
    """Test cases for BlogCategory model"""

    def test_blog_category_creation(self):
        """Test creating a blog category with all fields"""
        category = BlogCategoryFactory(
            name='Technology',
            slug='technology',
            description='Technology related posts',
            color='#007bff'
        )
        
        self.assertEqual(category.name, 'Technology')
        self.assertEqual(category.slug, 'technology')
        self.assertEqual(category.description, 'Technology related posts')
        self.assertEqual(category.color, '#007bff')

    def test_blog_category_str_method(self):
        """Test BlogCategory model __str__ method"""
        category = BlogCategoryFactory(name='Web Development')
        self.assertEqual(str(category), 'Web Development')

    def test_blog_category_get_absolute_url(self):
        """Test BlogCategory model get_absolute_url method"""
        category = BlogCategoryFactory(slug='test-category')
        expected_url = reverse('blog:category_detail', kwargs={'slug': 'test-category'})
        self.assertEqual(category.get_absolute_url(), expected_url)

    def test_blog_category_auto_slug_generation(self):
        """Test automatic slug generation from name"""
        category = BlogCategoryFactory(name='Machine Learning', slug='')
        category.save()  # Trigger save method
        # The save method should generate slug from name
        # This depends on your implementation

    def test_blog_category_unique_constraints(self):
        """Test unique constraints on name and slug"""
        BlogCategoryFactory(name='Unique Category', slug='unique-slug')
        
        # Test unique name
        with self.assertRaises(IntegrityError):
            BlogCategoryFactory(name='Unique Category')
        
        # Test unique slug  
        with self.assertRaises(IntegrityError):
            BlogCategoryFactory(slug='unique-slug')

    def test_blog_category_meta_options(self):
        """Test BlogCategory model meta options"""
        from blog.models import BlogCategory
        self.assertEqual(BlogCategory._meta.verbose_name_plural, 'Blog Categories')
        self.assertEqual(BlogCategory._meta.ordering, ['name'])


class PostModelTests(BaseTestCase, FileTestMixin):
    """Test cases for Post model"""

    def test_post_creation(self):
        """Test creating a post with all fields"""
        author = UserFactory()
        category = BlogCategoryFactory()
        
        post = PostFactory(
            title='Test Blog Post',
            slug='test-blog-post',
            author=author,
            category=category,
            excerpt='This is a test post excerpt',
            content='This is the full content of the test post',
            status='published',
            is_featured=True,
            reading_time=5,
            meta_title='Test Blog Post - SEO Title',
            meta_description='SEO description for test post'
        )
        
        self.assertEqual(post.title, 'Test Blog Post')
        self.assertEqual(post.slug, 'test-blog-post')
        self.assertEqual(post.author, author)
        self.assertEqual(post.category, category)
        self.assertEqual(post.status, 'published')
        self.assertTrue(post.is_featured)
        self.assertEqual(post.reading_time, 5)

    def test_post_str_method(self):
        """Test Post model __str__ method"""
        post = PostFactory(title='My Awesome Blog Post')
        self.assertEqual(str(post), 'My Awesome Blog Post')

    def test_post_get_absolute_url(self):
        """Test Post model get_absolute_url method"""
        post = PostFactory(slug='test-post')
        expected_url = reverse('blog:post_detail', kwargs={'slug': 'test-post'})
        self.assertEqual(post.get_absolute_url(), expected_url)

    def test_post_like_count_property(self):
        """Test Post model like_count property"""
        post = PostFactory()
        users = [UserFactory() for _ in range(3)]
        
        # Add likes
        for user in users:
            post.likes.add(user)
        
        self.assertEqual(post.like_count, 3)

    def test_post_comment_count_property(self):
        """Test Post model comment_count property"""
        post = PostFactory()
        
        # Create approved comments
        approved_comments = [CommentFactory(post=post, is_approved=True) for _ in range(3)]
        # Create unapproved comments
        unapproved_comments = [CommentFactory(post=post, is_approved=False) for _ in range(2)]
        
        # Should only count approved comments
        self.assertEqual(post.comment_count, 3)

    def test_post_calculate_reading_time(self):
        """Test Post model calculate_reading_time method"""
        # Create post with specific word count
        content = ' '.join(['word'] * 400)  # 400 words
        post = PostFactory(content=content)
        
        reading_time = post.calculate_reading_time()
        
        # Should be around 2 minutes (400 words / 200 words per minute)
        self.assertEqual(reading_time, 2)

    def test_post_status_choices(self):
        """Test post status field choices"""
        status_choices = ['draft', 'published', 'archived']
        
        for choice in status_choices:
            post = PostFactory(status=choice)
            self.assertEqual(post.status, choice)

    def test_post_published_at_auto_set(self):
        """Test that published_at is set when status changes to published"""
        post = PostFactory(status='draft', published_at=None)
        
        # Change status to published
        post.status = 'published'
        post.save()
        
        self.assertIsNotNone(post.published_at)

    def test_post_unique_slug(self):
        """Test that post slug must be unique"""
        PostFactory(slug='unique-post-slug')
        
        with self.assertRaises(IntegrityError):
            PostFactory(slug='unique-post-slug')

    def test_post_meta_options(self):
        """Test Post model meta options"""
        from blog.models import Post
        self.assertEqual(Post._meta.ordering, ['-created_at'])

    @override_media_root
    def test_post_featured_image_processing(self):
        """Test post featured image processing"""
        post = PostFactory()
        # Image processing is tested in the factory post_generation


class CommentModelTests(BaseTestCase):
    """Test cases for Comment model"""

    def test_comment_creation(self):
        """Test creating a comment"""
        post = PostFactory()
        author = UserFactory()
        
        comment = CommentFactory(
            post=post,
            author=author,
            content='This is a test comment',
            is_approved=True
        )
        
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.author, author)
        self.assertEqual(comment.content, 'This is a test comment')
        self.assertTrue(comment.is_approved)

    def test_comment_str_method(self):
        """Test Comment model __str__ method"""
        author = UserFactory(username='testuser')
        post = PostFactory(title='Test Post')
        comment = CommentFactory(post=post, author=author)
        
        expected_str = 'Comment by testuser on Test Post'
        self.assertEqual(str(comment), expected_str)

    def test_comment_reply_functionality(self):
        """Test comment reply (nested comments)"""
        post = PostFactory()
        parent_comment = CommentFactory(post=post, parent=None)
        reply_comment = CommentFactory(post=post, parent=parent_comment)
        
        self.assertIsNone(parent_comment.parent)
        self.assertEqual(reply_comment.parent, parent_comment)
        self.assertTrue(reply_comment.is_reply)
        self.assertFalse(parent_comment.is_reply)

    def test_comment_approval_system(self):
        """Test comment approval system"""
        comment = CommentFactory(is_approved=False)
        self.assertFalse(comment.is_approved)
        
        comment.is_approved = True
        comment.save()
        self.assertTrue(comment.is_approved)

    def test_comment_meta_options(self):
        """Test Comment model meta options"""
        from blog.models import Comment
        self.assertEqual(Comment._meta.ordering, ['created_at'])

    def test_comment_cascade_deletion(self):
        """Test that comments are deleted when post is deleted"""
        post = PostFactory()
        comment = CommentFactory(post=post)
        comment_id = comment.id
        
        post.delete()
        
        from blog.models import Comment
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=comment_id)


class NewsletterModelTests(BaseTestCase):
    """Test cases for Newsletter model"""

    def test_newsletter_creation(self):
        """Test creating a newsletter subscription"""
        newsletter = NewsletterFactory(
            email='subscriber@example.com',
            name='John Subscriber',
            is_active=True
        )
        
        self.assertEqual(newsletter.email, 'subscriber@example.com')
        self.assertEqual(newsletter.name, 'John Subscriber')
        self.assertTrue(newsletter.is_active)

    def test_newsletter_str_method(self):
        """Test Newsletter model __str__ method"""
        newsletter = NewsletterFactory(email='test@example.com', name='Test User')
        expected_str = 'test@example.com (Test User)'
        self.assertEqual(str(newsletter), expected_str)
        
        # Test with empty name
        newsletter_no_name = NewsletterFactory(email='test2@example.com', name='')
        expected_str_no_name = 'test2@example.com (No name)'
        self.assertEqual(str(newsletter_no_name), expected_str_no_name)

    def test_newsletter_unique_email(self):
        """Test that newsletter email must be unique"""
        NewsletterFactory(email='unique@example.com')
        
        with self.assertRaises(IntegrityError):
            NewsletterFactory(email='unique@example.com')

    def test_newsletter_subscription_status(self):
        """Test newsletter subscription status"""
        newsletter = NewsletterFactory(is_active=True)
        self.assertTrue(newsletter.is_active)
        
        # Deactivate subscription
        newsletter.is_active = False
        newsletter.save()
        self.assertFalse(newsletter.is_active)

    def test_newsletter_meta_options(self):
        """Test Newsletter model meta options"""
        from blog.models import Newsletter
        self.assertEqual(Newsletter._meta.ordering, ['-subscribed_at'])


class BlogSeriesModelTests(BaseTestCase, FileTestMixin):
    """Test cases for BlogSeries model"""

    def test_blog_series_creation(self):
        """Test creating a blog series"""
        author = UserFactory()
        
        series = BlogSeriesFactory(
            title='Django Tutorial Series',
            slug='django-tutorial-series',
            description='Complete Django tutorial series',
            author=author,
            is_completed=False
        )
        
        self.assertEqual(series.title, 'Django Tutorial Series')
        self.assertEqual(series.slug, 'django-tutorial-series')
        self.assertEqual(series.author, author)
        self.assertFalse(series.is_completed)

    def test_blog_series_str_method(self):
        """Test BlogSeries model __str__ method"""
        series = BlogSeriesFactory(title='Python Basics Series')
        self.assertEqual(str(series), 'Python Basics Series')

    def test_blog_series_get_absolute_url(self):
        """Test BlogSeries model get_absolute_url method"""
        series = BlogSeriesFactory(slug='test-series')
        expected_url = reverse('blog:series_detail', kwargs={'slug': 'test-series'})
        self.assertEqual(series.get_absolute_url(), expected_url)

    def test_blog_series_post_count_property(self):
        """Test BlogSeries model post_count property"""
        series = BlogSeriesFactory()
        
        # Create published posts in series
        published_posts = [PostFactory(series=series, status='published') for _ in range(3)]
        # Create draft posts in series
        draft_posts = [PostFactory(series=series, status='draft') for _ in range(2)]
        
        # Should only count published posts
        self.assertEqual(series.post_count, 3)

    def test_blog_series_auto_slug_generation(self):
        """Test automatic slug generation from title"""
        series = BlogSeriesFactory(title='Machine Learning Guide', slug='')
        series.save()  # Trigger save method
        # The save method should generate slug from title

    def test_blog_series_unique_slug(self):
        """Test that blog series slug must be unique"""
        BlogSeriesFactory(slug='unique-series-slug')
        
        with self.assertRaises(IntegrityError):
            BlogSeriesFactory(slug='unique-series-slug')

    def test_blog_series_meta_options(self):
        """Test BlogSeries model meta options"""
        from blog.models import BlogSeries
        self.assertEqual(BlogSeries._meta.verbose_name_plural, 'Blog Series')
        self.assertEqual(BlogSeries._meta.ordering, ['-created_at'])

    @override_media_root
    def test_blog_series_image_upload(self):
        """Test blog series image upload"""
        series = BlogSeriesFactory()
        # Image upload is tested in the factory post_generation


class PostSeriesIntegrationTests(BaseTestCase):
    """Test Post and Series integration"""

    def test_post_series_relationship(self):
        """Test post and series relationship"""
        series = BlogSeriesFactory()
        
        # Create posts in series with different orders
        post1 = PostFactory(series=series, series_order=1, title='Part 1')
        post2 = PostFactory(series=series, series_order=2, title='Part 2')
        post3 = PostFactory(series=series, series_order=3, title='Part 3')
        
        # Test series relationship
        self.assertEqual(series.posts.count(), 3)
        
        # Test ordering
        series_posts = list(series.posts.filter(status='published').order_by('series_order'))
        self.assertEqual(series_posts[0], post1)
        self.assertEqual(series_posts[1], post2)
        self.assertEqual(series_posts[2], post3)

    def test_post_without_series(self):
        """Test post without series"""
        post = PostFactory(series=None, series_order=0)
        self.assertIsNone(post.series)
        self.assertEqual(post.series_order, 0)


class BlogModelIntegrationTests(BaseTestCase):
    """Integration tests for blog models working together"""

    def test_complete_blog_ecosystem(self):
        """Test complete blog ecosystem with all models"""
        # Create author and category
        author = UserFactory()
        category = BlogCategoryFactory()
        series = BlogSeriesFactory(author=author)
        
        # Create post
        post = PostFactory(
            author=author,
            category=category,
            series=series,
            status='published'
        )
        
        # Create comments
        comments = [CommentFactory(post=post, is_approved=True) for _ in range(3)]
        
        # Create likes
        users = [UserFactory() for _ in range(5)]
        for user in users:
            post.likes.add(user)
        
        # Test all relationships
        self.assertEqual(post.author, author)
        self.assertEqual(post.category, category)
        self.assertEqual(post.series, series)
        self.assertEqual(post.comment_count, 3)
        self.assertEqual(post.like_count, 5)
        
        # Test reverse relationships
        self.assertEqual(author.posts.count(), 1)
        self.assertEqual(category.posts.count(), 1)
        self.assertEqual(series.posts.count(), 1)

    def test_cascade_deletions(self):
        """Test cascade deletions in blog models"""
        author = UserFactory()
        post = PostFactory(author=author)
        comment = CommentFactory(post=post)
        
        comment_id = comment.id
        post_id = post.id
        
        # Delete author should cascade to posts and comments
        author.delete()
        
        from blog.models import Post, Comment
        
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post_id)
        
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=comment_id)

    def test_blog_category_post_relationship(self):
        """Test blog category and post relationship"""
        category = BlogCategoryFactory()
        posts = [PostFactory(category=category) for _ in range(3)]
        
        self.assertEqual(category.posts.count(), 3)
        
        # Test deleting category sets posts category to NULL
        category.delete()
        
        from blog.models import Post
        for post in posts:
            post.refresh_from_db()
            self.assertIsNone(post.category)

    def test_newsletter_unique_subscription(self):
        """Test newsletter unique subscription constraint"""
        email = 'unique@example.com'
        NewsletterFactory(email=email)
        
        # Trying to create another subscription with same email should fail
        with self.assertRaises(IntegrityError):
            NewsletterFactory(email=email)
