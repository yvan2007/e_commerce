from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderItem, Cart, CartItem, ShippingAddress, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """
    Inline pour les articles de commande
    """
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('product', 'variant', 'quantity', 'unit_price', 'total_price')


class OrderStatusHistoryInline(admin.TabularInline):
    """
    Inline pour l'historique des statuts
    """
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('status', 'notes', 'created_by', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Administration des commandes
    """
    list_display = ('order_number', 'user', 'status', 'payment_method', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at', 'shipped_at', 'delivered_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'shipping_first_name', 'shipping_last_name')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'shipped_at', 'delivered_at', 'payment_date')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('order_number', 'user', 'status', 'created_at', 'updated_at')
        }),
        (_('Paiement'), {
            'fields': ('payment_method', 'payment_status', 'payment_reference', 'payment_date')
        }),
        (_('Adresse de livraison'), {
            'fields': ('shipping_first_name', 'shipping_last_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_postal_code', 'shipping_country')
        }),
        (_('Adresse de facturation'), {
            'fields': ('billing_address',),
            'classes': ('collapse',)
        }),
        (_('Montants'), {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'total_amount')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Dates de livraison'), {
            'fields': ('shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        """Marquer comme confirmées"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} commande(s) confirmée(s) avec succès.')
    mark_as_confirmed.short_description = "Marquer comme confirmées"
    
    def mark_as_processing(self, request, queryset):
        """Marquer comme en cours de traitement"""
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} commande(s) marquée(s) comme en cours de traitement.')
    mark_as_processing.short_description = "Marquer comme en cours de traitement"
    
    def mark_as_shipped(self, request, queryset):
        """Marquer comme expédiées"""
        from django.utils import timezone
        updated = queryset.update(status='shipped', shipped_at=timezone.now())
        self.message_user(request, f'{updated} commande(s) marquée(s) comme expédiées.')
    mark_as_shipped.short_description = "Marquer comme expédiées"
    
    def mark_as_delivered(self, request, queryset):
        """Marquer comme livrées"""
        from django.utils import timezone
        updated = queryset.update(status='delivered', delivered_at=timezone.now())
        self.message_user(request, f'{updated} commande(s) marquée(s) comme livrées.')
    mark_as_delivered.short_description = "Marquer comme livrées"
    
    def mark_as_cancelled(self, request, queryset):
        """Marquer comme annulées"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} commande(s) marquée(s) comme annulées.')
    mark_as_cancelled.short_description = "Marquer comme annulées"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Administration des articles de commande
    """
    list_display = ('order', 'product', 'variant', 'quantity', 'unit_price', 'total_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__order_number', 'product__name', 'variant__name')
    readonly_fields = ('total_price', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'product', 'variant')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Administration des paniers
    """
    list_display = ('user', 'item_count', 'total_price', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def item_count(self, obj):
        """Nombre d'articles dans le panier"""
        return obj.items.count()
    item_count.short_description = 'Articles'
    
    def total_price(self, obj):
        """Prix total du panier"""
        return f"{obj.get_total_price():.2f} FCFA"
    total_price.short_description = 'Total'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Administration des articles de panier
    """
    list_display = ('cart', 'product', 'variant', 'quantity', 'unit_price', 'total_price', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('cart__user__username', 'product__name', 'variant__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def unit_price(self, obj):
        """Prix unitaire"""
        return f"{obj.get_unit_price():.2f} FCFA"
    unit_price.short_description = 'Prix unitaire'
    
    def total_price(self, obj):
        """Prix total"""
        return f"{obj.get_total_price():.2f} FCFA"
    total_price.short_description = 'Total'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart__user', 'product', 'variant')


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    """
    Administration des adresses de livraison
    """
    list_display = ('user', 'first_name', 'last_name', 'city', 'country', 'is_default', 'created_at')
    list_filter = ('is_default', 'country', 'created_at')
    search_fields = ('user__username', 'user__email', 'first_name', 'last_name', 'city')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'is_default')
        }),
        (_('Informations de contact'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Adresse'), {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """
    Administration de l'historique des statuts
    """
    list_display = ('order', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'created_by__username', 'notes')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'created_by')