"""
User Management Permissions
Location: apps/users/permissions.py

Custom permission classes for user-related operations.
"""

from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to view/edit their own profile
    or allow admins to view/edit any profile.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the object
        
        Args:
            request: HTTP request
            view: View being accessed
            obj: Object being accessed (User instance)
            
        Returns:
            bool: True if user has permission
        """
        # Admins can access any user
        if request.user.is_admin or request.user.is_staff:
            return True
        
        # Users can only access their own profile
        return obj == request.user


class IsAdmin(permissions.BasePermission):
    """
    Permission class to only allow admin users
    """
    
    def has_permission(self, request, view):
        """
        Check if user is an admin
        
        Args:
            request: HTTP request
            view: View being accessed
            
        Returns:
            bool: True if user is admin
        """
        return request.user and request.user.is_authenticated and request.user.is_admin