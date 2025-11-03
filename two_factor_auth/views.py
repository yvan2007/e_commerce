import base64
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO

import pyotp
import qrcode
import qrcode.image.svg
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.models import User

from .models import TwoFactorAuth, TwoFactorCode, TwoFactorDevice, TwoFactorSession

logger = logging.getLogger(__name__)


@login_required
def setup_2fa(request):
    """Configurer l'authentification à deux facteurs"""

    # Vérifier si l'utilisateur a déjà configuré 2FA
    if hasattr(request.user, "twofactorauth") and request.user.twofactorauth.is_enabled:
        messages.info(
            request, "L'authentification à deux facteurs est déjà configurée."
        )
        return redirect("two_factor_auth:verify_2fa")

    if request.method == "POST":
        # Générer une clé secrète
        secret_key = pyotp.random_base32()

        # Créer ou mettre à jour l'enregistrement 2FA
        two_factor_auth, created = TwoFactorAuth.objects.get_or_create(
            user=request.user,
            defaults={
                "secret_key": secret_key,
                "is_enabled": False,
                "backup_codes": generate_backup_codes(),
            },
        )

        if not created:
            two_factor_auth.secret_key = secret_key
            two_factor_auth.backup_codes = generate_backup_codes()
            two_factor_auth.save()

        # Générer le QR code
        totp = pyotp.TOTP(secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=request.user.email, issuer_name=settings.SITE_NAME or "E-commerce Site"
        )

        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir en base64 pour l'affichage
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        context = {
            "secret_key": secret_key,
            "qr_code": img_str,
            "provisioning_uri": provisioning_uri,
            "backup_codes": two_factor_auth.backup_codes,
        }

        return render(request, "two_factor_auth/setup_2fa.html", context)

    return render(request, "two_factor_auth/setup_2fa.html")


@login_required
def verify_2fa_setup(request):
    """Vérifier la configuration 2FA avec un code"""

    if request.method == "POST":
        code = request.POST.get("code")

        if not code:
            messages.error(request, "Veuillez entrer un code de vérification.")
            return redirect("two_factor_auth:setup_2fa")

        try:
            two_factor_auth = TwoFactorAuth.objects.get(user=request.user)
            totp = pyotp.TOTP(two_factor_auth.secret_key)

            if totp.verify(code, valid_window=1):
                # Activer 2FA
                two_factor_auth.is_enabled = True
                two_factor_auth.save()

                # Créer une session 2FA
                TwoFactorSession.objects.create(
                    user=request.user,
                    session_key=request.session.session_key,
                    expires_at=timezone.now() + timedelta(hours=24),
                )

                messages.success(
                    request, "Authentification à deux facteurs activée avec succès !"
                )
                return redirect("two_factor_auth:backup_codes")
            else:
                messages.error(request, "Code de vérification invalide.")
                return redirect("two_factor_auth:setup_2fa")

        except TwoFactorAuth.DoesNotExist:
            messages.error(request, "Configuration 2FA introuvable.")
            return redirect("two_factor_auth:setup_2fa")
        except Exception as e:
            logger.error(f"Erreur vérification 2FA: {e}")
            messages.error(request, "Une erreur est survenue lors de la vérification.")
            return redirect("two_factor_auth:setup_2fa")

    return redirect("two_factor_auth:setup_2fa")


@login_required
def backup_codes(request):
    """Afficher les codes de sauvegarde"""
    try:
        two_factor_auth = TwoFactorAuth.objects.get(user=request.user, is_enabled=True)

        context = {
            "backup_codes": two_factor_auth.backup_codes,
        }

        return render(request, "two_factor_auth/backup_codes.html", context)
    except TwoFactorAuth.DoesNotExist:
        messages.error(request, "Configuration 2FA introuvable.")
        return redirect("two_factor_auth:setup_2fa")


