"""
Services de notification pour l'envoi d'emails et SMS
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
import logging
import requests
import json

from .models import (
    NotificationTemplate, 
    Notification, 
    EmailQueue, 
    SMSQueue,
    NotificationPreference
)
from accounts.models import User
from orders.models import Order
from products.models import Product

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service principal de gestion des notifications
    """
    
    @staticmethod
    def send_order_notification(order, trigger_type, extra_data=None):
        """
        Envoyer une notification de commande
        """
        try:
            # Récupérer le template
            template = NotificationTemplate.objects.filter(
                trigger_type=trigger_type,
                is_active=True
            ).first()
            
            if not template:
                logger.warning(f"Aucun template trouvé pour {trigger_type}")
                return False
            
            # Préparer les données
            context = {
                'order': order,
                'user': order.user,
                'order_items': order.items.all(),
                'total_amount': order.total_amount,
                'order_date': order.created_at,
                'tracking_number': order.tracking_number,
                'delivery_address': order.shipping_address,
                **(extra_data or {})
            }
            
            # Rendre le contenu
            subject = template.subject.format(**context)
            content = template.content.format(**context)
            
            # Créer la notification
            notification = Notification.objects.create(
                user=order.user,
                template=template,
                type=template.type,
                subject=subject,
                content=content,
                metadata=context
            )
            
            # Envoyer selon le type
            if template.type == 'email':
                return NotificationService.send_email_notification(notification)
            elif template.type == 'sms':
                return NotificationService.send_sms_notification(notification)
            elif template.type == 'in_app':
                return NotificationService.send_in_app_notification(notification)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification {trigger_type}: {str(e)}")
            return False
    
    @staticmethod
    def send_email_notification(notification):
        """
        Envoyer une notification par email
        """
        try:
            # Vérifier les préférences utilisateur
            if not NotificationService._check_email_preference(notification.user, notification.template.trigger_type):
                return True
            
            # Créer l'email
            subject = notification.subject
            text_content = notification.content
            html_content = NotificationService._render_email_template(notification)
            
            # Envoyer l'email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.user.email]
            )
            
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            
            msg.send()
            
            # Mettre à jour le statut
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            logger.info(f"Email envoyé à {notification.user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'email: {str(e)}")
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save()
            return False
    
    @staticmethod
    def send_sms_notification(notification):
        """
        Envoyer une notification par SMS
        """
        try:
            # Vérifier les préférences utilisateur
            if not NotificationService._check_sms_preference(notification.user, notification.template.trigger_type):
                return True
            
            # Préparer le message
            message = notification.content
            phone_number = notification.user.get_full_phone_number()
            
            if not phone_number:
                logger.warning(f"Aucun numéro de téléphone pour {notification.user.username}")
                return False
            
            # Envoyer le SMS (simulation pour l'instant)
            # Dans un vrai projet, vous utiliseriez un service SMS comme Twilio, SMS API, etc.
            success = NotificationService._send_sms_via_api(phone_number, message)
            
            if success:
                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save()
                logger.info(f"SMS envoyé à {phone_number}")
                return True
            else:
                notification.status = 'failed'
                notification.error_message = "Échec de l'envoi SMS"
                notification.save()
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de SMS: {str(e)}")
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save()
            return False
    
    @staticmethod
    def send_in_app_notification(notification):
        """
        Envoyer une notification in-app
        """
        try:
            # Vérifier les préférences utilisateur
            if not NotificationService._check_in_app_preference(notification.user, notification.template.trigger_type):
                return True
            
            # Marquer comme envoyé (les notifications in-app sont stockées en base)
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            logger.info(f"Notification in-app créée pour {notification.user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de notification in-app: {str(e)}")
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save()
            return False
    
    @staticmethod
    def _check_email_preference(user, trigger_type):
        """
        Vérifier les préférences email de l'utilisateur
        """
        try:
            prefs = user.notification_preferences
            if trigger_type in ['order_placed', 'order_confirmed', 'order_shipped', 'order_delivered']:
                return prefs.email_order_updates
            elif trigger_type == 'promotion':
                return prefs.email_promotions
            elif trigger_type == 'product_review':
                return prefs.email_reviews
            return True
        except:
            return True
    
    @staticmethod
    def _check_sms_preference(user, trigger_type):
        """
        Vérifier les préférences SMS de l'utilisateur
        """
        try:
            prefs = user.notification_preferences
            if trigger_type in ['order_placed', 'order_confirmed', 'order_shipped', 'order_delivered']:
                return prefs.sms_order_updates
            elif trigger_type == 'promotion':
                return prefs.sms_promotions
            return True
        except:
            return True
    
    @staticmethod
    def _check_in_app_preference(user, trigger_type):
        """
        Vérifier les préférences in-app de l'utilisateur
        """
        try:
            prefs = user.notification_preferences
            if trigger_type in ['order_placed', 'order_confirmed', 'order_shipped', 'order_delivered']:
                return prefs.in_app_order_updates
            elif trigger_type == 'promotion':
                return prefs.in_app_promotions
            elif trigger_type == 'product_review':
                return prefs.in_app_reviews
            return True
        except:
            return True
    
    @staticmethod
    def _render_email_template(notification):
        """
        Rendre le template email HTML
        """
        try:
            template_name = f'emails/{notification.template.trigger_type}.html'
            context = {
                'notification': notification,
                'user': notification.user,
                'order': notification.metadata.get('order'),
                'site_name': 'KefyStore',
                'site_url': settings.SITE_URL,
            }
            
            return render_to_string(template_name, context)
        except:
            return None
    
    @staticmethod
    def _send_sms_via_api(phone_number, message):
        """
        Envoyer un SMS via API (simulation)
        """
        # Simulation d'envoi SMS
        # Dans un vrai projet, vous utiliseriez une API SMS réelle
        logger.info(f"SMS simulé envoyé à {phone_number}: {message}")
        return True


