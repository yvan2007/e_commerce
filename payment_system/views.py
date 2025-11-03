import hashlib
import hmac
import json
import logging
import time
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.models import User
from orders.models import Order

from .models import (
    BankCard,
    MobileMoneyAccount,
    PaymentMethod,
    PaymentTransaction,
    RefundRequest,
)

logger = logging.getLogger(__name__)


class PaymentMethodListView(ListView):
    """Vue pour lister les méthodes de paiement disponibles"""

    model = PaymentMethod
    template_name = "payment_system/payment_methods.html"
    context_object_name = "payment_methods"

    def get_queryset(self):
        return PaymentMethod.objects.filter(is_active=True).order_by("name")


class PaymentMethodDetailView(DetailView):
    """Vue pour afficher les détails d'une méthode de paiement"""

    model = PaymentMethod
    template_name = "payment_system/payment_method_detail.html"
    context_object_name = "payment_method"


@login_required
def initiate_payment(request, order_id):
    """Initier un paiement pour une commande"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != "pending":
        messages.error(request, "Cette commande ne peut pas être payée.")
        return redirect("orders:order_detail", order_id=order_id)

    if request.method == "POST":
        payment_method_id = request.POST.get("payment_method")
        payment_method = get_object_or_404(
            PaymentMethod, id=payment_method_id, is_active=True
        )

        try:
            with transaction.atomic():
                # Créer la transaction de paiement
                payment_transaction = PaymentTransaction.objects.create(
                    order=order,
                    user=request.user,
                    payment_method=payment_method,
                    amount=order.total_amount,
                    currency="XOF",
                    status="pending",
                )

                # Initier le paiement selon la méthode choisie
                if payment_method.name.lower() == "wave":
                    return initiate_wave_payment(request, payment_transaction)
                elif payment_method.name.lower() == "orange money":
                    return initiate_orange_money_payment(request, payment_transaction)
                elif payment_method.name.lower() == "mtn money":
                    return initiate_mtn_money_payment(request, payment_transaction)
                elif payment_method.name.lower() == "moov money":
                    return initiate_moov_money_payment(request, payment_transaction)
                else:
                    # Paiement par carte bancaire ou autre
                    return initiate_card_payment(request, payment_transaction)

        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du paiement: {e}")
            messages.error(
                request, "Une erreur est survenue lors de l'initiation du paiement."
            )
            return redirect("orders:order_detail", order_id=order_id)

    # Afficher le formulaire de sélection de méthode de paiement
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    context = {
        "order": order,
        "payment_methods": payment_methods,
    }
    return render(request, "payment_system/initiate_payment.html", context)


def initiate_wave_payment(request, payment_transaction):
    """Initier un paiement Wave"""
    try:
        # Configuration Wave (à adapter selon l'API réelle)
        wave_config = {
            "merchant_id": getattr(settings, "WAVE_MERCHANT_ID", ""),
            "api_key": getattr(settings, "WAVE_API_KEY", ""),
            "callback_url": request.build_absolute_uri(
                reverse_lazy("payment_system:payment_callback")
            ),
            "return_url": request.build_absolute_uri(
                reverse_lazy("payment_system:payment_success")
            ),
        }

        # Simuler l'enregistrement Wave
        payment_transaction.external_transaction_id = (
            f"WAVE_{payment_transaction.id}_{int(time.time())}"
        )
        payment_transaction.save()

        # Simuler l'appel API Wave (à remplacer par l'API réelle)
        payment_url = f"https://wave.com/pay?amount={payment_transaction.amount}&ref={payment_transaction.external_transaction_id}"

        # En production, rediriger vers l'URL de paiement Wave
        return redirect(payment_url)

    except Exception as e:
        logger.error(f"Erreur Wave payment: {e}")
        messages.error(request, "Erreur lors de l'initiation du paiement Wave.")
        return redirect("orders:order_detail", order_id=payment_transaction.order.id)


def initiate_orange_money_payment(request, payment_transaction):
    """Initier un paiement Orange Money"""
    try:
        # Configuration Orange Money
        orange_config = {
            "merchant_id": getattr(settings, "ORANGE_MERCHANT_ID", ""),
            "api_key": getattr(settings, "ORANGE_API_KEY", ""),
            "callback_url": request.build_absolute_uri(
                reverse_lazy("payment_system:payment_callback")
            ),
        }

        # Simuler l'enregistrement Orange Money
        payment_transaction.external_transaction_id = (
            f"ORANGE_{payment_transaction.id}_{int(time.time())}"
        )
        payment_transaction.save()

        # Simuler l'appel API Orange Money
        payment_url = f"https://api.orange.com/orange-money-webpay/ci/v1/webpayment?amount={payment_transaction.amount}&ref={payment_transaction.external_transaction_id}"

        return redirect(payment_url)

    except Exception as e:
        logger.error(f"Erreur Orange Money payment: {e}")
        messages.error(request, "Erreur lors de l'initiation du paiement Orange Money.")
        return redirect("orders:order_detail", order_id=payment_transaction.order.id)


def initiate_mtn_money_payment(request, payment_transaction):
    """Initier un paiement MTN Money"""
    try:
        # Configuration MTN Money
        mtn_config = {
            "merchant_id": getattr(settings, "MTN_MERCHANT_ID", ""),
            "api_key": getattr(settings, "MTN_API_KEY", ""),
            "callback_url": request.build_absolute_uri(
                reverse_lazy("payment_system:payment_callback")
            ),
        }

        # Simuler l'enregistrement MTN Money
        payment_transaction.external_transaction_id = (
            f"MTN_{payment_transaction.id}_{int(time.time())}"
        )
        payment_transaction.save()

        # Simuler l'appel API MTN Money
        payment_url = f"https://api.mtn.com/momo/ci/v1/requesttopay?amount={payment_transaction.amount}&ref={payment_transaction.external_transaction_id}"

        return redirect(payment_url)

    except Exception as e:
        logger.error(f"Erreur MTN Money payment: {e}")
        messages.error(request, "Erreur lors de l'initiation du paiement MTN Money.")
        return redirect("orders:order_detail", order_id=payment_transaction.order.id)


def initiate_moov_money_payment(request, payment_transaction):
    """Initier un paiement Moov Money"""
    try:
        # Configuration Moov Money
        moov_config = {
            "merchant_id": getattr(settings, "MOOV_MERCHANT_ID", ""),
            "api_key": getattr(settings, "MOOV_API_KEY", ""),
            "callback_url": request.build_absolute_uri(
                reverse_lazy("payment_system:payment_callback")
            ),
        }

        # Simuler l'enregistrement Moov Money
        payment_transaction.external_transaction_id = (
            f"MOOV_{payment_transaction.id}_{int(time.time())}"
        )
        payment_transaction.save()

        # Simuler l'appel API Moov Money
        payment_url = f"https://api.moov.ci/payment?amount={payment_transaction.amount}&ref={payment_transaction.external_transaction_id}"

        return redirect(payment_url)

    except Exception as e:
        logger.error(f"Erreur Moov Money payment: {e}")
        messages.error(request, "Erreur lors de l'initiation du paiement Moov Money.")
        return redirect("orders:order_detail", order_id=payment_transaction.order.id)


def initiate_card_payment(request, payment_transaction):
    """Initier un paiement par carte bancaire"""
    try:
        # Configuration pour les cartes bancaires
        # Ici vous pouvez intégrer Stripe, PayPal, ou autre processeur de paiement

        # Simuler le paiement par carte
        payment_transaction.status = "processing"
        payment_transaction.save()

        # En production, rediriger vers le processeur de paiement
        messages.info(request, "Redirection vers le processeur de paiement...")
        return redirect(
            "payment_system:payment_success", transaction_id=payment_transaction.id
        )

    except Exception as e:
        logger.error(f"Erreur card payment: {e}")
        messages.error(request, "Erreur lors de l'initiation du paiement par carte.")
        return redirect("orders:order_detail", order_id=payment_transaction.order.id)


@csrf_exempt
@require_http_methods(["POST"])
def payment_callback(request):
    """Webhook pour recevoir les callbacks de paiement"""
    try:
        # Récupérer les données du callback
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST

        # Vérifier la signature du webhook (sécurité)
        signature = request.headers.get("X-Webhook-Signature", "")
        if not verify_webhook_signature(request.body, signature):
            logger.warning("Signature webhook invalide")
            return HttpResponse(status=400)

        # Traiter le callback selon le fournisseur
        provider = data.get("provider", "").lower()

        if provider == "wave":
            return handle_wave_callback(data)
        elif provider == "orange":
            return handle_orange_callback(data)
        elif provider == "mtn":
            return handle_mtn_callback(data)
        elif provider == "moov":
            return handle_moov_callback(data)
        else:
            return handle_generic_callback(data)

    except Exception as e:
        logger.error(f"Erreur dans payment_callback: {e}")
        return HttpResponse(status=500)


def verify_webhook_signature(payload, signature):
    """Vérifier la signature du webhook"""
    # Implémentation de la vérification de signature
    # À adapter selon le fournisseur de paiement
    return True  # Placeholder


def handle_wave_callback(data):
    """Traiter le callback Wave"""
    try:
        transaction_id = data.get("transaction_id")
        status = data.get("status")

        payment_transaction = PaymentTransaction.objects.get(
            external_transaction_id=transaction_id
        )
        payment_transaction.status = "completed" if status == "success" else "failed"
        payment_transaction.save()

        # Mettre à jour la commande
        if status == "success":
            payment_transaction.order.status = "confirmed"
            payment_transaction.order.save()

        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Erreur handle_wave_callback: {e}")
        return HttpResponse(status=500)


def handle_orange_callback(data):
    """Traiter le callback Orange Money"""
    try:
        transaction_id = data.get("transaction_id")
        status = data.get("status")

        payment_transaction = PaymentTransaction.objects.get(
            external_transaction_id=transaction_id
        )
        payment_transaction.status = "completed" if status == "success" else "failed"
        payment_transaction.save()

        if status == "success":
            payment_transaction.order.status = "confirmed"
            payment_transaction.order.save()

        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Erreur handle_orange_callback: {e}")
        return HttpResponse(status=500)


def handle_mtn_callback(data):
    """Traiter le callback MTN Money"""
    try:
        transaction_id = data.get("transaction_id")
        status = data.get("status")

        payment_transaction = PaymentTransaction.objects.get(
            external_transaction_id=transaction_id
        )
        payment_transaction.status = "completed" if status == "success" else "failed"
        payment_transaction.save()

        if status == "success":
            payment_transaction.order.status = "confirmed"
            payment_transaction.order.save()

        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Erreur handle_mtn_callback: {e}")
        return HttpResponse(status=500)


def handle_moov_callback(data):
    """Traiter le callback Moov Money"""
    try:
        transaction_id = data.get("transaction_id")
        status = data.get("status")

        payment_transaction = PaymentTransaction.objects.get(
            external_transaction_id=transaction_id
        )
        payment_transaction.status = "completed" if status == "success" else "failed"
        payment_transaction.save()

        if status == "success":
            payment_transaction.order.status = "confirmed"
            payment_transaction.order.save()

        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Erreur handle_moov_callback: {e}")
        return HttpResponse(status=500)


def handle_generic_callback(data):
    """Traiter les callbacks génériques"""
    try:
        transaction_id = data.get("transaction_id")
        status = data.get("status")

        payment_transaction = PaymentTransaction.objects.get(
            transaction_id=transaction_id
        )
        payment_transaction.status = "completed" if status == "success" else "failed"
        payment_transaction.save()

        if status == "success":
            payment_transaction.order.status = "paid"
            payment_transaction.order.save()

        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Erreur handle_generic_callback: {e}")
        return HttpResponse(status=500)


def payment_success(request, transaction_id):
    """Page de succès du paiement"""
    payment_transaction = get_object_or_404(PaymentTransaction, id=transaction_id)

    context = {
        "payment_transaction": payment_transaction,
        "order": payment_transaction.order,
    }
    return render(request, "payment_system/payment_success.html", context)


def payment_failure(request, transaction_id):
    """Page d'échec du paiement"""
    payment_transaction = get_object_or_404(PaymentTransaction, id=transaction_id)

    context = {
        "payment_transaction": payment_transaction,
        "order": payment_transaction.order,
    }
    return render(request, "payment_system/payment_failure.html", context)


