"""
Vues pour le système de popups, captcha et confidentialité
"""
import hashlib
import json
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .models import (
    CaptchaChallenge,
    CaptchaSession,
    CookieConsent,
    Popup,
    PopupInteraction,
    PrivacyPolicy,
    TermsOfService,
    UserConsent,
)


class PopupView(TemplateView):
    """Vue pour afficher les popups"""

    template_name = "popups/popup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        popup_id = self.kwargs.get("popup_id")
        popup = get_object_or_404(Popup, id=popup_id)
        context["popup"] = popup
        return context


@csrf_exempt
@require_http_methods(["POST"])
def track_popup_interaction(request):
    """Tracker les interactions avec les popups"""
    try:
        data = json.loads(request.body)
        popup_id = data.get("popup_id")
        action = data.get("action")

        popup = get_object_or_404(Popup, id=popup_id)

        # Créer l'interaction
        interaction = PopupInteraction.objects.create(
            popup=popup,
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key or "",
            action=action,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            page_url=request.META.get("HTTP_REFERER", ""),
        )

        # Mettre à jour les compteurs
        if action == "shown":
            popup.show_count += 1
        elif action == "converted":
            popup.conversion_count += 1

        popup.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_popups(request):
    """Récupérer les popups à afficher"""
    try:
        # Vérifier les conditions d'affichage
        user = request.user if request.user.is_authenticated else None
        current_page = request.META.get("HTTP_REFERER", "")

        # Récupérer les popups actifs
        popups = Popup.objects.filter(
            is_active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now()
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=timezone.now()),
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now()),
        )

        # Filtrer selon le type d'utilisateur
        if user:
            if not popups.filter(show_to_authenticated=True).exists():
                popups = popups.none()
        else:
            if not popups.filter(show_to_anonymous=True).exists():
                popups = popups.none()

        # Filtrer selon les pages
        if current_page:
            popups = popups.filter(
                Q(pages__isnull=True) | Q(pages__contains=[current_page])
            )

        # Convertir en JSON
        popups_data = []
        for popup in popups:
            popups_data.append(
                {
                    "id": popup.id,
                    "type": popup.popup_type,
                    "title": popup.title,
                    "content": popup.content,
                    "button_text": popup.button_text,
                    "button_url": popup.button_url,
                    "trigger_type": popup.trigger_type,
                    "trigger_delay": popup.trigger_delay,
                    "trigger_scroll": popup.trigger_scroll,
                    "trigger_time": popup.trigger_time,
                    "background_color": popup.background_color,
                    "text_color": popup.text_color,
                    "button_color": popup.button_color,
                    "overlay_opacity": float(popup.overlay_opacity),
                }
            )

        return JsonResponse({"popups": popups_data})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def generate_captcha(request):
    """Générer un nouveau captcha"""
    try:
        # Récupérer un défi aléatoire
        challenge = (
            CaptchaChallenge.objects.filter(is_active=True).order_by("?").first()
        )

        if not challenge:
            return JsonResponse(
                {"status": "error", "message": "Aucun défi captcha disponible"}
            )

        # Créer une session captcha
        session_key = request.session.session_key or request.session.create()
        expires_at = timezone.now() + timedelta(minutes=10)

        captcha_session = CaptchaSession.objects.create(
            session_key=session_key,
            challenge=challenge,
            expires_at=expires_at,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        # Préparer la réponse
        response_data = {
            "session_id": captcha_session.id,
            "challenge_type": challenge.challenge_type,
            "question": challenge.question,
            "options": challenge.options,
            "difficulty": challenge.difficulty,
        }

        return JsonResponse({"status": "success", "data": response_data})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def verify_captcha(request):
    """Vérifier la réponse du captcha"""
    try:
        data = json.loads(request.body)
        session_id = data.get("session_id")
        answer = data.get("answer")

        captcha_session = get_object_or_404(CaptchaSession, id=session_id)

        success, message = captcha_session.solve(answer)

        return JsonResponse(
            {
                "status": "success" if success else "error",
                "message": message,
                "is_solved": captcha_session.is_solved,
            }
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def save_cookie_consent(request):
    """Sauvegarder le consentement aux cookies"""
    try:
        data = json.loads(request.body)

        # Créer ou mettre à jour le consentement
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key or request.session.create()

        consent, created = UserConsent.objects.get_or_create(
            user=user,
            session_key=session_key,
            defaults={
                "necessary_cookies": data.get("necessary", True),
                "analytics_cookies": data.get("analytics", False),
                "marketing_cookies": data.get("marketing", False),
                "preferences_cookies": data.get("preferences", False),
                "social_cookies": data.get("social", False),
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )

        if not created:
            consent.necessary_cookies = data.get("necessary", True)
            consent.analytics_cookies = data.get("analytics", False)
            consent.marketing_cookies = data.get("marketing", False)
            consent.preferences_cookies = data.get("preferences", False)
            consent.social_cookies = data.get("social", False)
            consent.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
@require_http_methods(["GET"])
def get_cookie_consent(request):
    """Récupérer les paramètres de consentement aux cookies"""
    try:
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key or ""

        # Récupérer le consentement existant
        consent = UserConsent.objects.filter(
            Q(user=user) | Q(session_key=session_key)
        ).first()

        if consent:
            return JsonResponse(
                {
                    "status": "success",
                    "consent": {
                        "necessary": consent.necessary_cookies,
                        "analytics": consent.analytics_cookies,
                        "marketing": consent.marketing_cookies,
                        "preferences": consent.preferences_cookies,
                        "social": consent.social_cookies,
                    },
                }
            )
        else:
            return JsonResponse({"status": "success", "consent": None})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


class PrivacyPolicyView(TemplateView):
    """Vue pour afficher la politique de confidentialité"""

    template_name = "popups/privacy_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language = self.request.GET.get("lang", "fr")

        privacy_policy = (
            PrivacyPolicy.objects.filter(language=language, version_type="published")
            .order_by("-effective_date")
            .first()
        )

        context["privacy_policy"] = privacy_policy
        return context


class TermsOfServiceView(TemplateView):
    """Vue pour afficher les conditions d'utilisation"""

    template_name = "popups/terms_of_service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language = self.request.GET.get("lang", "fr")

        terms = (
            TermsOfService.objects.filter(language=language, version_type="published")
            .order_by("-effective_date")
            .first()
        )

        context["terms_of_service"] = terms
        return context


@csrf_exempt
@require_http_methods(["GET"])
def get_cookie_settings(request):
    """Récupérer les paramètres de cookies"""
    try:
        cookies = CookieConsent.objects.filter(is_active=True).order_by(
            "consent_type", "name"
        )

        cookies_data = []
        for cookie in cookies:
            cookies_data.append(
                {
                    "id": cookie.id,
                    "name": cookie.name,
                    "description": cookie.description,
                    "type": cookie.consent_type,
                    "required": cookie.is_required,
                    "cookie_name": cookie.cookie_name,
                    "cookie_domain": cookie.cookie_domain,
                    "cookie_duration": cookie.cookie_duration,
                }
            )

        return JsonResponse({"status": "success", "cookies": cookies_data})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
