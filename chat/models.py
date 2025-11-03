"""
Modèles pour le système de chat en direct
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class ChatRoom(models.Model):
    """Modèle pour les salles de chat"""

    ROOM_TYPES = [
        ("support", "Support client"),
        ("product", "Question produit"),
        ("general", "Général"),
    ]

    STATUS_CHOICES = [
        ("active", "Actif"),
        ("closed", "Fermé"),
        ("pending", "En attente"),
    ]

    room_id = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customer_chats",
        limit_choices_to={"user_type": "client"},
    )
    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="vendor_chats",
        limit_choices_to={"user_type": "vendeur"},
        null=True,
        blank=True,
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_chats",
        limit_choices_to={"is_staff": True},
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL, null=True, blank=True
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL, null=True, blank=True
    )
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default="support")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    subject = models.CharField(max_length=200, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=[
            ("low", "Faible"),
            ("medium", "Moyenne"),
            ("high", "Élevée"),
            ("urgent", "Urgente"),
        ],
        default="medium",
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Salle de chat"
        verbose_name_plural = "Salles de chat"
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["vendor", "status"]),
            models.Index(fields=["status", "priority"]),
        ]

    def __str__(self):
        return f"Chat #{self.room_id} - {self.customer.get_display_name()}"

    def get_participants(self):
        """Récupérer tous les participants"""
        participants = [self.customer]
        if self.vendor:
            participants.append(self.vendor)
        if self.admin:
            participants.append(self.admin)
        return participants

    def get_unread_count(self, user):
        """Récupérer le nombre de messages non lus pour un utilisateur"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def mark_as_read(self, user):
        """Marquer tous les messages comme lus pour un utilisateur"""
        self.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    def close_room(self, closed_by):
        """Fermer la salle de chat"""
        self.status = "closed"
        self.closed_at = timezone.now()
        self.save()

        # Créer un message système
        ChatMessage.objects.create(
            room=self,
            sender=closed_by,
            message="Cette conversation a été fermée.",
            message_type="system",
        )


class ChatMessage(models.Model):
    """Modèle pour les messages de chat"""

    MESSAGE_TYPES = [
        ("text", "Texte"),
        ("image", "Image"),
        ("file", "Fichier"),
        ("system", "Système"),
        ("order", "Commande"),
        ("product", "Produit"),
    ]

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_messages"
    )
    message = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=MESSAGE_TYPES, default="text"
    )

    # Pour les messages avec fichiers
    attachment = models.FileField(upload_to="chat_attachments/", null=True, blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)

    # Pour les messages de commande/produit
    related_order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL, null=True, blank=True
    )
    related_product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Métadonnées
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message de chat"
        verbose_name_plural = "Messages de chat"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["room", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"Message de {self.sender.get_display_name()} dans {self.room.room_id}"

    def mark_as_read(self):
        """Marquer le message comme lu"""
        if not self.is_read:
            self.is_read = True
            self.save()

    def edit_message(self, new_content):
        """Modifier le contenu du message"""
        self.message = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save()


class ChatParticipant(models.Model):
    """Modèle pour les participants aux chats"""

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_participations"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Participant de chat"
        verbose_name_plural = "Participants de chat"
        unique_together = ["room", "user"]

    def __str__(self):
        return f"{self.user.get_display_name()} dans {self.room.room_id}"


class ChatNotification(models.Model):
    """Modèle pour les notifications de chat"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_notifications"
    )
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="notifications"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification de chat"
        verbose_name_plural = "Notifications de chat"
        unique_together = ["user", "message"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification pour {self.user.get_display_name()} - {self.room.room_id}"
