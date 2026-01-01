from django.urls import path
from .views import (
    PaymentListCreateView,
    PaymentDetailView,
    PaymentInitiateView,
    PaymentExecuteView,
    PaymentWebhookView
)

app_name = 'payments'

urlpatterns = [
    path('', PaymentListCreateView.as_view(), name='payment-list-create'),
    path('<int:id>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('<int:payment_id>/initiate/', PaymentInitiateView.as_view(), name='payment-initiate'),
    path('<int:payment_id>/execute/', PaymentExecuteView.as_view(), name='payment-execute'),
    path('webhook/<str:provider>/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
