"""
Mixins pour la gestion des permissions et accès selon le type d'utilisateur
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class UserTypeRequiredMixin:
    """
    Mixin pour vérifier le type d'utilisateur requis
    """
    required_user_types = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, _('Vous devez être connecté pour accéder à cette page.'))
            return redirect('accounts:login')
        
        if request.user.user_type not in self.required_user_types:
            messages.error(request, _('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.'))
            return redirect('products:home_page')
        
        return super().dispatch(request, *args, **kwargs)


class ClientRequiredMixin(UserTypeRequiredMixin):
    """
    Mixin pour les pages réservées aux clients
    """
    required_user_types = ['client']


class VendorRequiredMixin(UserTypeRequiredMixin):
    """
    Mixin pour les pages réservées aux vendeurs
    """
    required_user_types = ['vendeur']


class AdminRequiredMixin(UserTypeRequiredMixin):
    """
    Mixin pour les pages réservées aux administrateurs
    """
    required_user_types = ['admin']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, _('Vous devez être connecté pour accéder à cette page.'))
            return redirect('accounts:login')
        
        if not (request.user.is_superuser or request.user.user_type == 'admin'):
            messages.error(request, _('Accès refusé. Cette page est réservée aux administrateurs.'))
            return redirect('products:home_page')
        
        return super().dispatch(request, *args, **kwargs)


class VendorOrAdminRequiredMixin(UserTypeRequiredMixin):
    """
    Mixin pour les pages accessibles aux vendeurs et administrateurs
    """
    required_user_types = ['vendeur', 'admin']


class StaffRequiredMixin:
    """
    Mixin pour les pages réservées au staff (admin + vendeurs)
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, _('Vous devez être connecté pour accéder à cette page.'))
            return redirect('accounts:login')
        
        if not (request.user.is_staff or request.user.user_type in ['vendeur', 'admin']):
            messages.error(request, _('Accès refusé. Cette page est réservée au personnel.'))
            return redirect('products:home_page')
        
        return super().dispatch(request, *args, **kwargs)


class AnonymousRequiredMixin:
    """
    Mixin pour les pages réservées aux utilisateurs non connectés
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Rediriger vers la page appropriée selon le type d'utilisateur
            if request.user.user_type == 'vendeur':
                return redirect('dashboard:vendor_dashboard')
            elif request.user.user_type == 'client':
                return redirect('products:home_page')
            elif request.user.is_superuser or request.user.user_type == 'admin':
                return redirect('dashboard:admin_dashboard')
            else:
                return redirect('products:home_page')
        
        return super().dispatch(request, *args, **kwargs)
