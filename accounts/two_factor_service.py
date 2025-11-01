"""
Service d'authentification à 2 facteurs (2FA)
"""
import random
import string
import secrets
import pyotp
import qrcode
import io
import base64
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class TwoFactorService:
    """
    Service de gestion de l'authentification à 2 facteurs
    """
    
    @staticmethod
    def generate_secret():
        """
        Générer un secret pour l'authentification TOTP
        """
        return pyotp.random_base32()
    
    @staticmethod
    def generate_backup_codes(count=10):
        """
        Générer des codes de secours
        """
        codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            codes.append(code)
        return codes
    
    @staticmethod
    def generate_qr_code(user, secret):
        """
        Générer un QR code pour l'autregistrement de l'authentificateur
        """
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="KefyStore"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en base64 pour l'affichage dans le template
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    @staticmethod
    def verify_totp_code(secret, code):
        """
        Vérifier un code TOTP
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification TOTP: {str(e)}")
            return False
    
    @staticmethod
    def send_sms_code(phone_number, code):
        """
        Envoyer un code de vérification par SMS
        """
        try:
            message = f"Votre code de vérification KefyStore: {code}. Ce code expire dans 5 minutes."
            
            # Simulation d'envoi SMS
            # Dans un vrai projet, vous utiliseriez un service SMS comme Twilio
            logger.info(f"SMS envoyé à {phone_number}: {message}")
            
            # Stocker le code dans le cache avec expiration
            cache_key = f"sms_code_{phone_number}"
            cache.set(cache_key, code, timeout=300)  # 5 minutes
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi SMS: {str(e)}")
            return False
    
    @staticmethod
    def send_email_code(email, code):
        """
        Envoyer un code de vérification par email avec HTML
        """
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            
            subject = "Code de vérification - KefyStore"
            
            # Message texte
            message = f"""
            Bonjour,
            
            Votre code de vérification pour KefyStore est: {code}
            
            Ce code expire dans 5 minutes.
            
            Si vous n'avez pas demandé ce code, ignorez cet email.
            
            Cordialement,
            L'équipe KefyStore
            """
            
            # Rendre le template HTML
            try:
                html_content = render_to_string('emails/2fa_code.html', {
                    'code': code,
                    'site_name': 'KefyStore',
                    'site_url': settings.SITE_URL,
                })
            except:
                # Si le template n'existe pas, créer un contenu HTML simple
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #4A90E2; text-align: center;">Code de vérification</h2>
                        <p>Bonjour,</p>
                        <p>Votre code de vérification pour KefyStore est:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="display: inline-block; background-color: #4A90E2; color: white; font-size: 32px; font-weight: bold; padding: 20px 40px; border-radius: 8px; letter-spacing: 5px;">
                                {code}
                            </div>
                        </div>
                        <p style="color: #666; font-size: 14px;">Ce code expire dans 5 minutes.</p>
                        <p style="color: #666; font-size: 14px;">Si vous n'avez pas demandé ce code, ignorez cet email.</p>
                        <p>Cordialement,<br>L'équipe KefyStore</p>
                    </div>
                </body>
                </html>
                """
            
            # Créer l'email avec HTML
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            # Stocker le code dans le cache avec expiration
            cache_key = f"email_code_{email}"
            cache.set(cache_key, code, timeout=300)  # 5 minutes
            
            logger.info(f"Code de vérification envoyé par email à {email}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du code par email: {str(e)}")
            return False
    
    @staticmethod
    def generate_verification_code():
        """
        Générer un code de vérification à 6 chiffres
        """
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def verify_sms_code(phone_number, code):
        """
        Vérifier un code SMS
        """
        cache_key = f"sms_code_{phone_number}"
        stored_code = cache.get(cache_key)
        
        if stored_code and stored_code == code:
            cache.delete(cache_key)
            return True
        return False
    
    @staticmethod
    def verify_email_code(email, code):
        """
        Vérifier un code email
        """
        cache_key = f"email_code_{email}"
        stored_code = cache.get(cache_key)
        
        if stored_code and stored_code == code:
            cache.delete(cache_key)
            return True
        return False
    
    @staticmethod
    def verify_backup_code(user, code):
        """
        Vérifier un code de secours
        """
        if code in user.backup_codes:
            user.backup_codes.remove(code)
            user.save()
            return True
        return False
    
    @staticmethod
    def setup_2fa(user, method='totp'):
        """
        Configurer l'authentification à 2 facteurs pour un utilisateur
        """
        try:
            if method == 'totp':
                secret = TwoFactorService.generate_secret()
                user.two_factor_secret = secret
                user.two_factor_enabled = True
                user.backup_codes = TwoFactorService.generate_backup_codes()
                user.save()
                
                return {
                    'success': True,
                    'secret': secret,
                    'qr_code': TwoFactorService.generate_qr_code(user, secret),
                    'backup_codes': user.backup_codes
                }
            
            elif method == 'sms':
                if not user.phone_number:
                    return {'success': False, 'error': 'Numéro de téléphone requis'}
                
                user.two_factor_enabled = True
                user.save()
                
                return {
                    'success': True,
                    'method': 'sms',
                    'phone_number': user.get_full_phone_number()
                }
            
            elif method == 'email':
                user.two_factor_enabled = True
                user.save()
                
                return {
                    'success': True,
                    'method': 'email',
                    'email': user.email
                }
            
            return {'success': False, 'error': 'Méthode non supportée'}
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration 2FA: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def disable_2fa(user):
        """
        Désactiver l'authentification à 2 facteurs
        """
        try:
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.backup_codes = []
            user.save()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation 2FA: {str(e)}")
            return False
    
    @staticmethod
    def verify_2fa(user, code, method='totp'):
        """
        Vérifier l'authentification à 2 facteurs
        """
        try:
            if not user.two_factor_enabled:
                return True  # 2FA non activé
            
            if method == 'totp' and user.two_factor_secret:
                return TwoFactorService.verify_totp_code(user.two_factor_secret, code)
            
            elif method == 'sms' and user.phone_number:
                return TwoFactorService.verify_sms_code(user.get_full_phone_number(), code)
            
            elif method == 'email':
                return TwoFactorService.verify_email_code(user.email, code)
            
            elif method == 'backup':
                return TwoFactorService.verify_backup_code(user, code)
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification 2FA: {str(e)}")
            return False
    
    @staticmethod
    def send_verification_code(user, method='sms'):
        """
        Envoyer un code de vérification selon la méthode choisie
        """
        try:
            code = TwoFactorService.generate_verification_code()
            
            if method == 'sms' and user.phone_number:
                success = TwoFactorService.send_sms_code(user.get_full_phone_number(), code)
                return {'success': success, 'method': 'sms'}
            
            elif method == 'email':
                success = TwoFactorService.send_email_code(user.email, code)
                return {'success': success, 'method': 'email'}
            
            return {'success': False, 'error': 'Méthode non supportée'}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du code de vérification: {str(e)}")
            return {'success': False, 'error': str(e)}
