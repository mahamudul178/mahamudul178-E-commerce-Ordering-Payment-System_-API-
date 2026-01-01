from rest_framework import serializers
from .models import Payment, PaymentLog
from apps.orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'order_number',
            'provider',
            'amount',
            'currency',
            'transaction_id',
            'status',
            'payment_method',
            'metadata',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = [
            'transaction_id', 'status', 'payment_method',
            'metadata', 'created_at', 'updated_at', 'completed_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to create a Payment object
    """
    class Meta:
        model = Payment
        fields = ['order', 'provider', 'amount', 'currency']


class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = ['id', 'payment', 'event_type', 'message', 'data', 'created_at']
