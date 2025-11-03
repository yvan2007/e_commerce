import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView

logger = logging.getLogger(__name__)

from notifications.services import EmailService

from .forms import (
    PasswordChangeForm,
    PasswordResetForm,
    UserLoginForm,
    UserProfileForm,
    UserRegistrationForm,
    VendorProfileForm,
    VendorRegistrationForm,
)
from .models import User, UserProfile, VendorProfile
from .two_factor_views import (
    disable_2fa,
    send_2fa_code,
    setup_2fa,
    two_factor_required,
    verify_2fa_login,
    verify_2fa_setup,
)

User = get_user_model()


class HomeView(TemplateView):
    """
    Vue d'accueil avec redirection selon le type d'utilisateur
    """

    template_name = "accounts/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["user_type"] = self.request.user.user_type
        return context


class UserRegistrationView(TemplateView):
    """
    Vue d'inscription pour les utilisateurs avec redirection intelligente
    """

    template_name = "accounts/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Détecter le type d'inscription demandé
        user_type = self.request.GET.get("type", "client")

        context["form"] = context.get("form", UserRegistrationForm())
        context["vendor_form"] = context.get("vendor_form", VendorRegistrationForm())
        context["selected_type"] = user_type

        return context

    def post(self, request, *args, **kwargs):
        user_type = request.POST.get("user_type", "client")

        if user_type == "vendeur":
            form = VendorRegistrationForm(request.POST)
        else:
            form = UserRegistrationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save()

                # Connecter automatiquement l'utilisateur après inscription
                login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )

                # Envoyer un email de confirmation
                try:
                    self.send_confirmation_email(user)
                except Exception as e:
                    logger.error(
                        f"Erreur lors de l'envoi de l'email de confirmation: {e}"
                    )

                # Envoyer l'email de bienvenue
                try:
                    EmailService.send_welcome_email(user)
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")

                # Messages personnalisés selon le type d'utilisateur
                if user_type == "vendeur":
                    messages.success(
                        request,
                        f"Bienvenue {user.first_name}! Votre compte vendeur a été créé avec succès.",
                    )
                else:
                    messages.success(
                        request,
                        f"Bienvenue {user.first_name}! Votre compte a été créé avec succès.",
                    )

                return redirect("products:home_page")
            except Exception as e:
                logger.error(f"Erreur lors de la création du compte: {e}")
                messages.error(request, f"Une erreur est survenue: {str(e)}")
        else:
            # Log des erreurs du formulaire
            logger.error(f"Erreurs du formulaire: {form.errors}")

        context = self.get_context_data()
        context["form"] = form
        context["vendor_form"] = (
            VendorRegistrationForm() if user_type != "vendeur" else form
        )
        return render(request, self.template_name, context)

    def send_confirmation_email(self, user):
        """Envoie un email de confirmation personnalisé selon le type d'utilisateur"""
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Messages personnalisés selon le type d'utilisateur
        if user.user_type == "vendeur":
            subject = _("Confirmez votre compte vendeur - KefyStore")
            message = f"""
            Bonjour {user.first_name},

            Merci de vous être inscrit en tant que vendeur sur KefyStore.
            Veuillez cliquer sur le lien ci-dessous pour confirmer votre compte:

            {self.request.build_absolute_uri(reverse_lazy('accounts:confirm_email', kwargs={'uidb64': uid, 'token': token}))}

            Une fois votre compte confirmé, un administrateur examinera votre demande d'approbation.

            Cordialement,
            L'équipe KefyStore
            """
        else:
            subject = _("Confirmez votre compte client - KefyStore")
            message = f"""
            Bonjour {user.first_name},

            Merci de vous être inscrit sur KefyStore.
            Veuillez cliquer sur le lien ci-dessous pour confirmer votre compte:

            {self.request.build_absolute_uri(reverse_lazy('accounts:confirm_email', kwargs={'uidb64': uid, 'token': token}))}

            Cordialement,
            L'équipe KefyStore
            """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            # Ne pas bloquer l'inscription si l'email échoue
            logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {e}")


