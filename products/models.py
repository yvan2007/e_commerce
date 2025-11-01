from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import uuid

User = get_user_model()


class Category(models.Model):
    """
    Modèle pour les catégories de produits
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nom de la catégorie")
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Slug")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name=_("Image de la catégorie")
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
        verbose_name=_("Catégorie parente")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})


class Tag(models.Model):
    """
    Modèle pour les étiquettes/tags des produits
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom de l'étiquette")
    )
    
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Slug")
    )
    
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=_("Couleur")
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Étiquette")
        verbose_name_plural = _("Étiquettes")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Modèle principal pour les produits
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]
    
    # Informations de base
    name = models.CharField(
        max_length=200,
        verbose_name=_("Nom du produit")
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name=_("Slug")
    )
    
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("SKU")
    )
    
    description = CKEditor5Field(
        verbose_name=_("Description"),
        config_name='extends'
    )
    
    short_description = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("Description courte")
    )
    
    # Informations détaillées
    features = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name=_("Caractéristiques"),
        config_name='default'
    )
    
    specifications = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name=_("Spécifications"),
        config_name='default'
    )
    
    usage_instructions = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name=_("Instructions d'utilisation"),
        config_name='default'
    )
    
    warranty_info = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name=_("Informations de garantie"),
        config_name='default'
    )
    
    # Relations
    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Vendeur")
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Catégorie")
    )
    
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='products',
        verbose_name=_("Étiquettes")
    )
    
    # Prix et stock
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Prix")
    )
    
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_("Prix original")
    )
    
    discount_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        verbose_name=_("Pourcentage de remise")
    )
    
    is_on_sale = models.BooleanField(
        default=False,
        verbose_name=_("En promotion")
    )
    
    sale_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Début de la promotion")
    )
    
    sale_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fin de la promotion")
    )
    
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Prix de comparaison")
    )
    
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Stock")
    )
    
    min_stock = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Stock minimum")
    )
    
    # Images
    main_image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name=_("Image principale")
    )
    
    # Statut et dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_("Statut")
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Produit vedette")
    )
    
    is_digital = models.BooleanField(
        default=False,
        verbose_name=_("Produit numérique")
    )
    
    # Métriques
    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Vues")
    )
    
    sales_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de ventes")
    )
    
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name=_("Note moyenne")
    )
    
    review_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre d'avis")
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    scheduled_publish_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Date de publication programmée"),
        help_text=_("Si défini, le produit sera automatiquement publié à cette date/heure")
    )
    
    class Meta:
        verbose_name = _("Produit")
        verbose_name_plural = _("Produits")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['vendor', 'status']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # S'assurer que le slug est unique (exclure l'instance courante si c'est une mise à jour)
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
        
        # S'assurer que le SKU est unique (exclure l'instance courante si c'est une mise à jour)
        if self.sku and Product.objects.filter(sku=self.sku).exclude(pk=self.pk).exists():
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
        
        # Ne définir published_at que si le produit est publié maintenant (pas programmé)
        if self.status == 'published' and not self.published_at and not self.scheduled_publish_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        # Si le produit est programmé et que la date est passée, le publier automatiquement
        elif self.scheduled_publish_at:
            from django.utils import timezone
            if timezone.now() >= self.scheduled_publish_at and self.status != 'published':
                self.status = 'published'
                if not self.published_at:
                    self.published_at = self.scheduled_publish_at
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    
    def get_discount_percentage(self):
        """Calcule le pourcentage de réduction"""
        if self.is_on_sale and self.original_price and self.original_price > self.price:
            return round(((self.original_price - self.price) / self.original_price) * 100)
        elif self.compare_price and self.compare_price > self.price:
            return round(((self.compare_price - self.price) / self.compare_price) * 100)
        return self.discount_percentage
    
    def get_original_price(self):
        """Retourne le prix original pour l'affichage"""
        if self.is_on_sale and self.original_price:
            return self.original_price
        elif self.compare_price:
            return self.compare_price
        return None
    
    def is_currently_on_sale(self):
        """Vérifie si le produit est actuellement en promotion"""
        if not self.is_on_sale:
            return False
        
        from django.utils import timezone
        now = timezone.now()
        
        if self.sale_start_date and now < self.sale_start_date:
            return False
        if self.sale_end_date and now > self.sale_end_date:
            return False
        
        return True
    
    def calculate_sale_price(self):
        """Calcule le prix de vente avec remise"""
        from decimal import Decimal
        if self.is_currently_on_sale() and self.original_price:
            return Decimal(str(self.price))
        return Decimal(str(self.price))
    
    def get_display_price(self):
        """Retourne le prix avec préservation des décimales"""
        from decimal import Decimal
        return Decimal(str(self.price))
    
    def is_in_stock(self):
        """Vérifie si le produit est en stock"""
        return self.stock > 0
    
    def is_low_stock(self):
        """Vérifie si le stock est faible"""
        return self.stock <= self.min_stock
    
    def is_out_of_stock(self):
        """Vérifie si le produit est en rupture de stock"""
        return self.stock == 0
    
    def set_out_of_stock(self):
        """Met le produit en rupture de stock"""
        self.stock = 0
        self.status = 'archived'  # Masque le produit
        self.save()
    
    def set_in_stock(self, quantity):
        """Remet le produit en stock avec une certaine quantité"""
        if quantity > 0:
            self.stock = quantity
            self.status = 'published'  # Remet le produit en ligne
            self.save()
            return True
        return False
    
    def update_rating(self):
        """Met à jour la note moyenne et le nombre d'avis"""
        from django.db.models import Avg, Count
        reviews = self.reviews.filter(is_approved=True)
        self.rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        self.review_count = reviews.count()
        self.save(update_fields=['rating', 'review_count'])
    
    def has_main_image(self):
        """Vérifie si le produit a une image principale valide"""
        try:
            return bool(self.main_image and self.main_image.url)
        except (ValueError, AttributeError):
            return False


