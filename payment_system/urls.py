from django.urls import path
from . import views

app_name = 'payment_system'

urlpatterns = [
    # Méthodes de paiement
    path('methods/', views.PaymentMethodListView.as_view(), name='payment_methods'),
    path('methods/<int:pk>/', views.PaymentMethodDetailView.as_view(), name='payment_method_detail'),
    
    # Initiation des paiements
    path('initiate/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    
    # Callbacks et webhooks
    path('callback/', views.payment_callback, name='payment_callback'),
    path('webhook/', views.webhook_handler, name='webhook_handler'),
    
    # Pages de résultat
    path('success/<int:transaction_id>/', views.payment_success, name='payment_success'),
    path('failure/<int:transaction_id>/', views.payment_failure, name='payment_failure'),
    
    # Historique et détails
    path('history/', views.payment_history, name='payment_history'),
    path('detail/<int:transaction_id>/', views.payment_detail, name='payment_detail'),
    
    # Remboursements
    path('refund/<int:transaction_id>/', views.request_refund, name='request_refund'),
]