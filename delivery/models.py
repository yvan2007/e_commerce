"""
Modèles pour le système de géolocalisation et livraison
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Country(models.Model):
    """Modèle pour les pays"""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)  # CIV, FRA, etc.
    phone_code = models.CharField(max_length=5)  # +225, +33, etc.
    currency_code = models.CharField(max_length=3, default="XOF")  # XOF, EUR, USD
    currency_symbol = models.CharField(max_length=5, default="FCFA")
    is_active = models.BooleanField(default=True)

    # Configuration de livraison
    default_delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    free_delivery_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("50000.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pays"
        verbose_name_plural = "Pays"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Region(models.Model):
    """Modèle pour les régions/provinces"""

    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="regions"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        ordering = ["name"]
        unique_together = ["country", "name"]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class City(models.Model):
    """Modèle pour les villes"""

    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    # Coordonnées GPS
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ["name"]
        unique_together = ["region", "name"]

    def __str__(self):
        return f"{self.name}, {self.region.name}"


class DeliveryZone(models.Model):
    """Modèle pour les zones de livraison"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Zone géographique
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="delivery_zones"
    )
    regions = models.ManyToManyField(Region, blank=True, related_name="delivery_zones")
    cities = models.ManyToManyField(City, blank=True, related_name="delivery_zones")
    postal_codes = models.JSONField(default=list, blank=True)  # Liste des codes postaux

    # Configuration de livraison
    delivery_cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    free_delivery_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    estimated_days_min = models.IntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    estimated_days_max = models.IntegerField(
        default=3, validators=[MinValueValidator(1)]
    )

    # Statut
    is_active = models.BooleanField(default=True)
    is_express = models.BooleanField(default=False)  # Livraison express

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zone de livraison"
        verbose_name_plural = "Zones de livraison"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.country.name}"

    def get_estimated_delivery_days(self):
        """Retourner la plage de jours de livraison"""
        if self.estimated_days_min == self.estimated_days_max:
            return f"{self.estimated_days_min} jour{'s' if self.estimated_days_min > 1 else ''}"
        return f"{self.estimated_days_min}-{self.estimated_days_max} jours"

    def calculate_delivery_cost(self, order_amount):
        """Calculer le coût de livraison pour un montant donné"""
        if order_amount >= self.free_delivery_threshold:
            return Decimal("0.00")
        return self.delivery_cost


class DeliveryMethod(models.Model):
    """Modèle pour les méthodes de livraison"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Classe d'icône Font Awesome

    # Configuration
    is_active = models.BooleanField(default=True)
    is_express = models.BooleanField(default=False)
    requires_signature = models.BooleanField(default=False)
    allows_cod = models.BooleanField(default=True)  # Paiement à la livraison

    # Zones applicables
    delivery_zones = models.ManyToManyField(
        DeliveryZone, blank=True, related_name="delivery_methods"
    )

    # Coûts
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    cost_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Méthode de livraison"
        verbose_name_plural = "Méthodes de livraison"
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserLocation(models.Model):
    """Modèle pour les localisations des utilisateurs"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="location")

    # Adresse
    address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)

    # Coordonnées GPS
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )

    # Métadonnées
    is_verified = models.BooleanField(default=False)
    is_default = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Localisation utilisateur"
        verbose_name_plural = "Localisations utilisateurs"

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.address}"

    def get_delivery_zones(self):
        """Récupérer les zones de livraison applicables"""
        if not self.city:
            return DeliveryZone.objects.none()

        return DeliveryZone.objects.filter(
            models.Q(cities=self.city)
            | models.Q(regions=self.city.region)
            | models.Q(country=self.city.region.country)
        ).distinct()


class DeliveryTracking(models.Model):
    """Modèle pour le suivi des livraisons"""

    STATUS_CHOICES = [
        ("preparing", "En préparation"),
        ("shipped", "Expédié"),
        ("in_transit", "En transit"),
        ("out_for_delivery", "En cours de livraison"),
        ("delivered", "Livré"),
        ("failed", "Échec de livraison"),
        ("returned", "Retourné"),
    ]

    order = models.OneToOneField(
        "orders.Order", on_delete=models.CASCADE, related_name="delivery_tracking"
    )
    tracking_number = models.CharField(max_length=50, unique=True)
    delivery_method = models.ForeignKey(
        DeliveryMethod, on_delete=models.CASCADE, related_name="trackings"
    )
    delivery_zone = models.ForeignKey(
        DeliveryZone, on_delete=models.CASCADE, related_name="trackings"
    )

    # Statut et dates
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="preparing"
    )
    estimated_delivery_date = models.DateTimeField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)

    # Informations de livraison
    delivery_address = models.TextField()
    delivery_instructions = models.TextField(blank=True)
    recipient_name = models.CharField(max_length=200)
    recipient_phone = models.CharField(max_length=20)

    # Suivi
    current_location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suivi de livraison"
        verbose_name_plural = "Suivis de livraison"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Suivi #{self.tracking_number} - {self.order.order_number}"

    def generate_tracking_number(self):
        """Générer un numéro de suivi unique"""
        import uuid

        return f"TRK-{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)


class DeliveryStatusUpdate(models.Model):
    """Modèle pour les mises à jour de statut de livraison"""

    tracking = models.ForeignKey(
        DeliveryTracking, on_delete=models.CASCADE, related_name="status_updates"
    )
    status = models.CharField(max_length=20, choices=DeliveryTracking.STATUS_CHOICES)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivery_status_updates",
    )
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mise à jour de statut de livraison"
        verbose_name_plural = "Mises à jour de statut de livraison"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.tracking.tracking_number} - {self.status}"
