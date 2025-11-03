"""
Vues API REST pour l'e-commerce
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile, VendorProfile
from orders.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    ShippingAddress,
)
from products.models import Category, Product, ProductReview, Tag

from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    DashboardStatsSerializer,
    OrderSerializer,
    ProductReviewSerializer,
    ProductSerializer,
    ShippingAddressSerializer,
    UserProfileSerializer,
    UserSerializer,
    VendorProfileSerializer,
    VendorStatsSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des utilisateurs"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtrer les utilisateurs selon les permissions"""
        if self.request.user.is_staff:
            return User.objects.all()
        elif self.request.user.user_type == "vendeur":
            return User.objects.filter(user_type="client")
        else:
            return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=["get"])
    def profile(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "patch"])
    def update_profile(self, request):
        """Mettre à jour le profil de l'utilisateur connecté"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les catégories (lecture seule)"""

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """Récupérer les produits d'une catégorie"""
        category = self.get_object()
        products = Product.objects.filter(category=category, status="published")
        serializer = ProductSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des produits"""

    queryset = Product.objects.filter(status="published")
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Filtrer les produits selon les permissions"""
        queryset = Product.objects.filter(status="published")

        # Filtres
        category = self.request.query_params.get("category")
        vendor = self.request.query_params.get("vendor")
        search = self.request.query_params.get("search")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        featured = self.request.query_params.get("featured")

        if category:
            queryset = queryset.filter(category__slug=category)
        if vendor:
            queryset = queryset.filter(vendor__username=vendor)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(short_description__icontains=search)
            )
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if featured:
            queryset = queryset.filter(is_featured=True)

        # Tri
        sort_by = self.request.query_params.get("sort_by", "created_at")
        if sort_by == "price_asc":
            queryset = queryset.order_by("price")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-price")
        elif sort_by == "name":
            queryset = queryset.order_by("name")
        elif sort_by == "rating":
            queryset = queryset.order_by("-rating")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_permissions(self):
        """Permissions selon l'action"""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Créer un produit avec le vendeur connecté"""
        if self.request.user.user_type == "vendeur":
            serializer.save(vendor=self.request.user)
        else:
            raise permissions.PermissionDenied(
                "Seuls les vendeurs peuvent créer des produits"
            )

    def perform_update(self, serializer):
        """Mettre à jour un produit"""
        if (
            self.request.user.user_type == "vendeur"
            and serializer.instance.vendor == self.request.user
        ) or self.request.user.is_staff:
            serializer.save()
        else:
            raise permissions.PermissionDenied("Vous ne pouvez pas modifier ce produit")

    def perform_destroy(self, instance):
        """Supprimer un produit"""
        if (
            self.request.user.user_type == "vendeur"
            and instance.vendor == self.request.user
        ) or self.request.user.is_staff:
            instance.delete()
        else:
            raise permissions.PermissionDenied(
                "Vous ne pouvez pas supprimer ce produit"
            )

    @action(detail=True, methods=["post"])
    def add_review(self, request, pk=None):
        """Ajouter un avis sur un produit"""
        product = self.get_object()
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        """Récupérer les avis d'un produit"""
        product = self.get_object()
        reviews = product.reviews.filter(approved=True)
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class CartViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion du panier"""

    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Récupérer le panier de l'utilisateur connecté"""
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        """Récupérer ou créer le panier de l'utilisateur"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=["get"])
    def my_cart(self, request):
        """Récupérer le panier de l'utilisateur connecté"""
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """Ajouter un article au panier"""
        cart = self.get_object()
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)
        variant_id = request.data.get("variant_id")

        try:
            product = Product.objects.get(id=product_id, status="published")
        except Product.DoesNotExist:
            return Response(
                {"error": "Produit non trouvé"}, status=status.HTTP_404_NOT_FOUND
            )

        # Vérifier le stock
        if product.stock < quantity:
            return Response(
                {"error": "Stock insuffisant"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Créer ou mettre à jour l'article du panier
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant_id=variant_id if variant_id else None,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        """Supprimer un article du panier"""
        cart = self.get_object()
        product_id = request.data.get("product_id")
        variant_id = request.data.get("variant_id")

        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product_id=product_id,
                variant_id=variant_id if variant_id else None,
            )
            cart_item.delete()
            return Response({"message": "Article supprimé du panier"})
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Article non trouvé dans le panier"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"])
    def update_item(self, request):
        """Mettre à jour la quantité d'un article"""
        cart = self.get_object()
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")
        variant_id = request.data.get("variant_id")

        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product_id=product_id,
                variant_id=variant_id if variant_id else None,
            )
            cart_item.quantity = quantity
            cart_item.save()
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Article non trouvé dans le panier"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"])
    def clear(self, request):
        """Vider le panier"""
        cart = self.get_object()
        cart.items.all().delete()
        return Response({"message": "Panier vidé"})


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des commandes"""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtrer les commandes selon les permissions"""
        if self.request.user.is_staff:
            return Order.objects.all()
        elif self.request.user.user_type == "vendeur":
            return Order.objects.filter(
                items__product__vendor=self.request.user
            ).distinct()
        else:
            return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Créer une commande pour l'utilisateur connecté"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Annuler une commande"""
        order = self.get_object()
        if order.can_be_cancelled():
            order.status = "cancelled"
            order.save()
            return Response({"message": "Commande annulée"})
        return Response(
            {"error": "Cette commande ne peut pas être annulée"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une commande"""
        order = self.get_object()
        new_status = request.data.get("status")
        notes = request.data.get("notes", "")

        if not new_status:
            return Response(
                {"error": "Statut requis"}, status=status.HTTP_400_BAD_REQUEST
            )

        old_status = order.status
        order.status = new_status
        order.save()

        # Créer l'historique de statut
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes or f"Statut changé de {old_status} à {new_status}",
            created_by=request.user,
        )

        return Response({"message": "Statut mis à jour"})


class ShippingAddressViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des adresses de livraison"""

    queryset = ShippingAddress.objects.all()
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Récupérer les adresses de l'utilisateur connecté"""
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Créer une adresse pour l'utilisateur connecté"""
        serializer.save(user=self.request.user)


class DashboardStatsView(APIView):
    """Vue pour les statistiques du dashboard admin"""

    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request):
        """Récupérer les statistiques du dashboard"""
        # Statistiques générales
        total_users = User.objects.count()
        total_vendors = User.objects.filter(user_type="vendeur").count()
        total_products = Product.objects.filter(status="published").count()
        total_orders = Order.objects.count()
        total_revenue = (
            Order.objects.filter(status="delivered").aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )
        pending_orders = Order.objects.filter(status="pending").count()
        completed_orders = Order.objects.filter(status="delivered").count()

        # Commandes récentes
        recent_orders = Order.objects.order_by("-created_at")[:10]

        # Produits les plus vendus
        top_products = Product.objects.filter(status="published").order_by(
            "-sales_count"
        )[:10]

        # Vendeurs les plus actifs
        top_vendors = User.objects.filter(user_type="vendeur").order_by(
            "-vendorprofile__total_sales"
        )[:10]

        stats = {
            "total_users": total_users,
            "total_vendors": total_vendors,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "recent_orders": recent_orders,
            "top_products": top_products,
            "top_vendors": top_vendors,
        }

        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)


