from django.contrib import admin
from .models import Payment, PaymentLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id',
        'order',
        'provider',
        'amount',
        'currency',
        'status',
        'payment_method',
        'created_at',
        'completed_at',
    )
    list_filter = ('provider', 'status', 'currency', 'created_at')
    search_fields = ('transaction_id', 'order__order_number')
    readonly_fields = (
        'transaction_id',
        'status',
        'payment_method',
        'raw_response',
        'metadata',
        'created_at',
        'updated_at',
        'completed_at',
    )
    ordering = ('-created_at',)


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('payment', 'event_type', 'message', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('payment__transaction_id', 'message')
    readonly_fields = ('payment', 'event_type', 'message', 'data', 'created_at')
    ordering = ('-created_at',)