class UserLoginView(LoginView):
    """
    Vue de connexion personnalisée avec redirection selon le type d'utilisateur
    """

    template_name = "accounts/login.html"
    form_class = UserLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Override form_valid pour gérer la connexion avec vérification 2FA"""
        remember_me = form.cleaned_data.get("remember_me", False)

        # Récupérer l'utilisateur AVANT la connexion
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        # Authentifier l'utilisateur
        from django.contrib.auth import authenticate
        from django.contrib.auth import login as auth_login

        user = authenticate(self.request, username=username, password=password)

        if user is None:
            messages.error(self.request, "Nom d'utilisateur ou mot de passe incorrect.")
            return self.form_invalid(form)

        # Vérifier si 2FA est activé
        if user.two_factor_enabled:
            # Ne PAS connecter l'utilisateur, stocker dans la session
            self.request.session["2fa_user_id"] = user.id
            self.request.session["2fa_verified"] = False

            # Rediriger vers la page de vérification 2FA
            messages.info(
                self.request,
                "Un code de vérification a été envoyé à votre adresse email.",
            )
            return redirect("accounts:two_factor_required")

        # Si pas de 2FA, connecter normalement
        auth_login(
            self.request, user, backend="django.contrib.auth.backends.ModelBackend"
        )

        # Si "Se souvenir de moi" n'est pas coché, la session expire à la fermeture du navigateur
        if not remember_me:
            self.request.session.set_expiry(0)

        # Messages personnalisés selon le type d'utilisateur
        if user.user_type == "vendeur":
            if hasattr(user, "vendor_profile") and user.vendor_profile.is_approved:
                messages.success(
                    self.request,
                    f"Bienvenue dans votre espace vendeur, {user.first_name}!",
                )
            else:
                messages.info(
                    self.request,
                    f"Bienvenue {user.first_name}! Votre compte vendeur est en attente d'approbation.",
                )
        elif user.user_type == "client":
            messages.success(
                self.request, f"Bienvenue {user.first_name}! Découvrez nos produits."
            )
        elif user.is_superuser:
            messages.success(
                self.request, f"Bienvenue dans l'administration, {user.first_name}!"
            )

        # Redirection
        return redirect(self.get_success_url())

    def get_success_url(self):
        """
        Redirection intelligente selon le type d'utilisateur
        """
        user = self.request.user

        # Redirection selon le type d'utilisateur
        if user.is_superuser or user.user_type == "admin":
            return reverse("dashboard:admin_dashboard")
        elif user.user_type == "vendeur":
            # Vérifier si le vendeur est approuvé
            if hasattr(user, "vendor_profile") and user.vendor_profile.is_approved:
                return reverse("dashboard:vendor_dashboard")
            else:
                messages.info(
                    self.request,
                    _(
                        "Votre compte vendeur est en attente d'approbation. Vous recevrez un email une fois approuvé."
                    ),
                )
                return reverse("products:home_page")
        elif user.user_type == "client":
            return reverse("products:home_page")
        else:
            return reverse("products:home_page")


class UserLogoutView(LogoutView):
    """
    Vue de déconnexion
    """

    next_page = reverse_lazy("products:home_page")


@login_required
def account_dashboard(request):
    """
    Page dédiée pour les options du compte utilisateur
    """
    user = request.user
    context = {
        "user": user,
        "user_type": user.get_user_type_display(),
    }

    # Ajouter des données spécifiques selon le type d'utilisateur
    if user.user_type == "client":
        try:
            from orders.models import Cart, CartItem, Order

            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart).select_related("product")
            recent_orders = Order.objects.filter(user=user).order_by("-created_at")[:5]

            context.update(
                {
                    "cart_items": cart_items,
                    "recent_orders": recent_orders,
                }
            )
        except Cart.DoesNotExist:
            context["cart_items"] = []
            context["recent_orders"] = []

    elif user.user_type == "vendeur":
        try:
            from orders.models import Order, OrderItem
            from products.models import Product

            products = Product.objects.filter(vendor=user).order_by("-created_at")[:5]
            orders = (
                Order.objects.filter(items__product__vendor=user)
                .distinct()
                .order_by("-created_at")[:5]
            )

            context.update(
                {
                    "products": products,
                    "orders": orders,
                }
            )
        except Exception:
            context["products"] = []
            context["orders"] = []

    return render(request, "accounts/account_dashboard.html", context)


@login_required
def profile_view(request):
    """
    Vue du profil utilisateur
    """
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Votre profil a été mis à jour avec succès."))
            return redirect("accounts:profile")
    else:
        form = UserProfileForm(instance=user)

    context = {
        "form": form,
        "profile": profile,
        "user": user,
    }

    # Ajouter le formulaire vendeur si nécessaire
    if user.user_type == "vendeur":
        try:
            vendor_profile = user.vendor_profile
            vendor_form = VendorProfileForm(instance=vendor_profile)
        except VendorProfile.DoesNotExist:
            vendor_profile = VendorProfile.objects.create(user=user)
            vendor_form = VendorProfileForm(instance=vendor_profile)

        if request.method == "POST" and "vendor_form" in request.POST:
            vendor_form = VendorProfileForm(request.POST, instance=vendor_profile)
            if vendor_form.is_valid():
                vendor_form.save()
                messages.success(request, _("Votre profil vendeur a été mis à jour."))
                return redirect("accounts:profile")

        context["vendor_form"] = vendor_form
        context["vendor_profile"] = vendor_profile

    return render(request, "accounts/profile.html", context)


@login_required
def view_user_profile(request, user_id):
    """
    Vue pour afficher le profil d'un utilisateur spécifique (admin uniquement)
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    target_user = get_object_or_404(User, pk=user_id)

    try:
        profile = target_user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=target_user)

    try:
        vendor_profile = target_user.vendor_profile
    except VendorProfile.DoesNotExist:
        vendor_profile = None

    context = {
        "user": target_user,
        "profile": profile,
        "vendor_profile": vendor_profile,
        "is_admin_view": True,  # Flag pour distinguer dans le template
    }

    return render(request, "accounts/view_user_profile.html", context)


