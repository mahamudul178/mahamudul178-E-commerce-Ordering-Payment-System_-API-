"""
Order Management Views
Location: apps/orders/views.py

Views for order CRUD operations and management.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Order, OrderItem, OrderStatusHistory
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderStatusUpdateSerializer,
    OrderItemUpdateSerializer,
    OrderSummarySerializer
)
from apps.users.permissions import IsAdmin

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order CRUD operations
    
    Customers can only see their own orders.
    Admins can see all orders.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['order_number', 'shipping_address', 'shipping_city']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return orders based on user role
        
        - Customers: Only their own orders
        - Admins: All orders
        """
        user = self.request.user
        
        if user.is_admin or user.is_staff:
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(user=user)
        
        # Optimize queries
        queryset = queryset.select_related('user').prefetch_related(
            'items__product',
            'status_history'
        )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderDetailSerializer
    
    @swagger_auto_schema(
        operation_description="Create a new order with items",
        request_body=OrderCreateSerializer,
        responses={201: OrderDetailSerializer}
    )
    def create(self, request, *args, **kwargs):
        """
        Create new order
        
        Creates order with multiple items and calculates totals.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        logger.info(f"Order created: {order.order_number} by {request.user.email}")
        
        return Response({
            'message': 'Order created successfully',
            'order': OrderDetailSerializer(order, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="Get order detail",
        responses={200: OrderDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """Get order detail"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'message': 'Order retrieved successfully',
            'order': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Update order status",
        request_body=OrderStatusUpdateSerializer,
        responses={200: OrderDetailSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def update_status(self, request, pk=None):
        """
        Update order status (Admin only)
        
        Validates status transitions and creates history entry.
        """
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.save()
        
        logger.info(
            f"Order {order.order_number} status updated to {updated_order.status} "
            f"by {request.user.email}"
        )
        
        return Response({
            'message': 'Order status updated successfully',
            'order': OrderDetailSerializer(updated_order, context={'request': request}).data
        })
    
    @swagger_auto_schema(
        operation_description="Cancel order",
        responses={200: OrderDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel order
        
        Customers can cancel their own pending orders.
        Admins can cancel any order (except delivered).
        """
        order = self.get_object()
        
        # Check permissions
        if not (request.user == order.user or request.user.is_admin):
            return Response({
                'error': 'You do not have permission to cancel this order'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if can be canceled
        if not order.can_be_canceled:
            return Response({
                'error': f'Order cannot be canceled. Current status: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel order
        order.cancel_order()
        
        logger.info(f"Order {order.order_number} canceled by {request.user.email}")
        
        return Response({
            'message': 'Order canceled successfully',
            'order': OrderDetailSerializer(order, context={'request': request}).data
        })
    
    @swagger_auto_schema(
        operation_description="Update order item quantity",
        request_body=OrderItemUpdateSerializer
    )
    @action(detail=True, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, pk=None, item_id=None):
        """
        Update order item quantity
        
        Only for pending orders.
        """
        order = self.get_object()
        
        # Only allow for pending orders
        if order.status != Order.Status.PENDING:
            return Response({
                'error': 'Can only update items in pending orders'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get order item
        try:
            order_item = OrderItem.objects.get(id=item_id, order=order)
        except OrderItem.DoesNotExist:
            return Response({
                'error': 'Order item not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update quantity
        serializer = OrderItemUpdateSerializer(
            data=request.data,
            context={'order_item': order_item}
        )
        serializer.is_valid(raise_exception=True)
        updated_item = serializer.save()
        
        # Reload order to get updated totals
        order.refresh_from_db()
        
        return Response({
            'message': 'Order item updated successfully',
            'order': OrderDetailSerializer(order, context={'request': request}).data
        })
    
    @swagger_auto_schema(
        operation_description="Get order summary statistics (Admin only)",
        responses={200: OrderSummarySerializer}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def summary(self, request):
        """
        Get order summary statistics
        
        Returns total orders, revenue, average order value, etc.
        """
        queryset = self.get_queryset()
        
        summary = {
            'total_orders': queryset.count(),
            'pending_orders': queryset.filter(status=Order.Status.PENDING).count(),
            'paid_orders': queryset.filter(status=Order.Status.PAID).count(),
            'total_revenue': queryset.filter(
                status__in=[Order.Status.PAID, Order.Status.PROCESSING, 
                           Order.Status.SHIPPED, Order.Status.DELIVERED]
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            'average_order_value': queryset.aggregate(
                avg=Avg('total_amount')
            )['avg'] or 0
        }
        
        serializer = OrderSummarySerializer(summary)
        
        return Response({
            'message': 'Order summary retrieved successfully',
            'summary': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Get my orders (customer)",
        responses={200: OrderListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        Get orders for current user
        
        Returns all orders for the authenticated user.
        """
        orders = Order.objects.filter(user=request.user).select_related('user').prefetch_related('items')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        serializer = OrderListSerializer(orders, many=True, context={'request': request})
        
        return Response({
            'message': 'Your orders retrieved successfully',
            'count': orders.count(),
            'orders': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Get order status history",
        responses={200: openapi.Response('Order status history')}
    )
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get status change history for order"""
        order = self.get_object()
        history = order.status_history.all()
        
        from .serializers import OrderStatusHistorySerializer
        serializer = OrderStatusHistorySerializer(history, many=True)
        
        return Response({
            'message': 'Order history retrieved successfully',
            'count': history.count(),
            'history': serializer.data
        })


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OrderItem read operations
    
    Items are managed through Order endpoints.
    This is for viewing only.
    """
    queryset = OrderItem.objects.select_related('order', 'product')
    permission_classes = [IsAuthenticated]
    
    from .serializers import OrderItemSerializer
    serializer_class = OrderItemSerializer
    
    def get_queryset(self):
        """Filter items by user's orders"""
        user = self.request.user
        
        if user.is_admin or user.is_staff:
            return OrderItem.objects.all().select_related('order', 'product')
        else:
            return OrderItem.objects.filter(
                order__user=user
            ).select_related('order', 'product')