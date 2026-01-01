"""
Payment Management Models
Location: apps/payments/models.py

This module contains Payment model with support for multiple providers.
Uses Strategy Pattern for different payment gateways.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging

from apps.orders.models import Order

User = get_user_model()
logger = logging.getLogger(__name__)


class Payment(models.Model):
    """
    Payment Model
    
    Stores payment information for orders.
    Supports multiple payment providers (Stripe, bKash).
    Uses Strategy Pattern for provider-specific logic.
    """
    
    class Provider(models.TextChoices):
        STRIPE = 'stripe', 'Stripe'
        BKASH = 'bkash', 'bKash'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
    
    # Order relationship
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Order'
    )
    
    # Payment provider
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        db_index=True,
        verbose_name='Payment Provider'
    )
    
    # Transaction details
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Transaction ID',
        help_text='Unique transaction ID from payment provider'
    )
    
    # Amount
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Payment Amount'
    )
    
    # Currency
    currency = models.CharField(
        max_length=3,
        default='BDT',
        verbose_name='Currency'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Payment Status'
    )
    
    # Provider-specific data (stored as JSON)
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Raw Provider Response',
        help_text='Complete response from payment provider'
    )
    
    # Payment method details (optional)
    payment_method = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Payment Method',
        help_text='e.g., card, mobile wallet, etc.'
    )
    
    # Error information
    error_message = models.TextField(
        blank=True,
        verbose_name='Error Message'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Additional Metadata'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['order']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.provider} - {self.get_status_display()}"
    
    def mark_as_success(self):
        """
        Mark payment as successful
        
        This will:
        1. Update payment status to SUCCESS
        2. Update order status to PAID
        3. Reduce stock for order items
        4. Set completion timestamp
        """
        from django.utils import timezone
        
        if self.status != self.Status.SUCCESS:
            self.status = self.Status.SUCCESS
            self.completed_at = timezone.now()
            self.save()
            
            # Update order status and reduce stock
            self.order.mark_as_paid()
            
            logger.info(
                f"Payment {self.transaction_id} marked as success. "
                f"Order {self.order.order_number} updated to PAID."
            )
    
    def mark_as_failed(self, error_message=None):
        """Mark payment as failed"""
        self.status = self.Status.FAILED
        if error_message:
            self.error_message = error_message
        self.save()
        
        logger.warning(
            f"Payment {self.transaction_id} failed. "
            f"Error: {error_message or 'Unknown error'}"
        )
    
    def refund(self):
        """
        Process refund
        
        This will:
        1. Mark payment as REFUNDED
        2. Update order status to CANCELED
        3. Restore stock
        """
        if self.status == self.Status.SUCCESS:
            self.status = self.Status.REFUNDED
            self.save()
            
            # Cancel order and restore stock
            self.order.cancel_order()
            
            logger.info(
                f"Payment {self.transaction_id} refunded. "
                f"Order {self.order.order_number} canceled and stock restored."
            )
    
    @property
    def is_successful(self):
        """Check if payment is successful"""
        return self.status == self.Status.SUCCESS
    
    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == self.Status.PENDING
    
    @property
    def is_failed(self):
        """Check if payment is failed"""
        return self.status == self.Status.FAILED
    
    @property
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return self.status == self.Status.SUCCESS


class PaymentLog(models.Model):
    """
    Payment Log Model
    
    Tracks all payment-related events for debugging and auditing.
    """
    
    class EventType(models.TextChoices):
        INITIATED = 'initiated', 'Payment Initiated'
        PROCESSING = 'processing', 'Processing'
        SUCCESS = 'success', 'Payment Success'
        FAILED = 'failed', 'Payment Failed'
        WEBHOOK = 'webhook', 'Webhook Received'
        REFUND = 'refund', 'Refund Processed'
        ERROR = 'error', 'Error Occurred'
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Payment'
    )
    
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name='Event Type'
    )
    
    message = models.TextField(
        verbose_name='Event Message'
    )
    
    data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Event Data'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_logs'
        verbose_name = 'Payment Log'
        verbose_name_plural = 'Payment Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', '-created_at']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.payment.transaction_id}"
    
    @classmethod
    def log_event(cls, payment, event_type, message, data=None):
        """
        Create a log entry
        
        Args:
            payment: Payment instance
            event_type: EventType choice
            message: Log message
            data: Additional data (optional)
        """
        log = cls.objects.create(
            payment=payment,
            event_type=event_type,
            message=message,
            data=data or {}
        )
        
        logger.info(
            f"Payment log created: {payment.transaction_id} - "
            f"{event_type} - {message}"
        )
        
        return log