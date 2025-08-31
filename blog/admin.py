from django.contrib import admin
from django.utils.html import format_html
from .models import BlogCategory, Post, Comment, Newsletter, BlogSeries


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'color_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def post_count(self, obj):
        return obj.posts.filter(status='published').count()
    post_count.short_description = 'Published Posts'
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category', 'status', 'is_featured',
        'views', 'like_count', 'comment_count', 'published_at'
    ]
    list_filter = [
        'status', 'is_featured', 'category', 'created_at', 'published_at', 'author'
    ]
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['likes']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'category', 'series', 'series_order')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image')
        }),
        ('Publishing', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'tags'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('reading_time', 'views', 'likes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['views', 'reading_time']
    
    def like_count(self, obj):
        return obj.like_count
    like_count.short_description = 'Likes'
    
    def comment_count(self, obj):
        return obj.comment_count
    comment_count.short_description = 'Comments'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new post
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'author', 'post', 'content_preview', 'is_approved', 'is_reply', 'created_at'
    ]
    list_filter = ['is_approved', 'created_at', 'post']
    search_fields = ['author__username', 'author__email', 'content']
    list_editable = ['is_approved']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def is_reply(self, obj):
        return obj.is_reply
    is_reply.boolean = True
    is_reply.short_description = 'Reply'


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email', 'name']
    list_editable = ['is_active']
    date_hierarchy = 'subscribed_at'
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscriptions activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscriptions deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'


@admin.register(BlogSeries)
class BlogSeriesAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'post_count', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'author', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    
    def post_count(self, obj):
        return obj.post_count
    post_count.short_description = 'Posts'