@login_required
def change_password_view(request):
    """
    Vue de changement de mot de passe
    """
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Votre mot de passe a été changé avec succès."))
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})


def password_reset_view(request):
    """
    Vue de réinitialisation de mot de passe
    """
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(email=email)

            # Toujours afficher le message de succès pour des raisons de sécurité
            # (ne pas révéler si l'email existe dans la base de données)
            if users.exists():
                # Si plusieurs utilisateurs avec le même email, prendre le plus récent actif
                if users.count() > 1:
                    user = users.filter(is_active=True).order_by("-date_joined").first()
                    if not user:
                        user = users.order_by("-date_joined").first()
                else:
                    user = users.first()

                if user:
                    # Générer le token de réinitialisation
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))

                    # Envoyer l'email
                    subject = _("Réinitialisation de votre mot de passe")
                    reset_url = request.build_absolute_uri(
                        reverse_lazy(
                            "accounts:password_reset_confirm",
                            kwargs={"uidb64": uid, "token": token},
                        )
                    )

                    # Message texte
                    message = f"""
                    Bonjour {user.first_name},

                    Vous avez demandé la réinitialisation de votre mot de passe.
                    Veuillez cliquer sur le lien ci-dessous pour créer un nouveau mot de passe:

                    {reset_url}

                    Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

                    Cordialement,
                    L'équipe KefyStore
                    """

                    # Rendre le template HTML
                    try:
                        html_content = render_to_string(
                            "emails/password_reset.html",
                            {
                                "user": user,
                                "reset_url": reset_url,
                                "site_name": "KefyStore",
                                "site_url": settings.SITE_URL,
                            },
                        )
                    except:
                        # Si le template n'existe pas, créer un contenu HTML simple
                        html_content = f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
                            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <div style="text-align: center; background: linear-gradient(135deg, #ff6b6b, #ee5a6f); color: white; padding: 30px; border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-size: 28px;">🔐 Réinitialisation de mot de passe</h1>
                                </div>
                                <div style="padding: 30px;">
                                    <p>👋 Bonjour {user.first_name},</p>
                                    <p>Vous avez demandé la réinitialisation de votre mot de passe pour votre compte KefyStore.</p>
                                    <div style="text-align: center; margin: 30px 0;">
                                        <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #ff6b6b, #ee5a6f); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600;">
                                            🔑 Réinitialiser mon mot de passe
                                        </a>
                                    </div>
                                    <p style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 4px; color: #856404;">
                                        ⚠️ <strong>Important :</strong> Si vous n'avez pas demandé cette réinitialisation, ignorez cet email. Votre mot de passe restera inchangé.
                                    </p>
                                    <p>Cordialement,<br>L'équipe KefyStore</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """

                    # Créer l'email avec HTML
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[email],
                    )

                    msg.attach_alternative(html_content, "text/html")
                    try:
                        msg.send()
                    except Exception as e:
                        # Ne pas bloquer la réinitialisation si l'email échoue
                        logger.error(
                            f"Erreur lors de l'envoi de l'email de réinitialisation: {e}"
                        )

            # Toujours afficher le message de succès (même si l'email n'existe pas)
            # pour des raisons de sécurité - ne pas révéler si l'email existe dans la base
            messages.success(
                request,
                _(
                    "Si un compte existe avec cet email, un lien de réinitialisation vous a été envoyé."
                ),
            )
            return redirect("accounts:login")
    else:
        form = PasswordResetForm()

    return render(request, "accounts/password_reset.html", {"form": form})


