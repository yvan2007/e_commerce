from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('livraison/', views.LivraisonView.as_view(), name='livraison'),
    path('retours/', views.RetoursView.as_view(), name='retours'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('promotions/', views.PromotionsView.as_view(), name='promotions'),
]

