from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

User = get_user_model()


class Order(models.Model):
    """
    Modèle pour les commandes
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('processing', 'En cours de traitement'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash à la livraison'),
        ('moovmoney', 'Moov Money'),
        ('orangemoney', 'Orange Money'),
        ('mtnmoney', 'MTN Money'),
        ('wave', 'Wave'),
        ('carte', 'Carte bancaire'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('failed', 'Échec'),
        ('refunded', 'Remboursé'),
    ]
    
    # Informations de base
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Numéro de commande")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_("Client")
    )
    
    # Statuts
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Statut")
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name=_("Méthode de paiement")
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name=_("Statut du paiement")
    )
    
    # Adresse de livraison
    shipping_first_name = models.CharField(
        max_length=100,
        verbose_name=_("Prénom")
    )
    
    shipping_last_name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    
    shipping_phone = models.CharField(
        max_length=20,
        verbose_name=_("Téléphone")
    )
    
    shipping_address = models.TextField(
        verbose_name=_("Adresse")
    )
    
    shipping_city = models.CharField(
        max_length=100,
        verbose_name=_("Ville")
    )
    
    shipping_postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Code postal")
    )
    
    shipping_country = models.CharField(
        max_length=100,
        default='Côte d\'Ivoire',
        verbose_name=_("Pays")
    )
    
    # Adresse de facturation (optionnelle)
    billing_address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Adresse de facturation")
    )
    
    # Montants
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Sous-total")
    )
    
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Frais de livraison")
    )
    
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Montant des taxes")
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Montant total")
    )
    
    # Notes et commentaires
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    # Informations de paiement
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Référence de paiement")
    )
    
    payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Date de paiement")
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"Commande {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"CMD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('orders:order_detail', kwargs={'order_number': self.order_number})
    
    def get_status_display_color(self):
        """Retourne la couleur CSS pour le statut"""
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'primary',
            'shipped': 'info',
            'delivered': 'success',
            'cancelled': 'danger',
            'refunded': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def can_be_cancelled(self):
        """Vérifie si la commande peut être annulée"""
        return self.status in ['pending', 'confirmed']


class OrderItem(models.Model):
    """
    Modèle pour les articles d'une commande
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Commande")
    )
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name=_("Produit")
    )
    
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Variante")
    )
    
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Quantité")
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Prix unitaire")
    )
    
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Prix total")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Article de commande")
        verbose_name_plural = _("Articles de commande")
        unique_together = ['order', 'product', 'variant']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # S'assurer que le calcul respecte les décimales
        from decimal import Decimal
        self.total_price = Decimal(str(self.unit_price)) * Decimal(str(self.quantity))
        super().save(*args, **kwargs)


class Cart(models.Model):
    """
    Modèle pour le panier d'achat
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_("Utilisateur")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Panier")
        verbose_name_plural = _("Paniers")
    
    def __str__(self):
        return f"Panier de {self.user.username}"
    
    def get_total_items(self):
        """Retourne le nombre total d'articles dans le panier"""
        return sum(item.quantity for item in self.items.all())
    
    def get_total_price(self):
        """Retourne le prix total du panier"""
        from decimal import Decimal
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.get_total_price()
        return total
    
    def clear(self):
        """Vide le panier"""
        self.items.all().delete()


class CartItem(models.Model):
    """
    Modèle pour les articles du panier
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Panier")
    )
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name=_("Produit")
    )
    
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Variante")
    )
    
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Quantité")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Article du panier")
        verbose_name_plural = _("Articles du panier")
        unique_together = ['cart', 'product', 'variant']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_unit_price(self):
        """Retourne le prix unitaire"""
        from decimal import Decimal
        if self.variant:
            return Decimal(str(self.variant.price))
        return Decimal(str(self.product.price))
    
    def get_total_price(self):
        """Retourne le prix total pour cet article"""
        from decimal import Decimal
        return self.get_unit_price() * Decimal(str(self.quantity))


class ShippingAddress(models.Model):
    """
    Modèle pour les adresses de livraison sauvegardées
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shipping_addresses',
        verbose_name=_("Utilisateur")
    )
    
    first_name = models.CharField(
        max_length=100,
        verbose_name=_("Prénom")
    )
    
    last_name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    
    phone = models.CharField(
        max_length=20,
        verbose_name=_("Téléphone")
    )
    
    address = models.TextField(
        verbose_name=_("Adresse")
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name=_("Ville")
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Code postal")
    )
    
    country = models.CharField(
        max_length=100,
        default='Côte d\'Ivoire',
        verbose_name=_("Pays")
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Adresse par défaut")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Adresse de livraison")
        verbose_name_plural = _("Adresses de livraison")
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.city}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Désactiver les autres adresses par défaut
            ShippingAddress.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Modèle pour l'historique des statuts de commande
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_("Commande")
    )
    
    status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name=_("Statut")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Créé par")
    )
    
    class Meta:
        verbose_name = _("Historique des statuts")
        verbose_name_plural = _("Historiques des statuts")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"