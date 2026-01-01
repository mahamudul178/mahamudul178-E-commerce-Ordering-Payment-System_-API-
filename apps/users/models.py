from django.db import models

# Create your models here.
"""
User Management Models
Location: apps/users/models.py

This module contains User and UserProfile models with OOP principles.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    """
    Custom user manager for User model
    Handles user creation and superuser creation
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with email and password
        
        Args:
            email (str): User's email address
            password (str): User's password
            **extra_fields: Additional user fields
            
        Returns:
            User: Created user instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        logger.info(f"User created: {email}")
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with admin privileges
        
        Args:
            email (str): Admin's email address
            password (str): Admin's password
            **extra_fields: Additional user fields
            
        Returns:
            User: Created superuser instance
            
        Raises:
            ValueError: If is_staff or is_superuser is not True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as the username field
    
    This model represents users in the system with role-based access control.
    It extends Django's AbstractBaseUser and PermissionsMixin for authentication.
    """
    
    class Role(models.TextChoices):
        """User role choices"""
        ADMIN = 'admin', 'Admin'
        CUSTOMER = 'customer', 'Customer'
    
    # Basic Information
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Email Address',
        help_text='User email address (unique)',
        error_messages={
            'unique': 'A user with this email already exists.'
        }
    )
    
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='First Name'
    )
    
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Last Name'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Phone Number',
        help_text='Contact phone number'
    )
    
    # Role and Permissions
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='User Role',
        help_text='User role in the system'
    )
    
    # Status Fields
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active Status',
        help_text='Designates whether this user should be treated as active.'
    )
    
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Staff Status',
        help_text='Designates whether the user can log into admin site.'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Email Verified',
        help_text='Designates whether the user has verified their email.'
    )
    
    # Timestamps
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name='Date Joined'
    )
    
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Login'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Updated'
    )
    
    # Manager
    objects = UserManager()
    
    # Authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email'], name='idx_users_email'),
            models.Index(fields=['role'], name='idx_users_role'),
            models.Index(fields=['is_active'], name='idx_users_active'),
        ]
    
    def __str__(self):
        """String representation of the user"""
        return self.email
    
    def __repr__(self):
        """Developer-friendly representation"""
        return f"<User: {self.email} ({self.role})>"
    
    def get_full_name(self):
        """
        Return the full name of the user
        
        Returns:
            str: Full name or email if name is not provided
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """
        Return the short name for the user
        
        Returns:
            str: First name or email
        """
        return self.first_name if self.first_name else self.email
    
    @property
    def is_admin(self):
        """
        Check if user has admin role
        
        Returns:
            bool: True if user is admin
        """
        return self.role == self.Role.ADMIN
    
    @property
    def is_customer(self):
        """
        Check if user has customer role
        
        Returns:
            bool: True if user is customer
        """
        return self.role == self.Role.CUSTOMER
    
    def has_perm(self, perm, obj=None):
        """
        Check if user has a specific permission
        Admins have all permissions
        """
        if self.is_active and self.is_superuser:
            return True
        return super().has_perm(perm, obj)
    
    def has_module_perms(self, app_label):
        """
        Check if user has permissions to view the app
        Admins have access to all modules
        """
        if self.is_active and self.is_superuser:
            return True
        return super().has_module_perms(app_label)


class UserProfile(models.Model):
    """
    Extended user profile with additional information
    
    This model stores additional user information like address,
    date of birth, and avatar. It has a one-to-one relationship
    with the User model.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
        verbose_name='User',
        help_text='Related user account'
    )
    
    # Address Information
    address_line_1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Address Line 1'
    )
    
    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Address Line 2'
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='City'
    )
    
    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='State/Division'
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Postal Code'
    )
    
    country = models.CharField(
        max_length=100,
        default='Bangladesh',
        verbose_name='Country'
    )
    
    # Additional Information
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date of Birth'
    )
    
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Profile Picture'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        """String representation of the profile"""
        return f"Profile of {self.user.email}"
    
    def __repr__(self):
        """Developer-friendly representation"""
        return f"<UserProfile: {self.user.email}>"
    
    def get_full_address(self):
        """
        Return formatted full address
        
        Returns:
            str: Complete formatted address
        """
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        # Filter out empty parts and join with comma
        return ', '.join(filter(None, address_parts))
    
    def get_age(self):
        """
        Calculate and return user's age
        
        Returns:
            int: Age in years or None if date_of_birth not set
        """
        if not self.date_of_birth:
            return None
        
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        
        return age