class VendorStatsView(APIView):
    """Vue pour les statistiques du vendeur"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Récupérer les statistiques du vendeur"""
        if request.user.user_type != "vendeur":
            return Response(
                {"error": "Accès non autorisé"}, status=status.HTTP_403_FORBIDDEN
            )

        # Statistiques du vendeur
        total_products = Product.objects.filter(vendor=request.user).count()
        active_products = Product.objects.filter(
            vendor=request.user, status="published"
        ).count()
        total_orders = (
            Order.objects.filter(items__product__vendor=request.user).distinct().count()
        )
        total_revenue = (
            Order.objects.filter(
                items__product__vendor=request.user, status="delivered"
            )
            .distinct()
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )
        pending_orders = (
            Order.objects.filter(items__product__vendor=request.user, status="pending")
            .distinct()
            .count()
        )
        completed_orders = (
            Order.objects.filter(
                items__product__vendor=request.user, status="delivered"
            )
            .distinct()
            .count()
        )

        # Note moyenne et nombre d'avis
        reviews = ProductReview.objects.filter(
            product__vendor=request.user, approved=True
        )
        average_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0
        total_reviews = reviews.count()

        # Commandes récentes
        recent_orders = (
            Order.objects.filter(items__product__vendor=request.user)
            .distinct()
            .order_by("-created_at")[:10]
        )

        # Produits les plus vendus du vendeur
        top_products = Product.objects.filter(
            vendor=request.user, status="published"
        ).order_by("-sales_count")[:10]

        stats = {
            "total_products": total_products,
            "active_products": active_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "average_rating": average_rating,
            "total_reviews": total_reviews,
            "recent_orders": recent_orders,
            "top_products": top_products,
        }

        serializer = VendorStatsSerializer(stats)
        return Response(serializer.data)
