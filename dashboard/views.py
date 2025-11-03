import json

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from accounts.mixins import (
    AdminRequiredMixin,
    VendorOrAdminRequiredMixin,
    VendorRequiredMixin,
)
from accounts.models import User, VendorProfile
from orders.models import Order, OrderItem
from products.models import Category, Product, ProductReview


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """
    Tableau de bord administrateur - Accès restreint aux administrateurs uniquement
    """

    template_name = "dashboard/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistiques générales
        total_users = User.objects.count()
        total_vendors = User.objects.filter(user_type="vendeur").count()
        total_clients = User.objects.filter(user_type="client").count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        total_revenue = (
            Order.objects.filter(status="delivered").aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )

        # Commandes récentes
        recent_orders = Order.objects.select_related("user").order_by("-created_at")[
            :10
        ]

        # Produits les plus vendus
        top_products = Product.objects.annotate(
            total_sales=Sum("orderitem__quantity")
        ).order_by("-total_sales")[:10]

        # Vendeurs les plus performants
        top_vendors = (
            User.objects.filter(user_type="vendeur")
            .annotate(
                total_sales=Sum("products__orderitem__quantity"),
                total_revenue=Sum("products__orderitem__total_price"),
            )
            .order_by("-total_revenue")[:10]
        )

        # Statistiques par mois (derniers 12 mois)
        monthly_stats = self.get_monthly_statistics()

        # Statistiques des commandes par statut
        order_status_stats = list(
            Order.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        # Sérialiser les données pour les graphiques
        monthly_stats_json = json.dumps(monthly_stats, default=str)
        order_status_stats_json = json.dumps(order_status_stats)

        # Catégories les plus populaires
        popular_categories = Category.objects.annotate(
            product_count=Count("products"),
            order_count=Sum("products__orderitem__quantity"),
        ).order_by("-order_count")[:10]

        # Avis récents
        recent_reviews = (
            ProductReview.objects.select_related("user", "product")
            .filter(is_approved=True)
            .order_by("-created_at")[:10]
        )

        # Notifications pour l'admin
        try:
            from notifications.models import Notification

            notifications = Notification.objects.filter(
                user=request.user, is_read=False
            ).order_by("-created_at")[:10]
        except Exception as e:
            notifications = []

        context.update(
            {
                "total_users": total_users,
                "total_vendors": total_vendors,
                "total_clients": total_clients,
                "total_products": total_products,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "recent_orders": recent_orders,
                "top_products": top_products,
                "top_vendors": top_vendors,
                "monthly_stats": monthly_stats_json,
                "order_status_stats": order_status_stats_json,
                "popular_categories": popular_categories,
                "recent_reviews": recent_reviews,
                "notifications": notifications,
            }
        )

        return context

    def get_monthly_statistics(self):
        """Récupère les statistiques mensuelles"""
        from datetime import timedelta

        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        monthly_data = (
            Order.objects.filter(created_at__gte=start_date, status="delivered")
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(order_count=Count("id"), revenue=Sum("total_amount"))
            .order_by("month")
        )

        return list(monthly_data)


class VendorDashboardView(VendorRequiredMixin, TemplateView):
    """
    Tableau de bord vendeur - Accès restreint aux vendeurs uniquement
    """

    template_name = "dashboard/vendor_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Produits du vendeur
        products = Product.objects.filter(vendor=user)

        # Statistiques des produits
        total_products = products.count()
        published_products = products.filter(status="published").count()
        draft_products = products.filter(status="draft").count()
        low_stock_products = products.filter(stock__lte=F("min_stock")).count()

        # Commandes contenant des produits du vendeur
        vendor_orders = Order.objects.filter(items__product__vendor=user).distinct()

        # Statistiques des commandes
        total_orders = vendor_orders.count()
        pending_orders = vendor_orders.filter(status="pending").count()
        # Commandes livrées = uniquement celles qui ont le statut 'delivered'
        completed_orders = vendor_orders.filter(status="delivered").count()
        # Commandes expédiées = 'shipped' ou 'delivered'
        shipped_orders = vendor_orders.filter(
            status__in=["shipped", "delivered"]
        ).count()

        # Revenus - Calculer le revenu uniquement pour les produits du vendeur
        total_revenue = (
            OrderItem.objects.filter(
                order__status="delivered", product__vendor=user
            ).aggregate(total=Sum("total_price"))["total"]
            or 0
        )

        # Commandes récentes
        recent_orders = vendor_orders.select_related("user").order_by("-created_at")[
            :10
        ]

        # Produits les plus vendus - Utiliser OrderItem au lieu de orderitem
        top_products = (
            products.annotate(total_sales=Sum("orderitem__quantity"))
            .filter(orderitem__order__status="delivered")
            .order_by("-total_sales")[:10]
        )

        # Statistiques par mois
        monthly_stats = self.get_vendor_monthly_statistics(user)

        # Avis sur les produits du vendeur
        product_reviews = (
            ProductReview.objects.filter(product__vendor=user, is_approved=True)
            .select_related("user", "product")
            .order_by("-created_at")[:10]
        )

        # Note moyenne
        average_rating = products.aggregate(avg_rating=Avg("rating"))["avg_rating"] or 0

        # Notifications pour le vendeur
        try:
            from notifications.models import Notification

            notifications = Notification.objects.filter(
                user=user, is_read=False
            ).order_by("-created_at")[:10]
        except Exception as e:
            # Si le modèle Notification n'existe pas ou a une erreur
            notifications = []
            print(f"Erreur récupération notifications: {e}")

        # Commandes nécessitant une attention
        attention_orders = vendor_orders.filter(
            status__in=["pending", "confirmed", "processing"]
        ).order_by("-created_at")[:5]

        # Statistiques de performance du mois en cours
        from datetime import datetime, timedelta

        current_month_start = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_month_orders = vendor_orders.filter(created_at__gte=current_month_start)

        monthly_revenue = (
            OrderItem.objects.filter(
                order__in=current_month_orders,
                order__status="delivered",
                product__vendor=user,
            ).aggregate(total=Sum("total_price"))["total"]
            or 0
        )

        monthly_orders_count = current_month_orders.count()

        # Produits en rupture de stock (stock = 0)
        out_of_stock_products = products.filter(stock=0).count()

        # Produits archivés (rupture de stock)
        archived_products = products.filter(status="archived").count()

        # Commandes en cours de traitement
        processing_orders = vendor_orders.filter(status="processing").count()

        # Produits par catégorie
        products_by_category = products.values("category__name").annotate(
            count=Count("id")
        )

        # Statistiques de conversion
        # Taux de conversion des vues en ventes (approximation)
        # Compter les vues des produits via la relation view_history
        # Pour chaque produit, compter le nombre de vues
        from products.models import ProductViewHistory

        total_product_views = ProductViewHistory.objects.filter(
            product__vendor=user
        ).count()

        conversion_rate = 0
        if total_product_views > 0 and completed_orders > 0:
            conversion_rate = (completed_orders / total_product_views) * 100

        # Variantes de produits
        total_variants = products.aggregate(total=Count("variants"))["total"] or 0

        context.update(
            {
                "total_products": total_products,
                "published_products": published_products,
                "draft_products": draft_products,
                "low_stock_products": low_stock_products,
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
                "total_revenue": total_revenue,
                "recent_orders": recent_orders,
                "top_products": top_products,
                "monthly_stats": monthly_stats,
                "product_reviews": product_reviews,
                "average_rating": average_rating,
                "notifications": notifications,
                "attention_orders": attention_orders,
                "monthly_revenue": monthly_revenue,
                "monthly_orders_count": monthly_orders_count,
                "out_of_stock_products": out_of_stock_products,
                "archived_products": archived_products,
                "processing_orders": processing_orders,
                "shipped_orders": shipped_orders,
                "products_by_category": products_by_category,
                "conversion_rate": conversion_rate,
                "total_variants": total_variants,
                "total_product_views": total_product_views,
            }
        )

        return context

    def get_vendor_monthly_statistics(self, user):
        """Récupère les statistiques mensuelles du vendeur"""
        from datetime import timedelta

        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        # Calculer les revenus mensuels via OrderItem
        monthly_data = []
        current_date = start_date
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)

            # Commandes livrées du vendeur pour ce mois
            month_orders = Order.objects.filter(
                items__product__vendor=user,
                created_at__gte=month_start,
                created_at__lt=month_end,
                status="delivered",
            ).distinct()

            # Revenus du vendeur pour ce mois
            month_revenue = (
                OrderItem.objects.filter(
                    order__in=month_orders, product__vendor=user
                ).aggregate(total=Sum("total_price"))["total"]
                or 0
            )

            monthly_data.append(
                {
                    "month": month_start.strftime("%Y-%m-%d"),
                    "order_count": month_orders.count(),
                    "revenue": float(month_revenue),
                }
            )

            current_date = month_end

        return monthly_data


