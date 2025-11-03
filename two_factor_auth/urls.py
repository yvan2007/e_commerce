from django.urls import path

from . import views

app_name = "two_factor_auth"

urlpatterns = [
    # Configuration 2FA
    path("setup/", views.setup_2fa, name="setup"),
    path("verify-setup/", views.verify_2fa_setup, name="verify_setup"),
    path("verify/", views.verify_2fa, name="verify"),
    path("disable/", views.disable_2fa, name="disable"),
    # Codes de sauvegarde
    path("backup-codes/", views.backup_codes, name="backup_codes"),
    path(
        "regenerate-backup-codes/",
        views.regenerate_backup_codes,
        name="regenerate_backup_codes",
    ),
    # Gestion des appareils
    path("devices/", views.manage_devices, name="manage_devices"),
    path("devices/add/", views.add_trusted_device, name="add_trusted_device"),
    path(
        "devices/<int:device_id>/remove/",
        views.remove_trusted_device,
        name="remove_trusted_device",
    ),
    # Paramètres
    path("settings/", views.two_factor_settings, name="settings"),
    # Connexion avec 2FA
    path("login/", views.login_2fa, name="login"),
    # API pour l'envoi de codes
    path("api/send-code/", views.send_2fa_code, name="send_code"),
]