class EmailService:
    """
    Service de gestion des emails
    """
    
    @staticmethod
    def send_welcome_email(user):
        """
        Envoyer un email de bienvenue
        """
        try:
            subject = f"Bienvenue sur KefyStore, {user.first_name}!"
            
            # Rendre le template HTML
            try:
                html_content = render_to_string('emails/welcome.html', {
                    'user': user,
                    'site_name': 'KefyStore',
                    'site_url': settings.SITE_URL,
                })
            except:
                # Si le template n'existe pas, créer un contenu HTML simple
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #4A90E2;">🎉 Bienvenue sur KefyStore, {user.first_name}!</h2>
                        <p>Nous sommes ravis de vous compter parmi nos clients.</p>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                            <h3>Vous pouvez maintenant :</h3>
                            <ul>
                                <li>Parcourir nos produits</li>
                                <li>Passer des commandes</li>
                                <li>Suivre vos livraisons</li>
                                <li>Laisser des avis</li>
                            </ul>
                        </div>
                        <p><strong>Informations de votre compte :</strong></p>
                        <ul>
                            <li><strong>Nom d'utilisateur :</strong> {user.username}</li>
                            <li><strong>Email :</strong> {user.email}</li>
                            <li><strong>Type de compte :</strong> {user.get_user_type_display()}</li>
                        </ul>
                        <p>Merci de nous faire confiance !</p>
                        <p>L'équipe KefyStore</p>
                    </div>
                </body>
                </html>
                """
            
            message = f"""
            Bonjour {user.first_name},
            
            Bienvenue sur KefyStore ! Nous sommes ravis de vous compter parmi nos clients.
            
            Vous pouvez maintenant :
            - Parcourir nos produits
            - Passer des commandes
            - Suivre vos livraisons
            - Laisser des avis
            
            Merci de nous faire confiance !
            
            L'équipe KefyStore
            """
            
            # Créer l'email avec HTML
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Email de bienvenue envoye a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
            return False
    
    @staticmethod
    def send_order_confirmation_email(order):
        """
        Envoyer un email de confirmation de commande avec photos des produits
        """
        try:
            subject = f"Confirmation de commande #{order.order_number} - KefyStore"
            
            # Récupérer tous les items avec les produits et leurs images
            order_items = order.items.select_related('product', 'variant').all()
            
            # Construire les URLs absolues pour les images
            def get_absolute_image_url(image_field):
                if image_field and hasattr(image_field, 'url'):
                    return f"{settings.SITE_URL}{image_field.url}"
                return None
            
            # Préparer les items avec URLs absolues
            items_with_images = []
            for item in order_items:
                item_data = {
                    'product': item.product,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price,
                    'variant': item.variant if hasattr(item, 'variant') else None,
                    'product_image_url': get_absolute_image_url(item.product.image),
                }
                items_with_images.append(item_data)
            
            # Rendre le template HTML
            try:
                html_content = render_to_string('emails/order_confirmation.html', {
                    'order': order,
                    'user': order.user,
                    'order_items': items_with_images,
                    'site_name': 'KefyStore',
                    'site_url': settings.SITE_URL,
                })
            except Exception as e:
                logger.error(f"Erreur lors du rendu du template: {e}")
                # Si le template n'existe pas, créer un contenu HTML simple
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #28a745;">✅ Confirmation de commande #{order.order_number}</h2>
                        <p>Bonjour {order.user.first_name},</p>
                        <p>Votre commande #{order.order_number} a été confirmée avec succès.</p>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                            <h3>Détails de la commande:</h3>
                            <p><strong>Numéro:</strong> {order.order_number}</p>
                            <p><strong>Date:</strong> {order.created_at.strftime('%d/%m/%Y à %H:%M')}</p>
                            <p><strong>Montant total:</strong> {order.total_amount} FCFA</p>
                            <p><strong>Statut:</strong> {order.get_status_display()}</p>
                        </div>
                        <h3>Articles commandés:</h3>
                        """
                for item in order_items:
                    html_content += f"""
                        <div style="border-bottom: 1px solid #ddd; padding: 10px;">
                            <p><strong>{item.product.name}</strong> × {item.quantity}</p>
                            <p>Prix total: {item.total_price} FCFA</p>
                        </div>
                        """
                html_content += """
                        <p>Merci pour votre confiance!</p>
                        <p>L'équipe KefyStore</p>
                    </div>
                </body>
                </html>
                """
            
            # Créer l'email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=f"Bonjour {order.user.first_name},\n\nVotre commande #{order.order_number} a été confirmée avec succès.\n\nTotal: {order.total_amount} FCFA\n\nMerci pour votre confiance!\n\nL'équipe KefyStore",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.user.email]
            )
            
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Email de confirmation envoye pour la commande {order.order_number}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {str(e)}")
            return False
    
    @staticmethod
    def send_delivery_notification_email(order):
        """
        Envoyer un email de notification de livraison
        """
        try:
            subject = f"Votre commande #{order.id} a été livrée - KefyStore"
            
            # Rendre le template HTML
            try:
                html_content = render_to_string('emails/order_delivered.html', {
                    'order': order,
                    'user': order.user,
                    'order_items': order.items.all() if hasattr(order, 'items') else [],
                    'site_name': 'KefyStore',
                    'site_url': settings.SITE_URL,
                })
            except:
                # Si le template n'existe pas, créer un contenu HTML simple
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #28a745;">Commande livrée #{order.id}</h2>
                        <p>Bonjour {order.user.first_name},</p>
                        <p>Excellente nouvelle ! Votre commande #{order.id} a été livrée avec succès.</p>
                        <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">
                            <h3>Détails de la livraison:</h3>
                            <p><strong>Numéro de commande:</strong> #{order.id}</p>
                            <p><strong>Montant total:</strong> {order.total_amount} FCFA</p>
                            <p><strong>Date de livraison:</strong> {order.created_at}</p>
                        </div>
                        <p>Merci pour votre confiance et à bientôt sur KefyStore!</p>
                        <p>L'équipe KefyStore</p>
                    </div>
                </body>
                </html>
                """
            
            # Créer l'email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=f"Votre commande #{order.id} a été livrée.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.user.email]
            )
            
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Email de livraison envoyé pour la commande {order.id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de livraison: {str(e)}")
            return False


class SMSService:
    """
    Service de gestion des SMS
    """
    
    @staticmethod
    def send_order_sms(order, message_type='confirmation'):
        """
        Envoyer un SMS de commande
        """
        try:
            phone_number = order.user.get_full_phone_number()
            if not phone_number:
                return False
            
            if message_type == 'confirmation':
                message = f"Votre commande #{order.id} a été confirmée. Montant: {order.total_amount} FCFA. KefyStore"
            elif message_type == 'shipped':
                message = f"Votre commande #{order.id} a été expédiée. Numéro de suivi: {order.tracking_number}. KefyStore"
            elif message_type == 'delivered':
                message = f"Votre commande #{order.id} a été livrée. Merci pour votre confiance! KefyStore"
            else:
                return False
            
            # Envoyer le SMS
            success = NotificationService._send_sms_via_api(phone_number, message)
            
            if success:
                logger.info(f"SMS {message_type} envoyé pour la commande {order.id}")
                return True
            else:
                logger.error(f"Échec de l'envoi du SMS {message_type} pour la commande {order.id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du SMS: {str(e)}")
            return False