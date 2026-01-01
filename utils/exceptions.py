"""
Custom Exception Handler
Location: utils/exceptions.py

Provides consistent error response format across the API.
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF
    
    Returns consistent error response format for all exceptions.
    
    Response format:
    {
        "success": false,
        "error": {
            "message": "Error message",
            "details": {...}  // Optional
        }
    }
    
    Args:
        exc: The exception instance
        context: Extra context data
        
    Returns:
        Response: Formatted error response
    """
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'success': False,
            'error': {
                'message': None,
                'details': None
            }
        }
        
        # Handle validation errors
        if isinstance(exc, ValidationError):
            custom_response_data['error']['message'] = 'Validation Error'
            custom_response_data['error']['details'] = response.data
        
        # Handle other exceptions
        else:
            # Get error message
            if isinstance(response.data, dict):
                if 'detail' in response.data:
                    custom_response_data['error']['message'] = response.data['detail']
                elif 'non_field_errors' in response.data:
                    custom_response_data['error']['message'] = response.data['non_field_errors'][0]
                else:
                    custom_response_data['error']['message'] = 'An error occurred'
                    custom_response_data['error']['details'] = response.data
            elif isinstance(response.data, list):
                custom_response_data['error']['message'] = response.data[0] if response.data else 'An error occurred'
            else:
                custom_response_data['error']['message'] = str(response.data)
        
        response.data = custom_response_data
        
        # Log the error
        logger.error(
            f"API Error [{response.status_code}]: {custom_response_data['error']['message']}",
            extra={
                'context': context,
                'exception': str(exc)
            }
        )
    
    # Handle unexpected errors (ObjectDoesNotExist, Http404)
    elif isinstance(exc, (ObjectDoesNotExist, Http404)):
        from rest_framework.response import Response
        
        custom_response_data = {
            'success': False,
            'error': {
                'message': 'Resource not found',
                'details': str(exc) if str(exc) else None
            }
        }
        response = Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
        logger.error(f"Resource not found: {str(exc)}")
    
    # Handle other unexpected exceptions
    elif exc:
        from rest_framework.response import Response
        
        custom_response_data = {
            'success': False,
            'error': {
                'message': 'Internal server error',
                'details': str(exc) if settings.DEBUG else None
            }
        }
        response = Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(
            f"Unexpected error: {str(exc)}",
            exc_info=True,
            extra={'context': context}
        )
    
    return response


# Import settings for DEBUG check
from django.conf import settings