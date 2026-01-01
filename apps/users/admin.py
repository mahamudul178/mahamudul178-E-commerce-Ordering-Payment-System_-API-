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


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for User model
    """
    
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
    
    def get_full_name_display(self, obj):
        """Display full name in list view"""
        if not obj:
            return '-'
        try:
            full_name = obj.get_full_name()
            return full_name if full_name else '-'
        except Exception:
            return '-'
    get_full_name_display.short_description = 'Full Name'
    
    def role_badge(self, obj):
        """Display role as colored badge"""
        if not obj or not hasattr(obj, 'role'):
            return format_html('<span style="color: gray;">{}</span>', 'No role')
        try:
            colors = {
                'admin': '#dc3545',
                'customer': '#28a745'
            }
            color = colors.get(obj.role, '#6c757d')
            try:
                role_display = obj.get_role_display()
            except (AttributeError, Exception):
                role_display = str(obj.role) if obj.role else 'Unknown'
            
            return format_html(
                '<span style="background-color: {}; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                color,
                role_display
            )
        except Exception:
            return format_html('<span style="color: gray;">{}</span>', 'Error')
    role_badge.short_description = 'Role'
    
    def is_active_badge(self, obj):
        """Display active status as badge"""
        if not obj or not hasattr(obj, 'is_active'):
            return format_html('<span style="color: gray;">{}</span>', '-')
        
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✓ Active')
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', '✗ Inactive')
    is_active_badge.short_description = 'Status'
    
    def is_verified_badge(self, obj):
        """Display verified status as badge"""
        if not obj or not hasattr(obj, 'is_verified'):
            return format_html('<span style="color: gray;">{}</span>', '-')
        
        if obj.is_verified:
            return format_html('<span style="color: green;">{}</span>', '✓ Verified')
        else:
            return format_html('<span style="color: orange;">{}</span>', '✗ Not Verified')
    is_verified_badge.short_description = 'Email Verified'
    
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
    
    def user_email(self, obj):
        """Display user email"""
        if not obj or not hasattr(obj, 'user') or not obj.user or not hasattr(obj.user, 'email'):
            return '-'
        return obj.user.email or '-'
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def has_avatar(self, obj):
        """Check if user has avatar"""
        if not obj or not hasattr(obj, 'avatar') or not obj.avatar:
            return format_html('<span style="color: gray;">{}</span>', '✗ No')
        
        try:
            if hasattr(obj.avatar, 'name') and obj.avatar.name:
                return format_html('<span style="color: green;">{}</span>', '✓ Yes')
        except Exception:
            return format_html('<span style="color: gray;">{}</span>', '✗ No')
        
        return format_html('<span style="color: gray;">{}</span>', '✗ No')
    has_avatar.short_description = 'Has Avatar'


# Customize admin site header and title
admin.site.site_header = "E-Commerce Admin Panel"
admin.site.site_title = "E-Commerce Admin"
admin.site.index_title = "Welcome to E-Commerce Administration"




