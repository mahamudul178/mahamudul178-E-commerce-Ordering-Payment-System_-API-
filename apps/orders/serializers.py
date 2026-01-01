"""
Order Management Serializers
Location: apps/orders/serializers.py

Serializers for orders, order items, and status history.
"""

from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem, OrderStatusHistory
from apps.products.models import Product
from apps.products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items with product details"""
    
    product_details = ProductListSerializer(source='product', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'product_details', 'quantity', 'price',
            'subtotal', 'created_at'
        ]
        read_only_fields = ['id', 'price', 'subtotal', 'created_at']
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items"""
    
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    
    def validate_product_id(self, value):
        """Validate product exists and is available"""
        try:
            product = Product.objects.get(id=value)
            if not product.is_in_stock:
                raise serializers.ValidationError(
                    f"Product '{product.name}' is not in stock."
                )
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
    
    def validate(self, attrs):
        """Validate stock availability"""
        product = Product.objects.get(id=attrs['product_id'])
        quantity = attrs['quantity']
        
        if quantity > product.stock:
            raise serializers.ValidationError({
                'quantity': f"Only {product.stock} items available in stock."
            })
        
        return attrs


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for order status history"""
    
    changed_by_name = serializers.CharField(
        source='changed_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'from_status', 'to_status',
            'changed_by', 'changed_by_name',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list view (minimal data)"""
    
    customer_name = serializers.CharField(source='user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='user.email', read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'status', 'status_display', 'total_amount',
            'item_count', 'created_at', 'paid_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order detail view (complete data)"""
    
    customer_name = serializers.CharField(source='user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='user.email', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    can_be_canceled = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'customer_name', 'customer_email',
            'subtotal', 'tax', 'shipping_cost', 'discount', 'total_amount',
            'status', 'status_display', 'is_paid', 'can_be_canceled',
            'shipping_address', 'shipping_city', 'shipping_postal_code',
            'shipping_phone', 'notes', 'item_count',
            'items', 'status_history',
            'created_at', 'updated_at', 'paid_at',
            'shipped_at', 'delivered_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'subtotal', 'tax', 'total_amount',
            'created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    
    items = OrderItemCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_city',
            'shipping_postal_code', 'shipping_phone',
            'notes', 'items', 'shipping_cost', 'discount'
        ]
    
    def validate_items(self, value):
        """Validate at least one item"""
        if not value:
            raise serializers.ValidationError("Order must have at least one item.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create order with items
        
        Uses transaction to ensure atomicity:
        - Create order
        - Create all items
        - Calculate totals
        """
        items_data = validated_data.pop('items')
        
        # Get current user
        user = self.context['request'].user
        
        # Create order
        order = Order.objects.create(
            user=user,
            **validated_data
        )
        
        # Create order items
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price  # Store current price
            )
        
        # Calculate and save totals
        order.calculate_totals()
        order.save()
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order details"""
    
    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_city',
            'shipping_postal_code', 'shipping_phone',
            'notes', 'shipping_cost', 'discount'
        ]
    
    def update(self, instance, validated_data):
        """Update order and recalculate totals"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Recalculate if shipping or discount changed
        if 'shipping_cost' in validated_data or 'discount' in validated_data:
            instance.calculate_totals()
        
        instance.save()
        return instance


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status"""
    
    status = serializers.ChoiceField(choices=Order.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Validate status transition"""
        order = self.context.get('order')
        current_status = order.status
        
        # Define allowed transitions
        allowed_transitions = {
            Order.Status.PENDING: [Order.Status.PAID, Order.Status.CANCELED],
            Order.Status.PAID: [Order.Status.PROCESSING, Order.Status.CANCELED],
            Order.Status.PROCESSING: [Order.Status.SHIPPED, Order.Status.CANCELED],
            Order.Status.SHIPPED: [Order.Status.DELIVERED],
            Order.Status.DELIVERED: [],  # Final state
            Order.Status.CANCELED: [],  # Final state
        }
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}'."
            )
        
        return value
    
    def save(self):
        """Update order status and create history entry"""
        order = self.context['order']
        new_status = self.validated_data['status']
        notes = self.validated_data.get('notes', '')
        user = self.context['request'].user
        
        # Create history entry
        OrderStatusHistory.objects.create(
            order=order,
            from_status=order.status,
            to_status=new_status,
            changed_by=user,
            notes=notes
        )
        
        # Update order status
        old_status = order.status
        order.status = new_status
        
        # Update timestamps based on status
        from django.utils import timezone
        if new_status == Order.Status.PAID:
            order.paid_at = timezone.now()
            order._reduce_stock()  # Reduce stock on payment
        elif new_status == Order.Status.SHIPPED:
            order.shipped_at = timezone.now()
        elif new_status == Order.Status.DELIVERED:
            order.delivered_at = timezone.now()
        
        order.save()
        
        return order


class OrderItemUpdateSerializer(serializers.Serializer):
    """Serializer for updating order item quantity"""
    
    quantity = serializers.IntegerField(min_value=0)
    
    def validate(self, attrs):
        """Validate stock availability"""
        order_item = self.context['order_item']
        product = order_item.product
        quantity = attrs['quantity']
        
        if quantity > 0 and quantity > product.stock:
            raise serializers.ValidationError({
                'quantity': f"Only {product.stock} items available in stock."
            })
        
        return attrs
    
    def save(self):
        """Update order item quantity"""
        order_item = self.context['order_item']
        quantity = self.validated_data['quantity']
        
        if quantity == 0:
            # Remove item
            order = order_item.order
            order_item.delete()
            order.calculate_totals()
            order.save()
            return None
        else:
            # Update quantity
            order_item.quantity = quantity
            order_item.save()
            return order_item


class OrderSummarySerializer(serializers.Serializer):
    """Serializer for order summary statistics"""
    
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    paid_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)