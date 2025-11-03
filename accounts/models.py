from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec distinction vendeur/client
    """

    USER_TYPE_CHOICES = [
        ("client", "Client"),
        ("vendeur", "Vendeur"),
        ("admin", "Administrateur"),
    ]

    COUNTRY_CHOICES = [
        ("+225", "Côte d'Ivoire"),
        ("+33", "France"),
        ("+1", "États-Unis"),
        ("+44", "Royaume-Uni"),
        ("+49", "Allemagne"),
        ("+237", "Cameroun"),
        ("+221", "Sénégal"),
        ("+226", "Burkina Faso"),
        ("+223", "Mali"),
        ("+224", "Guinée"),
    ]

    # Champs personnalisés
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default="client",
        verbose_name=_("Type d'utilisateur"),
    )

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés.",
    )

    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        verbose_name=_("Numéro de téléphone"),
    )

    country_code = models.CharField(
        max_length=5,
        choices=COUNTRY_CHOICES,
        default="+225",
        verbose_name=_("Code pays"),
    )

    address = models.TextField(blank=True, null=True, verbose_name=_("Adresse"))

    city = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Ville")
    )

    postal_code = models.CharField(
        max_length=20, blank=True, null=True, verbose_name=_("Code postal")
    )

    profile_picture = models.ImageField(
        upload_to="profiles/", blank=True, null=True, verbose_name=_("Photo de profil")
    )

    date_of_birth = models.DateField(
        blank=True, null=True, verbose_name=_("Date de naissance")
    )

    is_verified = models.BooleanField(default=False, verbose_name=_("Compte vérifié"))

    # Champs pour l'authentification à 2 facteurs
    two_factor_enabled = models.BooleanField(
        default=False, verbose_name=_("2FA activé")
    )

    two_factor_secret = models.CharField(
        max_length=32, blank=True, null=True, verbose_name=_("Secret 2FA")
    )

    backup_codes = models.JSONField(
        default=list, blank=True, verbose_name=_("Codes de secours")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_phone_number(self):
        """
        Retourne le numéro de téléphone complet avec le code pays
        """
        if self.phone_number:
            return f"{self.country_code}{self.phone_number}"
        return None

    def get_user_type_display(self):
        """
        Retourne l'affichage du type d'utilisateur
        """
        return dict(self.USER_TYPE_CHOICES).get(self.user_type, self.user_type)

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

    def get_display_name(self):
        """Retourne le nom d'affichage de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def get_user_type_display(self):
        """Retourne l'affichage du type d'utilisateur"""
        type_display = dict(self.USER_TYPE_CHOICES)
        return type_display.get(self.user_type, "Client")

    def is_vendor(self):
        """Vérifie si l'utilisateur est un vendeur"""
        return self.user_type == "vendeur"

    def is_client(self):
        """Vérifie si l'utilisateur est un client"""
        return self.user_type == "client"

    def is_admin_user(self):
        """Vérifie si l'utilisateur est un administrateur"""
        return self.is_superuser or self.user_type == "admin"

    def get_full_phone_number(self):
        """Retourne le numéro de téléphone complet avec le code pays"""
        if self.phone_number:
            return f"{self.country_code}{self.phone_number}"
        return None

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class UserProfile(models.Model):
    """
    Profil étendu pour les utilisateurs
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("Utilisateur"),
    )

    bio = models.TextField(blank=True, null=True, verbose_name=_("Biographie"))

    website = models.URLField(blank=True, null=True, verbose_name=_("Site web"))

    social_facebook = models.URLField(blank=True, null=True, verbose_name=_("Facebook"))

    social_twitter = models.URLField(blank=True, null=True, verbose_name=_("Twitter"))

    social_instagram = models.URLField(
        blank=True, null=True, verbose_name=_("Instagram")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Profil utilisateur")
        verbose_name_plural = _("Profils utilisateurs")

    def __str__(self):
        return f"Profil de {self.user.username}"


class VendorProfile(models.Model):
    """
    Profil spécifique pour les vendeurs
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
        verbose_name=_("Vendeur"),
    )

    business_name = models.CharField(
        max_length=200, verbose_name=_("Nom de l'entreprise")
    )

    business_description = models.TextField(
        verbose_name=_("Description de l'entreprise")
    )

    business_license = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Numéro de licence")
    )

    tax_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Numéro fiscal")
    )

    bank_name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name=_("Nom de la banque")
    )

    bank_account = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Numéro de compte")
    )

    is_approved = models.BooleanField(default=False, verbose_name=_("Vendeur approuvé"))

    approval_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Date d'approbation")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Profil vendeur")
        verbose_name_plural = _("Profils vendeurs")

    def __str__(self):
        return f"Profil vendeur de {self.business_name}"
