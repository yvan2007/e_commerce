"""
Modèles pour le système de coupons et promotions
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class Coupon(models.Model):
    """Modèle pour les coupons de réduction"""

    DISCOUNT_TYPES = [
        ("percentage", "Pourcentage"),
        ("fixed", "Montant fixe"),
        ("free_shipping", "Livraison gratuite"),
    ]

    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    max_uses = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    used_count = models.IntegerField(default=0)
    max_uses_per_user = models.IntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    applicable_products = models.ManyToManyField(
        "products.Product", blank=True, related_name="applicable_coupons"
    )
    applicable_categories = models.ManyToManyField(
        "products.Category", blank=True, related_name="applicable_coupons"
    )
    applicable_users = models.ManyToManyField(
        User, blank=True, related_name="applicable_coupons"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_coupons"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def is_valid(self, user=None, order_amount=None):
        """Vérifier si le coupon est valide"""
        now = timezone.now()

        # Vérifications de base
        if not self.is_active:
            return False, "Ce coupon n'est plus actif"

        if now < self.valid_from:
            return False, "Ce coupon n'est pas encore valide"

        if now > self.valid_until:
            return False, "Ce coupon a expiré"

        if self.used_count >= self.max_uses:
            return False, "Ce coupon a atteint sa limite d'utilisation"

        # Vérifications spécifiques à l'utilisateur
        if user:
            user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_usage >= self.max_uses_per_user:
                return (
                    False,
                    "Vous avez déjà utilisé ce coupon le nombre maximum de fois",
                )

            if (
                self.applicable_users.exists()
                and user not in self.applicable_users.all()
            ):
                return False, "Ce coupon n'est pas valide pour votre compte"

        # Vérification du montant minimum
        if order_amount and order_amount < self.min_order_amount:
            return (
                False,
                f"Le montant minimum de commande est de {self.min_order_amount} FCFA",
            )

        return True, "Coupon valide"

    def calculate_discount(self, order_amount, products=None):
        """Calculer le montant de la réduction"""
        if not self.is_valid(order_amount=order_amount)[0]:
            return Decimal("0.00")

        if self.discount_type == "percentage":
            discount = (order_amount * self.discount_value) / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        elif self.discount_type == "fixed":
            discount = self.discount_value
        elif self.discount_type == "free_shipping":
            discount = Decimal("0.00")  # Géré séparément
        else:
            discount = Decimal("0.00")

        return min(
            discount, order_amount
        )  # Ne peut pas dépasser le montant de la commande

    def use_coupon(self, user, order):
        """Utiliser le coupon"""
        is_valid, message = self.is_valid(user=user, order_amount=order.subtotal)

        if not is_valid:
            return False, message

        # Créer l'usage du coupon
        usage = CouponUsage.objects.create(
            coupon=self,
            user=user,
            order=order,
            discount_amount=self.calculate_discount(order.subtotal),
        )

        # Incrémenter le compteur d'utilisation
        self.used_count += 1
        self.save()

        return True, "Coupon utilisé avec succès"


class CouponUsage(models.Model):
    """Historique d'utilisation des coupons"""

    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="coupon_usages"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="coupon_usages"
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Usage de coupon"
        verbose_name_plural = "Usages de coupons"
        ordering = ["-used_at"]
        unique_together = [
            "coupon",
            "order",
        ]  # Un coupon ne peut être utilisé qu'une fois par commande

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.coupon.code} - {self.discount_amount} FCFA"


class Promotion(models.Model):
    """Modèle pour les promotions"""

    PROMOTION_TYPES = [
        ("flash_sale", "Vente Flash"),
        ("seasonal", "Saisonnière"),
        ("clearance", "Liquidation"),
        ("new_customer", "Nouveau Client"),
        ("loyalty", "Fidélité"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    applicable_products = models.ManyToManyField(
        "products.Product", blank=True, related_name="promotions"
    )
    applicable_categories = models.ManyToManyField(
        "products.Category", blank=True, related_name="promotions"
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_promotions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.discount_percentage}%"

    def is_active_now(self):
        """Vérifier si la promotion est active maintenant"""
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until

    def get_applicable_products(self):
        """Récupérer tous les produits applicables"""
        products = set()

        # Produits spécifiques
        products.update(self.applicable_products.filter(status="published"))

        # Produits des catégories
        for category in self.applicable_categories.filter(is_active=True):
            products.update(category.products.filter(status="published"))

        return list(products)
