from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from delivery_system.forms import DeliveryAddressForm
from delivery_system.services import DeliveryService
from notifications.services import EmailService
from products.models import Product

from .forms import CheckoutForm, OrderSearchForm, OrderStatusUpdateForm
from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    ShippingAddress,
)


class CartView(LoginRequiredMixin, ListView):
    """
    Vue pour afficher le panier
    """

    template_name = "orders/cart.html"
    context_object_name = "cart_items"

    def get_queryset(self):
        try:
            cart = self.request.user.cart
            return cart.items.select_related("product", "variant").all()
        except Cart.DoesNotExist:
            return CartItem.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            cart = self.request.user.cart
            context["cart_total"] = cart.get_total_price()
            context["cart_count"] = cart.get_total_items()
        except Cart.DoesNotExist:
            context["cart_total"] = 0
            context["cart_count"] = 0
        return context


class CheckoutView(LoginRequiredMixin, FormView):
    """
    Vue pour le processus de commande
    """

    template_name = "orders/checkout.html"
    form_class = CheckoutForm
    success_url = reverse_lazy("orders:order_confirmation")

    def get_form_kwargs(self):
        """Retourne les arguments à passer au formulaire"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            cart = self.request.user.cart
            cart_items = cart.items.select_related("product", "variant").all()
            context["cart_items"] = cart_items
            context["cart_total"] = float(
                cart.get_total_price()
            )  # Convertir en float pour éviter les problèmes de formatage
            context["cart_count"] = cart.get_total_items()
            context["shipping_addresses"] = self.request.user.shipping_addresses.all()

            # Initialiser les frais de livraison par défaut
            context["delivery_zones"] = DeliveryService.get_delivery_zones()
            context["default_delivery_fee"] = 2500  # Abidjan par défaut
        except Cart.DoesNotExist:
            context["cart_items"] = []
            context["cart_total"] = 0
            context["cart_count"] = 0
            context["shipping_addresses"] = []
            context["delivery_zones"] = []
            context["default_delivery_fee"] = 0
        return context

    def form_valid(self, form):
        try:
            cart = self.request.user.cart
            cart_items = cart.items.select_related("product", "variant").all()
        except Cart.DoesNotExist:
            messages.error(self.request, _("Votre panier est vide."))
            return redirect("orders:cart")

        if not cart_items:
            messages.error(self.request, _("Votre panier est vide."))
            return redirect("orders:cart")

        # Calculer les totaux
        subtotal = sum(item.get_total_price() for item in cart_items)

        # Récupérer les frais de livraison depuis le formulaire
        calculated_delivery_fee = form.cleaned_data.get(
            "calculated_delivery_fee", Decimal("0.00")
        )

        # Frais de livraison et taxes
        shipping_cost = (
            calculated_delivery_fee if calculated_delivery_fee else Decimal("0.00")
        )
        tax_amount = Decimal("0.00")

        # Le total est le sous-total + frais de livraison
        total_amount = subtotal + shipping_cost

        # Créer la commande
        with transaction.atomic():
            # Déterminer la ville correctement (nom pour CIV, valeur pour autres pays)
            city = form.cleaned_data.get("shipping_city", "")
            city_int = form.cleaned_data.get("shipping_city_int", "")
            city_name = form.cleaned_data.get("shipping_city_name", "")

            # Si city_name est défini (CIV avec nom de ville), l'utiliser
            # Sinon si city_int est défini (autres pays), utiliser city_int
            # Sinon utiliser city (fallback)
            final_city = city_name if city_name else (city_int if city_int else city)

            order = Order.objects.create(
                user=self.request.user,
                shipping_first_name=form.cleaned_data["shipping_first_name"],
                shipping_last_name=form.cleaned_data["shipping_last_name"],
                shipping_phone=form.cleaned_data["shipping_phone"],
                shipping_address=form.cleaned_data["shipping_address"],
                shipping_city=final_city,
                shipping_postal_code=form.cleaned_data.get("shipping_postal_code", ""),
                payment_method=form.cleaned_data["payment_method"],
                notes=form.cleaned_data.get("notes", ""),
                billing_address=form.cleaned_data.get("billing_address", ""),
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                total_amount=total_amount,
            )

            # Créer les articles de commande
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.get_unit_price(),
                    total_price=cart_item.get_total_price(),
                )

                # Mettre à jour le stock
                if cart_item.variant:
                    cart_item.variant.stock -= cart_item.quantity
                    cart_item.variant.save()
                else:
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.sales_count += cart_item.quantity
                    cart_item.product.save()

            # Vider le panier
            cart.clear()

            # Créer l'historique de statut
            OrderStatusHistory.objects.create(
                order=order,
                status="pending",
                notes="Commande créée",
                created_by=self.request.user,
            )

        # Envoyer l'email de confirmation
        try:
            EmailService.send_order_confirmation_email(order)
        except Exception as e:
            # Ne pas bloquer la commande si l'email échoue
            print(f"Erreur lors de l'envoi de l'email: {e}")
            import logging

            logging.error(
                f"Impossible d'envoyer l'email de confirmation pour la commande {order.order_number}: {e}"
            )

        # Notifier les vendeurs
        # vendors = set()
        # for item in order.items.all():
        #     if item.product.vendor:
        #         vendors.add(item.product.vendor)

        # for vendor in vendors:
        #     send_vendor_notification_email(order, vendor)

        messages.success(
            self.request,
            _("Votre commande a été passée avec succès! Numéro de commande: {}").format(
                order.order_number
            ),
        )

        return redirect("orders:order_detail", order_number=order.order_number)

    def send_order_confirmation_email(self, order):
        """Envoie un email de confirmation de commande"""
        subject = _("Confirmation de votre commande {}").format(order.order_number)

        # Construire le message avec les détails de la commande
        message = f"""
        Bonjour {order.shipping_first_name},

        Votre commande a été reçue avec succès!

        Numéro de commande: {order.order_number}
        Date: {order.created_at.strftime('%d/%m/%Y à %H:%M')}

        Détails de la commande:
        """

        for item in order.items.all():
            message += f"""
        - {item.product.name}
          Quantité: {item.quantity}
          Prix unitaire: {item.unit_price} FCFA
          Total: {item.total_price} FCFA
        """

        message += f"""

        Total: {order.total_amount} FCFA

        Adresse de livraison:
        {order.shipping_first_name} {order.shipping_last_name}
        {order.shipping_address}
        {order.shipping_city}
        Téléphone: {order.shipping_phone}

        Méthode de paiement: {order.get_payment_method_display()}

        Nous vous contacterons bientôt pour confirmer votre commande.

        Cordialement,
        L'équipe e-commerce
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )


class OrderListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister les commandes de l'utilisateur
    """

    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Vue pour afficher les détails d'une commande
    """

    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    pk_url_kwarg = "order_number"

    def get_object(self, queryset=None):
        """
        Récupère l'objet commande par son order_number
        """
        order_number = self.kwargs.get(self.pk_url_kwarg)

        try:
            # Chercher la commande par order_number
            order = Order.objects.get(order_number=order_number)

            # Vérifier que l'utilisateur est le propriétaire, admin, ou vendeur
            is_owner = order.user == self.request.user
            is_admin = self.request.user.is_staff or self.request.user.is_superuser
            is_vendor = False

            # Vérifier si l'utilisateur est vendeur ET vend des produits dans cette commande
            if not is_owner and not is_admin:
                vendor_items = order.items.filter(product__vendor=self.request.user)
                if vendor_items.exists():
                    is_vendor = True

            if not (is_owner or is_admin or is_vendor):
                from django.contrib import messages
                from django.core.exceptions import PermissionDenied

                messages.error(self.request, "Vous n'avez pas accès à cette commande")
                raise PermissionDenied("Vous n'avez pas accès à cette commande")

            return order
        except Order.DoesNotExist:
            from django.contrib import messages
            from django.http import Http404

            messages.error(self.request, f"Commande {order_number} non trouvée")
            raise Http404(f"Commande {order_number} non trouvée")
        except Order.MultipleObjectsReturned:
            # En cas de doublon (normalement impossible avec unique=True)
            order = Order.objects.filter(order_number=order_number).first()
            return order


class OrderCancelView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour annuler une commande
    """

    model = Order
    fields = []
    template_name = "orders/order_cancel.html"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"

    def test_func(self):
        order = self.get_object()
        return order.user == self.request.user and order.can_be_cancelled()

    def form_valid(self, form):
        order = self.get_object()
        order.status = "cancelled"
        order.save()

        # Créer l'historique de statut
        OrderStatusHistory.objects.create(
            order=order,
            status="cancelled",
            notes="Commande annulée par le client",
            created_by=self.request.user,
        )

        # Restaurer le stock
        for item in order.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()
            else:
                item.product.stock += item.quantity
                item.product.sales_count -= item.quantity
                item.product.save()

        messages.success(self.request, _("Votre commande a été annulée."))
        return redirect("orders:order_detail", order_number=order.order_number)


class ShippingAddressListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister les adresses de livraison
    """

    model = ShippingAddress
    template_name = "orders/shipping_address_list.html"
    context_object_name = "addresses"

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user).order_by(
            "-is_default", "-created_at"
        )


class ShippingAddressCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour créer une adresse de livraison
    """

    model = ShippingAddress
    form_class = DeliveryAddressForm
    template_name = "orders/shipping_address_form.html"
    success_url = reverse_lazy("orders:shipping_address_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ShippingAddressUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier une adresse de livraison
    """

    model = ShippingAddress
    form_class = DeliveryAddressForm
    template_name = "orders/shipping_address_form.html"
    success_url = reverse_lazy("orders:shipping_address_list")

    def test_func(self):
        return self.get_object().user == self.request.user


class ShippingAddressDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour supprimer une adresse de livraison
    """

    model = ShippingAddress
    success_url = reverse_lazy("orders:shipping_address_list")

    def test_func(self):
        return self.get_object().user == self.request.user


# Vues pour les vendeurs et administrateurs
class VendorOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Vue pour lister les commandes d'un vendeur
    """

    model = Order
    template_name = "orders/vendor_order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def test_func(self):
        return self.request.user.user_type == "vendeur"

    def get_queryset(self):
        # Récupérer les commandes contenant des produits du vendeur
        return (
            Order.objects.filter(items__product__vendor=self.request.user)
            .distinct()
            .order_by("-created_at")
        )


class AdminOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Vue pour lister toutes les commandes (admin)
    """

    model = Order
    template_name = "orders/admin_order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = Order.objects.all().order_by("-created_at")

        # Filtres
        search_form = OrderSearchForm(self.request.GET)
        if search_form.is_valid():
            query = search_form.cleaned_data.get("query")
            status = search_form.cleaned_data.get("status")
            date_from = search_form.cleaned_data.get("date_from")
            date_to = search_form.cleaned_data.get("date_to")

            if query:
                queryset = queryset.filter(
                    Q(order_number__icontains=query)
                    | Q(user__username__icontains=query)
                    | Q(user__email__icontains=query)
                    | Q(shipping_first_name__icontains=query)
                    | Q(shipping_last_name__icontains=query)
                )

            if status:
                queryset = queryset.filter(status=status)

            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)

            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = OrderSearchForm(self.request.GET)
        return context


class OrderStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour mettre à jour le statut d'une commande
    """

    model = Order
    form_class = OrderStatusUpdateForm
    template_name = "orders/order_status_update.html"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"

    def test_func(self):
        order = self.get_object()
        return self.request.user.is_staff or (
            self.request.user.user_type == "vendeur"
            and order.items.filter(product__vendor=self.request.user).exists()
        )

    def form_valid(self, form):
        order = self.get_object()
        old_status = order.status
        new_status = form.cleaned_data["status"]
        notes = form.cleaned_data.get("notes", "")

        order.status = new_status

        # Mettre à jour les dates selon le statut
        if new_status == "shipped" and not order.shipped_at:
            order.shipped_at = timezone.now()
        elif new_status == "delivered" and not order.delivered_at:
            order.delivered_at = timezone.now()

        order.save()

        # Créer l'historique de statut
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes or f"Statut changé de {old_status} à {new_status}",
            created_by=self.request.user,
        )

        # Envoyer un email de notification
        # send_order_status_update_email(order, old_status, new_status)

        # Si la commande est livrée, envoyer un email de confirmation de livraison
        # if new_status == 'delivered':
        #     send_delivery_confirmation_email(order)

        messages.success(self.request, _("Le statut de la commande a été mis à jour."))
        return redirect("orders:order_detail", order_number=order.order_number)

    def send_status_notification_email(self, order, new_status):
        """Envoie un email de notification de changement de statut"""
        status_messages = {
            "confirmed": "Votre commande a été confirmée.",
            "processing": "Votre commande est en cours de traitement.",
            "shipped": "Votre commande a été expédiée.",
            "delivered": "Votre commande a été livrée.",
            "cancelled": "Votre commande a été annulée.",
        }

        if new_status in status_messages:
            subject = f"Mise à jour de votre commande {order.order_number}"
            message = f"""
            Bonjour {order.shipping_first_name},

            {status_messages[new_status]}

            Numéro de commande: {order.order_number}
            Nouveau statut: {order.get_status_display()}

            Vous pouvez suivre votre commande en cliquant sur le lien suivant:
            {self.request.build_absolute_uri(reverse('orders:order_detail', kwargs={'order_number': order.order_number}))}

            Cordialement,
            L'équipe e-commerce
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=False,
            )


@login_required
def order_statistics(request):
    """
    Vue pour les statistiques des commandes
    """
    if not request.user.is_staff:
        messages.error(request, _("Accès non autorisé."))
        return redirect("products:home")

    # Statistiques générales
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status="pending").count()
    completed_orders = Order.objects.filter(status="delivered").count()
    total_revenue = (
        Order.objects.filter(status="delivered").aggregate(total=Sum("total_amount"))[
            "total"
        ]
        or 0
    )

    # Statistiques par mois (derniers 12 mois)
    from django.db.models.functions import TruncMonth

    monthly_stats = (
        Order.objects.filter(
            status="delivered",
            created_at__gte=timezone.now() - timezone.timedelta(days=365),
        )
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"), revenue=Sum("total_amount"))
        .order_by("month")
    )

    context = {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "total_revenue": total_revenue,
        "monthly_stats": monthly_stats,
    }

    return render(request, "orders/order_statistics.html", context)
