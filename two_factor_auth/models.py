"""
Modèles pour l'authentification à deux facteurs (2FA)
"""
import base64
import io
from datetime import timedelta

import pyotp
import qrcode
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class TwoFactorAuth(models.Model):
    """Modèle pour l'authentification à deux facteurs"""

    METHOD_CHOICES = [
        ("totp", "TOTP (Google Authenticator)"),
        ("sms", "SMS"),
        ("email", "Email"),
        ("backup", "Codes de sauvegarde"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="two_factor_auth",
        verbose_name="Utilisateur",
    )

    # Configuration 2FA
    is_enabled = models.BooleanField(default=False, verbose_name="2FA activé")
    primary_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default="totp",
        verbose_name="Méthode principale",
    )

    # TOTP (Google Authenticator)
    totp_secret = models.CharField(
        max_length=32, blank=True, verbose_name="Secret TOTP"
    )
    totp_verified = models.BooleanField(default=False, verbose_name="TOTP vérifié")

    # SMS
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Le numéro de téléphone doit être au format: '+999999999'.",
            )
        ],
        verbose_name="Numéro de téléphone",
    )
    sms_verified = models.BooleanField(default=False, verbose_name="SMS vérifié")

    # Email
    email_verified = models.BooleanField(default=False, verbose_name="Email vérifié")

    # Codes de sauvegarde
    backup_codes = models.JSONField(
        default=list, blank=True, verbose_name="Codes de sauvegarde"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(
        null=True, blank=True, verbose_name="Dernière utilisation"
    )

    class Meta:
        verbose_name = "Authentification à deux facteurs"
        verbose_name_plural = "Authentifications à deux facteurs"

    def __str__(self):
        return f"2FA - {self.user.get_display_name()}"

    def generate_totp_secret(self):
        """Générer un secret TOTP"""
        if not self.totp_secret:
            self.totp_secret = pyotp.random_base32()
            self.save()
        return self.totp_secret

    def get_totp_qr_code(self):
        """Générer le QR code pour TOTP"""
        if not self.totp_secret:
            self.generate_totp_secret()

        totp = pyotp.TOTP(self.totp_secret)
        provisioning_uri = totp.provisioning_uri(
            name=self.user.email, issuer_name="KefyStore"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def verify_totp_code(self, code):
        """Vérifier un code TOTP"""
        if not self.totp_secret:
            return False

        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(code, valid_window=1)

    def generate_backup_codes(self, count=10):
        """Générer des codes de sauvegarde"""
        import secrets
        import string

        codes = []
        for _ in range(count):
            code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
            )
            codes.append(code)

        self.backup_codes = codes
        self.save()
        return codes

    def verify_backup_code(self, code):
        """Vérifier un code de sauvegarde"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False

    def is_method_verified(self, method):
        """Vérifier si une méthode est vérifiée"""
        if method == "totp":
            return self.totp_verified
        elif method == "sms":
            return self.sms_verified
        elif method == "email":
            return self.email_verified
        return False

    def enable_2fa(self):
        """Activer la 2FA"""
        self.is_enabled = True
        self.save()

    def disable_2fa(self):
        """Désactiver la 2FA"""
        self.is_enabled = False
        self.totp_secret = ""
        self.totp_verified = False
        self.sms_verified = False
        self.email_verified = False
        self.backup_codes = []
        self.save()


class TwoFactorCode(models.Model):
    """Modèle pour les codes de vérification 2FA"""

    CODE_TYPES = [
        ("totp", "TOTP"),
        ("sms", "SMS"),
        ("email", "Email"),
        ("backup", "Code de sauvegarde"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="two_factor_codes",
        verbose_name="Utilisateur",
    )

    code_type = models.CharField(
        max_length=20, choices=CODE_TYPES, verbose_name="Type de code"
    )
    code = models.CharField(max_length=10, verbose_name="Code")

    # Expiration
    expires_at = models.DateTimeField(verbose_name="Expire à")
    is_used = models.BooleanField(default=False, verbose_name="Utilisé")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Utilisé à")

    # Métadonnées
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Code 2FA"
        verbose_name_plural = "Codes 2FA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "code_type", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Code {self.code_type} - {self.user.get_display_name()}"

    def is_expired(self):
        """Vérifier si le code est expiré"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Vérifier si le code est valide"""
        return not self.is_used and not self.is_expired()

    def use_code(self):
        """Utiliser le code"""
        if self.is_valid():
            self.is_used = True
            self.used_at = timezone.now()
            self.save()
            return True
        return False

    @classmethod
    def generate_sms_code(cls, user, phone_number, ip_address, user_agent=""):
        """Générer un code SMS"""
        import random

        code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        # Désactiver les anciens codes SMS
        cls.objects.filter(user=user, code_type="sms", is_used=False).update(
            is_used=True
        )

        return cls.objects.create(
            user=user,
            code_type="sms",
            code=code,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def generate_email_code(cls, user, ip_address, user_agent=""):
        """Générer un code email"""
        import random

        code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=15)

        # Désactiver les anciens codes email
        cls.objects.filter(user=user, code_type="email", is_used=False).update(
            is_used=True
        )

        return cls.objects.create(
            user=user,
            code_type="email",
            code=code,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )


class TwoFactorSession(models.Model):
    """Modèle pour les sessions 2FA"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="two_factor_sessions",
        verbose_name="Utilisateur",
    )

    session_key = models.CharField(
        max_length=100, unique=True, verbose_name="Clé de session"
    )
    is_verified = models.BooleanField(default=False, verbose_name="Vérifié")

    # Métadonnées
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    device_info = models.JSONField(
        default=dict, blank=True, verbose_name="Informations appareil"
    )

    # Expiration
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name="Expire à")
    last_activity = models.DateTimeField(
        auto_now=True, verbose_name="Dernière activité"
    )

    class Meta:
        verbose_name = "Session 2FA"
        verbose_name_plural = "Sessions 2FA"
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["user", "is_verified"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Session 2FA - {self.user.get_display_name()}"

    def is_expired(self):
        """Vérifier si la session est expirée"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Vérifier si la session est valide"""
        return self.is_verified and not self.is_expired()

    @classmethod
    def create_session(cls, user, ip_address, user_agent="", device_info=None):
        """Créer une nouvelle session 2FA"""
        import secrets

        session_key = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)

        return cls.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info or {},
            expires_at=expires_at,
        )


