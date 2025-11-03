import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class NotificationTemplate(models.Model):
    """
    Modèles de notifications
    """

    NOTIFICATION_TYPES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notification"),
        ("in_app", "Notification In-App"),
    ]

    TRIGGER_TYPES = [
        ("order_placed", "Commande passée"),
        ("order_confirmed", "Commande confirmée"),
        ("order_shipped", "Commande expédiée"),
        ("order_delivered", "Commande livrée"),
        ("payment_success", "Paiement réussi"),
        ("payment_failed", "Paiement échoué"),
        ("vendor_approved", "Vendeur approuvé"),
        ("vendor_rejected", "Vendeur rejeté"),
        ("product_review", "Avis produit"),
        ("low_stock", "Stock faible"),
        ("promotion", "Promotion"),
        ("welcome", "Bienvenue"),
    ]

    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, verbose_name=_("Type")
    )
    trigger_type = models.CharField(
        max_length=30, choices=TRIGGER_TYPES, verbose_name=_("Déclencheur")
    )
    subject = models.CharField(max_length=200, verbose_name=_("Sujet"))
    content = models.TextField(verbose_name=_("Contenu"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Modèle de notification")
        verbose_name_plural = _("Modèles de notification")
        unique_together = ["type", "trigger_type"]

    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"


class Notification(models.Model):
    """
    Notifications envoyées aux utilisateurs
    """

    NOTIFICATION_TYPES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notification"),
        ("in_app", "Notification In-App"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("sent", "Envoyé"),
        ("delivered", "Livré"),
        ("failed", "Échoué"),
        ("read", "Lu"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Utilisateur"),
    )
    template = models.ForeignKey(
        NotificationTemplate, on_delete=models.CASCADE, verbose_name=_("Modèle")
    )
    type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, verbose_name=_("Type")
    )
    subject = models.CharField(max_length=200, verbose_name=_("Sujet"))
    content = models.TextField(verbose_name=_("Contenu"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Statut"),
    )
    is_read = models.BooleanField(default=False, verbose_name=_("Lu"))
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Envoyé le"))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Lu le"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Métadonnées"))
    error_message = models.TextField(blank=True, verbose_name=_("Message d'erreur"))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.subject}"

    def mark_as_read(self):
        """Marquer comme lu"""
        from django.utils import timezone

        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class NotificationPreference(models.Model):
    """
    Préférences de notification des utilisateurs
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name=_("Utilisateur"),
    )

    # Préférences email
    email_order_updates = models.BooleanField(
        default=True, verbose_name=_("Mises à jour de commande par email")
    )
    email_promotions = models.BooleanField(
        default=True, verbose_name=_("Promotions par email")
    )
    email_newsletter = models.BooleanField(
        default=True, verbose_name=_("Newsletter par email")
    )
    email_reviews = models.BooleanField(default=True, verbose_name=_("Avis par email"))

    # Préférences SMS
    sms_order_updates = models.BooleanField(
        default=True, verbose_name=_("Mises à jour de commande par SMS")
    )
    sms_promotions = models.BooleanField(
        default=False, verbose_name=_("Promotions par SMS")
    )

    # Préférences push
    push_order_updates = models.BooleanField(
        default=True, verbose_name=_("Mises à jour de commande par push")
    )
    push_promotions = models.BooleanField(
        default=True, verbose_name=_("Promotions par push")
    )
    push_reviews = models.BooleanField(default=True, verbose_name=_("Avis par push"))

    # Préférences in-app
    in_app_order_updates = models.BooleanField(
        default=True, verbose_name=_("Mises à jour de commande in-app")
    )
    in_app_promotions = models.BooleanField(
        default=True, verbose_name=_("Promotions in-app")
    )
    in_app_reviews = models.BooleanField(default=True, verbose_name=_("Avis in-app"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Préférence de notification")
        verbose_name_plural = _("Préférences de notification")

    def __str__(self):
        return f"Préférences de {self.user.username}"


class EmailQueue(models.Model):
    """
    File d'attente des emails
    """

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("processing", "En cours"),
        ("sent", "Envoyé"),
        ("failed", "Échoué"),
    ]

    PRIORITY_CHOICES = [
        (1, "Très haute"),
        (2, "Haute"),
        (3, "Normale"),
        (4, "Basse"),
        (5, "Très basse"),
    ]

    to_email = models.EmailField(verbose_name=_("Email destinataire"))
    subject = models.CharField(max_length=200, verbose_name=_("Sujet"))
    content = models.TextField(verbose_name=_("Contenu"))
    html_content = models.TextField(blank=True, verbose_name=_("Contenu HTML"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Statut"),
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES, default=3, verbose_name=_("Priorité")
    )
    retry_count = models.PositiveIntegerField(
        default=0, verbose_name=_("Nombre de tentatives")
    )
    max_retries = models.PositiveIntegerField(
        default=3, verbose_name=_("Tentatives maximum")
    )
    scheduled_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Programmé pour")
    )
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Envoyé le"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Métadonnées"))
    error_message = models.TextField(blank=True, verbose_name=_("Message d'erreur"))

    class Meta:
        verbose_name = _("Email en file d'attente")
        verbose_name_plural = _("Emails en file d'attente")
        ordering = ["priority", "created_at"]

    def __str__(self):
        return f"{self.to_email} - {self.subject}"


class SMSQueue(models.Model):
    """
    File d'attente des SMS
    """

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("processing", "En cours"),
        ("sent", "Envoyé"),
        ("failed", "Échoué"),
    ]

    to_phone = models.CharField(max_length=20, verbose_name=_("Téléphone destinataire"))
    message = models.TextField(verbose_name=_("Message"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Statut"),
    )
    retry_count = models.PositiveIntegerField(
        default=0, verbose_name=_("Nombre de tentatives")
    )
    max_retries = models.PositiveIntegerField(
        default=3, verbose_name=_("Tentatives maximum")
    )
    scheduled_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Programmé pour")
    )
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Envoyé le"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Métadonnées"))
    error_message = models.TextField(blank=True, verbose_name=_("Message d'erreur"))

    class Meta:
        verbose_name = _("SMS en file d'attente")
        verbose_name_plural = _("SMS en file d'attente")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.to_phone} - {self.message[:50]}..."
