from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Category, Tag, Product, ProductImage, ProductVariant, ProductReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Administration des catégories
    """
    list_display = ('name', 'parent', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Image'), {
            'fields': ('image',)
        }),
        (_('Hiérarchie'), {
            'fields': ('parent',)
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        """Nombre de produits dans cette catégorie"""
        return obj.products.count()
    product_count.short_description = 'Produits'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Administration des étiquettes
    """
    list_display = ('name', 'color_preview', 'product_count', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('updated_at',)
    
    def color_preview(self, obj):
        """Aperçu de la couleur de l'étiquette"""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.color,
            obj.color
        )
    color_preview.short_description = 'Couleur'
    
    def product_count(self, obj):
        """Nombre de produits avec cette étiquette"""
        return obj.products.count()
    product_count.short_description = 'Produits'


class ProductImageInline(admin.TabularInline):
    """
    Inline pour les images de produits
    """
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order', 'is_active')


class ProductVariantInline(admin.TabularInline):
    """
    Inline pour les variantes de produits
    """
    model = ProductVariant
    extra = 1
    fields = ('name', 'price', 'stock', 'is_active')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Administration des produits
    """
    list_display = ('name', 'vendor', 'category', 'price', 'stock', 'status', 'is_featured', 'rating', 'sales_count', 'created_at')
    list_filter = ('status', 'is_featured', 'is_digital', 'category', 'vendor', 'created_at')
    search_fields = ('name', 'description', 'sku', 'vendor__username')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('sku', 'views', 'sales_count', 'rating', 'review_count', 'created_at', 'updated_at', 'published_at')
    filter_horizontal = ('tags',)
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('name', 'slug', 'sku', 'description', 'short_description')
        }),
        (_('Vendeur et catégorie'), {
            'fields': ('vendor', 'category', 'tags')
        }),
        (_('Prix et stock'), {
            'fields': ('price', 'compare_price', 'stock', 'min_stock')
        }),
        (_('Image principale'), {
            'fields': ('main_image',)
        }),
        (_('Statut'), {
            'fields': ('status', 'is_featured', 'is_digital')
        }),
        (_('Statistiques'), {
            'fields': ('views', 'sales_count', 'rating', 'review_count'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_products', 'unpublish_products', 'feature_products', 'unfeature_products']
    
    def publish_products(self, request, queryset):
        """Publier les produits sélectionnés"""
        from django.utils import timezone
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} produit(s) publié(s) avec succès.')
    publish_products.short_description = "Publier les produits sélectionnés"
    
    def unpublish_products(self, request, queryset):
        """Dépublier les produits sélectionnés"""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} produit(s) dépublié(s) avec succès.')
    unpublish_products.short_description = "Dépublier les produits sélectionnés"
    
    def feature_products(self, request, queryset):
        """Mettre en vedette les produits sélectionnés"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} produit(s) mis en vedette avec succès.')
    feature_products.short_description = "Mettre en vedette les produits sélectionnés"
    
    def unfeature_products(self, request, queryset):
        """Retirer de la vedette les produits sélectionnés"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} produit(s) retiré(s) de la vedette avec succès.')
    unfeature_products.short_description = "Retirer de la vedette les produits sélectionnés"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendor', 'category').prefetch_related('tags')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Administration des images de produits
    """
    list_display = ('product', 'image_preview', 'alt_text', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('product__name', 'alt_text')
    list_editable = ('order', 'is_active')
    
    def image_preview(self, obj):
        """Aperçu de l'image"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Aperçu'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Administration des variantes de produits
    """
    list_display = ('product', 'name', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('product__name', 'name', 'sku')
    list_editable = ('price', 'stock', 'is_active')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """
    Administration des avis sur les produits
    """
    list_display = ('product', 'user', 'rating', 'title', 'is_approved', 'is_verified_purchase', 'helpful_votes', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at', 'helpful_votes')
    
    fieldsets = (
        (None, {
            'fields': ('product', 'user', 'rating', 'title', 'comment')
        }),
        (_('Statut'), {
            'fields': ('is_approved', 'is_verified_purchase')
        }),
        (_('Engagement'), {
            'fields': ('helpful_votes',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        """Approuver les avis sélectionnés"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} avis approuvé(s) avec succès.')
    approve_reviews.short_description = "Approuver les avis sélectionnés"
    
    def disapprove_reviews(self, request, queryset):
        """Désapprouver les avis sélectionnés"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} avis désapprouvé(s) avec succès.')
    disapprove_reviews.short_description = "Désapprouver les avis sélectionnés"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'user')