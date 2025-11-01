"""
Modèles pour la gestion avancée des stocks et inventaire
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Supplier(models.Model):
    """Modèle pour les fournisseurs"""
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom du fournisseur")
    contact_person = models.CharField(max_length=100, verbose_name="Personne de contact")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    address = models.TextField(verbose_name="Adresse")
    city = models.CharField(max_length=100, verbose_name="Ville")
    country = models.CharField(max_length=100, default="Côte d'Ivoire", verbose_name="Pays")
    tax_id = models.CharField(max_length=50, blank=True, verbose_name="Numéro fiscal")
    payment_terms = models.CharField(max_length=100, default="30 jours", verbose_name="Conditions de paiement")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_total_products(self):
        """Nombre total de produits fournis"""
        return self.products.count()
    
    def get_average_rating(self):
        """Note moyenne du fournisseur"""
        return self.rating


class StockAlert(models.Model):
    """Modèle pour les alertes de stock"""
    ALERT_TYPES = [
        ('low_stock', 'Stock bas'),
        ('out_of_stock', 'Rupture de stock'),
        ('overstock', 'Surstock'),
        ('expiring', 'Expiration proche'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]
    
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stock_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    threshold_value = models.IntegerField(verbose_name="Seuil d'alerte")
    current_stock = models.IntegerField(verbose_name="Stock actuel")
    message = models.TextField(verbose_name="Message d'alerte")
    is_resolved = models.BooleanField(default=False, verbose_name="Résolu")
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Alerte de stock"
        verbose_name_plural = "Alertes de stock"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alerte {self.alert_type} - {self.product.name}"
    
    def resolve(self, user):
        """Résoudre l'alerte"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()


class InventoryTransaction(models.Model):
    """Modèle pour les transactions d'inventaire"""
    TRANSACTION_TYPES = [
        ('in', 'Entrée'),
        ('out', 'Sortie'),
        ('adjustment', 'Ajustement'),
        ('transfer', 'Transfert'),
        ('return', 'Retour'),
    ]
    
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='inventory_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(verbose_name="Quantité")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût unitaire")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût total")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_transactions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transaction d'inventaire"
        verbose_name_plural = "Transactions d'inventaire"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        if self.unit_cost and self.quantity:
            self.total_cost = self.unit_cost * self.quantity
        super().save(*args, **kwargs)


class ProductSupplier(models.Model):
    """Modèle pour la relation produit-fournisseur"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='suppliers')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    supplier_sku = models.CharField(max_length=100, blank=True, verbose_name="SKU fournisseur")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix d'achat")
    minimum_order_quantity = models.IntegerField(default=1, verbose_name="Quantité minimum de commande")
    lead_time_days = models.IntegerField(default=7, verbose_name="Délai de livraison (jours)")
    is_primary = models.BooleanField(default=False, verbose_name="Fournisseur principal")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Fournisseur de produit"
        verbose_name_plural = "Fournisseurs de produits"
        unique_together = ['product', 'supplier']
    
    def __str__(self):
        return f"{self.product.name} - {self.supplier.name}"


class StockMovement(models.Model):
    """Modèle pour les mouvements de stock"""
    MOVEMENT_TYPES = [
        ('sale', 'Vente'),
        ('return', 'Retour'),
        ('adjustment', 'Ajustement'),
        ('transfer', 'Transfert'),
        ('damage', 'Dégât'),
        ('expired', 'Expiré'),
    ]
    
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(verbose_name="Quantité")
    previous_stock = models.IntegerField(verbose_name="Stock précédent")
    new_stock = models.IntegerField(verbose_name="Nouveau stock")
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_movements')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.movement_type} - {self.product.name} - {self.quantity}"


class InventoryReport(models.Model):
    """Modèle pour les rapports d'inventaire"""
    REPORT_TYPES = [
        ('stock_levels', 'Niveaux de stock'),
        ('movements', 'Mouvements'),
        ('alerts', 'Alertes'),
        ('valuation', 'Évaluation'),
        ('turnover', 'Rotation'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200, verbose_name="Titre du rapport")
    description = models.TextField(blank=True, verbose_name="Description")
    data = models.JSONField(default=dict, verbose_name="Données du rapport")
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Rapport d'inventaire"
        verbose_name_plural = "Rapports d'inventaire"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%d/%m/%Y')}"