class TwoFactorDevice(models.Model):
    """Modèle pour les appareils de confiance"""

    DEVICE_TYPES = [
        ("mobile", "Mobile"),
        ("tablet", "Tablette"),
        ("desktop", "Ordinateur"),
        ("other", "Autre"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trusted_devices",
        verbose_name="Utilisateur",
    )

    device_name = models.CharField(max_length=100, verbose_name="Nom de l'appareil")
    device_type = models.CharField(
        max_length=20, choices=DEVICE_TYPES, verbose_name="Type d'appareil"
    )
    device_fingerprint = models.CharField(
        max_length=100, unique=True, verbose_name="Empreinte appareil"
    )

    # Métadonnées
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    user_agent = models.TextField(verbose_name="User Agent")
    location = models.CharField(max_length=200, blank=True, verbose_name="Localisation")

    # Statut
    is_trusted = models.BooleanField(default=True, verbose_name="Appareil de confiance")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True, verbose_name="Dernière utilisation")

    class Meta:
        verbose_name = "Appareil de confiance"
        verbose_name_plural = "Appareils de confiance"
        ordering = ["-last_used"]
        unique_together = ["user", "device_fingerprint"]

    def __str__(self):
        return f"{self.device_name} - {self.user.get_display_name()}"

    @classmethod
    def create_device_fingerprint(cls, user_agent, ip_address):
        """Créer une empreinte d'appareil"""
        import hashlib

        fingerprint_data = f"{user_agent}:{ip_address}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
