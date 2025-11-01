from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.urls import reverse_lazy
from datetime import datetime, timedelta
import json
import logging

from .models import (
    DeliveryZone, DeliveryAddress, DeliveryCalculation
)
from .services import DeliveryService
from orders.models import Order

logger = logging.getLogger(__name__)


class DeliveryZoneListView(ListView):
    """Vue pour lister les zones de livraison"""
    model = DeliveryZone
    template_name = 'delivery_system/delivery_zones.html'
    context_object_name = 'delivery_zones'
    
    def get_queryset(self):
        return DeliveryZone.objects.filter(is_active=True).order_by('zone_type', 'name')


class DeliveryAddressListView(ListView):
    """Vue pour lister les adresses de livraison de l'utilisateur"""
    model = DeliveryAddress
    template_name = 'delivery_system/delivery_addresses.html'
    context_object_name = 'delivery_addresses'
    
    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')


class DeliveryAddressCreateView(CreateView):
    """Vue pour créer une adresse de livraison"""
    model = DeliveryAddress
    fields = ['first_name', 'last_name', 'phone_number', 'address_line_1', 'address_line_2', 'city', 'postal_code', 'country', 'is_default']
    template_name = 'delivery_system/delivery_address_form.html'
    success_url = reverse_lazy('delivery_system:delivery_addresses')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Déterminer la zone de livraison
        delivery_info = DeliveryService.calculate_delivery_fee(form.instance.city)
        form.instance.zone = delivery_info['zone']
        
        messages.success(self.request, 'Adresse de livraison créée avec succès.')
        return super().form_valid(form)


class DeliveryAddressUpdateView(UpdateView):
    """Vue pour modifier une adresse de livraison"""
    model = DeliveryAddress
    fields = ['first_name', 'last_name', 'phone_number', 'address_line_1', 'address_line_2', 'city', 'postal_code', 'country', 'is_default']
    template_name = 'delivery_system/delivery_address_form.html'
    success_url = reverse_lazy('delivery_system:delivery_addresses')
    
    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        # Déterminer la zone de livraison
        delivery_info = DeliveryService.calculate_delivery_fee(form.instance.city)
        form.instance.zone = delivery_info['zone']
        
        messages.success(self.request, 'Adresse de livraison mise à jour avec succès.')
        return super().form_valid(form)


@login_required
def calculate_delivery_fee(request):
    """API pour calculer les frais de livraison"""
    try:
        if request.method == 'POST':
            city = request.POST.get('city', '').strip()
            country = request.POST.get('country', 'Côte d\'Ivoire').strip()
            
            if not city:
                return JsonResponse({'error': 'Ville requise'}, status=400)
            
            # Calculer les frais de livraison
            delivery_info = DeliveryService.calculate_delivery_fee(city, country)
            
            return JsonResponse({
                'success': True,
                'delivery_fee': float(delivery_info['fee']),
                'estimated_days': delivery_info['estimated_days'],
                'estimated_date': delivery_info['estimated_date'].strftime('%d/%m/%Y'),
                'zone_name': delivery_info['zone'].name,
                'zone_description': delivery_info['zone'].description
            })
        
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    except Exception as e:
        logger.error(f"Erreur calcul frais livraison: {e}")
        return JsonResponse({'error': 'Erreur lors du calcul'}, status=500)


@staff_member_required
def delivery_dashboard(request):
    """Tableau de bord des livraisons"""
    
    # Statistiques générales
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    
    # Livraisons d'aujourd'hui
    today = timezone.now().date()
    today_orders = Order.objects.filter(created_at__date=today)
    
    # Performance par zone de livraison
    zone_performance = DeliveryCalculation.objects.values(
        'zone__name'
    ).annotate(
        total_count=Count('id'),
        total_fees=Sum('total_delivery_fee')
    ).order_by('-total_count')
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'today_orders': today_orders,
        'zone_performance': zone_performance,
    }
    
    return render(request, 'delivery_system/dashboard.html', context)


@staff_member_required
def create_delivery_zones(request):
    """Créer les zones de livraison par défaut"""
    if request.method == 'POST':
        DeliveryService.create_delivery_zones()
        messages.success(request, 'Zones de livraison créées avec succès.')
        return redirect('delivery_system:delivery_zones')
    
    return render(request, 'delivery_system/create_zones.html')