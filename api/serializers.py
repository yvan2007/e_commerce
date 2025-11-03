"""
Serializers pour l'API REST de l'e-commerce
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserProfile, VendorProfile
from orders.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    ShippingAddress,
)
from products.models import (
    Category,
    Product,
    ProductImage,
    ProductReview,
    ProductVariant,
    Tag,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle User"""

    full_name = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()
    vendor_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "country_code",
            "address",
            "city",
            "postal_code",
            "user_type",
            "is_verified",
            "date_joined",
            "last_login",
            "user_profile",
            "vendor_profile",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_user_profile(self, obj):
        try:
            profile = obj.userprofile
            return UserProfileSerializer(profile).data
        except UserProfile.DoesNotExist:
            return None

    def get_vendor_profile(self, obj):
        try:
            profile = obj.vendorprofile
            return VendorProfileSerializer(profile).data
        except VendorProfile.DoesNotExist:
            return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle UserProfile"""

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "bio",
            "website",
            "facebook",
            "twitter",
            "instagram",
            "preferences",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VendorProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle VendorProfile"""

    class Meta:
        model = VendorProfile
        fields = [
            "id",
            "business_name",
            "business_type",
            "business_address",
            "business_city",
            "business_phone",
            "business_email",
            "business_license",
            "tax_id",
            "bank_account",
            "description",
            "is_approved",
            "rating",
            "total_sales",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "rating", "total_sales", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Category"""

    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "parent",
            "is_active",
            "product_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_product_count(self, obj):
        return obj.products.filter(status="published").count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Tag"""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ProductImage"""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ProductVariant"""

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "sku",
            "price",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ProductReview"""

    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "user",
            "user_name",
            "user_avatar",
            "rating",
            "title",
            "comment",
            "verified_purchase",
            "approved",
            "helpful_votes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "helpful_votes", "created_at", "updated_at"]

    def get_user_name(self, obj):
        return obj.user.get_display_name()

    def get_user_avatar(self, obj):
        if obj.user.profile_picture:
            return obj.user.profile_picture.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Product"""

    vendor_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "short_description",
            "vendor",
            "vendor_name",
            "category",
            "category_name",
            "tags",
            "price",
            "compare_price",
            "stock",
            "min_stock",
            "main_image",
            "images",
            "variants",
            "reviews",
            "status",
            "is_featured",
            "is_digital",
            "views",
            "sales_count",
            "rating",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "views",
            "sales_count",
            "rating",
            "created_at",
            "updated_at",
        ]

    def get_vendor_name(self, obj):
        return obj.vendor.get_display_name() if obj.vendor else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_average_rating(self, obj):
        return obj.rating

    def get_review_count(self, obj):
        return obj.review_count


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle CartItem"""

    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "variant",
            "variant_id",
            "quantity",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "total_price", "created_at", "updated_at"]

    def get_total_price(self, obj):
        return obj.get_total_price()


class CartSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Cart"""

    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "items",
            "total_items",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_items",
            "total_price",
            "created_at",
            "updated_at",
        ]

    def get_total_items(self, obj):
        return obj.get_total_items()

    def get_total_price(self, obj):
        return obj.get_total_price()


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle OrderItem"""

    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "variant",
            "quantity",
            "unit_price",
            "total_price",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer pour le modèle OrderStatusHistory"""

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusHistory
        fields = [
            "id",
            "status",
            "notes",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_created_by_name(self, obj):
        return obj.created_by.get_display_name() if obj.created_by else None


class OrderSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Order"""

    user_name = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.SerializerMethodField()
    payment_method_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "user_name",
            "status",
            "status_display",
            "payment_method",
            "payment_method_display",
            "payment_status",
            "shipping_first_name",
            "shipping_last_name",
            "shipping_phone",
            "shipping_address",
            "shipping_city",
            "shipping_postal_code",
            "shipping_country",
            "billing_address",
            "subtotal",
            "shipping_cost",
            "tax_amount",
            "total_amount",
            "notes",
            "payment_reference",
            "items",
            "status_history",
            "created_at",
            "updated_at",
            "confirmed_at",
            "shipped_at",
            "delivered_at",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "created_at",
            "updated_at",
            "confirmed_at",
            "shipped_at",
            "delivered_at",
        ]

    def get_user_name(self, obj):
        return obj.user.get_display_name() if obj.user else None

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_payment_method_display(self, obj):
        return obj.get_payment_method_display()


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ShippingAddress"""

    class Meta:
        model = ShippingAddress
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "address",
            "city",
            "postal_code",
            "country",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# Serializers pour les statistiques
class DashboardStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du dashboard"""

    total_users = serializers.IntegerField()
    total_vendors = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    recent_orders = OrderSerializer(many=True)
    top_products = ProductSerializer(many=True)
    top_vendors = UserSerializer(many=True)


class VendorStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du vendeur"""

    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    recent_orders = OrderSerializer(many=True)
    top_products = ProductSerializer(many=True)
