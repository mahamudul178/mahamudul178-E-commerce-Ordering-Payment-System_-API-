from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Payment, PaymentLog
from .serializers import PaymentSerializer, PaymentCreateSerializer
from .strategies import StripePaymentStrategy, BkashPaymentStrategy


class PaymentListCreateView(generics.ListCreateAPIView):
    """
    List all payments or create a new payment
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        # Create payment instance
        payment = serializer.save()
        return payment


class PaymentDetailView(generics.RetrieveAPIView):
    """
    Retrieve a payment by ID
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    lookup_field = 'id'


class PaymentInitiateView(APIView):
    """
    Initiate payment using the selected provider strategy
    """

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Select strategy
        if payment.provider == Payment.Provider.STRIPE:
            strategy = StripePaymentStrategy(payment)
        elif payment.provider == Payment.Provider.BKASH:
            strategy = BkashPaymentStrategy(payment)
        else:
            return Response({'error': 'Unsupported provider'}, status=400)
        
        # Create payment intent
        result = strategy.create_payment_intent()
        return Response(result, status=status.HTTP_200_OK if result.get('success') else 400)


class PaymentExecuteView(APIView):
    """
    Execute / confirm a payment
    """
    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Select strategy
        if payment.provider == Payment.Provider.STRIPE:
            strategy = StripePaymentStrategy(payment)
        elif payment.provider == Payment.Provider.BKASH:
            strategy = BkashPaymentStrategy(payment)
        else:
            return Response({'error': 'Unsupported provider'}, status=400)
        
        result = strategy.execute_payment(request.data)
        return Response({'success': result}, status=200 if result else 400)


class PaymentWebhookView(APIView):
    """
    Handle webhook from payment providers
    """
    def post(self, request, provider):
        payment_id = request.data.get('payment_id') or request.data.get('id')
        if not payment_id:
            return Response({'error': 'Missing payment id'}, status=400)
        
        payment = get_object_or_404(Payment, transaction_id=payment_id)
        
        # Select strategy
        if provider.lower() == 'stripe':
            strategy = StripePaymentStrategy(payment)
        elif provider.lower() == 'bkash':
            strategy = BkashPaymentStrategy(payment)
        else:
            return Response({'error': 'Unsupported provider'}, status=400)
        
        success = strategy.process_webhook(request.data)
        return Response({'success': success})
