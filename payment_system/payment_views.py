"""
Vues de paiement avec intégration des vraies APIs Mobile Money
"""
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import TemplateView

from orders.models import Order
from payment_system.hybrid_service import HybridMobileMoneyService
from payment_system.models import PaymentMethod, PaymentTransaction
from payment_system.simulator import mobile_money_simulator

logger = logging.getLogger(__name__)


class PaymentMethodListView(TemplateView):
    """
    Vue pour afficher les méthodes de paiement disponibles
    """

    template_name = "payment_system/payment_methods.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment_methods"] = PaymentMethod.objects.filter(is_active=True)
        return context


class PaymentInitiationView(TemplateView):
    """
    Vue pour initier un paiement Mobile Money
    """

    template_name = "payment_system/payment_initiation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get("order_id")
        context["order"] = get_object_or_404(Order, id=order_id, user=self.request.user)
        context["payment_methods"] = PaymentMethod.objects.filter(
            is_active=True, payment_type__in=["mobile_money", "wave"]
        )
        return context

    def post(self, request, order_id):
        """
        Traiter l'initiation du paiement
        """
        order = get_object_or_404(Order, id=order_id, user=request.user)
        provider = request.POST.get("provider")
        phone_number = request.POST.get("phone_number")

        if not provider or not phone_number:
            messages.error(
                request,
                "Veuillez sélectionner une méthode de paiement et saisir votre numéro de téléphone.",
            )
            return redirect("payment_system:payment_initiation", order_id=order_id)

        # Validation du numéro de téléphone
        if not self._validate_phone_number(phone_number):
            messages.error(
                request, "Numéro de téléphone invalide. Format attendu: +225XXXXXXXXX"
            )
            return redirect("payment_system:payment_initiation", order_id=order_id)

        # Initier le paiement
        mobile_money_service = HybridMobileMoneyService()
        payment_result = mobile_money_service.initiate_payment(
            provider=provider,
            amount=order.total_amount,
            phone_number=phone_number,
            order_id=str(order.id),
            description=f"Paiement commande #{order.id} - KefyStore",
        )

        if payment_result["success"]:
            # Créer la transaction de paiement
            payment_transaction = PaymentTransaction.objects.create(
                order=order,
                user=request.user,
                payment_method=PaymentMethod.objects.get(
                    name=f"{provider.upper()} Money"
                ),
                amount=order.total_amount,
                status="pending",
                external_transaction_id=payment_result["transaction_id"],
                metadata={
                    "provider": provider,
                    "phone_number": phone_number,
                    "payment_result": payment_result,
                },
            )

            # Mettre à jour le statut de la commande
            order.payment_status = "pending"
            order.save()

            messages.success(
                request,
                f"Paiement {provider.upper()} initié avec succès ! Vérifiez votre téléphone.",
            )

            # Rediriger vers la page de suivi
            return redirect(
                "payment_system:payment_status", transaction_id=payment_transaction.id
            )
        else:
            messages.error(
                request,
                f'Erreur lors de l\'initiation du paiement: {payment_result["error"]}',
            )
            return redirect("payment_system:payment_initiation", order_id=order_id)

    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        Valider le format du numéro de téléphone
        """
        # Format attendu: +225XXXXXXXXX ou 225XXXXXXXXX ou 0XXXXXXXXX
        cleaned = phone_number.replace(" ", "").replace("-", "")

        if cleaned.startswith("+225") and len(cleaned) == 13:
            return True
        elif cleaned.startswith("225") and len(cleaned) == 12:
            return True
        elif cleaned.startswith("0") and len(cleaned) == 10:
            return True

        return False


class PaymentStatusView(TemplateView):
    """
    Vue pour afficher le statut du paiement
    """

    template_name = "payment_system/payment_status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_id = self.kwargs.get("transaction_id")
        context["transaction"] = get_object_or_404(
            PaymentTransaction, id=transaction_id, user=self.request.user
        )
        return context


@login_required
@require_POST
def check_payment_status(request, transaction_id):
    """
    API pour vérifier le statut d'un paiement
    """
    try:
        transaction = get_object_or_404(
            PaymentTransaction, id=transaction_id, user=request.user
        )

        # Vérifier le statut avec le provider
        mobile_money_service = HybridMobileMoneyService()
        provider = transaction.metadata.get("provider", "")

        status_result = mobile_money_service.check_payment_status(
            provider=provider, transaction_id=transaction.external_transaction_id
        )

        if status_result["success"]:
            # Mettre à jour le statut de la transaction
            new_status = status_result["status"]
            transaction.status = new_status
            transaction.save()

            # Mettre à jour le statut de la commande si le paiement est confirmé
            if new_status in ["SUCCESSFUL", "completed", "success"]:
                transaction.order.payment_status = "paid"
                transaction.order.status = "confirmed"
                transaction.order.save()

                return JsonResponse(
                    {
                        "success": True,
                        "status": new_status,
                        "message": "Paiement confirmé avec succès !",
                        "redirect_url": reverse(
                            "orders:order_detail",
                            kwargs={"slug": transaction.order.order_number},
                        ),
                    }
                )
            elif new_status in ["FAILED", "failed", "error"]:
                transaction.order.payment_status = "failed"
                transaction.order.save()

                return JsonResponse(
                    {
                        "success": False,
                        "status": new_status,
                        "message": "Paiement échoué. Veuillez réessayer.",
                        "redirect_url": reverse(
                            "payment_system:payment_initiation",
                            kwargs={"order_id": transaction.order.id},
                        ),
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": True,
                        "status": new_status,
                        "message": "Paiement en cours...",
                        "redirect_url": None,
                    }
                )
        else:
            return JsonResponse({"success": False, "error": status_result["error"]})

    except Exception as e:
        logger.error(f"Erreur vérification statut paiement: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": "Erreur technique lors de la vérification du paiement",
            }
        )


@csrf_exempt
@require_POST
def payment_webhook(request, provider):
    """
    Webhook pour recevoir les notifications de paiement
    """
    try:
        # Vérifier la signature du webhook (à implémenter selon le provider)
        payload = json.loads(request.body)

        webhook_handler = PaymentWebhookHandler()
        result = webhook_handler.handle_webhook(provider, payload)

        if result["success"]:
            # Mettre à jour la transaction
            transaction_id = result["transaction_id"]
            try:
                transaction = PaymentTransaction.objects.get(
                    external_transaction_id=transaction_id
                )

                new_status = result["status"]
                transaction.status = new_status
                transaction.save()

                # Mettre à jour la commande
                if new_status in ["SUCCESSFUL", "completed", "success"]:
                    transaction.order.payment_status = "paid"
                    transaction.order.status = "confirmed"
                    transaction.order.save()

                    logger.info(
                        f"Paiement confirmé via webhook {provider}: {transaction_id}"
                    )

            except PaymentTransaction.DoesNotExist:
                logger.warning(
                    f"Transaction non trouvée pour le webhook {provider}: {transaction_id}"
                )

            return HttpResponse("OK", status=200)
        else:
            logger.error(f"Erreur webhook {provider}: {result['error']}")
            return HttpResponse("Error", status=400)

    except Exception as e:
        logger.error(f"Erreur webhook {provider}: {str(e)}")
        return HttpResponse("Error", status=500)


class PaymentSuccessView(TemplateView):
    """
    Vue de succès de paiement
    """

    template_name = "payment_system/payment_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_id = self.request.GET.get("transaction_id")
        if transaction_id:
            try:
                context["transaction"] = PaymentTransaction.objects.get(
                    id=transaction_id, user=self.request.user
                )
            except PaymentTransaction.DoesNotExist:
                pass
        return context


class PaymentFailureView(TemplateView):
    """
    Vue d'échec de paiement
    """

    template_name = "payment_system/payment_failure.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_id = self.request.GET.get("transaction_id")
        if transaction_id:
            try:
                context["transaction"] = PaymentTransaction.objects.get(
                    id=transaction_id, user=self.request.user
                )
            except PaymentTransaction.DoesNotExist:
                pass
        return context


@login_required
def payment_history(request):
    """
    Historique des paiements de l'utilisateur
    """
    transactions = PaymentTransaction.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    context = {"transactions": transactions}

    return render(request, "payment_system/payment_history.html", context)


@login_required
def payment_detail(request, transaction_id):
    """
    Détails d'une transaction de paiement
    """
    transaction = get_object_or_404(
        PaymentTransaction, id=transaction_id, user=request.user
    )

    context = {"transaction": transaction}

    return render(request, "payment_system/payment_detail.html", context)


# Vues spécifiques pour chaque provider
@csrf_exempt
@require_POST
def orange_callback(request):
    """
    Callback Orange Money
    """
    return payment_webhook(request, "orange")


@csrf_exempt
@require_POST
def wave_callback(request):
    """
    Callback Wave
    """
    return payment_webhook(request, "wave")


@csrf_exempt
@require_POST
def mtn_callback(request):
    """
    Callback MTN
    """
    return payment_webhook(request, "mtn")


@csrf_exempt
@require_POST
def moov_callback(request):
    """
    Callback Moov
    """
    return payment_webhook(request, "moov")