@login_required
def regenerate_backup_codes(request):
    """Régénérer les codes de sauvegarde"""
    try:
        two_factor_auth = TwoFactorAuth.objects.get(user=request.user, is_enabled=True)
        two_factor_auth.backup_codes = generate_backup_codes()
        two_factor_auth.save()

        messages.success(request, "Codes de sauvegarde régénérés avec succès.")
        return redirect("two_factor_auth:backup_codes")
    except TwoFactorAuth.DoesNotExist:
        messages.error(request, "Configuration 2FA introuvable.")
        return redirect("two_factor_auth:setup_2fa")


@login_required
def verify_2fa(request):
    """Vérifier le code 2FA pour la connexion"""

    # Vérifier si l'utilisateur a 2FA activé
    if (
        not hasattr(request.user, "twofactorauth")
        or not request.user.twofactorauth.is_enabled
    ):
        messages.info(request, "L'authentification à deux facteurs n'est pas activée.")
        return redirect("accounts:profile")

    # Vérifier si l'utilisateur a déjà une session 2FA valide
    if TwoFactorSession.objects.filter(
        user=request.user,
        session_key=request.session.session_key,
        expires_at__gt=timezone.now(),
    ).exists():
        messages.info(request, "Vous êtes déjà authentifié avec 2FA.")
        return redirect("accounts:profile")

    if request.method == "POST":
        code = request.POST.get("code")
        use_backup_code = request.POST.get("use_backup_code", False)

        if not code:
            messages.error(request, "Veuillez entrer un code de vérification.")
            return render(request, "two_factor_auth/verify_2fa.html")

        try:
            two_factor_auth = TwoFactorAuth.objects.get(
                user=request.user, is_enabled=True
            )

            if use_backup_code:
                # Vérifier le code de sauvegarde
                if code in two_factor_auth.backup_codes:
                    # Supprimer le code de sauvegarde utilisé
                    backup_codes = two_factor_auth.backup_codes
                    backup_codes.remove(code)
                    two_factor_auth.backup_codes = backup_codes
                    two_factor_auth.save()

                    # Créer une session 2FA
                    TwoFactorSession.objects.create(
                        user=request.user,
                        session_key=request.session.session_key,
                        expires_at=timezone.now() + timedelta(hours=24),
                    )

                    messages.success(
                        request, "Authentification réussie avec le code de sauvegarde."
                    )
                    return redirect("accounts:profile")
                else:
                    messages.error(request, "Code de sauvegarde invalide.")
                    return render(request, "two_factor_auth/verify_2fa.html")
            else:
                # Vérifier le code TOTP
                totp = pyotp.TOTP(two_factor_auth.secret_key)

                if totp.verify(code, valid_window=1):
                    # Créer une session 2FA
                    TwoFactorSession.objects.create(
                        user=request.user,
                        session_key=request.session.session_key,
                        expires_at=timezone.now() + timedelta(hours=24),
                    )

                    messages.success(
                        request, "Authentification à deux facteurs réussie !"
                    )
                    return redirect("accounts:profile")
                else:
                    messages.error(request, "Code de vérification invalide.")
                    return render(request, "two_factor_auth/verify_2fa.html")

        except TwoFactorAuth.DoesNotExist:
            messages.error(request, "Configuration 2FA introuvable.")
            return redirect("two_factor_auth:setup_2fa")
        except Exception as e:
            logger.error(f"Erreur vérification 2FA: {e}")
            messages.error(request, "Une erreur est survenue lors de la vérification.")
            return render(request, "two_factor_auth/verify_2fa.html")

    return render(request, "two_factor_auth/verify_2fa.html")


