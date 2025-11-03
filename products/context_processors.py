from django.db.models import Count, Q, Sum

from .models import Category


def categories(request):
    """
    Context processor pour ajouter les catégories à tous les templates
    Seules les catégories avec des produits publiés sont affichées (directs OU via sous-catégories)
    """
    try:
        from django.db.models import Count, Q

        # Récupérer les catégories qui ont des produits publiés (directement ou via sous-catégories)
        categories_with_products = Category.objects.filter(
            is_active=True, products__status="published"
        ).distinct()

        # Extraire les catégories parentes qui ont des produits (directement ou via enfants)
        parent_categories = []
        for cat in categories_with_products:
            parent = cat.parent if cat.parent else cat
            if parent not in parent_categories and parent.is_active:
                parent_categories.append(parent)

        # Annoter avec le nombre de produits (directs + sous-catégories)
        categories = Category.objects.filter(
            pk__in=[p.pk for p in parent_categories],
            is_active=True,
            parent__isnull=True,  # Seulement les catégories principales
        ).annotate(
            direct_products_count=Count(
                "products", filter=Q(products__status="published")
            ),
            children_products_count=Count(
                "children__products", filter=Q(children__products__status="published")
            ),
        )

        # Calculer le total et filtrer uniquement celles avec au moins un produit
        categories_to_display = []
        for cat in categories:
            total_products = (cat.direct_products_count or 0) + (
                cat.children_products_count or 0
            )
            if total_products > 0:
                cat.published_products_count = total_products
                categories_to_display.append(cat)

        # Trier par nom et limiter
        categories_to_display.sort(key=lambda x: x.name)

        return {"categories": categories_to_display[:15]}
    except Exception as e:
        print(f"Erreur dans categories context processor: {e}")
        return {"categories": []}


def cart_context(request):
    """
    Context processor pour ajouter les informations du panier à tous les templates
    """
    from decimal import Decimal

    cart_items_count = 0
    cart_total = Decimal("0.00")

    try:
        if request.user.is_authenticated:
            from orders.models import Cart, CartItem

            try:
                cart = Cart.objects.get(user=request.user)
                cart_items = CartItem.objects.filter(cart=cart).select_related(
                    "product", "variant"
                )
                cart_items_count = (
                    cart_items.aggregate(Sum("quantity"))["quantity__sum"] or 0
                )
                cart_total = (
                    cart.get_total_price()
                )  # Utilise la méthode du modèle qui gère les décimales
            except Cart.DoesNotExist:
                pass
        else:
            # Pour les utilisateurs non connectés, utiliser la session
            cart_data = request.session.get("cart", {})
            cart_items_count = sum(cart_data.values()) if cart_data else 0
            cart_total = Decimal("0.00")
    except Exception:
        pass

    return {
        "cart_items_count": cart_items_count,
        "cart_total": cart_total,
    }