@login_required
def vendor_products(request):
    """
    Vue pour gérer les produits du vendeur
    """
    if request.user.user_type != "vendeur":
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    products = Product.objects.filter(vendor=request.user).order_by("-created_at")

    # Filtres
    status_filter = request.GET.get("status")
    category_filter = request.GET.get("category")
    search_query = request.GET.get("search")
    stock_filter = request.GET.get("stock")

    if status_filter:
        products = products.filter(status=status_filter)

    if category_filter:
        products = products.filter(category_id=category_filter)

    if stock_filter == "0":
        products = products.filter(stock=0)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    # Contexte
    categories = Category.objects.filter(is_active=True)
    status_choices = Product.STATUS_CHOICES

    context = {
        "products": products,
        "categories": categories,
        "status_choices": status_choices,
        "current_status": status_filter,
        "current_category": category_filter,
        "search_query": search_query,
    }

    return render(request, "dashboard/vendor_products.html", context)


@login_required
def vendor_orders(request):
    """
    Vue pour gérer les commandes du vendeur
    """
    if request.user.user_type != "vendeur":
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    # Gérer le changement de statut
    if request.method == "POST" and request.POST.get("action") == "update_status":
        from orders.models import OrderStatusHistory

        order_id = request.POST.get("order_id")
        new_status = request.POST.get("status")

        try:
            order = Order.objects.get(id=order_id)

            # Vérifier que la commande contient des produits du vendeur
            vendor_order_items = order.items.filter(product__vendor=request.user)

            if vendor_order_items.exists():
                old_status = order.status

                # Empêcher seulement l'annulation (seul le client peut annuler)
                if new_status in ["cancelled", "refunded"]:
                    messages.error(
                        request,
                        "Seul le client peut annuler ou demander un remboursement.",
                    )
                    return redirect("dashboard:vendor_orders")

                # Mettre à jour le statut
                order.status = new_status
                order.save()

                # Créer un historique du statut
                OrderStatusHistory.objects.create(
                    order=order,
                    status=new_status,
                    created_by=request.user,
                    notes=f"Statut changé de {dict(Order.STATUS_CHOICES)[old_status]} à {dict(Order.STATUS_CHOICES)[new_status]} par {request.user.get_display_name()}",
                )

                messages.success(
                    request,
                    f'Statut de la commande {order.order_number} mis à jour en "{order.get_status_display()}"',
                )
            else:
                messages.error(
                    request, "Vous n'avez pas la permission de modifier cette commande"
                )

        except Order.DoesNotExist:
            messages.error(request, "Commande non trouvée")

    orders = (
        Order.objects.filter(items__product__vendor=request.user)
        .distinct()
        .order_by("-created_at")
    )

    # Filtres
    status_filter = request.GET.get("status")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if status_filter:
        orders = orders.filter(status=status_filter)

    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)

    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get("page")
    orders = paginator.get_page(page_number)

    context = {
        "orders": orders,
        "status_choices": Order.STATUS_CHOICES,
        "current_status": status_filter,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(request, "dashboard/vendor_orders.html", context)


@login_required
def admin_users(request):
    """
    Vue pour gérer les utilisateurs (admin)
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    users = User.objects.all().order_by("-date_joined")

    # Filtres
    user_type_filter = request.GET.get("user_type")
    search_query = request.GET.get("search")

    if user_type_filter:
        users = users.filter(user_type=user_type_filter)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get("page")
    users = paginator.get_page(page_number)

    context = {
        "users": users,
        "user_type_choices": User.USER_TYPE_CHOICES,
        "current_user_type": user_type_filter,
        "search_query": search_query,
    }

    return render(request, "dashboard/admin_users.html", context)


@login_required
@require_http_methods(["POST"])
def admin_user_toggle_status(request, user_id):
    """Activer/désactiver un utilisateur"""
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "error": "Accès non autorisé"}, status=403
        )

    user = get_object_or_404(User, pk=user_id)
    user.is_active = not user.is_active
    user.save()

    messages.success(request, _(f"Le statut de {user.username} a été modifié."))
    return JsonResponse(
        {
            "success": True,
            "is_active": user.is_active,
            "message": f'Statut mis à jour: {"Actif" if user.is_active else "Inactif"}',
        }
    )


@login_required
@require_http_methods(["POST"])
def admin_user_delete(request, user_id):
    """Supprimer un utilisateur"""
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "error": "Accès non autorisé"}, status=403
        )

    user = get_object_or_404(User, pk=user_id)

    # Empêcher la suppression de soi-même
    if user.id == request.user.id:
        return JsonResponse(
            {
                "success": False,
                "error": "Vous ne pouvez pas supprimer votre propre compte",
            },
            status=400,
        )

    username = user.username
    user.delete()

    messages.success(request, _(f"L'utilisateur {username} a été supprimé."))
    return JsonResponse({"success": True, "message": "Utilisateur supprimé"})


@login_required
def admin_user_create(request):
    """Créer un nouvel utilisateur"""
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    from django.contrib.auth.forms import UserCreationForm

    from accounts.forms import UserRegistrationForm
    from accounts.models import UserProfile

    # Créer un formulaire personnalisé pour l'admin (sans terms_accepted)
    class AdminUserCreationForm(UserCreationForm):
        email = forms.EmailField(
            required=True, widget=forms.EmailInput(attrs={"class": "form-control"})
        )
        first_name = forms.CharField(
            max_length=30,
            required=True,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
        last_name = forms.CharField(
            max_length=30,
            required=True,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
        phone_number = forms.CharField(
            max_length=17,
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
        country_code = forms.ChoiceField(
            choices=User.COUNTRY_CHOICES,
            initial="+225",
            widget=forms.Select(attrs={"class": "form-select"}),
        )
        date_of_birth = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        )
        address = forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        )
        city = forms.CharField(
            max_length=100,
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
        postal_code = forms.CharField(
            max_length=20,
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
        profile_picture = forms.ImageField(
            required=False, widget=forms.FileInput(attrs={"class": "form-control"})
        )
        user_type = forms.ChoiceField(
            choices=User.USER_TYPE_CHOICES,
            initial="client",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

        class Meta:
            model = User
            fields = (
                "username",
                "email",
                "first_name",
                "last_name",
                "password1",
                "password2",
                "phone_number",
                "country_code",
                "user_type",
                "date_of_birth",
                "address",
                "city",
                "postal_code",
                "profile_picture",
            )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["username"].widget.attrs.update({"class": "form-control"})
            self.fields["password1"].widget.attrs.update({"class": "form-control"})
            self.fields["password2"].widget.attrs.update({"class": "form-control"})

        def clean_email(self):
            email = self.cleaned_data.get("email")
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    _("Un utilisateur avec cette adresse email existe déjà.")
                )
            return email

        def save(self, commit=True):
            user = super().save(commit=False)
            user.email = self.cleaned_data["email"]
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.phone_number = self.cleaned_data.get("phone_number", "")
            user.country_code = self.cleaned_data.get("country_code", "+225")
            user.user_type = self.cleaned_data.get("user_type", "client")
            user.date_of_birth = self.cleaned_data.get("date_of_birth")
            user.address = self.cleaned_data.get("address", "")
            user.city = self.cleaned_data.get("city", "")
            user.postal_code = self.cleaned_data.get("postal_code", "")

            if (
                "profile_picture" in self.cleaned_data
                and self.cleaned_data["profile_picture"]
            ):
                user.profile_picture = self.cleaned_data["profile_picture"]

            if commit:
                user.save()
                UserProfile.objects.get_or_create(user=user)

            return user

    if request.method == "POST":
        form = AdminUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, _(f"L'utilisateur {user.username} a été créé avec succès.")
            )
            return redirect("dashboard:admin_users")
    else:
        form = AdminUserCreationForm()

    return render(
        request,
        "dashboard/admin_user_form.html",
        {"form": form, "title": "Créer un utilisateur", "action": "create"},
    )


@login_required
def admin_user_edit(request, user_id):
    """Modifier un utilisateur"""
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    user = get_object_or_404(User, pk=user_id)
    from accounts.forms import UserProfileForm

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            # Gérer les champs supplémentaires
            if "is_active" in request.POST:
                user.is_active = True
            else:
                user.is_active = False

            if "is_staff" in request.POST:
                user.is_staff = True
            else:
                user.is_staff = False

            if "user_type" in request.POST:
                user.user_type = request.POST["user_type"]

            user.save()
            messages.success(
                request, _(f"L'utilisateur {user.username} a été modifié avec succès.")
            )
            return redirect("dashboard:admin_users")
    else:
        form = UserProfileForm(instance=user)

    return render(
        request,
        "dashboard/admin_user_form.html",
        {
            "form": form,
            "user": user,
            "title": f"Modifier {user.username}",
            "action": "edit",
        },
    )


@login_required
@require_http_methods(["POST"])
def admin_vendor_toggle_approval(request, user_id):
    """Approuver/désapprouver un vendeur"""
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "error": "Accès non autorisé"}, status=403
        )

    user = get_object_or_404(User, pk=user_id)

    if user.user_type != "vendeur":
        return JsonResponse(
            {"success": False, "error": "Cet utilisateur n'est pas un vendeur"},
            status=400,
        )

    vendor_profile, created = VendorProfile.objects.get_or_create(user=user)
    vendor_profile.is_approved = not vendor_profile.is_approved

    if vendor_profile.is_approved:
        from django.utils import timezone

        vendor_profile.approval_date = timezone.now()

    vendor_profile.save()

    messages.success(
        request,
        _(
            f'Le vendeur {user.username} a été {"approuvé" if vendor_profile.is_approved else "désapprouvé"}.'
        ),
    )
    return JsonResponse(
        {
            "success": True,
            "is_approved": vendor_profile.is_approved,
            "message": f'Statut: {"Approuvé" if vendor_profile.is_approved else "En attente"}',
        }
    )


@login_required
def admin_products(request):
    """
    Vue pour gérer tous les produits (admin)
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    products = Product.objects.select_related("vendor", "category").order_by(
        "-created_at"
    )

    # Filtres
    status_filter = request.GET.get("status")
    vendor_filter = request.GET.get("vendor")
    category_filter = request.GET.get("category")
    search_query = request.GET.get("search")

    if status_filter:
        products = products.filter(status=status_filter)

    if vendor_filter:
        products = products.filter(vendor_id=vendor_filter)

    if category_filter:
        products = products.filter(category_id=category_filter)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(vendor__username__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    # Contexte
    vendors = User.objects.filter(user_type="vendeur")
    categories = Category.objects.filter(is_active=True)

    context = {
        "products": products,
        "vendors": vendors,
        "categories": categories,
        "status_choices": Product.STATUS_CHOICES,
        "current_status": status_filter,
        "current_vendor": vendor_filter,
        "current_category": category_filter,
        "search_query": search_query,
    }

    return render(request, "dashboard/admin_products.html", context)


@login_required
def admin_categories(request):
    """
    Vue pour gérer les catégories (admin) - Liste
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    categories = Category.objects.all().order_by("name")

    # Filtres
    search_query = request.GET.get("search")
    active_filter = request.GET.get("active")

    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    if active_filter is not None:
        categories = categories.filter(is_active=active_filter == "true")

    # Pagination
    paginator = Paginator(categories, 20)
    page_number = request.GET.get("page")
    categories = paginator.get_page(page_number)

    context = {
        "categories": categories,
        "search_query": search_query,
        "current_active": active_filter,
    }

    return render(request, "dashboard/admin_categories.html", context)


@login_required
def admin_category_create(request):
    """
    Vue pour créer une catégorie (admin)
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("dashboard:admin_categories")

    from products.forms import CategoryForm

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, _("Catégorie créée avec succès !"))
            return redirect("dashboard:admin_categories")
    else:
        form = CategoryForm()

    return render(
        request,
        "dashboard/admin_category_form.html",
        {
            "form": form,
            "title": "Créer une catégorie",
        },
    )


@login_required
def admin_category_update(request, category_id):
    """
    Vue pour modifier une catégorie (admin)
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("dashboard:admin_categories")

    from django.shortcuts import get_object_or_404

    from products.forms import CategoryForm

    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie modifiée avec succès !"))
            return redirect("dashboard:admin_categories")
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "dashboard/admin_category_form.html",
        {
            "form": form,
            "category": category,
            "title": "Modifier la catégorie",
        },
    )


@login_required
@require_http_methods(["POST"])
def admin_category_delete(request, category_id):
    """
    Vue pour supprimer une catégorie (admin)
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("dashboard:admin_categories")

    from django.shortcuts import get_object_or_404

    category = get_object_or_404(Category, id=category_id)
    category_name = category.name

    # Vérifier si la catégorie a des produits
    products_count = category.products.count()
    subcategories_count = category.children.count()

    if products_count > 0 or subcategories_count > 0:
        messages.error(
            request,
            _(
                "Impossible de supprimer cette catégorie. Elle contient {} produits et {} sous-catégories.".format(
                    products_count, subcategories_count
                )
            ),
        )
        return redirect("dashboard:admin_categories")

    category.delete()
    messages.success(
        request, _('Catégorie "{}" supprimée avec succès.'.format(category_name))
    )
    return redirect("dashboard:admin_categories")


@login_required
def admin_reviews(request):
    """
    Vue pour gérer les avis (admin)
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    reviews = ProductReview.objects.select_related("user", "product").order_by(
        "-created_at"
    )

    # Filtres
    approved_filter = request.GET.get("approved")
    rating_filter = request.GET.get("rating")
    search_query = request.GET.get("search")

    if approved_filter is not None:
        reviews = reviews.filter(is_approved=approved_filter == "true")

    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)

    if search_query:
        reviews = reviews.filter(
            Q(product__name__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get("page")
    reviews = paginator.get_page(page_number)

    context = {
        "reviews": reviews,
        "rating_choices": ProductReview.RATING_CHOICES,
        "current_approved": approved_filter,
        "current_rating": rating_filter,
        "search_query": search_query,
    }

    return render(request, "dashboard/admin_reviews.html", context)


@require_http_methods(["POST"])
@login_required
def approve_review(request, review_id):
    """
    API pour approuver/désapprouver un avis
    """
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "error": "Accès non autorisé"}, status=403
        )

    from products.models import ProductReview

    review = get_object_or_404(ProductReview, pk=review_id)
    review.is_approved = not review.is_approved
    review.save()

    # Mettre à jour la note du produit si disponible
    if hasattr(review.product, "update_rating"):
        try:
            review.product.update_rating()
        except:
            pass

    messages.success(
        request,
        _(f'L\'avis a été {"approuvé" if review.is_approved else "désapprouvé"}.'),
    )
    return JsonResponse(
        {
            "success": True,
            "is_approved": review.is_approved,
            "message": f'Statut: {"Approuvé" if review.is_approved else "En attente"}',
        }
    )


@require_http_methods(["POST"])
@login_required
def delete_review(request, review_id):
    """
    API pour supprimer un avis
    """
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "error": "Accès non autorisé"}, status=403
        )

    from products.models import ProductReview

    review = get_object_or_404(ProductReview, pk=review_id)
    product_name = review.product.name
    review.delete()

    messages.success(request, _(f'L\'avis pour "{product_name}" a été supprimé.'))
    return JsonResponse({"success": True, "message": "Avis supprimé"})


@require_http_methods(["POST"])
@login_required
def toggle_product_status(request, product_id):
    """
    API pour changer le statut d'un produit
    """
    if not request.user.is_staff:
        return JsonResponse({"error": "Accès non autorisé"}, status=403)

    try:
        product = Product.objects.get(id=product_id)
        if product.status == "published":
            product.status = "draft"
        else:
            product.status = "published"
        product.save()

        return JsonResponse(
            {
                "success": True,
                "status": product.status,
                "status_display": product.get_status_display(),
            }
        )
    except Product.DoesNotExist:
        return JsonResponse({"error": "Produit non trouvé"}, status=404)


@require_http_methods(["POST"])
@login_required
def toggle_user_status(request, user_id):
    """
    API pour activer/désactiver un utilisateur
    """
    if not request.user.is_staff:
        return JsonResponse({"error": "Accès non autorisé"}, status=403)

    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()

        return JsonResponse({"success": True, "is_active": user.is_active})
    except User.DoesNotExist:
        return JsonResponse({"error": "Utilisateur non trouvé"}, status=404)
