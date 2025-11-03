"""
Système de notifications email pour l'e-commerce
Gestion des emails de confirmation, livraison, etc.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Service de gestion des notifications email
    """

    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.site_name = "E-Commerce CI"
        self.site_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    def send_order_confirmation(self, order):
        """
        Envoie un email de confirmation de commande
        """
        try:
            subject = f"Confirmation de votre commande {order.order_number}"

            # Contexte pour le template
            context = {
                "order": order,
                "site_name": self.site_name,
                "site_url": self.site_url,
                "customer_name": f"{order.shipping_first_name} {order.shipping_last_name}",
            }

            # Rendu du template HTML
            html_content = render_to_string("emails/order_confirmation.html", context)
            text_content = strip_tags(html_content)

            # Création de l'email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[order.user.email],
            )

            email.attach_alternative(html_content, "text/html")

            # Ajout des images des produits en pièces jointes
            self._attach_product_images(email, order)

            # Envoi de l'email
            email.send()

            logger.info(
                f"Email de confirmation envoyé pour la commande {order.order_number}"
            )
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {e}")
            return False

    def send_order_status_update(self, order, old_status, new_status):
        """
        Envoie un email de mise à jour de statut
        """
        try:
            status_messages = {
                "confirmed": "Votre commande a été confirmée",
                "processing": "Votre commande est en cours de traitement",
                "shipped": "Votre commande a été expédiée",
                "delivered": "Votre commande a été livrée",
                "cancelled": "Votre commande a été annulée",
                "refunded": "Votre commande a été remboursée",
            }

            subject = f"Mise à jour de votre commande {order.order_number}"

            context = {
                "order": order,
                "site_name": self.site_name,
                "site_url": self.site_url,
                "customer_name": f"{order.shipping_first_name} {order.shipping_last_name}",
                "status_message": status_messages.get(new_status, "Statut mis à jour"),
                "old_status": old_status,
                "new_status": new_status,
            }

            html_content = render_to_string("emails/order_status_update.html", context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[order.user.email],
            )

            email.attach_alternative(html_content, "text/html")

            # Ajout des images des produits
            self._attach_product_images(email, order)

            email.send()

            logger.info(
                f"Email de mise à jour envoyé pour la commande {order.order_number}"
            )
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de mise à jour: {e}")
            return False

    def send_delivery_confirmation(self, order):
        """
        Envoie un email de confirmation de livraison
        """
        try:
            subject = f"Votre commande {order.order_number} a été livrée"

            context = {
                "order": order,
                "site_name": self.site_name,
                "site_url": self.site_url,
                "customer_name": f"{order.shipping_first_name} {order.shipping_last_name}",
                "delivery_date": order.delivered_at,
            }

            html_content = render_to_string(
                "emails/delivery_confirmation.html", context
            )
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[order.user.email],
            )

            email.attach_alternative(html_content, "text/html")

            # Ajout des images des produits
            self._attach_product_images(email, order)

            email.send()

            logger.info(
                f"Email de livraison envoyé pour la commande {order.order_number}"
            )
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de livraison: {e}")
            return False

    def send_welcome_email(self, user):
        """
        Envoie un email de bienvenue
        """
        try:
            subject = f"Bienvenue sur {self.site_name}"

            context = {
                "user": user,
                "site_name": self.site_name,
                "site_url": self.site_url,
                "user_name": user.get_display_name(),
            }

            html_content = render_to_string("emails/welcome.html", context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[user.email],
            )

            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Email de bienvenue envoyé à {user.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
            return False

    def send_password_reset(self, user, reset_url):
        """
        Envoie un email de réinitialisation de mot de passe
        """
        try:
            subject = f"Réinitialisation de votre mot de passe - {self.site_name}"

            context = {
                "user": user,
                "site_name": self.site_name,
                "site_url": self.site_url,
                "reset_url": reset_url,
                "user_name": user.get_display_name(),
            }

            html_content = render_to_string("emails/password_reset.html", context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[user.email],
            )

            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Email de réinitialisation envoyé à {user.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
            return False

    def send_vendor_notification(self, order, vendor):
        """
        Envoie une notification au vendeur pour une nouvelle commande
        """
        try:
            subject = (
                f"Nouvelle commande #{order.order_number} - Produits de votre boutique"
            )

            # Récupérer les produits du vendeur dans cette commande
            vendor_items = order.items.filter(product__vendor=vendor)

            context = {
                "order": order,
                "vendor": vendor,
                "vendor_items": vendor_items,
                "site_name": self.site_name,
                "site_url": self.site_url,
                "vendor_name": vendor.get_display_name(),
            }

            html_content = render_to_string("emails/vendor_notification.html", context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[vendor.email],
            )

            email.attach_alternative(html_content, "text/html")

            # Ajout des images des produits du vendeur
            self._attach_vendor_product_images(email, vendor_items)

            email.send()

            logger.info(
                f"Notification vendeur envoyée pour la commande {order.order_number}"
            )
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification vendeur: {e}")
            return False

    def _attach_product_images(self, email, order):
        """
        Attache les images des produits en pièces jointes
        """
        try:
            for item in order.items.all():
                if item.product.main_image:
                    try:
                        email.attach_file(item.product.main_image.path)
                    except Exception as e:
                        logger.warning(
                            f"Impossible d'attacher l'image du produit {item.product.name}: {e}"
                        )
        except Exception as e:
            logger.warning(f"Erreur lors de l'attachement des images: {e}")

    def _attach_vendor_product_images(self, email, vendor_items):
        """
        Attache les images des produits du vendeur
        """
        try:
            for item in vendor_items:
                if item.product.main_image:
                    try:
                        email.attach_file(item.product.main_image.path)
                    except Exception as e:
                        logger.warning(
                            f"Impossible d'attacher l'image du produit {item.product.name}: {e}"
                        )
        except Exception as e:
            logger.warning(f"Erreur lors de l'attachement des images vendeur: {e}")


# Instance globale du service
email_service = EmailNotificationService()


# Fonctions utilitaires pour faciliter l'utilisation
def send_order_confirmation_email(order):
    """Envoie un email de confirmation de commande"""
    return email_service.send_order_confirmation(order)


def send_order_status_update_email(order, old_status, new_status):
    """Envoie un email de mise à jour de statut"""
    return email_service.send_order_status_update(order, old_status, new_status)


def send_delivery_confirmation_email(order):
    """Envoie un email de confirmation de livraison"""
    return email_service.send_delivery_confirmation(order)


def send_welcome_email(user):
    """Envoie un email de bienvenue"""
    return email_service.send_welcome_email(user)


def send_password_reset_email(user, reset_url):
    """Envoie un email de réinitialisation de mot de passe"""
    return email_service.send_password_reset(user, reset_url)


def send_vendor_notification_email(order, vendor):
    """Envoie une notification au vendeur"""
    return email_service.send_vendor_notification(order, vendor)
