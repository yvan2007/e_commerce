"""
Modèles pour le système de popups, captcha et confidentialité
"""
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class Popup(models.Model):
    """Modèle pour les popups du site"""

    POPUP_TYPES = [
        ("welcome", "Bienvenue"),
        ("newsletter", "Newsletter"),
        ("promotion", "Promotion"),
        ("cookie_consent", "Consentement cookies"),
        ("exit_intent", "Intention de sortie"),
        ("social_proof", "Preuve sociale"),
        ("custom", "Personnalisé"),
    ]

    TRIGGER_TYPES = [
        ("immediate", "Immédiat"),
        ("delay", "Avec délai"),
        ("scroll", "Au scroll"),
        ("exit_intent", "Intention de sortie"),
        ("time_on_page", "Temps sur page"),
        ("page_views", "Nombre de vues"),
    ]

    name = models.CharField(max_length=200)
    popup_type = models.CharField(max_length=20, choices=POPUP_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    button_text = models.CharField(max_length=50, default="Fermer")
    button_url = models.URLField(blank=True)

    # Configuration d'affichage
    trigger_type = models.CharField(
        max_length=20, choices=TRIGGER_TYPES, default="delay"
    )
    trigger_delay = models.IntegerField(
        default=3, validators=[MinValueValidator(0)]
    )  # secondes
    trigger_scroll = models.IntegerField(
        default=50, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # pourcentage
    trigger_time = models.IntegerField(
        default=30, validators=[MinValueValidator(0)]
    )  # secondes
    trigger_page_views = models.IntegerField(
        default=3, validators=[MinValueValidator(1)]
    )

    # Ciblage
    show_to_authenticated = models.BooleanField(default=True)
    show_to_anonymous = models.BooleanField(default=True)
    user_types = models.JSONField(default=list)  # ['client', 'vendeur', 'admin']
    pages = models.JSONField(default=list)  # Pages où afficher le popup

    # Apparence
    background_color = models.CharField(max_length=7, default="#ffffff")
    text_color = models.CharField(max_length=7, default="#000000")
    button_color = models.CharField(max_length=7, default="#007bff")
    overlay_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)

    # Statut
    is_active = models.BooleanField(default=True)
    show_count = models.IntegerField(default=0)
    conversion_count = models.IntegerField(default=0)

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Popup"
        verbose_name_plural = "Popups"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.popup_type}"

    def is_visible_now(self):
        """Vérifier si le popup doit être affiché maintenant"""
        now = timezone.now()

        if not self.is_active:
            return False

        if self.start_date and now < self.start_date:
            return False

        if self.end_date and now > self.end_date:
            return False

        return True

    def get_conversion_rate(self):
        """Calculer le taux de conversion"""
        if self.show_count > 0:
            return (self.conversion_count / self.show_count) * 100
        return 0


class PopupInteraction(models.Model):
    """Modèle pour les interactions avec les popups"""

    popup = models.ForeignKey(
        Popup, on_delete=models.CASCADE, related_name="interactions"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    # Type d'interaction
    action = models.CharField(
        max_length=20,
        choices=[
            ("shown", "Affiché"),
            ("closed", "Fermé"),
            ("clicked", "Cliqué"),
            ("converted", "Converti"),
        ],
    )

    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    page_url = models.URLField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Interaction popup"
        verbose_name_plural = "Interactions popup"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.popup.name} - {self.action}"


class CaptchaChallenge(models.Model):
    """Modèle pour les défis captcha"""

    CHALLENGE_TYPES = [
        ("math", "Calcul mathématique"),
        ("text", "Texte à recopier"),
        ("image", "Sélection d'image"),
        ("slider", "Slider"),
        ("checkbox", "Checkbox simple"),
    ]

    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES)
    question = models.CharField(max_length=500)
    answer = models.CharField(max_length=100)
    options = models.JSONField(
        default=list, blank=True
    )  # Pour les questions à choix multiples

    # Configuration
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ("easy", "Facile"),
            ("medium", "Moyen"),
            ("hard", "Difficile"),
        ],
        default="medium",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Défi captcha"
        verbose_name_plural = "Défis captcha"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.challenge_type} - {self.question[:50]}"


