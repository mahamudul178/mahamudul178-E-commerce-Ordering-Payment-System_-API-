"""
Order Management Models
Location: apps/orders/models.py

This module contains Order and OrderItem models with
automatic total calculation and stock management.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging

from apps.products.models import Product

User = get_user_model()
logger = logging.getLogger(__name__)


class Order(models.Model):
    """
    Order Model
    
    Represents a customer order with multiple items.
    Calculates totals automatically using algorithm.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELED = 'canceled', 'Canceled'
    
    # User relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Customer'
    )
    
    # Order details
    order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Order Number'
    )
    
    # Pricing (calculated automatically)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        verbose_name='Subtotal',
        help_text='Sum of all item subtotals'
    )
    
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        verbose_name='Tax Amount'
    )
    
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        verbose_name='Shipping Cost'
    )
    
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        verbose_name='Discount Amount'
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        verbose_name='Total Amount',
        help_text='Subtotal + Tax + Shipping - Discount'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Order Status'
    )
    
    # Shipping information
    shipping_address = models.TextField(
        verbose_name='Shipping Address'
    )
    
    shipping_city = models.CharField(
        max_length=100,
        verbose_name='City'
    )
    
    shipping_postal_code = models.CharField(
        max_length=20,
        verbose_name='Postal Code'
    )
    
    shipping_phone = models.CharField(
        max_length=20,
        verbose_name='Contact Phone'
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        verbose_name='Order Notes'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not exists"""
        if not self.order_number:
            self.order_number = self._generate_order_number()
        
        # Calculate totals before saving
        if self.pk:  # Only if order already exists
            self.calculate_totals()
        
        super().save(*args, **kwargs)
        logger.info(f"Order saved: {self.order_number}")
    
    def _generate_order_number(self):
        """
        Generate unique order number
        Format: ORD-YYYYMMDD-XXXXX
        """
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        
        # Get last order number for today
        last_order = Order.objects.filter(
            order_number__startswith=f'ORD-{date_str}'
        ).order_by('-order_number').first()
        
        if last_order:
            # Extract sequence and increment
            last_seq = int(last_order.order_number.split('-')[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f'ORD-{date_str}-{new_seq:05d}'
    
    def calculate_totals(self):
        """
        Calculate order totals using algorithm
        
        Algorithm:
        1. Calculate subtotal = sum of all item subtotals
        2. Apply tax (if any)
        3. Add shipping cost
        4. Subtract discount
        5. Calculate final total
        """
        # Step 1: Calculate subtotal from all order items
        items_subtotal = self.items.aggregate(
            total=models.Sum(
                models.F('quantity') * models.F('price'),
                output_field=models.DecimalField()
            )
        )['total'] or Decimal('0.00')
        
        self.subtotal = items_subtotal
        
        # Step 2: Calculate tax (example: 5% VAT)
        # In production, this could be configurable
        tax_rate = Decimal('0.05')  # 5%
        self.tax = self.subtotal * tax_rate
        
        # Step 3 & 4: Total = Subtotal + Tax + Shipping - Discount
        self.total_amount = (
            self.subtotal + 
            self.tax + 
            self.shipping_cost - 
            self.discount
        )
        
        logger.info(
            f"Order {self.order_number} totals calculated: "
            f"Subtotal={self.subtotal}, Tax={self.tax}, "
            f"Shipping={self.shipping_cost}, Total={self.total_amount}"
        )
    
    def add_item(self, product, quantity):
        """
        Add item to order
        
        Args:
            product: Product instance
            quantity: Quantity to order
            
        Returns:
            OrderItem instance
            
        Raises:
            ValueError: If product out of stock
        """
        if not product.is_in_stock:
            raise ValueError(f"Product {product.name} is not in stock")
        
        if quantity > product.stock:
            raise ValueError(
                f"Insufficient stock for {product.name}. "
                f"Available: {product.stock}, Requested: {quantity}"
            )
        
        # Check if item already exists
        item, created = OrderItem.objects.get_or_create(
            order=self,
            product=product,
            defaults={
                'quantity': quantity,
                'price': product.price
            }
        )
        
        if not created:
            # Update quantity if item exists
            item.quantity += quantity
            item.save()
        
        # Recalculate totals
        self.calculate_totals()
        self.save()
        
        return item
    
    def remove_item(self, product):
        """Remove item from order"""
        OrderItem.objects.filter(order=self, product=product).delete()
        self.calculate_totals()
        self.save()
    
    def update_item_quantity(self, product, quantity):
        """Update item quantity"""
        if quantity <= 0:
            self.remove_item(product)
        else:
            item = OrderItem.objects.get(order=self, product=product)
            item.quantity = quantity
            item.save()
            
            self.calculate_totals()
            self.save()
    
    def mark_as_paid(self):
        """Mark order as paid"""
        from django.utils import timezone
        
        if self.status == self.Status.PENDING:
            self.status = self.Status.PAID
            self.paid_at = timezone.now()
            self.save()
            
            # Reduce stock for all items
            self._reduce_stock()
            
            logger.info(f"Order {self.order_number} marked as paid")
    
    def _reduce_stock(self):
        """
        Reduce stock for all items in order
        Called after successful payment
        """
        for item in self.items.all():
            try:
                item.product.reduce_stock(item.quantity)
                logger.info(
                    f"Stock reduced for {item.product.name}: "
                    f"-{item.quantity}"
                )
            except ValueError as e:
                logger.error(
                    f"Failed to reduce stock for {item.product.name}: {e}"
                )
                # In production, handle this error appropriately
                # Maybe cancel order or notify admin
    
    def cancel_order(self):
        """Cancel order"""
        if self.status not in [self.Status.DELIVERED, self.Status.CANCELED]:
            old_status = self.status
            self.status = self.Status.CANCELED
            self.save()
            
            # If order was paid, restore stock
            if old_status == self.Status.PAID:
                self._restore_stock()
            
            logger.info(f"Order {self.order_number} canceled")
    
    def _restore_stock(self):
        """Restore stock after order cancellation"""
        for item in self.items.all():
            item.product.increase_stock(item.quantity)
            logger.info(
                f"Stock restored for {item.product.name}: "
                f"+{item.quantity}"
            )
    
    @property
    def item_count(self):
        """Get total number of items in order"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def is_paid(self):
        """Check if order is paid"""
        return self.status != self.Status.PENDING
    
    @property
    def can_be_canceled(self):
        """Check if order can be canceled"""
        return self.status not in [
            self.Status.DELIVERED,
            self.Status.CANCELED
        ]


class OrderItem(models.Model):
    """
    Order Item Model
    
    Represents individual items in an order.
    Stores price at time of order (historical pricing).
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Order'
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Product'
    )
    
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantity'
    )
    
    # Store price at time of order
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Unit Price',
        help_text='Price at time of order'
    )
    
    # Calculated field
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        verbose_name='Subtotal',
        help_text='Quantity × Price'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['id']
        unique_together = ['order', 'product']
        indexes = [
            models.Index(fields=['order', 'product']),
        ]
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        """
        Calculate subtotal before saving
        
        Algorithm: subtotal = quantity × price
        """
        self.subtotal = Decimal(str(self.quantity)) * self.price
        
        super().save(*args, **kwargs)
        
        # Trigger order total recalculation
        if self.order:
            self.order.calculate_totals()
            self.order.save()
        
        logger.info(
            f"Order item saved: {self.product.name} "
            f"(Qty: {self.quantity}, Subtotal: {self.subtotal})"
        )
    
    def delete(self, *args, **kwargs):
        """Recalculate order totals after deletion"""
        order = self.order
        super().delete(*args, **kwargs)
        
        if order:
            order.calculate_totals()
            order.save()


class OrderStatusHistory(models.Model):
    """
    Order Status History Model
    
    Tracks all status changes for an order.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Order'
    )
    
    from_status = models.CharField(
        max_length=20,
        choices=Order.Status.choices,
        verbose_name='From Status'
    )
    
    to_status = models.CharField(
        max_length=20,
        choices=Order.Status.choices,
        verbose_name='To Status'
    )
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_status_changes',
        verbose_name='Changed By'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Notes'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} → {self.to_status}"