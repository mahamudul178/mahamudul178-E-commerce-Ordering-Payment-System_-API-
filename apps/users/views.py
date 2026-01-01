
# Create your views here.
"""
User Management Views
Location: apps/users/views.py

This module contains all API views for user management operations.
Views handle HTTP requests and return appropriate responses.
"""

from rest_framework import status, generics, permissions, authentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    ChangePasswordSerializer,
    UserUpdateSerializer,
    UserListSerializer
)
from .permissions import IsOwnerOrAdmin

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration
    
    POST /api/users/register/
    
    Allows new users to create an account. Returns user data
    and JWT tokens for immediate authentication.
    
    Public endpoint - no authentication required.
    """
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        responses={
            201: openapi.Response(
                description="User created successfully",
                examples={
                    "application/json": {
                        "message": "User registered successfully",
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "first_name": "John",
                            "last_name": "Doe"
                        },
                        "tokens": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                        }
                    }
                }
            ),
            400: "Bad Request - Validation Error"
        }
    )
    def create(self, request, *args, **kwargs):
        """
        Handle user registration
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: User data and JWT tokens
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"New user registered: {user.email}")
        
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    API endpoint for user login
    
    POST /api/users/login/
    
    Authenticates user credentials and returns JWT tokens.
    Public endpoint - no authentication required.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login with email and password",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "message": "Login successful",
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "role": "customer"
                        },
                        "tokens": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                        }
                    }
                }
            ),
            400: "Bad Request - Invalid credentials"
        }
    )
    def post(self, request):
        """
        Handle user login
        
        Args:
            request: HTTP request with email and password
            
        Returns:
            Response: User data and JWT tokens
        """
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"User logged in: {user.email}")
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for viewing and updating user profile
    
    GET /api/users/profile/
    PUT /api/users/profile/
    PATCH /api/users/profile/
    
    Allows authenticated users to view and update their own profile.
    Requires authentication.
    """
    
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get the current authenticated user"""
        return self.request.user
    
    @swagger_auto_schema(
        operation_description="Get current user profile",
        responses={
            200: UserSerializer,
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Get user profile
        
        Args:
            request: HTTP request
            
        Returns:
            Response: User profile data
        """
        instance = self.get_object()
        serializer = UserSerializer(instance)
        return Response({
            'message': 'Profile retrieved successfully',
            'user': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Update user profile",
        responses={
            200: UserSerializer,
            400: "Bad Request - Validation Error",
            401: "Unauthorized"
        }
    )
    def update(self, request, *args, **kwargs):
        """
        Update user profile
        
        Args:
            request: HTTP request with update data
            
        Returns:
            Response: Updated user data
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        logger.info(f"User profile updated: {instance.email}")
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(instance).data
        })


class ChangePasswordView(APIView):
    """
    API endpoint for changing password
    
    POST /api/users/change-password/
    
    Allows authenticated users to change their password.
    Requires old password verification.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Change user password",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully"
            ),
            400: "Bad Request - Validation Error",
            401: "Unauthorized"
        }
    )
    def post(self, request):
        """
        Handle password change
        
        Args:
            request: HTTP request with old and new passwords
            
        Returns:
            Response: Success message
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"Password changed for user: {request.user.email}")
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class UserLogoutView(APIView):
    """
    API endpoint for user logout
    
    POST /api/users/logout/
    
    Blacklists the refresh token to prevent further use.
    Requires authentication.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Logout user and blacklist refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Refresh token to blacklist'
                )
            }
        ),
        responses={
            200: openapi.Response(description="Logout successful"),
            400: "Bad Request - Invalid token",
            401: "Unauthorized"
        }
    )
    def post(self, request):
        """
        Handle user logout

        """
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logger.info(f"User logged out: {request.user.email}")
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(generics.RetrieveAPIView):
    """
    API endpoint for getting user details by ID
    
    GET /api/users/{id}/
    
    Admins can view any user. Regular users can only view themselves.
    Requires authentication.
    """
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = User.objects.all()
    
    @swagger_auto_schema(
        operation_description="Get user details by ID",
        responses={
            200: UserSerializer,
            401: "Unauthorized",
            403: "Forbidden - No permission",
            404: "Not Found"
        }
    )
    def get(self, request, *args, **kwargs):
        """Get user details"""
        return super().get(request, *args, **kwargs)


class UserListView(generics.ListAPIView):
    """
    API endpoint for listing all users
    
    GET /api/users/
    
    Admins can list all users. Regular users can only see themselves.
    Supports pagination, search, and filtering.
    Requires authentication.
    """
    
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [authentication.TokenAuthentication]
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    filterset_fields = ['role', 'is_active', 'is_verified']
    ordering_fields = ['date_joined', 'email']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        """
        Get queryset based on user role
        
        Admins see all users, regular users see only themselves.
        
        Returns:
            QuerySet: Filtered user queryset
        """
        if self.request.user.is_admin or self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

        # user = self.request.user
        # if user.is_authenticated and (user.is_superuser or user.is_staff or user.is_admin):
        #     return User.objects.all()

        # return User.objects.filter(id=user.id)
    
    
    @swagger_auto_schema(
        operation_description="List users (admin can see all, users see only themselves)",
        responses={
            200: UserListSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def get(self, request, *args, **kwargs):
        """List users"""
        return super().get(request, *args, **kwargs)


class UserDeleteView(generics.DestroyAPIView):
    """
    API endpoint for deleting user account
    
    DELETE /api/users/{id}/
    
    Only admins can delete user accounts.
    Requires admin authentication.
    """
    
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Delete user account (admin only)",
        responses={
            204: "User deleted successfully",
            401: "Unauthorized",
            403: "Forbidden - Admin only",
            404: "Not Found"
        }
    )
    
    def delete(self, request, *args, **kwargs):
        """
        Delete user account
        """
        instance = self.get_object()
        email = instance.email
        self.perform_destroy(instance)
        
        logger.info(f"User deleted by admin: {email}")
        
        return Response({
            'message': f'User {email} deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
        
        
        
