from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from orders.models import Order
import uuid

User = get_user_model()


class PaymentMethod(models.Model):
    """
    Méthodes de paiement disponibles
    """
    PAYMENT_TYPES = [
        ('mobile_money', 'Mobile Money'),
        ('bank_card', 'Carte Bancaire'),
        ('wave', 'Wave'),
        ('cash_on_delivery', 'Paiement à la Livraison'),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='mobile_money', verbose_name=_("Type"))
    logo = models.ImageField(upload_to='payment_logos/', blank=True, null=True, verbose_name=_("Logo"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    fees_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_("Frais (%)")
    )
    min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_("Montant minimum")
    )
    max_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=999999.99,
        validators=[MinValueValidator(0)],
        verbose_name=_("Montant maximum")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Méthode de paiement")
        verbose_name_plural = _("Méthodes de paiement")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PaymentTransaction(models.Model):
    """
    Transactions de paiement
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name=_("ID Transaction"))
    
    # Relations
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name=_("Commande"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', verbose_name=_("Utilisateur"))
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, verbose_name=_("Méthode de paiement"))
    
    # Montants
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Montant"))
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("Frais"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Montant total"))
    
    # Statut et dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Statut"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Terminé le"))
    
    # Informations de paiement
    payment_reference = models.CharField(max_length=200, blank=True, verbose_name=_("Référence de paiement"))
    external_transaction_id = models.CharField(max_length=200, blank=True, verbose_name=_("ID Transaction Externe"))
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Métadonnées"))
    error_message = models.TextField(blank=True, verbose_name=_("Message d'erreur"))
    
    class Meta:
        verbose_name = _("Transaction de paiement")
        verbose_name_plural = _("Transactions de paiement")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.order} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN_{self.id.hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def is_successful(self):
        return self.status == 'completed'
    
    def can_be_refunded(self):
        return self.status == 'completed' and self.order.status in ['delivered', 'completed']


class MobileMoneyAccount(models.Model):
    """
    Comptes Mobile Money des utilisateurs
    """
    PROVIDER_CHOICES = [
        ('moov', 'Moov Money'),
        ('orange', 'Orange Money'),
        ('mtn', 'MTN Money'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mobile_money_accounts', verbose_name=_("Utilisateur"))
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, verbose_name=_("Fournisseur"))
    phone_number = models.CharField(max_length=20, verbose_name=_("Numéro de téléphone"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Vérifié"))
    is_primary = models.BooleanField(default=False, verbose_name=_("Principal"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Compte Mobile Money")
        verbose_name_plural = _("Comptes Mobile Money")
        unique_together = ['user', 'provider', 'phone_number']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_provider_display()} - {self.phone_number}"


class BankCard(models.Model):
    """
    Cartes bancaires des utilisateurs
    """
    CARD_TYPES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_cards', verbose_name=_("Utilisateur"))
    card_type = models.CharField(max_length=20, choices=CARD_TYPES, verbose_name=_("Type de carte"))
    last_four_digits = models.CharField(max_length=4, verbose_name=_("4 derniers chiffres"))
    expiry_month = models.PositiveIntegerField(verbose_name=_("Mois d'expiration"))
    expiry_year = models.PositiveIntegerField(verbose_name=_("Année d'expiration"))
    cardholder_name = models.CharField(max_length=100, verbose_name=_("Nom du titulaire"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Vérifié"))
    is_primary = models.BooleanField(default=False, verbose_name=_("Principal"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Carte bancaire")
        verbose_name_plural = _("Cartes bancaires")
    
    def __str__(self):
        return f"{self.user.username} - {self.get_card_type_display()} ****{self.last_four_digits}"


class RefundRequest(models.Model):
    """
    Demandes de remboursement
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('processed', 'Traité'),
    ]
    
    REASON_CHOICES = [
        ('defective', 'Produit défectueux'),
        ('wrong_item', 'Mauvais article'),
        ('not_delivered', 'Non livré'),
        ('cancelled', 'Commande annulée'),
        ('other', 'Autre'),
    ]
    
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='refund_requests', verbose_name=_("Transaction"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests', verbose_name=_("Utilisateur"))
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, verbose_name=_("Raison"))
    description = models.TextField(verbose_name=_("Description"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Statut"))
    admin_notes = models.TextField(blank=True, verbose_name=_("Notes administrateur"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Traité le"))
    
    class Meta:
        verbose_name = _("Demande de remboursement")
        verbose_name_plural = _("Demandes de remboursement")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Remboursement {self.transaction.transaction_id} - {self.get_status_display()}"