@login_required
def payment_history(request):
    """Historique des paiements de l'utilisateur"""
    payments = PaymentTransaction.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    context = {
        "payments": payments,
    }
    return render(request, "payment_system/payment_history.html", context)


@login_required
def payment_detail(request, transaction_id):
    """Détails d'une transaction de paiement"""
    payment_transaction = get_object_or_404(
        PaymentTransaction, id=transaction_id, user=request.user
    )

    context = {
        "payment_transaction": payment_transaction,
    }
    return render(request, "payment_system/payment_detail.html", context)


@login_required
def request_refund(request, transaction_id):
    """Demander un remboursement"""
    payment_transaction = get_object_or_404(
        PaymentTransaction, id=transaction_id, user=request.user
    )

    if payment_transaction.status != "completed":
        messages.error(request, "Seuls les paiements réussis peuvent être remboursés.")
        return redirect("payment_system:payment_detail", transaction_id=transaction_id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        amount = request.POST.get("amount")

        try:
            refund = RefundRequest.objects.create(
                transaction=payment_transaction,
                user=request.user,
                reason=reason,
                description=reason,
                status="pending",
            )

            messages.success(request, "Demande de remboursement soumise avec succès.")
            return redirect(
                "payment_system:payment_detail", transaction_id=transaction_id
            )

        except Exception as e:
            logger.error(f"Erreur lors de la demande de remboursement: {e}")
            messages.error(
                request, "Erreur lors de la soumission de la demande de remboursement."
            )

    context = {
        "payment_transaction": payment_transaction,
    }
    return render(request, "payment_system/request_refund.html", context)


@login_required
def webhook_handler(request):
    """Gestionnaire de webhooks pour les administrateurs"""
    if not request.user.is_staff:
        return HttpResponse(status=403)

    # Récupérer les transactions récentes comme webhooks
    webhooks = PaymentTransaction.objects.all().order_by("-created_at")[:50]

    context = {
        "webhooks": webhooks,
    }
    return render(request, "payment_system/webhook_handler.html", context)
