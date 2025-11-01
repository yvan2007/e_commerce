"""
Signaux Django pour l'application orders
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
import logging

logger = logging.getLogger(__name__)


# Variable globale pour suivre l'ancien statut
_previous_status = {}


@receiver(pre_save, sender=Order)
def store_previous_status(sender, instance, **kwargs):
    """
    Stocker l'ancien statut de la commande
    """
    try:
        if instance.pk:
            old_instance = Order.objects.get(pk=instance.pk)
            _previous_status[instance.pk] = old_instance.status
    except Order.DoesNotExist:
        pass


@receiver(post_save, sender=Order)
def send_order_confirmation_email_signal(sender, instance, created, **kwargs):
    """
    Envoyer un email de confirmation de commande après la création
    """
    if created:
        try:
            from notifications.services import EmailService
            EmailService.send_order_confirmation_email(instance)
            logger.info(f"Email de confirmation de commande envoyé pour la commande {instance.order_number}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de confirmation pour la commande {instance.order_number}: {e}")
    
    # Envoyer un email si le statut change
    if not created and instance.pk in _previous_status:
        previous_status = _previous_status[instance.pk]
        if previous_status != instance.status:
            try:
                from notifications.services import EmailService
                # Envoyer un email de notification de changement de statut
                status_messages = {
                    'confirmed': 'confirmée',
                    'processing': 'en cours de traitement',
                    'shipped': 'expédiée',
                    'delivered': 'livrée',
                    'cancelled': 'annulée',
                }
                
                if instance.status in status_messages:
                    logger.info(f"Statut de la commande {instance.order_number} changé de {previous_status} à {instance.status}")
                    # TODO: Implémenter send_order_status_email si nécessaire
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email de changement de statut pour la commande {instance.order_number}: {e}")

