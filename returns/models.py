"""
Modèles pour le système de remboursement et retours
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()


class ReturnRequest(models.Model):
    """Modèle pour les demandes de retour"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('processing', 'En cours de traitement'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    REASON_CHOICES = [
        ('defective', 'Produit défectueux'),
        ('wrong_item', 'Mauvais article reçu'),
        ('not_as_described', 'Ne correspond pas à la description'),
        ('damaged_shipping', 'Endommagé pendant l\'expédition'),
        ('changed_mind', 'Changement d\'avis'),
        ('duplicate_order', 'Commande en double'),
        ('other', 'Autre'),
    ]
    
    RETURN_TYPES = [
        ('refund', 'Remboursement'),
        ('exchange', 'Échange'),
        ('store_credit', 'Crédit magasin'),
    ]
    
    # Informations de base
    request_number = models.CharField(max_length=20, unique=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='return_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    
    # Détails du retour
    return_type = models.CharField(max_length=20, choices=RETURN_TYPES, default='refund')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField()
    other_reason = models.CharField(max_length=200, blank=True)
    
    # Articles concernés
    items = models.ManyToManyField('orders.OrderItem', through='ReturnItem')
    
    # Statut et traitement
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)
    
    # Montants
    requested_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    approved_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Traitement
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_returns',
        limit_choices_to={'is_staff': True}
    )
    
    class Meta:
        verbose_name = "Demande de retour"
        verbose_name_plural = "Demandes de retour"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Retour #{self.request_number} - {self.user.get_display_name()}"
    
    def save(self, *args, **kwargs):
        if not self.request_number:
            self.request_number = self.generate_request_number()
        super().save(*args, **kwargs)
    
    def generate_request_number(self):
        """Générer un numéro de demande unique"""
        import uuid
        return f"RET-{uuid.uuid4().hex[:8].upper()}"
    
    def can_be_cancelled(self):
        """Vérifier si la demande peut être annulée"""
        return self.status in ['pending', 'approved']
    
    def approve(self, admin_user, approved_amount=None):
        """Approuver la demande de retour"""
        if self.status != 'pending':
            return False
        
        self.status = 'approved'
        self.approved_at = models.timezone.now()
        self.processed_by = admin_user
        if approved_amount:
            self.approved_amount = approved_amount
        else:
            self.approved_amount = self.requested_amount
        self.save()
        
        # Créer un historique
        ReturnStatusHistory.objects.create(
            return_request=self,
            status='approved',
            notes=f"Approuvé par {admin_user.get_display_name()}",
            changed_by=admin_user
        )
        
        return True
    
    def reject(self, admin_user, reason):
        """Rejeter la demande de retour"""
        if self.status != 'pending':
            return False
        
        self.status = 'rejected'
        self.processed_by = admin_user
        self.admin_notes = reason
        self.save()
        
        # Créer un historique
        ReturnStatusHistory.objects.create(
            return_request=self,
            status='rejected',
            notes=f"Rejeté par {admin_user.get_display_name()}: {reason}",
            changed_by=admin_user
        )
        
        return True


class ReturnItem(models.Model):
    """Modèle pour les articles dans une demande de retour"""
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='return_items')
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    reason = models.CharField(max_length=200, blank=True)
    condition = models.CharField(max_length=50, choices=[
        ('new', 'Neuf'),
        ('used', 'Utilisé'),
        ('damaged', 'Endommagé'),
        ('defective', 'Défectueux'),
    ], default='used')
    
    class Meta:
        verbose_name = "Article de retour"
        verbose_name_plural = "Articles de retour"
        unique_together = ['return_request', 'order_item']
    
    def __str__(self):
        return f"{self.order_item.product.name} - {self.quantity} unités"


class ReturnStatusHistory(models.Model):
    """Historique des statuts de retour"""
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=ReturnRequest.STATUS_CHOICES)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_status_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique de statut de retour"
        verbose_name_plural = "Historiques de statut de retour"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.return_request.request_number} - {self.status}"


class Refund(models.Model):
    """Modèle pour les remboursements"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    PAYMENT_METHODS = [
        ('original', 'Méthode originale'),
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('store_credit', 'Crédit magasin'),
    ]
    
    return_request = models.OneToOneField(ReturnRequest, on_delete=models.CASCADE, related_name='refund')
    refund_number = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='original')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Informations de paiement
    bank_account = models.CharField(max_length=50, blank=True)
    mobile_money_number = models.CharField(max_length=20, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Traitement
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_refunds',
        limit_choices_to={'is_staff': True}
    )
    
    class Meta:
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Remboursement #{self.refund_number} - {self.amount} FCFA"
    
    def save(self, *args, **kwargs):
        if not self.refund_number:
            self.refund_number = self.generate_refund_number()
        super().save(*args, **kwargs)
    
    def generate_refund_number(self):
        """Générer un numéro de remboursement unique"""
        import uuid
        return f"REF-{uuid.uuid4().hex[:8].upper()}"
    
    def process(self, admin_user):
        """Traiter le remboursement"""
        if self.status != 'pending':
            return False
        
        self.status = 'processing'
        self.processed_at = models.timezone.now()
        self.processed_by = admin_user
        self.save()
        
        return True
    
    def complete(self, transaction_id=None):
        """Marquer le remboursement comme terminé"""
        if self.status != 'processing':
            return False
        
        self.status = 'completed'
        self.completed_at = models.timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()
        
        return True


class StoreCredit(models.Model):
    """Modèle pour les crédits magasin"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_credits')
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    reason = models.CharField(max_length=200)
    return_request = models.ForeignKey(
        ReturnRequest, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='store_credits'
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Crédit magasin"
        verbose_name_plural = "Crédits magasin"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Crédit de {self.user.get_display_name()} - {self.balance} FCFA"
    
    def use_credit(self, amount):
        """Utiliser du crédit"""
        if self.balance >= amount and self.is_active:
            self.balance -= amount
            self.save()
            return True
        return False
    
    def is_expired(self):
        """Vérifier si le crédit est expiré"""
        if self.expires_at:
            return models.timezone.now() > self.expires_at
        return False
