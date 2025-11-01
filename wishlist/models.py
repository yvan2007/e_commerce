"""
Modèles pour le système de wishlist
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Wishlist(models.Model):
    """Modèle pour la liste de souhaits des utilisateurs"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField('products.Product', blank=True, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Liste de souhaits"
        verbose_name_plural = "Listes de souhaits"
    
    def __str__(self):
        return f"Wishlist de {self.user.get_display_name()}"
    
    def add_product(self, product):
        """Ajouter un produit à la wishlist"""
        if self.products.count() >= 50:  # Limite de 50 produits
            raise ValidationError("La liste de souhaits ne peut contenir que 50 produits maximum")
        
        if not self.products.filter(id=product.id).exists():
            self.products.add(product)
            return True
        return False
    
    def remove_product(self, product):
        """Retirer un produit de la wishlist"""
        if self.products.filter(id=product.id).exists():
            self.products.remove(product)
            return True
        return False
    
    def is_in_wishlist(self, product):
        """Vérifier si un produit est dans la wishlist"""
        return self.products.filter(id=product.id).exists()
    
    def get_products(self):
        """Récupérer tous les produits de la wishlist"""
        return self.products.all()


class WishlistItem(models.Model):
    """Modèle pour les articles de la wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Article de wishlist"
        verbose_name_plural = "Articles de wishlist"
        unique_together = ['wishlist', 'product']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.product.name} dans la wishlist de {self.wishlist.user.get_display_name()}"
    
    def clean(self):
        """Validation personnalisée"""
        if self.wishlist.items.count() >= 50:
            raise ValidationError("La liste de souhaits ne peut contenir que 50 produits maximum")


class WishlistShare(models.Model):
    """Modèle pour partager une wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_wishlists')
    shared_with_email = models.EmailField()
    message = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Partage de wishlist"
        verbose_name_plural = "Partages de wishlist"
        unique_together = ['wishlist', 'shared_with_email']
    
    def __str__(self):
        return f"Wishlist de {self.wishlist.user.get_display_name()} partagée avec {self.shared_with_email}"
