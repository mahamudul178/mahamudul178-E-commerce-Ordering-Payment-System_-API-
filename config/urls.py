"""
Main URL Configuration
Location: config/urls.py

This module defines the main URL routing for the entire project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ==================================================
# Swagger/OpenAPI Schema Configuration
# ==================================================

schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce Backend API",
        default_version='v1',
        description="""
        Comprehensive E-Commerce Backend API Documentation
        
        ## Features:
        - User Management (Registration, Login, Profile)
        - Product Management (CRUD, Categories)
        - Order Management (Create, Track Orders)
        - Payment Integration (Stripe, bKash)
        
        ## Authentication:
        This API uses JWT (JSON Web Tokens) for authentication.
        
        ### How to authenticate:
        1. Register a new user at `/api/users/register/`
        2. Login at `/api/users/login/` to get tokens
        3. Use the access token in the Authorization header:
           `Authorization: Bearer <your_access_token>`
        
        ### Token Refresh:
        When access token expires, use refresh token at `/api/users/token/refresh/`
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(
            name="E-Commerce Support",
            email="support@ecommerce.com"
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# ==================================================
# URL Patterns
# ==================================================

urlpatterns = [
    # ============================================
    # Admin Panel
    # ============================================
    path('admin/', admin.site.urls),
    
    # ============================================
    # API Documentation
    # ============================================
    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),
    path(
        'redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'
    ),
    path(
        'swagger.json',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
    ),
    path(
        'swagger.yaml',
        schema_view.without_ui(cache_timeout=0),
        name='schema-yaml'
    ),
    
 
    # ----------API Endpoints-----------------
    
    # User Management API
    path('api/users/', include('apps.users.urls')),
    
    # Product Management API 
    path('api/products/', include('apps.products.urls')),
    
    # Order Management API 
    path('api/orders/', include('apps.orders.urls')),
    
    # Payment API 
    path('api/payments/', include('apps.payments.urls')),
]

# ==================================================
# Serve Media Files in Development
# ==================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    
    # Debug toolbar (optional - install django-debug-toolbar if needed)
    # import debug_toolbar
    # urlpatterns = [
    #     path('__debug__/', include(debug_toolbar.urls)),
    # ] + urlpatterns

# ==================================================
# Custom Error Handlers (Optional)
# ==================================================

# handler404 = 'apps.core.views.custom_404'
# handler500 = 'apps.core.views.custom_500'
# handler403 = 'apps.core.views.custom_403'
# handler400 = 'apps.core.views.custom_400'