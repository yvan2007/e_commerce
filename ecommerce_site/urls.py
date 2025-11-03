from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.i18n import set_language

# URLs qui ne doivent PAS avoir de préfixe de langue
urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/setlang/", set_language, name="set_language"),
    path("ckeditor5/", include("django_ckeditor_5.urls")),  # CKEditor 5 URLs
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/images/favicon.ico", permanent=False),
    ),
]

# URLs avec préfixe de langue (fr/, en/)
urlpatterns += i18n_patterns(
    # Applications avec URLs spécifiques (doivent être AVANT les URLs génériques)
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),  # Allauth for Google OAuth
    path("orders/", include("orders.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("api/", include("api.urls")),
    path("popups/", include("popups.urls")),
    path("search/", include("search.urls")),
    path("home/", include("home.urls")),
    path("pages/", include("pages.urls")),
    path("wishlist/", include("wishlist.urls")),
    # Nouvelles applications avancées
    path("inventory/", include("inventory.urls")),
    path("delivery/", include("delivery_system.urls")),
    path("reviews/", include("reviews.urls")),
    path("payment/", include("payment_system.urls")),
    path("analytics/", include("analytics.urls")),
    path("2fa/", include("two_factor_auth.urls")),
    path("notifications/", include("notifications.urls")),
    # Applications avec URLs génériques (doivent être APRÈS les URLs spécifiques)
    path("", include("products.urls")),
    prefix_default_language=False,  # Pas de préfixe pour la langue par défaut (fr)
)

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug Toolbar URLs
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
