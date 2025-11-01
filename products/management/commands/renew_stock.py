from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Renouvelle le stock d\'un produit en rupture'

    def add_arguments(self, parser):
        parser.add_argument('product_id', type=int, help='ID du produit à renouveler')
        parser.add_argument('quantity', type=int, help='Quantité de stock à ajouter')

    def handle(self, *args, **options):
        product_id = options['product_id']
        quantity = options['quantity']

        try:
            product = Product.objects.get(id=product_id)
            
            if product.status == 'archived' and product.stock == 0:
                # Remettre le produit en stock
                product.set_in_stock(quantity)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Stock renouvelé pour "{product.name}" : {quantity} unités'
                    )
                )
            else:
                # Ajouter au stock existant
                product.stock += quantity
                product.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Stock mis à jour pour "{product.name}" : {product.stock} unités'
                    )
                )
                
        except Product.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Produit avec ID {product_id} non trouvé')
            )