class ProductImage(models.Model):
    """
    Modèle pour les images supplémentaires des produits
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Produit")
    )
    
    image = models.ImageField(
        upload_to='products/images/',
        verbose_name=_("Image")
    )
    
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Texte alternatif")
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Ordre")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Image de produit")
        verbose_name_plural = _("Images de produit")
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image de {self.product.name}"


class ProductVariant(models.Model):
    """
    Modèle pour les variantes de produits (taille, couleur, etc.)
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_("Produit")
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom de la variante")
    )
    
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("SKU")
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Prix")
    )
    
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Stock")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Variante de produit")
        verbose_name_plural = _("Variantes de produit")
        unique_together = ['product', 'name']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"VAR-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_display_price(self):
        """Retourne le prix avec préservation des décimales"""
        from decimal import Decimal
        return Decimal(str(self.price))


class ProductReview(models.Model):
    """
    Modèle pour les avis sur les produits
    """
    RATING_CHOICES = [
        (1, '1 étoile'),
        (2, '2 étoiles'),
        (3, '3 étoiles'),
        (4, '4 étoiles'),
        (5, '5 étoiles'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("Produit")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("Utilisateur")
    )
    
    rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre")
    )
    
    comment = models.TextField(
        verbose_name=_("Commentaire")
    )
    
    is_verified_purchase = models.BooleanField(
        default=False,
        verbose_name=_("Achat vérifié")
    )
    
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_("Approuvé")
    )
    
    helpful_votes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Votes utiles")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Avis produit")
        verbose_name_plural = _("Avis produits")
        ordering = ['-created_at']
        unique_together = ['product', 'user']
    
    def __str__(self):
        return f"Avis de {self.user.username} sur {self.product.name}"


class ProductViewHistory(models.Model):
    """
    Modèle pour l'historique des vues de produits
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='product_views',
        verbose_name=_("Utilisateur")
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='view_history',
        verbose_name=_("Produit")
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_("Adresse IP")
    )
    
    session_key = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name=_("Clé de session")
    )
    
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Vu le")
    )
    
    class Meta:
        verbose_name = _("Historique de vue")
        verbose_name_plural = _("Historique des vues")
        ordering = ['-viewed_at']
        unique_together = ['user', 'product', 'session_key']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} a vu {self.product.name}"
        return f"Visiteur a vu {self.product.name}"


# Signaux pour gérer la rupture de stock automatiquement


@receiver(pre_save, sender=Product)
def check_stock_before_save(sender, instance, **kwargs):
    """Vérifie et met à jour automatiquement le statut en fonction du stock"""
    if instance.pk:  # Si c'est une mise à jour (pas une création)
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            
            # Si le stock passe à 0, mettre le produit en archive
            if instance.stock == 0 and old_instance.stock > 0:
                instance.status = 'archived'
            
            # Si le stock repasse au-dessus de 0, remettre le produit en publié
            if instance.stock > 0 and old_instance.stock == 0 and instance.status == 'archived':
                instance.status = 'published'
        except sender.DoesNotExist:
            pass  # Produit n'existe pas encore


@receiver(post_save, sender=Product)
def notify_stock_change(sender, instance, created, **kwargs):
    """Notifie en cas de changement de statut de stock"""
    if not created:  # Si ce n'est pas une création
        # Vous pouvez ajouter ici une notification au vendeur
        # par exemple envoyer un email ou créer une notification
        pass