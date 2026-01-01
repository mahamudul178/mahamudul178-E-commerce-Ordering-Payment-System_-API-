from django.contrib import admin

# Register your models here.
"""
User Management Admin Configuration
Location: apps/users/admin.py

Django admin panel configuration for User and UserProfile models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for User model
    
    Provides a comprehensive interface for managing users
    in the Django admin panel.
    """
    
    # List display configuration
    list_display = [
        'email',
        'get_full_name_display',
        'role_badge',
        'is_active_badge',
        'is_verified_badge',
        'date_joined'
    ]
    
    list_filter = [
        'role',
        'is_active',
        'is_verified',
        'is_staff',
        'date_joined'
    ]
    
    search_fields = [
        'email',
        'first_name',
        'last_name',
        'phone'
    ]
    
    ordering = ['-date_joined']
    
    # Detail view configuration
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Permissions'), {
            'fields': (
                'role',
                'is_active',
                'is_verified',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Add user configuration
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'role',
                'is_active'
            ),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    # Custom display methods
    def get_full_name_display(self, obj):
        """Display full name in list view"""
        return obj.get_full_name()
    get_full_name_display.short_description = 'Full Name'
    
    def role_badge(self, obj):
        """Display role as colored badge"""
        colors = {
            'admin': '#dc3545',  # Red
            'customer': '#28a745'  # Green
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def is_active_badge(self, obj):
        """Display active status as badge"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactive</span>'
        )
    is_active_badge.short_description = 'Status'
    
    def is_verified_badge(self, obj):
        """Display verified status as badge"""
        if obj.is_verified:
            return format_html(
                '<span style="color: green;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: orange;">✗ Not Verified</span>'
        )
    is_verified_badge.short_description = 'Email Verified'
    
    # Actions
    actions = ['activate_users', 'deactivate_users', 'verify_users']
    
    def activate_users(self, request, queryset):
        """Bulk activate users"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} user(s) activated successfully.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Bulk deactivate users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def verify_users(self, request, queryset):
        """Bulk verify users"""
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} user(s) verified successfully.')
    verify_users.short_description = 'Verify selected users'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model
    
    Provides interface for managing user profiles
    including address and personal information.
    """
    
    list_display = [
        'user_email',
        'city',
        'country',
        'has_avatar',
        'created_at'
    ]
    
    list_filter = [
        'country',
        'city',
        'created_at'
    ]
    
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'city',
        'country'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Address Information'), {
            'fields': (
                'address_line_1',
                'address_line_2',
                'city',
                'state',
                'postal_code',
                'country'
            )
        }),
        (_('Additional Information'), {
            'fields': ('date_of_birth', 'avatar')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    # Custom display methods
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def has_avatar(self, obj):
        """Check if user has avatar"""
        if obj.avatar:
            return format_html(
                '<span style="color: green;">✓ Yes</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ No</span>'
        )
    has_avatar.short_description = 'Has Avatar'


# Customize admin site header and title
admin.site.site_header = "E-Commerce Admin Panel"
admin.site.site_title = "E-Commerce Admin"
admin.site.index_title = "Welcome to E-Commerce Administration"