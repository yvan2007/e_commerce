import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from delivery_system.models import City, Region
from delivery_system.services import DeliveryService


@require_http_methods(["GET"])
def get_regions(request):
    """API pour obtenir toutes les régions"""
    regions = DeliveryService.get_all_regions()
    regions_data = [
        {"id": region.id, "name": region.name, "code": region.code}
        for region in regions
    ]
    return JsonResponse({"regions": regions_data})


@require_http_methods(["GET"])
def get_cities(request, region_id):
    """API pour obtenir toutes les villes d'une région"""
    cities = DeliveryService.get_cities_by_region(region_id)
    cities_data = [
        {"id": city.id, "name": city.name, "postal_code": city.postal_code or ""}
        for city in cities
    ]
    return JsonResponse({"cities": cities_data})


@require_http_methods(["POST"])
@login_required
def calculate_delivery_fee(request):
    """API pour calculer les frais de livraison"""
    from decimal import Decimal

    try:
        data = json.loads(request.body)
        city = data.get("city", "")
        country = data.get("country", "Côte d'Ivoire")

        # Tarifs de livraison pour les pays hors Côte d'Ivoire
        country_delivery_fees = {
            # Pays proches : 10 000 FCFA
            "Mali": Decimal("10000"),
            "Burkina Faso": Decimal("10000"),
            "Sénégal": Decimal("10000"),
            "Guinée": Decimal("10000"),
            # Pays un peu plus éloignés : 15 000 FCFA
            "Ghana": Decimal("15000"),
            "Togo": Decimal("15000"),
            "Bénin": Decimal("15000"),
            "Niger": Decimal("15000"),
            "Nigeria": Decimal("15000"),
            "Cameroun": Decimal("15000"),
            "Congo": Decimal("15000"),
            "Gabon": Decimal("15000"),
            "Tchad": Decimal("15000"),
            "RCA": Decimal("15000"),
            "Tunisie": Decimal("15000"),
            "Maroc": Decimal("15000"),
            "Algérie": Decimal("15000"),
            "France": Decimal("15000"),
            "Belgique": Decimal("15000"),
        }

        # Si c'est hors Côte d'Ivoire, utiliser les tarifs fixes
        if country in country_delivery_fees:
            from datetime import datetime, timedelta

            fee = country_delivery_fees[country]
            estimated_days = 7 if fee == Decimal("10000") else 10

            return JsonResponse(
                {
                    "success": True,
                    "fee": str(fee),
                    "estimated_days": estimated_days,
                    "estimated_date": (
                        datetime.now() + timedelta(days=estimated_days)
                    ).strftime("%Y-%m-%d"),
                }
            )

        # Pour la Côte d'Ivoire, la ville est requise
        if not city:
            return JsonResponse(
                {"error": "Ville requise pour la Côte d'Ivoire"}, status=400
            )

        # Pour la Côte d'Ivoire, utiliser le service DeliveryService
        from datetime import datetime, timedelta

        from delivery_system.services import DeliveryService

        try:
            delivery_info = DeliveryService.calculate_delivery_fee(city, country)

            return JsonResponse(
                {
                    "success": True,
                    "fee": str(delivery_info["fee"]),
                    "estimated_days": delivery_info["estimated_days"],
                    "estimated_date": delivery_info["estimated_date"].strftime(
                        "%Y-%m-%d"
                    ),
                }
            )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Erreur calcul livraison: {e}")

            # Fallback avec un tarif par défaut
            return JsonResponse(
                {
                    "success": True,
                    "fee": "4500",
                    "estimated_days": 5,
                    "estimated_date": (datetime.now() + timedelta(days=5)).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_country_delivery_methods(request):
    """API pour obtenir les méthodes de paiement disponibles selon le pays"""
    country = request.GET.get("country", "Côte d'Ivoire")

    # Méthodes de paiement disponibles par pays
    methods = []

    if country == "Côte d'Ivoire":
        methods = [
            {"value": "cash", "label": "Paiement à la livraison"},
            {"value": "moovmoney", "label": "Moov Money"},
            {"value": "orangemoney", "label": "Orange Money"},
            {"value": "mtnmoney", "label": "MTN Money"},
            {"value": "wave", "label": "Wave"},
            {"value": "carte", "label": "Carte bancaire"},
        ]
    else:
        # Pour les autres pays, pas de paiement à la livraison
        methods = [
            {"value": "carte", "label": "Carte bancaire"},
            {"value": "paypal", "label": "PayPal"},
            {"value": "bank_transfer", "label": "Virement bancaire"},
        ]

    return JsonResponse({"methods": methods})


@require_http_methods(["GET"])
def get_payment_method_logo(request, method):
    """API pour obtenir le chemin du logo d'une méthode de paiement"""
    logos = {
        "cash": "/static/images/payment/livraison.png",
        "moovmoney": "/static/images/payment/moov-money.png",
        "orangemoney": "/static/images/payment/orange-money.png",
        "mtnmoney": "/static/images/payment/mtn-money.png",
        "wave": "/static/images/payment/wave.png",
        "carte": "/static/images/payment/carte-bancaire.png",
        "paypal": "/static/images/payment/paypal.png",
        "bank_transfer": "/static/images/payment/bank.png",
    }

    logo_path = logos.get(method, "/static/images/payment/default.png")
    return JsonResponse({"logo": logo_path})


@require_http_methods(["POST"])
@login_required
def update_cart_totals(request):
    """API pour mettre à jour les totaux du panier"""
    try:
        from .models import Cart

        cart = request.user.cart
        cart_total = cart.get_total_price()
        cart_count = cart.get_total_items()

        return JsonResponse(
            {"success": True, "cart_total": str(cart_total), "cart_count": cart_count}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def update_cart_item_ajax(request, item_id):
    """API pour mettre à jour la quantité d'un article dans le panier"""
    from .models import Cart, CartItem

    try:
        data = json.loads(request.body)
        quantity = int(data.get("quantity", 1))

        # Vérifier que le panier existe
        cart = request.user.cart
        cart_item = cart.items.get(id=item_id)

        # Mettre à jour la quantité
        cart_item.quantity = quantity
        cart_item.save()

        # Recalculer les totaux
        cart_total = cart.get_total_price()
        cart_count = cart.get_total_items()

        return JsonResponse(
            {
                "success": True,
                "subtotal": str(cart_item.get_total_price()),
                "total": str(cart_total),
                "cart_count": cart_count,
            }
        )

    except Cart.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Panier introuvable"}, status=404
        )
    except CartItem.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Article introuvable"}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def remove_cart_item_ajax(request, item_id):
    """API pour supprimer un article du panier"""
    from .models import Cart, CartItem

    try:
        # Vérifier que le panier existe
        cart = request.user.cart
        cart_item = cart.items.get(id=item_id)

        # Supprimer l'article
        cart_item.delete()

        # Recalculer les totaux
        cart_total = cart.get_total_price()
        cart_count = cart.get_total_items()

        return JsonResponse(
            {"success": True, "total": str(cart_total), "cart_count": cart_count}
        )

    except Cart.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Panier introuvable"}, status=404
        )
    except CartItem.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Article introuvable"}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def create_order_ajax(request):
    """API pour créer une commande via AJAX"""
    from decimal import Decimal

    from django.db import transaction
    from django.utils import timezone

    from notifications.services import EmailService

    from .forms import CheckoutForm
    from .models import Cart, Order, OrderItem, OrderStatusHistory

    try:
        # Parser les données JSON
        data = json.loads(request.body)

        # Créer le formulaire avec les données
        form_data = data.copy()
        form_data["user"] = request.user

        # Créer une instance de formulaire
        form = CheckoutForm(form_data)

        if not form.is_valid():
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

        # Vérifier le panier
        try:
            cart = request.user.cart
            cart_items = cart.items.select_related("product", "variant").all()
        except Cart.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Votre panier est vide."}, status=400
            )

        if not cart_items:
            return JsonResponse(
                {"success": False, "error": "Votre panier est vide."}, status=400
            )

        # Calculer les totaux
        subtotal = sum(item.get_total_price() for item in cart_items)

        # Récupérer les frais de livraison depuis le formulaire
        calculated_delivery_fee = form.cleaned_data.get(
            "calculated_delivery_fee", Decimal("0.00")
        )

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
                user=request.user,
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
                created_by=request.user,
            )

        # Envoyer l'email de confirmation
        try:
            EmailService.send_order_confirmation_email(order)
        except:
            pass  # Ne pas bloquer la commande si l'email échoue

        return JsonResponse(
            {
                "success": True,
                "order_number": order.order_number,
                "order_id": order.id,
                "message": "Votre commande a été passée avec succès!",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def cancel_order_ajax(request, order_number):
    """API pour annuler une commande via AJAX"""
    from .models import Order, OrderStatusHistory

    try:
        order = Order.objects.get(order_number=order_number, user=request.user)

        # Vérifier si la commande peut être annulée
        if not order.can_be_cancelled():
            return JsonResponse(
                {"success": False, "error": "Cette commande ne peut pas être annulée."},
                status=400,
            )

        # Annuler la commande
        order.status = "cancelled"
        order.save()

        # Créer l'historique de statut
        OrderStatusHistory.objects.create(
            order=order,
            status="cancelled",
            notes="Commande annulée par le client",
            created_by=request.user,
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

        return JsonResponse(
            {
                "success": True,
                "message": "Votre commande a été annulée.",
                "status": order.status,
            }
        )

    except Order.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Commande introuvable."}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
