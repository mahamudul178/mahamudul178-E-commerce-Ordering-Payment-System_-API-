# ==========================================
# File 3: apps/payments/strategies/stripe_strategy.py
# ==========================================
"""
Stripe Payment Strategy
Location: apps/payments/strategies/stripe_strategy.py

Implementation of Stripe payment provider.
"""

import stripe
from django.conf import settings
from decimal import Decimal
from .base import PaymentStrategy
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentStrategy(PaymentStrategy):
    """
    Stripe Payment Strategy Implementation
    
    Handles Stripe payment processing including:
    - Payment Intent creation
    - Payment confirmation
    - Webhook handling
    - Refunds
    """
    
    def create_payment_intent(self):
        """
        Create Stripe Payment Intent
        
        Returns:
            dict: Payment intent data with client_secret
        """
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(self.payment.amount * 100)
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=self.payment.currency.lower(),
                metadata={
                    'order_id': str(self.order.id),
                    'order_number': self.order.order_number,
                    'payment_id': str(self.payment.id)
                },
                description=f"Order {self.order.order_number}"
            )
            
            # Update payment with transaction ID
            self.payment.transaction_id = intent.id
            self.payment.raw_response = intent
            self.payment.save()
            
            # Log event
            self.log_event(
                'initiated',
                f"Stripe Payment Intent created: {intent.id}",
                {'intent_id': intent.id, 'amount': self.payment.amount}
            )
            
            logger.info(f"Stripe Payment Intent created: {intent.id}")
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': self.payment.amount,
                'currency': self.payment.currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            self.payment.mark_as_failed(str(e))
            self.log_event('error', f"Stripe error: {str(e)}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment(self, payment_data):
        """
        Confirm Stripe payment
        
        Args:
            payment_data: Data from frontend (payment_intent_id)
            
        Returns:
            bool: True if payment successful
        """
        try:
            payment_intent_id = payment_data.get('payment_intent_id')
            
            # Retrieve payment intent
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Update payment
            self.payment.raw_response = intent
            self.payment.payment_method = intent.get('payment_method_types', ['card'])[0]
            
            if intent.status == 'succeeded':
                self.payment.mark_as_success()
                self.log_event('success', "Payment confirmed successfully")
                logger.info(f"Stripe payment succeeded: {payment_intent_id}")
                return True
            else:
                self.payment.mark_as_failed(f"Payment status: {intent.status}")
                self.log_event('failed', f"Payment failed: {intent.status}")
                return False
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe execution error: {str(e)}")
            self.payment.mark_as_failed(str(e))
            self.log_event('error', f"Execution error: {str(e)}")
            return False
    
    def verify_payment(self):
        """
        Verify Stripe payment status
        
        Returns:
            bool: True if payment verified
        """
        try:
            intent = stripe.PaymentIntent.retrieve(self.payment.transaction_id)
            
            if intent.status == 'succeeded':
                if not self.payment.is_successful:
                    self.payment.mark_as_success()
                return True
            
            return False
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe verification error: {str(e)}")
            return False
    
    def process_webhook(self, webhook_data):
        """
        Process Stripe webhook
        
        Args:
            webhook_data: Stripe webhook event
            
        Returns:
            bool: True if processed successfully
        """
        try:
            event_type = webhook_data.get('type')
            
            self.log_event('webhook', f"Webhook received: {event_type}", webhook_data)
            
            if event_type == 'payment_intent.succeeded':
                payment_intent = webhook_data['data']['object']
                
                if self.payment.transaction_id == payment_intent['id']:
                    self.payment.mark_as_success()
                    logger.info(f"Webhook: Payment succeeded - {payment_intent['id']}")
                    return True
                    
            elif event_type == 'payment_intent.payment_failed':
                payment_intent = webhook_data['data']['object']
                
                if self.payment.transaction_id == payment_intent['id']:
                    error = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
                    self.payment.mark_as_failed(error)
                    logger.warning(f"Webhook: Payment failed - {payment_intent['id']}")
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return False
    
    def refund_payment(self, amount=None):
        """
        Refund Stripe payment
        
        Args:
            amount: Amount to refund (None for full refund)
            
        Returns:
            bool: True if refund successful
        """
        try:
            refund_amount = amount or self.payment.amount
            refund_cents = int(refund_amount * 100)
            
            refund = stripe.Refund.create(
                payment_intent=self.payment.transaction_id,
                amount=refund_cents
            )
            
            if refund.status == 'succeeded':
                self.payment.refund()
                self.log_event('refund', f"Refund processed: {refund.id}", {'amount': refund_amount})
                logger.info(f"Stripe refund succeeded: {refund.id}")
                return True
            
            return False
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}")
            return False