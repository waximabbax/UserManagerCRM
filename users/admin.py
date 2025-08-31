from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Profile
from .forms import UserRegistrationForm, CustomUserChangeForm


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserRegistrationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_verified', 'is_staff', 'created_at']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'is_verified', 'created_at']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'bio', 'profile_picture')
        }),
        ('Social Links', {
            'fields': ('website', 'github', 'linkedin', 'twitter'),
            'classes': ('collapse',)
        }),
        ('Location & Status', {
            'fields': ('location', 'is_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProfileInline]
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'position', 'is_available_for_hire', 'hourly_rate']
    list_filter = ['is_available_for_hire', 'company']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'company', 'position']
    readonly_fields = ['skill_list']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'phone', 'date_of_birth')
        }),
        ('Professional Information', {
            'fields': ('company', 'position', 'skills', 'skill_list', 'resume')
        }),
        ('Availability', {
            'fields': ('is_available_for_hire', 'hourly_rate')
        }),
    )
    
    def skill_list(self, obj):
        if obj.skills:
            skills = obj.skill_list
            return format_html('<br>'.join([f'• {skill}' for skill in skills]))
        return 'No skills added'
    skill_list.short_description = 'Skills List'
