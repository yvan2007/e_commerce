"""
Modèles pour le système de fidélité et récompenses
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class LoyaltyPoints(models.Model):
    """Modèle pour les points de fidélité des utilisateurs"""
    LEVEL_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Argent'),
        ('gold', 'Or'),
        ('platinum', 'Platine'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_points')
    points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='bronze')
    total_earned = models.IntegerField(default=0)
    total_spent = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Points de fidélité"
        verbose_name_plural = "Points de fidélité"
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.points} points ({self.level})"
    
    def add_points(self, amount, reason=""):
        """Ajouter des points avec une raison"""
        self.points += amount
        self.total_earned += amount
        self.update_level()
        self.save()
        
        # Créer un historique
        LoyaltyPointsHistory.objects.create(
            user=self.user,
            points=amount,
            reason=reason,
            balance_after=self.points
        )
    
    def spend_points(self, amount, reason=""):
        """Dépenser des points"""
        if self.points >= amount:
            self.points -= amount
            self.total_spent += amount
            self.save()
            
            # Créer un historique
            LoyaltyPointsHistory.objects.create(
                user=self.user,
                points=-amount,
                reason=reason,
                balance_after=self.points
            )
            return True
        return False
    
    def update_level(self):
        """Mettre à jour le niveau selon les points"""
        if self.points >= 5000:
            self.level = 'platinum'
        elif self.points >= 2000:
            self.level = 'gold'
        elif self.points >= 500:
            self.level = 'silver'
        else:
            self.level = 'bronze'
    
    def get_level_benefits(self):
        """Retourner les avantages du niveau actuel"""
        benefits = {
            'bronze': {
                'discount_rate': 0,
                'free_shipping_threshold': 50000,
                'priority_support': False,
                'exclusive_products': False,
            },
            'silver': {
                'discount_rate': 5,
                'free_shipping_threshold': 30000,
                'priority_support': True,
                'exclusive_products': False,
            },
            'gold': {
                'discount_rate': 10,
                'free_shipping_threshold': 20000,
                'priority_support': True,
                'exclusive_products': True,
            },
            'platinum': {
                'discount_rate': 15,
                'free_shipping_threshold': 0,
                'priority_support': True,
                'exclusive_products': True,
            }
        }
        return benefits.get(self.level, benefits['bronze'])


class LoyaltyPointsHistory(models.Model):
    """Historique des points de fidélité"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_history')
    points = models.IntegerField()  # Positif pour gain, négatif pour dépense
    reason = models.CharField(max_length=200)
    balance_after = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique des points"
        verbose_name_plural = "Historiques des points"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.points} points - {self.reason}"


class LoyaltyReward(models.Model):
    """Modèle pour les récompenses de fidélité"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    points_cost = models.IntegerField(validators=[MinValueValidator(1)])
    discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe'),
        ('free_shipping', 'Livraison gratuite'),
        ('product', 'Produit gratuit'),
    ])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    free_product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Récompense de fidélité"
        verbose_name_plural = "Récompenses de fidélité"
    
    def __str__(self):
        return f"{self.name} - {self.points_cost} points"


class UserReward(models.Model):
    """Récompenses utilisées par les utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_rewards')
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    used_in_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Récompense utilisateur"
        verbose_name_plural = "Récompenses utilisateurs"
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.reward.name}"
