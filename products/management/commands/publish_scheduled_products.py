"""
Commande Django pour publier automatiquement les produits programmés
À exécuter via cron ou task scheduler pour vérifier régulièrement les produits à publier
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from products.models import Product


class Command(BaseCommand):
    help = "Publie automatiquement les produits dont la date de publication programmée est passée"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("\n=== Vérification des produits programmés ===\n")
        )

        now = timezone.now()

        # Trouver tous les produits programmés dont la date est passée et qui ne sont pas encore publiés
        scheduled_products = Product.objects.filter(
            scheduled_publish_at__lte=now, status__in=["draft", "archived"]
        )

        count = 0
        for product in scheduled_products:
            old_status = product.status
            product.status = "published"
            if not product.published_at:
                product.published_at = product.scheduled_publish_at
            product.scheduled_publish_at = None  # Nettoyer la date programmée
            product.save(
                update_fields=["status", "published_at", "scheduled_publish_at"]
            )

            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'  [+] Produit "{product.name}" publié automatiquement '
                    f'(était: {old_status}, programmé pour: {product.published_at.strftime("%d/%m/%Y %H:%M")})'
                )
            )

        if count == 0:
            self.stdout.write(
                self.style.WARNING("  Aucun produit à publier pour le moment.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ {count} produit(s) publié(s) automatiquement.\n"
                )
            )
