# ==========================================
# File 2: apps/payments/strategies/base.py
# ==========================================
"""
Base Payment Strategy
Location: apps/payments/strategies/base.py

Abstract base class for payment strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PaymentStrategy(ABC):
    """
    Abstract base class for payment strategies
    
    All payment providers must implement this interface.
    This is the Strategy Pattern implementation.
    """
    
    def __init__(self, payment):
        """
        Initialize strategy with payment instance
        
        Args:
            payment: Payment model instance
        """
        self.payment = payment
        self.order = payment.order
    
    @abstractmethod
    def create_payment_intent(self) -> Dict[str, Any]:
        """
        Create payment intent/checkout session
        
        Returns:
            dict: Payment intent data including:
                - payment_url: URL to redirect user for payment
                - client_secret: Secret for frontend (if applicable)
                - additional data specific to provider
        """
        pass
    
    @abstractmethod
    def execute_payment(self, payment_data: Dict[str, Any]) -> bool:
        """
        Execute/confirm payment
        
        Args:
            payment_data: Data from payment provider
            
        Returns:
            bool: True if payment successful
        """
        pass
    
    @abstractmethod
    def verify_payment(self) -> bool:
        """
        Verify payment status
        
        Returns:
            bool: True if payment is verified as successful
        """
        pass
    
    @abstractmethod
    def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Process webhook notification from provider
        
        Args:
            webhook_data: Webhook payload
            
        Returns:
            bool: True if webhook processed successfully
        """
        pass
    
    @abstractmethod
    def refund_payment(self, amount: float = None) -> bool:
        """
        Process refund
        
        Args:
            amount: Amount to refund (None for full refund)
            
        Returns:
            bool: True if refund successful
        """
        pass
    
    def log_event(self, event_type: str, message: str, data: Dict = None):
        """Log payment event"""
        from apps.payments.models import PaymentLog
        
        PaymentLog.log_event(
            payment=self.payment,
            event_type=event_type,
            message=message,
            data=data or {}
        )
