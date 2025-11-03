"""
Interface d'administration pour le système de popups, captcha et confidentialité
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

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


@admin.register(Popup)
class PopupAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "popup_type",
        "trigger_type",
        "is_active",
        "show_count",
        "conversion_count",
        "conversion_rate",
        "created_at",
    ]
    list_filter = [
        "popup_type",
        "trigger_type",
        "is_active",
        "show_to_authenticated",
        "show_to_anonymous",
        "created_at",
    ]
    search_fields = ["name", "title", "content"]
    readonly_fields = ["show_count", "conversion_count", "created_at", "updated_at"]

    fieldsets = (
        (
            "Informations générales",
            {
                "fields": (
                    "name",
                    "popup_type",
                    "title",
                    "content",
                    "button_text",
                    "button_url",
                )
            },
        ),
        (
            "Configuration d'affichage",
            {
                "fields": (
                    "trigger_type",
                    "trigger_delay",
                    "trigger_scroll",
                    "trigger_time",
                    "trigger_page_views",
                )
            },
        ),
        (
            "Ciblage",
            {
                "fields": (
                    "show_to_authenticated",
                    "show_to_anonymous",
                    "user_types",
                    "pages",
                )
            },
        ),
        (
            "Apparence",
            {
                "fields": (
                    "background_color",
                    "text_color",
                    "button_color",
                    "overlay_opacity",
                )
            },
        ),
        (
            "Statut et dates",
            {
                "fields": (
                    "is_active",
                    "start_date",
                    "end_date",
                    "show_count",
                    "conversion_count",
                )
            },
        ),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def conversion_rate(self, obj):
        """Calculer le taux de conversion"""
        if obj.show_count > 0:
            rate = (obj.conversion_count / obj.show_count) * 100
            return f"{rate:.1f}%"
        return "0%"

    conversion_rate.short_description = "Taux de conversion"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(PopupInteraction)
class PopupInteractionAdmin(admin.ModelAdmin):
    list_display = ["popup", "user", "action", "ip_address", "timestamp"]
    list_filter = ["action", "timestamp", "popup__popup_type"]
    search_fields = ["popup__name", "user__email", "ip_address"]
    readonly_fields = ["timestamp"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("popup", "user")


@admin.register(CaptchaChallenge)
class CaptchaChallengeAdmin(admin.ModelAdmin):
    list_display = [
        "challenge_type",
        "question",
        "difficulty",
        "is_active",
        "created_at",
    ]
    list_filter = ["challenge_type", "difficulty", "is_active", "created_at"]
    search_fields = ["question", "answer"]

    fieldsets = (
        ("Défi", {"fields": ("challenge_type", "question", "answer", "options")}),
        ("Configuration", {"fields": ("difficulty", "is_active")}),
        ("Métadonnées", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(CaptchaSession)
class CaptchaSessionAdmin(admin.ModelAdmin):
    list_display = [
        "session_key",
        "challenge",
        "is_solved",
        "attempts",
        "created_at",
        "expires_at",
    ]
    list_filter = ["is_solved", "created_at", "expires_at"]
    search_fields = ["session_key", "challenge__question"]
    readonly_fields = ["created_at", "solved_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("challenge")


@admin.register(CookieConsent)
class CookieConsentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "consent_type",
        "is_required",
        "is_active",
        "cookie_duration",
    ]
    list_filter = ["consent_type", "is_required", "is_active"]
    search_fields = ["name", "description", "cookie_name"]

    fieldsets = (
        ("Informations", {"fields": ("name", "description", "consent_type")}),
        ("Configuration", {"fields": ("is_required", "is_active")}),
        ("Cookie", {"fields": ("cookie_name", "cookie_domain", "cookie_duration")}),
    )


@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    list_display = ["user", "session_key", "consent_summary", "consent_date"]
    list_filter = [
        "necessary_cookies",
        "analytics_cookies",
        "marketing_cookies",
        "preferences_cookies",
        "social_cookies",
        "consent_date",
    ]
    search_fields = ["user__email", "session_key", "ip_address"]
    readonly_fields = ["consent_date", "updated_at"]

    def consent_summary(self, obj):
        """Afficher un résumé des consentements"""
        consents = []
        if obj.necessary_cookies:
            consents.append("Nécessaires")
        if obj.analytics_cookies:
            consents.append("Analytiques")
        if obj.marketing_cookies:
            consents.append("Marketing")
        if obj.preferences_cookies:
            consents.append("Préférences")
        if obj.social_cookies:
            consents.append("Réseaux sociaux")

        return ", ".join(consents) if consents else "Aucun"

    consent_summary.short_description = "Consentements"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ["title", "version", "language", "version_type", "effective_date"]
    list_filter = ["version_type", "language", "effective_date"]
    search_fields = ["title", "content"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Informations", {"fields": ("title", "version", "version_type", "language")}),
        ("Contenu", {"fields": ("content",)}),
        ("Dates", {"fields": ("effective_date", "created_at", "updated_at")}),
    )


@admin.register(TermsOfService)
class TermsOfServiceAdmin(admin.ModelAdmin):
    list_display = ["title", "version", "language", "version_type", "effective_date"]
    list_filter = ["version_type", "language", "effective_date"]
    search_fields = ["title", "content"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Informations", {"fields": ("title", "version", "version_type", "language")}),
        ("Contenu", {"fields": ("content",)}),
        ("Dates", {"fields": ("effective_date", "created_at", "updated_at")}),
    )


# Configuration de l'admin
admin.site.site_header = "Administration E-commerce"
admin.site.site_title = "E-commerce Admin"
admin.site.index_title = "Gestion des Popups et Confidentialité"
