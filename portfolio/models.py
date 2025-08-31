from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from PIL import Image
from taggit.managers import TaggableManager

User = get_user_model()


class Category(models.Model):
    """Category model for projects"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('portfolio:category_detail', kwargs={'slug': self.slug})


class Skill(models.Model):
    """Skill model"""
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES)
    percentage = models.IntegerField(default=0, help_text="Proficiency percentage (0-100)")
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    category = models.CharField(max_length=100, blank=True, help_text="e.g., Programming, Design, etc.")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'user']
        ordering = ['-percentage', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_proficiency_display()})"


class Project(models.Model):
    """Project model for portfolio showcase"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, help_text="Brief description for cards")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    
    # Project details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    client = models.CharField(max_length=200, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Images and files
    featured_image = models.ImageField(upload_to='projects/featured/', blank=True)
    demo_url = models.URLField(blank=True, help_text="Live demo URL")
    source_url = models.URLField(blank=True, help_text="Source code URL (e.g., GitHub)")
    
    # Technologies
    technologies = models.TextField(
        blank=True, 
        help_text="Comma-separated list of technologies used"
    )
    
    # SEO and metadata
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name='liked_projects', blank=True)
    
    # Tags
    tags = TaggableManager(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
            models.Index(fields=['is_published', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('portfolio:project_detail', kwargs={'slug': self.slug})
    
    @property
    def technology_list(self):
        if self.technologies:
            return [tech.strip() for tech in self.technologies.split(',')]
        return []
    
    @property
    def like_count(self):
        return self.likes.count()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize featured image
        if self.featured_image:
            img = Image.open(self.featured_image.path)
            if img.height > 800 or img.width > 1200:
                output_size = (1200, 800)
                img.thumbnail(output_size, Image.Resampling.LANCZOS)
                img.save(self.featured_image.path, optimize=True, quality=85)


class ProjectImage(models.Model):
    """Additional images for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.project.title} - Image {self.order}"


class Experience(models.Model):
    """Work experience model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    company_url = models.URLField(blank=True)
    skills_used = models.TextField(
        blank=True,
        help_text="Comma-separated list of skills used in this role"
    )
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.position} at {self.company}"
    
    @property
    def duration(self):
        from django.utils import timezone
        end = self.end_date or timezone.now().date()
        duration = end - self.start_date
        years = duration.days // 365
        months = (duration.days % 365) // 30
        
        if years > 0:
            if months > 0:
                return f"{years} year{'s' if years > 1 else ''}, {months} month{'s' if months > 1 else ''}"
            return f"{years} year{'s' if years > 1 else ''}"
        return f"{months} month{'s' if months > 1 else ''}"


class Education(models.Model):
    """Education model"""
    DEGREE_CHOICES = [
        ('high_school', 'High School'),
        ('associate', 'Associate Degree'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    field_of_study = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    grade = models.CharField(max_length=50, blank=True, help_text="GPA, percentage, or grade")
    institution_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Education'
    
    def __str__(self):
        return f"{self.get_degree_display()} in {self.field_of_study} from {self.institution}"


class Achievement(models.Model):
    """Achievement/Award model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField()
    issuer = models.CharField(max_length=200, help_text="Organization that issued the achievement")
    date_received = models.DateField()
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='achievements/', blank=True)
    
    class Meta:
        ordering = ['-date_received']
    
    def __str__(self):
        return f"{self.title} - {self.issuer}"


class Testimonial(models.Model):
    """Client testimonials"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonials')
    client_name = models.CharField(max_length=200)
    client_position = models.CharField(max_length=200, blank=True)
    client_company = models.CharField(max_length=200, blank=True)
    client_image = models.ImageField(upload_to='testimonials/', blank=True)
    testimonial = models.TextField()
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    project = models.ForeignKey(
        Project, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='testimonials'
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Testimonial from {self.client_name}"
