"""
Modèles pour le système multi-langues
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Language(models.Model):
    """Modèle pour les langues supportées"""

    code = models.CharField(max_length=5, unique=True)  # fr, en, ar
    name = models.CharField(max_length=100)  # Français, English, العربية
    native_name = models.CharField(max_length=100)  # Français, English, العربية
    flag = models.CharField(max_length=10, blank=True)  # 🇫🇷, 🇺🇸, 🇸🇦
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    is_rtl = models.BooleanField(default=False)  # Right-to-left

    # Configuration
    date_format = models.CharField(max_length=20, default="%d/%m/%Y")
    time_format = models.CharField(max_length=20, default="%H:%M")
    currency_symbol = models.CharField(max_length=5, default="FCFA")
    currency_position = models.CharField(
        max_length=10,
        choices=[
            ("before", "Avant"),
            ("after", "Après"),
        ],
        default="after",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Langue"
        verbose_name_plural = "Langues"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        # S'assurer qu'une seule langue est par défaut
        if self.is_default:
            Language.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class ProductTranslation(models.Model):
    """Modèle pour les traductions de produits"""

    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="translations"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="product_translations"
    )

    # Champs traduits
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Spécifications traduites
    specifications = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Traduction de produit"
        verbose_name_plural = "Traductions de produits"
        unique_together = ["product", "language"]
        ordering = ["language__name"]

    def __str__(self):
        return f"{self.product.name} - {self.language.name}"


class CategoryTranslation(models.Model):
    """Modèle pour les traductions de catégories"""

    category = models.ForeignKey(
        "products.Category", on_delete=models.CASCADE, related_name="translations"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="category_translations"
    )

    # Champs traduits
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Traduction de catégorie"
        verbose_name_plural = "Traductions de catégories"
        unique_together = ["category", "language"]
        ordering = ["language__name"]

    def __str__(self):
        return f"{self.category.name} - {self.language.name}"


class TagTranslation(models.Model):
    """Modèle pour les traductions de tags"""

    tag = models.ForeignKey(
        "products.Tag", on_delete=models.CASCADE, related_name="translations"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="tag_translations"
    )

    # Champs traduits
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Traduction de tag"
        verbose_name_plural = "Traductions de tags"
        unique_together = ["tag", "language"]
        ordering = ["language__name"]

    def __str__(self):
        return f"{self.tag.name} - {self.language.name}"


class PageTranslation(models.Model):
    """Modèle pour les traductions de pages statiques"""

    PAGE_TYPES = [
        ("about", "À propos"),
        ("contact", "Contact"),
        ("privacy", "Politique de confidentialité"),
        ("terms", "Conditions d'utilisation"),
        ("shipping", "Livraison"),
        ("returns", "Retours"),
        ("faq", "FAQ"),
    ]

    page_type = models.CharField(max_length=20, choices=PAGE_TYPES)
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="page_translations"
    )

    # Contenu traduit
    title = models.CharField(max_length=200)
    content = models.TextField()
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Statut
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Traduction de page"
        verbose_name_plural = "Traductions de pages"
        unique_together = ["page_type", "language"]
        ordering = ["language__name"]

    def __str__(self):
        return f"{self.get_page_type_display()} - {self.language.name}"


class UserLanguagePreference(models.Model):
    """Modèle pour les préférences de langue des utilisateurs"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="language_preference"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="user_preferences"
    )

    # Préférences d'affichage
    show_currency_in_local = models.BooleanField(default=True)
    show_dates_in_local = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Préférence de langue"
        verbose_name_plural = "Préférences de langue"

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.language.name}"


class TranslationKey(models.Model):
    """Modèle pour les clés de traduction"""

    key = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Clé de traduction"
        verbose_name_plural = "Clés de traduction"
        ordering = ["key"]

    def __str__(self):
        return self.key


class TranslationValue(models.Model):
    """Modèle pour les valeurs de traduction"""

    key = models.ForeignKey(
        TranslationKey, on_delete=models.CASCADE, related_name="values"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="translation_values"
    )
    value = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Valeur de traduction"
        verbose_name_plural = "Valeurs de traduction"
        unique_together = ["key", "language"]
        ordering = ["language__name"]

    def __str__(self):
        return f"{self.key.key} - {self.language.name}"
