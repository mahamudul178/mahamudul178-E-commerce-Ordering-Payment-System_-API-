"""
Product Management URLs
Location: apps/products/urls.py

URL routing for products and categories.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, ProductImageViewSet

app_name = 'products'

# Create router
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'images', ProductImageViewSet, basename='product-image')

urlpatterns = [
    path('', include(router.urls)),
]