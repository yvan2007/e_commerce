"""
URLs pour le système de popups, captcha et confidentialité
"""
from django.urls import path

from . import views

app_name = "popups"

urlpatterns = [
    # Popups
    path("popup/<int:popup_id>/", views.PopupView.as_view(), name="popup"),
    path("api/popups/", views.get_popups, name="get_popups"),
    path(
        "api/popup-interaction/",
        views.track_popup_interaction,
        name="track_popup_interaction",
    ),
    # Captcha
    path("api/captcha/generate/", views.generate_captcha, name="generate_captcha"),
    path("api/captcha/verify/", views.verify_captcha, name="verify_captcha"),
    # Cookies et confidentialité
    path("api/cookie-consent/", views.save_cookie_consent, name="save_cookie_consent"),
    path(
        "api/cookie-consent/get/", views.get_cookie_consent, name="get_cookie_consent"
    ),
    path("api/cookie-settings/", views.get_cookie_settings, name="get_cookie_settings"),
    # Pages légales
    path("privacy-policy/", views.PrivacyPolicyView.as_view(), name="privacy_policy"),
    path(
        "terms-of-service/", views.TermsOfServiceView.as_view(), name="terms_of_service"
    ),
]
