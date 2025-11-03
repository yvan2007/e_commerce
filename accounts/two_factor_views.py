"""
Vues pour l'authentification à 2 facteurs
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import User
from .two_factor_service import TwoFactorService


@login_required
def setup_2fa(request):
    """
    Page de configuration de l'authentification à 2 facteurs
    """
    if request.method == "POST":
        method = request.POST.get("method", "totp")

        result = TwoFactorService.setup_2fa(request.user, method)

        if result["success"]:
            if method == "totp":
                messages.success(
                    request, _("Authentification à 2 facteurs configurée avec succès!")
                )
                return render(
                    request,
                    "accounts/setup_2fa_success.html",
                    {
                        "qr_code": result["qr_code"],
                        "backup_codes": result["backup_codes"],
                        "secret": result["secret"],
                    },
                )
            else:
                messages.success(
                    request, _("Authentification à 2 facteurs configurée avec succès!")
                )
                return redirect("accounts:verify_2fa_setup", method=method)
        else:
            messages.error(
                request, result.get("error", _("Erreur lors de la configuration"))
            )

    return render(request, "accounts/setup_2fa.html")


@login_required
def verify_2fa_setup(request, method):
    """
    Vérification de la configuration 2FA
    """
    # Envoyer le code automatiquement si la méthode est email ou SMS
    if request.method == "GET" and method in ["email", "sms"]:
        try:
            result = TwoFactorService.send_verification_code(request.user, method)
            if not result.get("success"):
                messages.warning(
                    request, _("Erreur lors de l'envoi du code. Veuillez réessayer.")
                )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'envoi du code 2FA: {e}")

    if request.method == "POST":
        code = request.POST.get("code")

        if TwoFactorService.verify_2fa(request.user, code, method):
            messages.success(request, _("Configuration 2FA vérifiée avec succès!"))
            return redirect("accounts:account_dashboard")
        else:
            messages.error(request, _("Code de vérification incorrect"))

    return render(
        request,
        "accounts/verify_2fa_setup.html",
        {"method": method, "user": request.user},
    )


@login_required
def disable_2fa(request):
    """
    Désactiver l'authentification à 2 facteurs
    """
    if request.method == "POST":
        if TwoFactorService.disable_2fa(request.user):
            messages.success(request, _("Authentification à 2 facteurs désactivée"))
        else:
            messages.error(request, _("Erreur lors de la désactivation"))

        return redirect("accounts:account_dashboard")

    return render(request, "accounts/disable_2fa.html")


@require_http_methods(["POST"])
@csrf_exempt
def send_2fa_code(request):
    """
    API pour envoyer un code de vérification 2FA
    """
    try:
        user_id = request.POST.get("user_id")
        method = request.POST.get("method", "sms")

        if not user_id:
            return JsonResponse({"success": False, "error": "ID utilisateur requis"})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "Utilisateur non trouvé"})

        result = TwoFactorService.send_verification_code(user, method)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@require_http_methods(["POST"])
@csrf_exempt
def verify_2fa_login(request):
    """
    API pour vérifier le code 2FA lors de la connexion
    """
    try:
        user_id = request.POST.get("user_id")
        code = request.POST.get("code")
        method = request.POST.get("method", "totp")

        if not user_id or not code:
            return JsonResponse({"success": False, "error": "Données manquantes"})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "Utilisateur non trouvé"})

        if TwoFactorService.verify_2fa(user, code, method):
            # Connecter l'utilisateur
            from django.contrib.auth import login as auth_login

            auth_login(
                request, user, backend="django.contrib.auth.backends.ModelBackend"
            )
            return JsonResponse({"success": True, "redirect_url": "/accounts/account/"})
        else:
            return JsonResponse(
                {"success": False, "error": "Code de vérification incorrect"}
            )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def two_factor_required(request):
    """
    Page de vérification 2FA obligatoire
    """
    # Récupérer l'ID utilisateur depuis la session
    user_id = request.session.get("2fa_user_id")
    if not user_id:
        messages.error(request, _("Session expirée. Veuillez vous reconnecter."))
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, _("Utilisateur non trouvé."))
        return redirect("accounts:login")

    # Envoyer le code automatiquement si c'est une nouvelle visite
    if request.method == "GET":
        # Déterminer la méthode 2FA (email par défaut)
        method = "email"  # ou 'sms' selon la configuration

        # Envoyer le code de vérification
        try:
            result = TwoFactorService.send_verification_code(user, method)
            if not result.get("success"):
                messages.warning(
                    request, _("Erreur lors de l'envoi du code. Veuillez réessayer.")
                )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'envoi du code 2FA: {e}")

    if request.method == "POST":
        code = request.POST.get("code")
        method = request.POST.get("method", "email")

        if TwoFactorService.verify_2fa(user, code, method):
            # Connecter l'utilisateur maintenant
            from django.contrib.auth import login

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            # Nettoyer la session
            del request.session["2fa_user_id"]
            request.session["2fa_verified"] = True

            # Messages personnalisés selon le type d'utilisateur
            if user.user_type == "vendeur":
                if hasattr(user, "vendor_profile") and user.vendor_profile.is_approved:
                    messages.success(
                        request,
                        f"Bienvenue dans votre espace vendeur, {user.first_name}!",
                    )
                else:
                    messages.info(
                        request,
                        f"Bienvenue {user.first_name}! Votre compte vendeur est en attente d'approbation.",
                    )
            elif user.user_type == "client":
                messages.success(
                    request, f"Bienvenue {user.first_name}! Découvrez nos produits."
                )
            elif user.is_superuser:
                messages.success(
                    request, f"Bienvenue dans l'administration, {user.first_name}!"
                )

            # Redirection selon le type d'utilisateur
            from django.urls import reverse

            if user.is_superuser or user.user_type == "admin":
                return redirect("dashboard:admin_dashboard")
            elif user.user_type == "vendeur":
                if hasattr(user, "vendor_profile") and user.vendor_profile.is_approved:
                    return redirect("dashboard:vendor_dashboard")
                else:
                    return redirect("products:home_page")
            elif user.user_type == "client":
                return redirect("products:home_page")
            else:
                return redirect("products:home_page")
        else:
            messages.error(request, _("Code de vérification incorrect"))

    return render(request, "accounts/two_factor_required.html", {"user": user})
