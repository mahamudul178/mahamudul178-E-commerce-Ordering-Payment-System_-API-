"""
Order Management Admin Configuration
Location: apps/orders/admin.py

Django admin panel configuration for orders.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, OrderStatusHistory


from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items"""
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal', 'price']
    fields = ['product', 'quantity', 'price', 'subtotal']
    
    def has_add_permission(self, request, obj=None):
        """Disable adding items through admin"""
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline admin for status history"""
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'changed_by', 'notes', 'created_at']
    fields = ['from_status', 'to_status', 'changed_by', 'notes', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for Order model"""
    
    list_display = [
        'order_number',
        'customer_link',
        'status_badge',
        'item_count_display',
        'total_amount_display',
        'created_at',
        'paid_at'
    ]
    
    list_filter = [
        'status',
        'created_at',
        'paid_at',
        'shipped_at'
    ]
    
    search_fields = [
        'order_number',
        'user__email',
        'user__first_name',
        'user__last_name',
        'shipping_address',
        'shipping_city'
    ]
    
    readonly_fields = [
        'order_number',
        'user',
        'subtotal',
        'tax',
        'total_amount',
        'item_count',
        'created_at',
        'updated_at',
        'paid_at',
        'shipped_at',
        'delivered_at'
    ]
    
    ordering = ['-created_at']
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number',
                'user',
                'status'
            )
        }),
        ('Pricing', {
            'fields': (
                'subtotal',
                'tax',
                'shipping_cost',
                'discount',
                'total_amount'
            )
        }),
        ('Shipping Details', {
            'fields': (
                'shipping_address',
                'shipping_city',
                'shipping_postal_code',
                'shipping_phone'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'paid_at',
                'shipped_at',
                'delivered_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def customer_link(self, obj):
        """Display customer with link"""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.get_full_name() or obj.user.email
        )
    customer_link.short_description = 'Customer'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': '#ffc107',
            'paid': '#28a745',
            'processing': '#17a2b8',
            'shipped': '#007bff',
            'delivered': '#28a745',
            'canceled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 4px 12px; border-radius: 4px; font-weight: bold; '
            'display: inline-block; min-width: 80px; text-align: center;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def item_count_display(self, obj):
        """Display item count"""
        count = obj.item_count
        return format_html(
            '<span style="font-weight: bold;">{} item{}</span>',
            count,
            's' if count != 1 else ''
        )
    item_count_display.short_description = 'Items'
    
    def total_amount_display(self, obj):
        """Display formatted total amount"""
        # ✅ FIX: প্রথমে format করুন, তারপর format_html এ pass করুন
        formatted_amount = f'{obj.total_amount:,.2f}'
        return format_html(
            '<strong style="color: #28a745; font-size: 14px;">৳{}</strong>',
            formatted_amount
        )
    total_amount_display.short_description = 'Total'
    
    actions = [
        'mark_as_paid',
        'mark_as_processing',
        'mark_as_shipped',
        'cancel_orders'
    ]
    
    def mark_as_paid(self, request, queryset):
        """Bulk mark orders as paid"""
        count = 0
        for order in queryset.filter(status=Order.Status.PENDING):
            order.mark_as_paid()
            count += 1
        self.message_user(request, f'{count} order(s) marked as paid.')
    mark_as_paid.short_description = 'Mark selected as PAID'
    
    def mark_as_processing(self, request, queryset):
        """Bulk mark orders as processing"""
        count = queryset.filter(status=Order.Status.PAID).update(
            status=Order.Status.PROCESSING
        )
        self.message_user(request, f'{count} order(s) marked as processing.')
    mark_as_processing.short_description = 'Mark selected as PROCESSING'
    
    def mark_as_shipped(self, request, queryset):
        """Bulk mark orders as shipped"""
        from django.utils import timezone
        count = queryset.filter(status=Order.Status.PROCESSING).update(
            status=Order.Status.SHIPPED,
            shipped_at=timezone.now()
        )
        self.message_user(request, f'{count} order(s) marked as shipped.')
    mark_as_shipped.short_description = 'Mark selected as SHIPPED'
    
    def cancel_orders(self, request, queryset):
        """Bulk cancel orders"""
        count = 0
        for order in queryset:
            if order.can_be_canceled:
                order.cancel_order()
                count += 1
        self.message_user(request, f'{count} order(s) canceled.')
    cancel_orders.short_description = 'Cancel selected orders'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin configuration for OrderItem model"""
    list_display = [
        'order_number_display',
        'product_link',
        'quantity',
        'price_display',
        'subtotal_display',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = [
        'order__order_number',
        'product__name',
        'product__sku'
    ]
    readonly_fields = [
        'order',
        'product',
        'quantity',
        'price',
        'subtotal',
        'created_at',
        'updated_at'
    ]
    ordering = ['-created_at']
    
    def order_number_display(self, obj):
        """Display order number with link"""
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.order.order_number
        )
    order_number_display.short_description = 'Order'
    
    def product_link(self, obj):
        """Display product with link"""
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.product.name
        )
    product_link.short_description = 'Product'
    
    def price_display(self, obj):
        """Display formatted price"""
        # ✅ Fix: প্রথমে format করুন, তারপর format_html এ pass করুন
        formatted_price = f'{obj.price:,.2f}'
        return format_html('৳{}', formatted_price)
    price_display.short_description = 'Price'
    
    def subtotal_display(self, obj):
        """Display formatted subtotal"""
        # ✅ Fix: প্রথমে format করুন, তারপর format_html এ pass করুন
        formatted_subtotal = f'{obj.subtotal:,.2f}'
        return format_html(
            '<strong style="color: #28a745;">৳{}</strong>',
            formatted_subtotal
        )
    subtotal_display.short_description = 'Subtotal'
    
    def has_add_permission(self, request):
        """Disable direct creation"""
        return False


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for OrderStatusHistory model"""
    
    list_display = [
        'order_number_display',
        'status_change_display',
        'changed_by_display',
        'created_at'
    ]
    
    list_filter = ['from_status', 'to_status', 'created_at']
    
    search_fields = [
        'order__order_number',
        'changed_by__email',
        'notes'
    ]
    
    readonly_fields = [
        'order',
        'from_status',
        'to_status',
        'changed_by',
        'notes',
        'created_at'
    ]
    
    ordering = ['-created_at']
    
    def order_number_display(self, obj):
        """Display order number with link"""
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.order.order_number
        )
    order_number_display.short_description = 'Order'
    
    def status_change_display(self, obj):
        """Display status change with colors"""
        from_color = '#ffc107' if obj.from_status == 'pending' else '#17a2b8'
        to_color = '#28a745' if obj.to_status == 'paid' else '#17a2b8'
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span> '
            '<span style="margin: 0 5px;">→</span> '
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            from_color,
            obj.get_from_status_display(),
            to_color,
            obj.get_to_status_display()
        )
    status_change_display.short_description = 'Status Change'
    
    def changed_by_display(self, obj):
        """Display changed by user"""
        if obj.changed_by:
            return obj.changed_by.get_full_name() or obj.changed_by.email
        return '-'
    changed_by_display.short_description = 'Changed By'
    
    def has_add_permission(self, request):
        """Disable direct creation"""
        return False