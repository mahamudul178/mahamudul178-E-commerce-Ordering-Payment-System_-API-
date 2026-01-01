"""
User Management URLs
Location: apps/users/urls.py

URL routing for user-related API endpoints.
"""



from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    ChangePasswordView,
    UserLogoutView,
    UserDetailView,
    UserListView,
    UserDeleteView
)

app_name = 'users'

urlpatterns = [
    # ============================================
    # Authentication Endpoints
    # ============================================
    
    # Register new user
    # POST /api/users/register/
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # Login user
    # POST /api/users/login/
    path('login/', UserLoginView.as_view(), name='login'),
    
    # Logout user
    # POST /api/users/logout/
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    # Refresh access token
    # POST /api/users/token/refresh/
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ============================================
    # Profile Management Endpoints
    # ============================================
    
    # Get/Update current user profile
    # GET/PUT/PATCH /api/users/profile/
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # Change password
    # POST /api/users/change-password/
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # ============================================
    # User Management Endpoints (Admin/Self)
    # ============================================
    
    # List all users (Admin sees all, Users see only themselves)
    # GET /api/users/
    path('', UserListView.as_view(), name='user_list'),
    
    # Get user by ID
    # GET /api/users/{id}/
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    
    # Delete user (Admin only)
    # DELETE /api/users/{id}/
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
]