def password_reset_confirm_view(request, uidb64, token):
    """
    Vue de confirmation de réinitialisation de mot de passe
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            password_confirm = request.POST.get("password_confirm")

            if password and password == password_confirm:
                user.set_password(password)
                user.save()
                messages.success(
                    request, _("Votre mot de passe a été réinitialisé avec succès.")
                )
                return redirect("accounts:login")
            else:
                messages.error(request, _("Les mots de passe ne correspondent pas."))

        return render(request, "accounts/password_reset_confirm.html", {"user": user})
    else:
        messages.error(
            request, _("Le lien de réinitialisation est invalide ou a expiré.")
        )
        return redirect("accounts:password_reset")


def confirm_email_view(request, uidb64, token):
    """
    Vue de confirmation d'email
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, _("Votre compte a été confirmé avec succès!"))
        return redirect("accounts:login")
    else:
        messages.error(request, _("Le lien de confirmation est invalide ou a expiré."))
        return redirect("accounts:register")


@login_required
def delete_account_view(request):
    """
    Vue de suppression de compte
    """
    if request.method == "POST":
        user = request.user
        user.delete()
        messages.success(request, _("Votre compte a été supprimé avec succès."))
        return redirect("products:home_page")

    return render(request, "accounts/delete_account.html")


@require_http_methods(["POST"])
@csrf_exempt
def google_auth_view(request):
    """
    Vue pour gérer l'authentification Google
    """
    try:
        data = request.POST
        email = data.get("email")
        name = data.get("name")

        if not email or not name:
            return JsonResponse({"success": False, "error": "Email et nom requis"})

        # Vérifier si l'utilisateur existe déjà
        users = User.objects.filter(email=email)
        if users.exists():
            # Si plusieurs utilisateurs avec le même email, prendre le plus récent actif
            if users.count() > 1:
                user = users.filter(is_active=True).order_by("-date_joined").first()
                if not user:
                    user = users.order_by("-date_joined").first()
            else:
                user = users.first()

            if user:
                # Connecter l'utilisateur existant
                login(request, user)
                return JsonResponse(
                    {
                        "success": True,
                        "redirect_url": reverse_lazy("products:home_page"),
                        "message": f"Bienvenue {user.first_name}!",
                    }
                )

        # Créer un nouvel utilisateur si aucun n'existe
        if not users.exists():
            # Créer un nouvel utilisateur
            username = email.split("@")[0] + "_google"
            # S'assurer que le nom d'utilisateur est unique
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=name.split()[0] if name.split() else name,
                last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                user_type="client",
                is_verified=True,  # Google vérifie déjà l'email
            )

            # Créer le profil utilisateur
            UserProfile.objects.create(user=user)

            # Connecter l'utilisateur
            login(request, user)

            return JsonResponse(
                {
                    "success": True,
                    "redirect_url": reverse_lazy("products:home_page"),
                    "message": f"Bienvenue {user.first_name}! Votre compte a été créé avec succès.",
                }
            )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@require_http_methods(["POST"])
@csrf_exempt
def check_username_availability(request):
    """
    API pour vérifier la disponibilité du nom d'utilisateur
    """
    username = request.POST.get("username")
    if username:
        exists = User.objects.filter(username=username).exists()
        return JsonResponse({"available": not exists})
    return JsonResponse({"available": False})


@require_http_methods(["POST"])
@csrf_exempt
def check_email_availability(request):
    """
    API pour vérifier la disponibilité de l'email
    """
    email = request.POST.get("email")
    if email:
        exists = User.objects.filter(email=email).exists()
        return JsonResponse({"available": not exists})
    return JsonResponse({"available": False})
