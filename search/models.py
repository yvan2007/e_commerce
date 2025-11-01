from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SearchHistory(models.Model):
    """Historique des recherches des utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=255)
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Historique de recherche"
        verbose_name_plural = "Historiques de recherche"
    
    def __str__(self):
        return f"{self.query} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class SearchSuggestion(models.Model):
    """Suggestions de recherche populaires"""
    query = models.CharField(max_length=255, unique=True)
    popularity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-popularity', 'query']
        verbose_name = "Suggestion de recherche"
        verbose_name_plural = "Suggestions de recherche"
    
    def __str__(self):
        return f"{self.query} ({self.popularity})"

class ProductFilter(models.Model):
    """Filtres de produits disponibles"""
    name = models.CharField(max_length=100)
    filter_type = models.CharField(max_length=50, choices=[
        ('category', 'Catégorie'),
        ('price_range', 'Gamme de prix'),
        ('brand', 'Marque'),
        ('rating', 'Note'),
        ('availability', 'Disponibilité'),
        ('discount', 'Remise'),
    ])
    filter_value = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Filtre de produit"
        verbose_name_plural = "Filtres de produits"
    
    def __str__(self):
        return f"{self.name} ({self.filter_type})"
