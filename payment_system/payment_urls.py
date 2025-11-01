"""
URLs pour le système de paiement Mobile Money
"""
from django.urls import path
from . import payment_views

app_name = 'payment_system'

urlpatterns = [
    # Vues principales
    path('methods/', payment_views.PaymentMethodListView.as_view(), name='payment_methods'),
    path('initiate/<int:order_id>/', payment_views.PaymentInitiationView.as_view(), name='payment_initiation'),
    path('status/<int:transaction_id>/', payment_views.PaymentStatusView.as_view(), name='payment_status'),
    path('success/', payment_views.PaymentSuccessView.as_view(), name='payment_success'),
    path('failure/', payment_views.PaymentFailureView.as_view(), name='payment_failure'),
    path('history/', payment_views.payment_history, name='payment_history'),
    path('detail/<int:transaction_id>/', payment_views.payment_detail, name='payment_detail'),
    
    # API endpoints
    path('api/check-status/<int:transaction_id>/', payment_views.check_payment_status, name='check_payment_status'),
    
    # Webhooks
    path('webhook/orange/', payment_views.orange_callback, name='orange_webhook'),
    path('webhook/wave/', payment_views.wave_callback, name='wave_webhook'),
    path('webhook/mtn/', payment_views.mtn_callback, name='mtn_webhook'),
    path('webhook/moov/', payment_views.moov_callback, name='moov_webhook'),
    
    # Callbacks spécifiques
    path('orange/callback/', payment_views.orange_callback, name='orange_callback'),
    path('orange/cancel/', payment_views.PaymentFailureView.as_view(), name='orange_cancel'),
    path('wave/callback/', payment_views.wave_callback, name='wave_callback'),
    path('wave/redirect/', payment_views.PaymentSuccessView.as_view(), name='wave_redirect'),
]
