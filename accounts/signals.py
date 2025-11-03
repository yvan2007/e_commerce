"""
Signaux Django pour l'application accounts
"""
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile_and_cart(sender, instance, created, **kwargs):
    """
    Créer automatiquement le profil utilisateur, le panier et envoyer l'email de bienvenue
    pour un nouvel utilisateur
    """
    if created:
        try:
            # Créer le profil utilisateur
            from .models import UserProfile

            UserProfile.objects.get_or_create(user=instance)

            # Créer le panier
            from orders.models import Cart

            Cart.objects.get_or_create(user=instance)

            logger.info(f"Profil et panier créés pour {instance.username}")

            # Envoyer l'email de bienvenue pour les nouveaux utilisateurs
            # Vérifier si l'utilisateur a été créé il y a moins de 5 minutes (pour éviter les doublons)
            if instance.date_joined > timezone.now() - timedelta(minutes=5):
                try:
                    from notifications.services import EmailService

                    EmailService.send_welcome_email(instance)
                    logger.info(f"Email de bienvenue envoyé à {instance.email}")
                except Exception as e:
                    logger.error(
                        f"Erreur lors de l'envoi de l'email de bienvenue pour {instance.username}: {e}"
                    )

        except Exception as e:
            logger.error(
                f"Erreur lors de la création du profil/panier pour {instance.username}: {e}"
            )
