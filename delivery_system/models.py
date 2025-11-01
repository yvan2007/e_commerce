from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class Region(models.Model):
    """
    Modèle pour les régions de Côte d'Ivoire
    """
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Nom de la région"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Code région"))
    is_active = models.BooleanField(default=True, verbose_name=_("Région active"))
    
    class Meta:
        verbose_name = _("Région")
        verbose_name_plural = _("Régions")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class City(models.Model):
    """
    Modèle pour les villes de Côte d'Ivoire
    """
    name = models.CharField(max_length=100, verbose_name=_("Nom de la ville"))
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities', verbose_name=_("Région"))
    postal_code = models.CharField(max_length=20, blank=True, verbose_name=_("Code postal"))
    is_active = models.BooleanField(default=True, verbose_name=_("Ville active"))
    
    class Meta:
        verbose_name = _("Ville")
        verbose_name_plural = _("Villes")
        unique_together = ['name', 'region']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"


class DeliveryZone(models.Model):
    """
    Modèle pour définir les zones de livraison avec leurs frais
    """
    ZONE_TYPES = [
        ('abidjan', _('Abidjan')),
        ('bassam', _('Grand-Bassam')),
        ('civ_other', _('Autres villes de Côte d\'Ivoire')),
        ('international', _('International')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom de la zone")
    )
    
    zone_type = models.CharField(
        max_length=20,
        choices=ZONE_TYPES,
        default='city',
        verbose_name=_("Type de zone")
    )
    
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=2500.00,
        verbose_name=_("Frais de livraison (FCFA)")
    )
    
    estimated_days = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Délai de livraison estimé (jours)")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Zone active")
    )
    
    # Relation avec la ville
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_zones',
        verbose_name=_("Ville")
    )
    
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    city_list = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Liste des villes pour cette zone (séparées par des virgules)",
        verbose_name=_("Liste des villes")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Zone de livraison")
        verbose_name_plural = _("Zones de livraison")
        ordering = ['zone_type', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.delivery_fee} FCFA"


class DeliveryAddress(models.Model):
    """
    Modèle pour les adresses de livraison des clients
    """
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='delivery_addresses',
        verbose_name=_("Utilisateur")
    )
    
    first_name = models.CharField(
        max_length=50,
        verbose_name=_("Prénom")
    )
    
    last_name = models.CharField(
        max_length=50,
        verbose_name=_("Nom")
    )
    
    phone_number = models.CharField(
        max_length=20,
        verbose_name=_("Numéro de téléphone")
    )
    
    address_line_1 = models.CharField(
        max_length=255,
        verbose_name=_("Adresse ligne 1")
    )
    
    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Adresse ligne 2")
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
    
    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Zone de livraison")
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
    
    def get_full_address(self):
        """Retourne l'adresse complète formatée"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, address_parts))


class DeliveryCalculation(models.Model):
    """
    Modèle pour stocker les calculs de livraison
    """
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery_calculation',
        verbose_name=_("Commande")
    )
    
    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.CASCADE,
        verbose_name=_("Zone de livraison")
    )
    
    base_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Frais de base")
    )
    
    additional_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Frais supplémentaires")
    )
    
    total_delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total frais de livraison")
    )
    
    estimated_delivery_date = models.DateField(
        verbose_name=_("Date de livraison estimée")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Calcul de livraison")
        verbose_name_plural = _("Calculs de livraison")
    
    def __str__(self):
        return f"Livraison {self.order.order_number} - {self.total_delivery_fee} FCFA"