class CaptchaSession(models.Model):
    """Modèle pour les sessions captcha"""

    session_key = models.CharField(max_length=40, unique=True)
    challenge = models.ForeignKey(CaptchaChallenge, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=100, blank=True)
    is_solved = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "Session captcha"
        verbose_name_plural = "Sessions captcha"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Session {self.session_key} - {'Résolu' if self.is_solved else 'En cours'}"
        )

    def is_expired(self):
        """Vérifier si la session est expirée"""
        return timezone.now() > self.expires_at

    def solve(self, answer):
        """Résoudre le captcha"""
        if self.is_expired():
            return False, "Session expirée"

        if self.attempts >= 3:
            return False, "Trop de tentatives"

        self.attempts += 1
        self.user_answer = answer

        if answer.lower().strip() == self.challenge.answer.lower().strip():
            self.is_solved = True
            self.solved_at = timezone.now()
            self.save()
            return True, "Captcha résolu"
        else:
            self.save()
            return False, "Réponse incorrecte"


class CookieConsent(models.Model):
    """Modèle pour le consentement aux cookies"""

    CONSENT_TYPES = [
        ("necessary", "Nécessaires"),
        ("analytics", "Analytiques"),
        ("marketing", "Marketing"),
        ("preferences", "Préférences"),
        ("social", "Réseaux sociaux"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    consent_type = models.CharField(max_length=20, choices=CONSENT_TYPES)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Configuration
    cookie_name = models.CharField(max_length=100, blank=True)
    cookie_domain = models.CharField(max_length=100, blank=True)
    cookie_duration = models.IntegerField(default=365)  # jours

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consentement cookie"
        verbose_name_plural = "Consentements cookies"
        ordering = ["consent_type", "name"]

    def __str__(self):
        return f"{self.name} - {self.consent_type}"


class UserConsent(models.Model):
    """Modèle pour les consentements utilisateur"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="consents", null=True, blank=True
    )
    session_key = models.CharField(max_length=40, blank=True)

    # Consentements
    necessary_cookies = models.BooleanField(default=True)
    analytics_cookies = models.BooleanField(default=False)
    marketing_cookies = models.BooleanField(default=False)
    preferences_cookies = models.BooleanField(default=False)
    social_cookies = models.BooleanField(default=False)

    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    consent_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consentement utilisateur"
        verbose_name_plural = "Consentements utilisateurs"
        unique_together = ["user", "session_key"]
        ordering = ["-consent_date"]

    def __str__(self):
        identifier = (
            self.user.get_display_name()
            if self.user
            else f"Session {self.session_key[:8]}"
        )
        return f"Consentement - {identifier}"


class PrivacyPolicy(models.Model):
    """Modèle pour les politiques de confidentialité"""

    VERSION_TYPES = [
        ("draft", "Brouillon"),
        ("published", "Publiée"),
        ("archived", "Archivée"),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    version = models.CharField(max_length=20, default="1.0")
    version_type = models.CharField(
        max_length=20, choices=VERSION_TYPES, default="draft"
    )

    # Langues
    language = models.CharField(max_length=5, default="fr")

    # Dates
    effective_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Politique de confidentialité"
        verbose_name_plural = "Politiques de confidentialité"
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.title} v{self.version} - {self.language}"


class TermsOfService(models.Model):
    """Modèle pour les conditions d'utilisation"""

    VERSION_TYPES = [
        ("draft", "Brouillon"),
        ("published", "Publiées"),
        ("archived", "Archivées"),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    version = models.CharField(max_length=20, default="1.0")
    version_type = models.CharField(
        max_length=20, choices=VERSION_TYPES, default="draft"
    )

    # Langues
    language = models.CharField(max_length=5, default="fr")

    # Dates
    effective_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conditions d'utilisation"
        verbose_name_plural = "Conditions d'utilisation"
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.title} v{self.version} - {self.language}"
