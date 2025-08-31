from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ContactMessage, ContactReply, FAQ, ContactInfo


class ContactReplyInline(admin.TabularInline):
    model = ContactReply
    extra = 0
    readonly_fields = ['created_at', 'is_sent', 'sent_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'display_subject', 'status', 'priority',
        'created_at', 'read_at'
    ]
    list_filter = ['status', 'priority', 'subject', 'created_at']
    search_fields = ['name', 'email', 'message', 'company']
    list_editable = ['status', 'priority']
    date_hierarchy = 'created_at'
    inlines = [ContactReplyInline]
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'company', 'website')
        }),
        ('Message Details', {
            'fields': ('subject', 'subject_custom', 'message')
        }),
        ('Project Information', {
            'fields': ('project_budget', 'project_timeline'),
            'classes': ('collapse',)
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'read_at', 'replied_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'read_at', 'replied_at', 'ip_address', 'user_agent']
    
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_archived']
    
    def mark_as_read(self, request, queryset):
        updated = 0
        for message in queryset:
            if message.status == 'new':
                message.status = 'read'
                message.read_at = timezone.now()
                message.save()
                updated += 1
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_replied(self, request, queryset):
        updated = queryset.exclude(status='replied').update(
            status='replied', 
            replied_at=timezone.now()
        )
        self.message_user(request, f'{updated} messages marked as replied.')
    mark_as_replied.short_description = 'Mark selected messages as replied'
    
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} messages archived.')
    mark_as_archived.short_description = 'Archive selected messages'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()


@admin.register(ContactReply)
class ContactReplyAdmin(admin.ModelAdmin):
    list_display = [
        'contact_message', 'admin_user', 'subject', 'is_sent', 'sent_at', 'created_at'
    ]
    list_filter = ['is_sent', 'created_at', 'admin_user']
    search_fields = ['subject', 'message', 'contact_message__name', 'contact_message__email']
    readonly_fields = ['created_at', 'sent_at']
    date_hierarchy = 'created_at'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'category', 'is_featured', 'order', 'created_at']
    list_filter = ['category', 'is_featured', 'created_at']
    search_fields = ['question', 'answer']
    list_editable = ['is_featured', 'order', 'category']
    
    def question_preview(self, obj):
        return obj.question[:100] + '...' if len(obj.question) > 100 else obj.question
    question_preview.short_description = 'Question'


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['business_name', 'email', 'description']
    
    fieldsets = (
        ('Business Information', {
            'fields': ('business_name', 'tagline', 'description')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'address', 'business_hours')
        }),
        ('Social Media', {
            'fields': ('website', 'linkedin', 'twitter', 'facebook', 'instagram', 'github')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of contact info to maintain at least one record
        return False
