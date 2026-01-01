"""
User Management Serializers
Location: apps/users/serializers.py

This module contains all serializers for user-related API operations.
Serializers handle data validation, serialization, and deserialization.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model
    
    Handles serialization and deserialization of user profile data
    including address and personal information.
    """
    
    full_address = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postal_code',
            'country',
            'date_of_birth',
            'avatar',
            'full_address',
            'age',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'full_address', 'age']
    
    def get_full_address(self, obj):
        """Get formatted full address"""
        return obj.get_full_address()
    
    def get_age(self, obj):
        """Get calculated age"""
        return obj.get_age()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model - General purpose
    
    Used for displaying user information in API responses.
    Includes nested profile information.
    """
    
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone',
            'role',
            'full_name',
            'is_active',
            'is_verified',
            'date_joined',
            'last_login',
            'profile'
        ]
        read_only_fields = [
            'id',
            'role',
            'date_joined',
            'last_login',
            'is_verified'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    
    Handles new user registration with password validation
    and confirmation. Automatically creates associated UserProfile.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Password must be at least 8 characters with letters and numbers'
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Re-enter password for confirmation'
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate_email(self, value):
        """
        Validate email uniqueness
        
        Args:
            value (str): Email address to validate
            
        Returns:
            str: Lowercased email
            
        Raises:
            ValidationError: If email already exists
        """
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()
    
    def validate_phone(self, value):
        """
        Validate phone number format (optional but basic validation)
        
        Args:
            value (str): Phone number to validate
            
        Returns:
            str: Validated phone number
            
        Raises:
            ValidationError: If phone format is invalid
        """
        if value:
            # Remove spaces and dashes
            cleaned_phone = value.replace(' ', '').replace('-', '')
            
            # Check if it contains only digits and optional + at start
            if not cleaned_phone.replace('+', '').isdigit():
                raise serializers.ValidationError(
                    "Phone number must contain only digits."
                )
            
            # Check length (basic validation)
            if len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
                raise serializers.ValidationError(
                    "Phone number must be between 10 and 15 digits."
                )
        
        return value
    
    def validate(self, attrs):
        """
        Validate password match
        
        Args:
            attrs (dict): Validated field data
            
        Returns:
            dict: Validated data
            
        Raises:
            ValidationError: If passwords don't match
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create user with hashed password and profile
        
        Args:
            validated_data (dict): Validated user data
            
        Returns:
            User: Created user instance with profile
        """
        # Remove password_confirm as it's not needed
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create associated user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    
    Validates user credentials and returns authenticated user.
    """
    
    email = serializers.EmailField(
        required=True,
        help_text='User email address'
    )
    
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='User password'
    )
    
    def validate(self, attrs):
        """
        Validate user credentials
        
        Args:
            attrs (dict): Login credentials
            
        Returns:
            dict: Validated data with user object
            
        Raises:
            ValidationError: If credentials are invalid
        """
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        if email and password:
            # Authenticate user
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Invalid email or password.',
                    code='authorization'
                )
            
            # Check if user is active
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password
    
    Validates old password and updates to new password.
    """
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Current password'
    )
    
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='New password (must be strong)'
    )
    
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirm new password'
    )
    
    def validate_old_password(self, value):
        """
        Validate old password is correct
        
        Args:
            value (str): Old password
            
        Returns:
            str: Validated old password
            
        Raises:
            ValidationError: If old password is incorrect
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """
        Validate new password match
        
        Args:
            attrs (dict): Password data
            
        Returns:
            dict: Validated data
            
        Raises:
            ValidationError: If new passwords don't match
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "New password fields didn't match."
            })
        
        # Check if new password is different from old
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                "new_password": "New password must be different from old password."
            })
        
        return attrs
    
    def save(self, **kwargs):
        """
        Update user password
        
        Returns:
            User: Updated user instance
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    
    Allows users to update their personal information
    and profile details.
    """
    
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone',
            'profile'
        ]
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if value:
            cleaned_phone = value.replace(' ', '').replace('-', '')
            if not cleaned_phone.replace('+', '').isdigit():
                raise serializers.ValidationError(
                    "Phone number must contain only digits."
                )
            if len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
                raise serializers.ValidationError(
                    "Phone number must be between 10 and 15 digits."
                )
        return value
    
    def update(self, instance, validated_data):
        """
        Update user and profile
        
        Args:
            instance (User): User instance to update
            validated_data (dict): Validated update data
            
        Returns:
            User: Updated user instance
        """
        # Extract profile data if provided
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile if data provided
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance






class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for user list (minimal information)
    
    Used in list views where we don't need full details.
    """
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'role',
            'is_active',
            'date_joined'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name()
    
    
    
    