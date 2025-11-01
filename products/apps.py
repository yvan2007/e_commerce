from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    
    def ready(self):
        """
        Vérifie et publie automatiquement les produits programmés au démarrage
        """
        # Publier automatiquement les produits programmés dont la date est passée
        from django.utils import timezone
        from products.models import Product
        
        try:
            scheduled_products = Product.objects.filter(
                scheduled_publish_at__lte=timezone.now(),
                status__in=['draft', 'archived']
            )
            
            for product in scheduled_products:
                product.status = 'published'
                if not product.published_at:
                    product.published_at = product.scheduled_publish_at
                product.scheduled_publish_at = None
                product.save(update_fields=['status', 'published_at', 'scheduled_publish_at'])
        except Exception:
            # Ignorer les erreurs au démarrage (migrations non appliquées, etc.)
            pass