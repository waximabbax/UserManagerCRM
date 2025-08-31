from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from PIL import Image

User = get_user_model()


class BlogCategory(models.Model):
    """Blog category model"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Blog Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    """Blog post model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(
        BlogCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='posts'
    )
    
    # Content
    excerpt = models.CharField(
        max_length=300, 
        help_text="Brief description for social media and search engines"
    )
    content = RichTextUploadingField()
    
    # Images
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True)
    
    # Meta information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    reading_time = models.PositiveIntegerField(
        default=0, 
        help_text="Estimated reading time in minutes"
    )
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Engagement
    views = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    
    # Tags
    tags = TaggableManager(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.filter(is_approved=True).count()
    
    def calculate_reading_time(self):
        """Calculate reading time based on content length"""
        import re
        from django.utils.html import strip_tags
        
        # Remove HTML tags and count words
        text = strip_tags(self.content)
        word_count = len(re.findall(r'\w+', text))
        
        # Average reading speed: 200 words per minute
        reading_time = max(1, round(word_count / 200))
        return reading_time
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-calculate reading time
        if self.content:
            self.reading_time = self.calculate_reading_time()
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Resize featured image
        if self.featured_image:
            img = Image.open(self.featured_image.path)
            if img.height > 600 or img.width > 1200:
                output_size = (1200, 600)
                img.thumbnail(output_size, Image.Resampling.LANCZOS)
                img.save(self.featured_image.path, optimize=True, quality=85)


class Comment(models.Model):
    """Blog comment model"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='replies'
    )
    
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'
    
    @property
    def is_reply(self):
        return self.parent is not None


class Newsletter(models.Model):
    """Newsletter subscription model"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.email} ({self.name or "No name"})'
    
    class Meta:
        ordering = ['-subscribed_at']


class BlogSeries(models.Model):
    """Blog series to group related posts"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='blog/series/', blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_series')
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Blog Series'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:series_detail', kwargs={'slug': self.slug})
    
    @property
    def post_count(self):
        return self.posts.filter(status='published').count()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


# Add series field to Post model
Post.add_to_class(
    'series',
    models.ForeignKey(
        BlogSeries,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
)

Post.add_to_class(
    'series_order',
    models.PositiveIntegerField(
        default=0,
        help_text="Order of this post in the series"
    )
)
