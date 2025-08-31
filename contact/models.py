from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class ContactMessage(models.Model):
    """Contact form messages from website visitors"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    ]
    
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('project', 'Project Collaboration'),
        ('freelance', 'Freelance Work'),
        ('support', 'Technical Support'),
        ('partnership', 'Partnership Opportunity'),
        ('other', 'Other'),
    ]
    
    # Contact Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Message Details
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    subject_custom = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Custom subject if 'Other' is selected"
    )
    message = models.TextField()
    
    # Project Details (optional)
    project_budget = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Expected budget range"
    )
    project_timeline = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Expected project timeline"
    )
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    
    # IP and User Agent for security
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"
    
    @property
    def display_subject(self):
        if self.subject == 'other' and self.subject_custom:
            return self.subject_custom
        return self.get_subject_display()
    
    def mark_as_read(self):
        if self.status == 'new':
            self.status = 'read'
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
    
    def mark_as_replied(self):
        self.status = 'replied'
        from django.utils import timezone
        self.replied_at = timezone.now()
        self.save(update_fields=['status', 'replied_at'])


class ContactReply(models.Model):
    """Admin replies to contact messages"""
    contact_message = models.ForeignKey(
        ContactMessage, 
        on_delete=models.CASCADE, 
        related_name='replies'
    )
    admin_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="Admin who sent this reply"
    )
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Email status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reply to {self.contact_message.name} - {self.subject}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('services', 'Services'),
        ('pricing', 'Pricing'),
        ('technical', 'Technical'),
        ('support', 'Support'),
    ]
    
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
    
    def __str__(self):
        return self.question[:100]


class ContactInfo(models.Model):
    """Contact information and business details"""
    # Business Information
    business_name = models.CharField(max_length=100, default="Portfolio Platform")
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Contact Details
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Social Media
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    github = models.URLField(blank=True)
    
    # Business Hours
    business_hours = models.TextField(
        blank=True,
        help_text="e.g., Monday - Friday: 9:00 AM - 6:00 PM"
    )
    
    # Location (for maps)
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=8, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=11, 
        decimal_places=8, 
        null=True, 
        blank=True
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contact Information'
        verbose_name_plural = 'Contact Information'
    
    def __str__(self):
        return self.business_name
