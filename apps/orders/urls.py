"""
Order Management URLs
Location: apps/orders/urls.py

URL routing for orders and order items.
"""

from django.urls import path, include
# from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from .views import OrderViewSet, OrderItemViewSet

app_name = 'orders'

# Create router
router = SimpleRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')

urlpatterns = [
    path('', include(router.urls)),
]