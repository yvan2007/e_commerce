from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from orders.models import Order, OrderItem
from products.models import Product

User = get_user_model()

class DeliveryProductReview(models.Model):
    """
    Modèle pour les avis sur les produits après livraison
    """
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='delivery_product_reviews',
        verbose_name=_("Utilisateur")
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='delivery_reviews',
        verbose_name=_("Produit")
    )
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name=_("Commande")
    )
    order_item = models.ForeignKey(
        OrderItem, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name=_("Article de commande")
    )
    
    rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre de l'avis")
    )
    
    comment = models.TextField(
        verbose_name=_("Commentaire")
    )
    
    # Photos optionnelles
    image_1 = models.ImageField(
        upload_to='reviews/images/',
        blank=True,
        null=True,
        verbose_name=_("Photo 1")
    )
    image_2 = models.ImageField(
        upload_to='reviews/images/',
        blank=True,
        null=True,
        verbose_name=_("Photo 2")
    )
    image_3 = models.ImageField(
        upload_to='reviews/images/',
        blank=True,
        null=True,
        verbose_name=_("Photo 3")
    )
    
    # Métadonnées
    is_verified_purchase = models.BooleanField(
        default=True,
        verbose_name=_("Achat vérifié")
    )
    is_helpful = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de 'utile'")
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_("Public")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Avis produit livraison")
        verbose_name_plural = _("Avis produits livraison")
        unique_together = ['user', 'order_item']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"
    
    @property
    def rating_stars(self):
        """Retourne les étoiles pour l'affichage"""
        return '⭐' * self.rating
    
    @property
    def has_images(self):
        """Vérifie si l'avis contient des images"""
        return any([self.image_1, self.image_2, self.image_3])

class DeliveryReview(models.Model):
    """
    Modèle pour les avis sur la livraison
    """
    DELIVERY_RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='delivery_reviews',
        verbose_name=_("Utilisateur")
    )
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name='delivery_review',
        verbose_name=_("Commande")
    )
    
    delivery_rating = models.PositiveIntegerField(
        choices=DELIVERY_RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note livraison")
    )
    
    delivery_comment = models.TextField(
        blank=True,
        verbose_name=_("Commentaire sur la livraison")
    )
    
    # Aspects spécifiques de la livraison
    delivery_speed_rating = models.PositiveIntegerField(
        choices=DELIVERY_RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rapidité de livraison")
    )
    
    packaging_rating = models.PositiveIntegerField(
        choices=DELIVERY_RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Emballage")
    )
    
    delivery_person_rating = models.PositiveIntegerField(
        choices=DELIVERY_RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Livreur")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Avis livraison")
        verbose_name_plural = _("Avis livraisons")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - Livraison {self.order.order_number} ({self.delivery_rating}/5)"
    
    @property
    def average_rating(self):
        """Calcule la note moyenne des aspects de livraison"""
        ratings = [self.delivery_speed_rating, self.packaging_rating, self.delivery_person_rating]
        return sum(ratings) / len(ratings)

class ReviewHelpful(models.Model):
    """
    Modèle pour les votes "utile" sur les avis
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name=_("Utilisateur")
    )
    review = models.ForeignKey(
        DeliveryProductReview, 
        on_delete=models.CASCADE,
        related_name='helpful_votes',
        verbose_name=_("Avis")
    )
    is_helpful = models.BooleanField(
        default=True,
        verbose_name=_("Utile")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Vote utile")
        verbose_name_plural = _("Votes utiles")
        unique_together = ['user', 'review']
    
    def __str__(self):
        return f"{self.user.username} - {'Utile' if self.is_helpful else 'Pas utile'}"

class ReviewResponse(models.Model):
    """
    Modèle pour les réponses des vendeurs aux avis
    """
    review = models.OneToOneField(
        DeliveryProductReview, 
        on_delete=models.CASCADE,
        related_name='response',
        verbose_name=_("Avis")
    )
    vendor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name=_("Vendeur")
    )
    response_text = models.TextField(
        verbose_name=_("Réponse")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Réponse avis")
        verbose_name_plural = _("Réponses avis")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Réponse de {self.vendor.username} à l'avis {self.review.id}"
