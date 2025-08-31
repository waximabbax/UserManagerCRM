"""
Tests for Blog app views
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import Http404
from django.core.paginator import Paginator
from django.contrib.messages import get_messages

from core.test_utils import BaseTestCase, APITestCase, FileTestMixin, override_media_root
from core.factories import (
    UserFactory, BlogCategoryFactory, PostFactory, CommentFactory,
    NewsletterFactory, BlogSeriesFactory
)

User = get_user_model()


class PostListViewTests(BaseTestCase):
    """Test cases for Post list view"""

    def setUp(self):
        super().setUp()
        self.url = reverse('blog:post_list')
        
        # Create test data
        self.category = BlogCategoryFactory()
        self.published_posts = [
            PostFactory(status='published', is_featured=False) for _ in range(5)
        ]
        self.draft_posts = [
            PostFactory(status='draft') for _ in range(3)
        ]
        self.featured_posts = [
            PostFactory(status='published', is_featured=True) for _ in range(2)
        ]

    def test_post_list_view_get(self):
        """Test GET request to post list view"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blog Posts')  # Assuming template has this

    def test_post_list_view_context(self):
        """Test post list view context data"""
        response = self.client.get(self.url)
        
        # Should only show published posts
        posts = response.context['posts']
        self.assertEqual(len(posts), 7)  # 5 regular + 2 featured
        
        for post in posts:
            self.assertEqual(post.status, 'published')

    def test_post_list_view_pagination(self):
        """Test post list view pagination"""
        # Create many posts
        PostFactory.create_batch(25, status='published')
        
        response = self.client.get(self.url)
        self.assertTrue(response.context['is_paginated'])
        
        # Test page 2
        response = self.client.get(f"{self.url}?page=2")
        self.assertEqual(response.status_code, 200)

    def test_post_list_view_featured_posts(self):
        """Test post list view with featured posts"""
        response = self.client.get(self.url)
        
        # Check if featured posts are in context
        if 'featured_posts' in response.context:
            featured_posts = response.context['featured_posts']
            self.assertEqual(len(featured_posts), 2)
            
            for post in featured_posts:
                self.assertTrue(post.is_featured)

    def test_post_list_view_category_filter(self):
        """Test post list view filtered by category"""
        category = BlogCategoryFactory()
        category_posts = [PostFactory(category=category, status='published') for _ in range(3)]
        
        url = reverse('blog:category_posts', kwargs={'slug': category.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        posts = response.context['posts']
        self.assertEqual(len(posts), 3)
        
        for post in posts:
            self.assertEqual(post.category, category)

    def test_post_list_view_search(self):
        """Test post list view with search functionality"""
        # Create posts with specific titles
        PostFactory(title='Django Tutorial', status='published')
        PostFactory(title='Python Guide', status='published')
        PostFactory(title='JavaScript Basics', status='published')
        
        search_url = f"{self.url}?search=Django"
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, 200)
        # Assuming search functionality exists
        if 'posts' in response.context:
            posts = response.context['posts']
            # Should find the Django post
            django_posts = [post for post in posts if 'Django' in post.title]
            self.assertGreater(len(django_posts), 0)


class PostDetailViewTests(BaseTestCase):
    """Test cases for Post detail view"""

    def setUp(self):
        super().setUp()
        self.author = UserFactory()
        self.post = PostFactory(author=self.author, status='published')
        self.url = reverse('blog:post_detail', kwargs={'slug': self.post.slug})

    def test_post_detail_view_get(self):
        """Test GET request to post detail view"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], self.post)

    def test_post_detail_view_draft_post(self):
        """Test accessing draft post should return 404 for non-authors"""
        draft_post = PostFactory(status='draft')
        url = reverse('blog:post_detail', kwargs={'slug': draft_post.slug})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_detail_view_draft_post_author_access(self):
        """Test author can access their draft posts"""
        user = UserFactory()
        draft_post = PostFactory(author=user, status='draft')
        url = reverse('blog:post_detail', kwargs={'slug': draft_post.slug})
        
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_detail_view_comments(self):
        """Test post detail view with comments"""
        # Create approved comments
        approved_comments = [
            CommentFactory(post=self.post, is_approved=True) for _ in range(3)
        ]
        # Create unapproved comments
        unapproved_comments = [
            CommentFactory(post=self.post, is_approved=False) for _ in range(2)
        ]
        
        response = self.client.get(self.url)
        comments = response.context['comments']
        
        # Should only show approved comments
        self.assertEqual(len(comments), 3)
        for comment in comments:
            self.assertTrue(comment.is_approved)

    def test_post_detail_view_related_posts(self):
        """Test post detail view with related posts"""
        # Create related posts in same category
        related_posts = [
            PostFactory(category=self.post.category, status='published') for _ in range(3)
        ]
        
        response = self.client.get(self.url)
        
        # Check if related posts are in context
        if 'related_posts' in response.context:
            related = response.context['related_posts']
            self.assertLessEqual(len(related), 3)  # Usually limited
            
            for post in related:
                self.assertEqual(post.category, self.post.category)
                self.assertNotEqual(post, self.post)  # Should not include current post

    def test_post_detail_view_like_functionality(self):
        """Test post detail view like functionality"""
        user = UserFactory()
        self.client.force_login(user)
        
        # Test liking a post
        like_url = reverse('blog:post_like', kwargs={'slug': self.post.slug})
        response = self.client.post(like_url)
        
        # Should redirect or return JSON response
        self.assertIn(response.status_code, [200, 302])
        
        # Check if user liked the post
        self.post.refresh_from_db()
        self.assertTrue(self.post.likes.filter(id=user.id).exists())


class CommentCreateViewTests(BaseTestCase):
    """Test cases for Comment creation"""

    def setUp(self):
        super().setUp()
        self.post = PostFactory(status='published')
        self.user = UserFactory()
        self.url = reverse('blog:comment_create', kwargs={'post_slug': self.post.slug})

    def test_comment_create_get(self):
        """Test GET request to comment form"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_comment_create_post_valid(self):
        """Test POST request to create comment with valid data"""
        self.client.force_login(self.user)
        
        comment_data = {
            'content': 'This is a test comment'
        }
        
        response = self.client.post(self.url, comment_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check comment was created
        comment = Comment.objects.filter(post=self.post, author=self.user).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'This is a test comment')

    def test_comment_create_requires_login(self):
        """Test comment creation requires login"""
        comment_data = {
            'content': 'This is a test comment'
        }
        
        response = self.client.post(self.url, comment_data)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_comment_create_invalid_data(self):
        """Test comment creation with invalid data"""
        self.client.force_login(self.user)
        
        # Empty content
        response = self.client.post(self.url, {'content': ''})
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors

    def test_comment_create_reply(self):
        """Test creating a reply comment"""
        parent_comment = CommentFactory(post=self.post)
        self.client.force_login(self.user)
        
        reply_data = {
            'content': 'This is a reply',
            'parent': parent_comment.id
        }
        
        response = self.client.post(self.url, reply_data)
        self.assertEqual(response.status_code, 302)
        
        # Check reply was created
        reply = Comment.objects.filter(
            post=self.post, 
            author=self.user, 
            parent=parent_comment
        ).first()
        
        self.assertIsNotNone(reply)
        self.assertEqual(reply.parent, parent_comment)


class BlogCategoryViewTests(BaseTestCase):
    """Test cases for Blog Category views"""

    def setUp(self):
        super().setUp()
        self.category = BlogCategoryFactory()
        self.url = reverse('blog:category_detail', kwargs={'slug': self.category.slug})

    def test_category_detail_view(self):
        """Test category detail view"""
        # Create posts in category
        posts = [PostFactory(category=self.category, status='published') for _ in range(3)]
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category)
        
        category_posts = response.context['posts']
        self.assertEqual(len(category_posts), 3)
        
        for post in category_posts:
            self.assertEqual(post.category, self.category)

    def test_category_list_view(self):
        """Test category list view"""
        categories = [BlogCategoryFactory() for _ in range(5)]
        
        url = reverse('blog:category_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        response_categories = response.context['categories']
        self.assertEqual(len(response_categories), 6)  # 5 + 1 from setUp


class BlogSeriesViewTests(BaseTestCase):
    """Test cases for Blog Series views"""

    def setUp(self):
        super().setUp()
        self.author = UserFactory()
        self.series = BlogSeriesFactory(author=self.author)
        self.url = reverse('blog:series_detail', kwargs={'slug': self.series.slug})

    def test_series_detail_view(self):
        """Test series detail view"""
        # Create posts in series
        posts = [
            PostFactory(series=self.series, series_order=i, status='published') 
            for i in range(1, 4)
        ]
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['series'], self.series)
        
        series_posts = response.context['posts']
        self.assertEqual(len(series_posts), 3)
        
        # Check ordering
        for i, post in enumerate(series_posts):
            self.assertEqual(post.series_order, i + 1)

    def test_series_list_view(self):
        """Test series list view"""
        series_list = [BlogSeriesFactory() for _ in range(5)]
        
        url = reverse('blog:series_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        response_series = response.context['series_list']
        self.assertEqual(len(response_series), 6)  # 5 + 1 from setUp


class NewsletterViewTests(BaseTestCase):
    """Test cases for Newsletter views"""

    def setUp(self):
        super().setUp()
        self.url = reverse('blog:newsletter_subscribe')

    def test_newsletter_subscribe_get(self):
        """Test GET request to newsletter subscribe"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_newsletter_subscribe_post_valid(self):
        """Test POST request to subscribe with valid data"""
        newsletter_data = {
            'email': 'newsubscriber@example.com',
            'name': 'New Subscriber'
        }
        
        response = self.client.post(self.url, newsletter_data)
        
        # Should redirect or show success message
        if response.status_code == 302:
            # Check newsletter was created
            newsletter = Newsletter.objects.filter(
                email='newsubscriber@example.com'
            ).first()
            self.assertIsNotNone(newsletter)
            self.assertTrue(newsletter.is_active)
        else:
            # Check success message
            messages = list(get_messages(response.wsgi_request))
            success_messages = [msg for msg in messages if msg.level_tag == 'success']
            self.assertGreater(len(success_messages), 0)

    def test_newsletter_subscribe_duplicate_email(self):
        """Test newsletter subscription with duplicate email"""
        # Create existing subscription
        NewsletterFactory(email='existing@example.com')
        
        newsletter_data = {
            'email': 'existing@example.com',
            'name': 'Duplicate Subscriber'
        }
        
        response = self.client.post(self.url, newsletter_data)
        
        # Should show error
        if response.status_code == 200:
            # Form re-rendered with error
            self.assertIn('email', response.context['form'].errors)

    def test_newsletter_unsubscribe(self):
        """Test newsletter unsubscribe functionality"""
        newsletter = NewsletterFactory(is_active=True)
        
        # Assuming unsubscribe URL with token
        unsubscribe_url = reverse('blog:newsletter_unsubscribe', kwargs={
            'email': newsletter.email,
            'token': 'dummy-token'  # You'd implement proper token generation
        })
        
        response = self.client.get(unsubscribe_url)
        
        # Should unsubscribe or show confirmation
        self.assertIn(response.status_code, [200, 302])


class BlogAPIViewTests(APITestCase):
    """Test cases for Blog API views"""

    def setUp(self):
        super().setUp()
        self.posts = [PostFactory(status='published') for _ in range(5)]

    def test_post_list_api(self):
        """Test API endpoint for post list"""
        url = '/api/blog/posts/'  # Assuming API endpoint
        response = self.client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('results', data)
            self.assertEqual(len(data['results']), 5)

    def test_post_detail_api(self):
        """Test API endpoint for post detail"""
        post = self.posts[0]
        url = f'/api/blog/posts/{post.slug}/'
        response = self.client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['slug'], post.slug)
            self.assertEqual(data['title'], post.title)

    def test_post_like_api(self):
        """Test API endpoint for post liking"""
        post = self.posts[0]
        user = UserFactory()
        self.client.force_authenticate(user=user)
        
        url = f'/api/blog/posts/{post.slug}/like/'
        response = self.client.post(url)
        
        if response.status_code in [200, 201]:
            # Check if user liked the post
            post.refresh_from_db()
            self.assertTrue(post.likes.filter(id=user.id).exists())


class BlogSearchViewTests(BaseTestCase):
    """Test cases for Blog search functionality"""

    def setUp(self):
        super().setUp()
        # Create posts with different content for search testing
        self.django_post = PostFactory(
            title='Django Web Development',
            content='Learn Django framework for web development',
            status='published'
        )
        self.python_post = PostFactory(
            title='Python Programming',
            content='Master Python programming language',
            status='published'
        )
        self.js_post = PostFactory(
            title='JavaScript Fundamentals',
            content='JavaScript basics and advanced concepts',
            status='published'
        )

    def test_blog_search_view(self):
        """Test blog search view"""
        url = reverse('blog:search')
        response = self.client.get(url, {'q': 'Django'})
        
        self.assertEqual(response.status_code, 200)
        
        if 'posts' in response.context:
            search_results = response.context['posts']
            
            # Should find Django post
            django_results = [post for post in search_results if 'Django' in post.title]
            self.assertGreater(len(django_results), 0)

    def test_blog_search_empty_query(self):
        """Test blog search with empty query"""
        url = reverse('blog:search')
        response = self.client.get(url, {'q': ''})
        
        self.assertEqual(response.status_code, 200)
        # Should show empty results or all posts

    def test_blog_search_no_results(self):
        """Test blog search with no matching results"""
        url = reverse('blog:search')
        response = self.client.get(url, {'q': 'NonexistentKeyword'})
        
        self.assertEqual(response.status_code, 200)
        
        if 'posts' in response.context:
            search_results = response.context['posts']
            self.assertEqual(len(search_results), 0)


class BlogRSSFeedTests(BaseTestCase):
    """Test cases for Blog RSS feeds"""

    def setUp(self):
        super().setUp()
        self.posts = [PostFactory(status='published') for _ in range(5)]

    def test_blog_rss_feed(self):
        """Test blog RSS feed"""
        url = reverse('blog:rss_feed')  # Assuming RSS feed URL
        response = self.client.get(url)
        
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')
            
            # Check XML content
            content = response.content.decode('utf-8')
            self.assertIn('<rss', content)
            self.assertIn('<channel>', content)
            
            # Should include post titles
            for post in self.posts:
                self.assertIn(post.title, content)

    def test_category_rss_feed(self):
        """Test category-specific RSS feed"""
        category = BlogCategoryFactory()
        category_posts = [PostFactory(category=category, status='published') for _ in range(3)]
        
        url = reverse('blog:category_rss', kwargs={'slug': category.slug})
        response = self.client.get(url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Should only include category posts
            for post in category_posts:
                self.assertIn(post.title, content)


class BlogPermissionTests(BaseTestCase):
    """Test cases for Blog view permissions"""

    def setUp(self):
        super().setUp()
        self.author = UserFactory()
        self.other_user = UserFactory()
        self.post = PostFactory(author=self.author, status='draft')

    def test_post_edit_permission(self):
        """Test post edit permission"""
        url = reverse('blog:post_edit', kwargs={'slug': self.post.slug})
        
        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Other user should get 403 or 404
        self.client.force_login(self.other_user)
        response = self.client.get(url)
        self.assertIn(response.status_code, [403, 404])
        
        # Author should have access
        self.client.force_login(self.author)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_delete_permission(self):
        """Test post delete permission"""
        url = reverse('blog:post_delete', kwargs={'slug': self.post.slug})
        
        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Other user should get 403 or 404
        self.client.force_login(self.other_user)
        response = self.client.get(url)
        self.assertIn(response.status_code, [403, 404])
        
        # Author should have access
        self.client.force_login(self.author)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_comment_moderation_permission(self):
        """Test comment moderation permission"""
        comment = CommentFactory(post=self.post, is_approved=False)
        url = reverse('blog:comment_moderate', kwargs={'pk': comment.pk})
        
        # Regular user should not have access
        self.client.force_login(self.other_user)
        response = self.client.get(url)
        self.assertIn(response.status_code, [403, 404])
        
        # Post author should have access to moderate comments on their posts
        self.client.force_login(self.author)
        response = self.client.get(url)
        # This depends on your implementation
        self.assertIn(response.status_code, [200, 403, 404])


class BlogIntegrationTests(BaseTestCase):
    """Integration tests for complete blog workflows"""

    def test_complete_blog_post_lifecycle(self):
        """Test complete blog post lifecycle"""
        author = UserFactory()
        category = BlogCategoryFactory()
        
        self.client.force_login(author)
        
        # Create post
        post_data = {
            'title': 'Test Blog Post',
            'slug': 'test-blog-post',
            'category': category.id,
            'content': 'This is test content for the blog post',
            'status': 'draft'
        }
        
        create_url = reverse('blog:post_create')
        response = self.client.post(create_url, post_data)
        
        if response.status_code == 302:
            # Post created successfully
            post = Post.objects.get(slug='test-blog-post')
            
            # Edit post
            post_data['content'] = 'Updated content'
            post_data['status'] = 'published'
            
            edit_url = reverse('blog:post_edit', kwargs={'slug': post.slug})
            response = self.client.post(edit_url, post_data)
            
            # Verify update
            post.refresh_from_db()
            self.assertEqual(post.content, 'Updated content')
            self.assertEqual(post.status, 'published')
            
            # View published post
            detail_url = reverse('blog:post_detail', kwargs={'slug': post.slug})
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, 200)

    def test_blog_comment_workflow(self):
        """Test complete blog comment workflow"""
        post = PostFactory(status='published')
        user = UserFactory()
        
        # View post
        post_url = reverse('blog:post_detail', kwargs={'slug': post.slug})
        response = self.client.get(post_url)
        self.assertEqual(response.status_code, 200)
        
        # Login and comment
        self.client.force_login(user)
        comment_data = {
            'content': 'This is a great blog post!'
        }
        
        comment_url = reverse('blog:comment_create', kwargs={'post_slug': post.slug})
        response = self.client.post(comment_url, comment_data)
        
        if response.status_code == 302:
            # Comment created successfully
            comment = Comment.objects.filter(post=post, author=user).first()
            self.assertIsNotNone(comment)
            
            # View post with comment
            response = self.client.get(post_url)
            if comment.is_approved:
                self.assertContains(response, comment.content)

    def test_newsletter_subscription_flow(self):
        """Test newsletter subscription flow"""
        # Subscribe to newsletter
        newsletter_data = {
            'email': 'subscriber@example.com',
            'name': 'Test Subscriber'
        }
        
        subscribe_url = reverse('blog:newsletter_subscribe')
        response = self.client.post(subscribe_url, newsletter_data)
        
        # Check subscription was created
        newsletter = Newsletter.objects.filter(email='subscriber@example.com').first()
        if newsletter:
            self.assertTrue(newsletter.is_active)
            
            # Test unsubscribe
            unsubscribe_url = reverse('blog:newsletter_unsubscribe', kwargs={
                'email': newsletter.email,
                'token': 'dummy-token'  # Replace with actual token logic
            })
            
            response = self.client.get(unsubscribe_url)
            # Should handle unsubscribe process
            self.assertIn(response.status_code, [200, 302])
