from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class HomePageBanner(models.Model):
    """Bannières de la page d'accueil"""

    title = models.CharField(max_length=200, verbose_name=_("Titre"))
    subtitle = models.CharField(
        max_length=300, blank=True, verbose_name=_("Sous-titre")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    image = models.ImageField(upload_to="banners/", verbose_name=_("Image"))
    button_text = models.CharField(
        max_length=50, blank=True, verbose_name=_("Texte du bouton")
    )
    button_url = models.URLField(blank=True, verbose_name=_("URL du bouton"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = _("Bannière")
        verbose_name_plural = _("Bannières")

    def __str__(self):
        return self.title


class FeaturedCategory(models.Model):
    """Catégories mises en avant sur la page d'accueil"""

    category = models.ForeignKey(
        "products.Category", on_delete=models.CASCADE, verbose_name=_("Catégorie")
    )
    title = models.CharField(max_length=200, verbose_name=_("Titre"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = _("Catégorie mise en avant")
        verbose_name_plural = _("Catégories mises en avant")

    def __str__(self):
        return self.title


class HomePageSection(models.Model):
    """Sections de la page d'accueil"""

    SECTION_TYPES = [
        ("hero", "Section Hero"),
        ("categories", "Catégories"),
        ("featured_products", "Produits vedettes"),
        ("bestsellers", "Meilleures ventes"),
        ("new_arrivals", "Nouveautés"),
        ("testimonials", "Témoignages"),
        ("newsletter", "Newsletter"),
        ("features", "Fonctionnalités"),
    ]

    title = models.CharField(max_length=200, verbose_name=_("Titre"))
    section_type = models.CharField(
        max_length=50, choices=SECTION_TYPES, verbose_name=_("Type de section")
    )
    content = models.TextField(blank=True, verbose_name=_("Contenu"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = _("Section de page d'accueil")
        verbose_name_plural = _("Sections de page d'accueil")

    def __str__(self):
        return f"{self.title} ({self.get_section_type_display()})"


class Testimonial(models.Model):
    """Témoignages clients"""

    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    title = models.CharField(max_length=100, blank=True, verbose_name=_("Titre"))
    content = models.TextField(verbose_name=_("Témoignage"))
    rating = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note"),
    )
    image = models.ImageField(
        upload_to="testimonials/", blank=True, null=True, verbose_name=_("Photo")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = _("Témoignage")
        verbose_name_plural = _("Témoignages")

    def __str__(self):
        return f"{self.name} - {self.rating} étoiles"


class SiteFeature(models.Model):
    """Fonctionnalités du site mises en avant"""

    title = models.CharField(max_length=100, verbose_name=_("Titre"))
    description = models.TextField(verbose_name=_("Description"))
    icon = models.CharField(max_length=50, verbose_name=_("Icône"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = _("Fonctionnalité")
        verbose_name_plural = _("Fonctionnalités")

    def __str__(self):
        return self.title
