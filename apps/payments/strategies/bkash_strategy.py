# ==========================================
# File 4: apps/payments/strategies/bkash_strategy.py
# ==========================================
"""
bKash Payment Strategy
Location: apps/payments/strategies/bkash_strategy.py

Implementation of bKash mobile payment provider.
"""

import requests
from django.conf import settings
from decimal import Decimal
from .base import PaymentStrategy
import logging

logger = logging.getLogger(__name__)


class BkashPaymentStrategy(PaymentStrategy):
    """
    bKash Payment Strategy Implementation
    
    Handles bKash payment processing including:
    - Token generation
    - Payment creation
    - Payment execution
    - Query payment status
    - Refunds
    """
    
    def __init__(self, payment):
        super().__init__(payment)
        self.base_url = settings.BKASH_BASE_URL
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD
        self._token = None
    
    def _get_token(self):
        """
        Get bKash auth token
        
        Returns:
            str: Auth token
        """
        if self._token:
            return self._token
        
        try:
            url = f"{self.base_url}/checkout/token/grant"
            headers = {
                'Content-Type': 'application/json',
                'username': self.username,
                'password': self.password
            }
            data = {
                'app_key': self.app_key,
                'app_secret': self.app_secret
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            self._token = result.get('id_token')
            
            logger.info("bKash token obtained successfully")
            return self._token
            
        except requests.RequestException as e:
            logger.error(f"bKash token error: {str(e)}")
            return None
    
    def create_payment_intent(self):
        """
        Create bKash payment
        
        Returns:
            dict: Payment creation response with bKashURL
        """
        try:
            token = self._get_token()
            if not token:
                return {'success': False, 'error': 'Failed to get auth token'}
            
            url = f"{self.base_url}/checkout/payment/create"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key
            }
            
            data = {
                'amount': str(self.payment.amount),
                'currency': 'BDT',
                'intent': 'sale',
                'merchantInvoiceNumber': self.order.order_number
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('statusCode') == '0000':
                # Success
                payment_id = result.get('paymentID')
                self.payment.transaction_id = payment_id
                self.payment.raw_response = result
                self.payment.save()
                
                self.log_event(
                    'initiated',
                    f"bKash payment created: {payment_id}",
                    result
                )
                
                logger.info(f"bKash payment created: {payment_id}")
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'bkashURL': result.get('bkashURL'),
                    'amount': self.payment.amount,
                    'currency': 'BDT'
                }
            else:
                error_msg = result.get('statusMessage', 'Payment creation failed')
                self.payment.mark_as_failed(error_msg)
                self.log_event('error', f"Creation failed: {error_msg}", result)
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.RequestException as e:
            logger.error(f"bKash creation error: {str(e)}")
            self.payment.mark_as_failed(str(e))
            self.log_event('error', f"Creation error: {str(e)}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment(self, payment_data):
        """
        Execute bKash payment
        
        Args:
            payment_data: Contains paymentID from bKash callback
            
        Returns:
            bool: True if payment successful
        """
        try:
            token = self._get_token()
            payment_id = payment_data.get('paymentID') or self.payment.transaction_id
            
            url = f"{self.base_url}/checkout/payment/execute/{payment_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key
            }
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            self.payment.raw_response = result
            self.payment.payment_method = 'bKash'
            
            if result.get('statusCode') == '0000':
                trx_id = result.get('trxID')
                self.payment.metadata['trx_id'] = trx_id
                self.payment.mark_as_success()
                
                self.log_event('success', f"Payment executed: {trx_id}", result)
                logger.info(f"bKash payment executed: {payment_id}, trxID: {trx_id}")
                return True
            else:
                error_msg = result.get('statusMessage', 'Execution failed')
                self.payment.mark_as_failed(error_msg)
                self.log_event('failed', f"Execution failed: {error_msg}", result)
                return False
                
        except requests.RequestException as e:
            logger.error(f"bKash execution error: {str(e)}")
            self.payment.mark_as_failed(str(e))
            self.log_event('error', f"Execution error: {str(e)}")
            return False
    
    def verify_payment(self):
        """
        Query bKash payment status
        
        Returns:
            bool: True if payment verified
        """
        try:
            token = self._get_token()
            payment_id = self.payment.transaction_id
            
            url = f"{self.base_url}/checkout/payment/query/{payment_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('transactionStatus') == 'Completed':
                if not self.payment.is_successful:
                    self.payment.mark_as_success()
                return True
            
            return False
            
        except requests.RequestException as e:
            logger.error(f"bKash query error: {str(e)}")
            return False
    
    def process_webhook(self, webhook_data):
        """
        Process bKash webhook (if implemented by bKash)
        
        Note: bKash webhook implementation varies
        """
        # bKash webhook implementation
        self.log_event('webhook', "Webhook received", webhook_data)
        return True
    
    def refund_payment(self, amount=None):
        """
        Refund bKash payment
        
        Args:
            amount: Amount to refund
            
        Returns:
            bool: True if refund successful
        """
        try:
            token = self._get_token()
            payment_id = self.payment.transaction_id
            trx_id = self.payment.metadata.get('trx_id')
            
            refund_amount = amount or self.payment.amount
            
            url = f"{self.base_url}/checkout/payment/refund"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key
            }
            
            data = {
                'paymentID': payment_id,
                'amount': str(refund_amount),
                'trxID': trx_id,
                'sku': 'refund',
                'reason': 'Order canceled'
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('statusCode') == '0000':
                self.payment.refund()
                self.log_event('refund', f"Refund processed", result)
                logger.info(f"bKash refund successful: {payment_id}")
                return True
            
            return False
            
        except requests.RequestException as e:
            logger.error(f"bKash refund error: {str(e)}")
            return False