@login_required
def disable_2fa(request):
    """Désactiver l'authentification à deux facteurs"""

    if request.method == "POST":
        password = request.POST.get("password")

        if not password:
            messages.error(request, "Veuillez entrer votre mot de passe.")
            return render(request, "two_factor_auth/disable_2fa.html")

        # Vérifier le mot de passe
        if not request.user.check_password(password):
            messages.error(request, "Mot de passe incorrect.")
            return render(request, "two_factor_auth/disable_2fa.html")

        try:
            two_factor_auth = TwoFactorAuth.objects.get(user=request.user)
            two_factor_auth.is_enabled = False
            two_factor_auth.save()

            # Supprimer les sessions 2FA
            TwoFactorSession.objects.filter(user=request.user).delete()

            messages.success(
                request, "Authentification à deux facteurs désactivée avec succès."
            )
            return redirect("accounts:profile")

        except TwoFactorAuth.DoesNotExist:
            messages.error(request, "Configuration 2FA introuvable.")
            return redirect("accounts:profile")
        except Exception as e:
            logger.error(f"Erreur désactivation 2FA: {e}")
            messages.error(request, "Une erreur est survenue lors de la désactivation.")
            return render(request, "two_factor_auth/disable_2fa.html")

    return render(request, "two_factor_auth/disable_2fa.html")


@login_required
def manage_devices(request):
    """Gérer les appareils de confiance"""

    devices = TwoFactorDevice.objects.filter(user=request.user, is_active=True)

    context = {
        "devices": devices,
    }

    return render(request, "two_factor_auth/manage_devices.html", context)


@login_required
def add_trusted_device(request):
    """Ajouter un appareil de confiance"""

    if request.method == "POST":
        device_name = request.POST.get("device_name")
        device_type = request.POST.get("device_type", "browser")

        if not device_name:
            messages.error(request, "Veuillez entrer un nom pour l'appareil.")
            return redirect("two_factor_auth:manage_devices")

        # Récupérer les informations de l'appareil
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        ip_address = get_client_ip(request)

        # Créer l'appareil de confiance
        device = TwoFactorDevice.objects.create(
            user=request.user,
            name=device_name,
            device_type=device_type,
            user_agent=user_agent,
            ip_address=ip_address,
            is_active=True,
        )

        messages.success(request, f"Appareil '{device_name}' ajouté avec succès.")
        return redirect("two_factor_auth:manage_devices")

    return redirect("two_factor_auth:manage_devices")


@login_required
def remove_trusted_device(request, device_id):
    """Supprimer un appareil de confiance"""

    try:
        device = TwoFactorDevice.objects.get(
            id=device_id, user=request.user, is_active=True
        )
        device.is_active = False
        device.save()

        messages.success(request, f"Appareil '{device.name}' supprimé avec succès.")
    except TwoFactorDevice.DoesNotExist:
        messages.error(request, "Appareil introuvable.")
    except Exception as e:
        logger.error(f"Erreur suppression appareil: {e}")
        messages.error(request, "Une erreur est survenue lors de la suppression.")

    return redirect("two_factor_auth:manage_devices")


@login_required
def two_factor_settings(request):
    """Paramètres 2FA"""

    try:
        two_factor_auth = TwoFactorAuth.objects.get(user=request.user)
        devices = TwoFactorDevice.objects.filter(user=request.user, is_active=True)
        recent_sessions = TwoFactorSession.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:10]

        context = {
            "two_factor_auth": two_factor_auth,
            "devices": devices,
            "recent_sessions": recent_sessions,
        }

        return render(request, "two_factor_auth/settings.html", context)
    except TwoFactorAuth.DoesNotExist:
        messages.info(
            request, "L'authentification à deux facteurs n'est pas configurée."
        )
        return redirect("two_factor_auth:setup_2fa")


