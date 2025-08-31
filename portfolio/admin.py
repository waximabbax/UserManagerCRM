from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Project, ProjectImage, Skill, Experience, 
    Education, Achievement, Testimonial
)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ['image', 'caption', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'project_count', 'color_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def project_count(self, obj):
        return obj.project_set.count()
    project_count.short_description = 'Projects'
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'category', 'status', 'is_featured', 'is_published',
        'views', 'like_count', 'created_at'
    ]
    list_filter = [
        'status', 'is_featured', 'is_published', 'category', 'created_at', 'user'
    ]
    search_fields = ['title', 'description', 'technologies']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['likes']
    inlines = [ProjectImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'user', 'category')
        }),
        ('Content', {
            'fields': ('short_description', 'description', 'featured_image')
        }),
        ('Project Details', {
            'fields': ('status', 'start_date', 'end_date', 'client', 'budget')
        }),
        ('Links & Technologies', {
            'fields': ('demo_url', 'source_url', 'technologies')
        }),
        ('SEO & Publishing', {
            'fields': ('is_featured', 'is_published', 'tags')
        }),
        ('Statistics', {
            'fields': ('views', 'likes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['views']
    
    def like_count(self, obj):
        return obj.like_count
    like_count.short_description = 'Likes'


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'category', 'proficiency', 'percentage', 'created_at']
    list_filter = ['proficiency', 'category', 'user', 'created_at']
    search_fields = ['name', 'category']
    list_editable = ['percentage']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = [
        'position', 'company', 'user', 'start_date', 'end_date', 'is_current'
    ]
    list_filter = ['is_current', 'start_date', 'user']
    search_fields = ['position', 'company', 'description']
    date_hierarchy = 'start_date'


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = [
        'degree', 'field_of_study', 'institution', 'user', 'start_date', 'end_date'
    ]
    list_filter = ['degree', 'is_current', 'start_date', 'user']
    search_fields = ['institution', 'field_of_study', 'description']
    date_hierarchy = 'start_date'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'issuer', 'user', 'date_received']
    list_filter = ['date_received', 'issuer', 'user']
    search_fields = ['title', 'issuer', 'description']
    date_hierarchy = 'date_received'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = [
        'client_name', 'client_company', 'user', 'rating', 'is_featured', 'created_at'
    ]
    list_filter = ['rating', 'is_featured', 'created_at', 'user']
    search_fields = ['client_name', 'client_company', 'testimonial']
    list_editable = ['is_featured', 'rating']