@csrf_exempt
@require_http_methods(["POST"])
def send_2fa_code(request):
    """Envoyer un code 2FA par SMS ou email"""

    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
        method = data.get("method", "email")  # 'email' ou 'sms'

        user = User.objects.get(id=user_id)

        # Générer un code temporaire
        code = generate_temporary_code()

        # Enregistrer le code
        TwoFactorCode.objects.create(
            user=user,
            code=code,
            method=method,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        # Envoyer le code (implémentation selon la méthode)
        if method == "email":
            send_2fa_email(user, code)
        elif method == "sms":
            send_2fa_sms(user, code)

        return JsonResponse({"status": "success", "message": "Code envoyé avec succès"})

    except User.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Utilisateur introuvable"}, status=400
        )
    except Exception as e:
        logger.error(f"Erreur envoi code 2FA: {e}")
        return JsonResponse(
            {"status": "error", "message": "Erreur lors de l'envoi"}, status=500
        )


def generate_backup_codes():
    """Générer des codes de sauvegarde"""
    import secrets
    import string

    codes = []
    for _ in range(10):
        code = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )
        codes.append(code)

    return codes


def generate_temporary_code():
    """Générer un code temporaire"""
    import secrets
    import string

    return "".join(secrets.choice(string.digits) for _ in range(6))


def get_client_ip(request):
    """Récupérer l'adresse IP du client"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def send_2fa_email(user, code):
    """Envoyer un code 2FA par email"""
    # Implémentation de l'envoi d'email
    # Utiliser Django's email system
    from django.conf import settings
    from django.core.mail import send_mail

    subject = "Code de vérification 2FA"
    message = (
        f"Votre code de vérification est : {code}\n\nCe code expire dans 10 minutes."
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)


def send_2fa_sms(user, code):
    """Envoyer un code 2FA par SMS"""
    # Implémentation de l'envoi SMS
    # Utiliser un service SMS comme Twilio, AWS SNS, etc.
    pass


class TwoFactorLoginView(LoginView):
    """Vue de connexion avec support 2FA"""

    template_name = "two_factor_auth/login_2fa.html"

    def form_valid(self, form):
        """Rediriger vers la vérification 2FA après connexion"""
        user = form.get_user()

        # Vérifier si l'utilisateur a 2FA activé
        if hasattr(user, "twofactorauth") and user.twofactorauth.is_enabled:
            # Stocker l'utilisateur dans la session temporairement
            self.request.session["temp_user_id"] = user.id
            return redirect("two_factor_auth:verify_2fa")
        else:
            # Connexion normale
            login(self.request, user)
            return redirect("accounts:profile")


@login_required
def login_2fa(request):
    """Page de connexion avec 2FA"""

    # Vérifier si l'utilisateur est déjà connecté
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    # Vérifier s'il y a un utilisateur temporaire
    temp_user_id = request.session.get("temp_user_id")
    if not temp_user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=temp_user_id)
    except User.DoesNotExist:
        return redirect("accounts:login")

    if request.method == "POST":
        code = request.POST.get("code")

        if not code:
            messages.error(request, "Veuillez entrer un code de vérification.")
            return render(request, "two_factor_auth/login_2fa.html")

        try:
            two_factor_auth = TwoFactorAuth.objects.get(user=user, is_enabled=True)
            totp = pyotp.TOTP(two_factor_auth.secret_key)

            if totp.verify(code, valid_window=1):
                # Connexion réussie
                login(request, user)

                # Créer une session 2FA
                TwoFactorSession.objects.create(
                    user=user,
                    session_key=request.session.session_key,
                    expires_at=timezone.now() + timedelta(hours=24),
                )

                # Nettoyer la session temporaire
                del request.session["temp_user_id"]

                messages.success(request, "Connexion réussie !")
                return redirect("accounts:profile")
            else:
                messages.error(request, "Code de vérification invalide.")
                return render(request, "two_factor_auth/login_2fa.html")

        except TwoFactorAuth.DoesNotExist:
            messages.error(request, "Configuration 2FA introuvable.")
            return redirect("accounts:login")
        except Exception as e:
            logger.error(f"Erreur connexion 2FA: {e}")
            messages.error(request, "Une erreur est survenue lors de la connexion.")
            return render(request, "two_factor_auth/login_2fa.html")

    return render(request, "two_factor_auth/login_2fa.html")
