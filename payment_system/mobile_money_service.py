"""
Service de paiement Mobile Money pour la Côte d'Ivoire
Intégration avec les APIs réelles : MTN, Moov, Orange Money, Wave
"""
import json
import logging
import os
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

import requests
from django.conf import settings
from django.utils import timezone
from moovio_sdk import Moov

logger = logging.getLogger(__name__)


class MobileMoneyService:
    """
    Service principal pour les paiements Mobile Money
    """

    def __init__(self):
        self.mtn_config = {
            "api_url": "https://sandbox.momodeveloper.mtn.com",
            "api_key": getattr(settings, "MTN_API_KEY", "your-mtn-api-key"),
            "subscription_key": getattr(
                settings, "MTN_SUBSCRIPTION_KEY", "your-mtn-subscription-key"
            ),
            "environment": getattr(
                settings, "MTN_ENVIRONMENT", "sandbox"
            ),  # sandbox ou production
        }

        self.moov_config = {
            "api_key": getattr(settings, "MOOV_API_KEY", "your-moov-api-key"),
            "environment": getattr(
                settings, "MOOV_ENVIRONMENT", "sandbox"
            ),  # sandbox ou production
        }

        self.orange_config = {
            "api_url": "https://api.orange.com",
            "client_id": getattr(settings, "ORANGE_CLIENT_ID", "your-orange-client-id"),
            "client_secret": getattr(
                settings, "ORANGE_CLIENT_SECRET", "your-orange-client-secret"
            ),
            "merchant_id": getattr(
                settings, "ORANGE_MERCHANT_ID", "your-orange-merchant-id"
            ),
        }

        self.wave_config = {
            "api_url": "https://api.wave.com",
            "api_key": getattr(settings, "WAVE_API_KEY", "your-wave-api-key"),
            "merchant_id": getattr(
                settings, "WAVE_MERCHANT_ID", "your-wave-merchant-id"
            ),
        }

    def initiate_payment(
        self,
        provider: str,
        amount: Decimal,
        phone_number: str,
        order_id: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Initier un paiement Mobile Money

        Args:
            provider: 'mtn', 'moov', 'orange', 'wave'
            amount: Montant à payer
            phone_number: Numéro de téléphone du client
            order_id: ID de la commande
            description: Description du paiement

        Returns:
            Dict avec le statut et les détails du paiement
        """
        try:
            if provider.lower() == "mtn":
                return self._initiate_mtn_payment(
                    amount, phone_number, order_id, description
                )
            elif provider.lower() == "moov":
                return self._initiate_moov_payment(
                    amount, phone_number, order_id, description
                )
            elif provider.lower() == "orange":
                return self._initiate_orange_payment(
                    amount, phone_number, order_id, description
                )
            elif provider.lower() == "wave":
                return self._initiate_wave_payment(
                    amount, phone_number, order_id, description
                )
            else:
                return {"success": False, "error": f"Provider {provider} non supporté"}
        except Exception as e:
            logger.error(
                f"Erreur lors de l'initiation du paiement {provider}: {str(e)}"
            )
            return {"success": False, "error": f"Erreur technique: {str(e)}"}

    def _initiate_mtn_payment(
        self, amount: Decimal, phone_number: str, order_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Initier un paiement MTN Mobile Money
        """
        try:
            # Formatage du numéro de téléphone pour MTN CI
            formatted_phone = self._format_phone_number(phone_number, "CI")

            # Préparation de la requête
            headers = {
                "Authorization": f"Bearer {self._get_mtn_token()}",
                "X-Reference-Id": order_id,
                "X-Target-Environment": self.mtn_config["environment"],
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": self.mtn_config["subscription_key"],
            }

            payload = {
                "amount": str(amount),
                "currency": "XOF",
                "externalId": order_id,
                "payer": {"partyIdType": "MSISDN", "partyId": formatted_phone},
                "payerMessage": description or f"Paiement commande #{order_id}",
                "payeeNote": f"Paiement KefyStore - Commande #{order_id}",
            }

            # Envoi de la requête
            response = requests.post(
                f"{self.mtn_config['api_url']}/collection/v1_0/requesttopay",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 202:
                return {
                    "success": True,
                    "transaction_id": order_id,
                    "status": "pending",
                    "message": "Paiement initié avec succès",
                    "provider": "MTN",
                    "phone_number": formatted_phone,
                    "amount": str(amount),
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "error": f'Erreur MTN: {error_data.get("message", "Erreur inconnue")}',
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"Erreur MTN payment: {str(e)}")
            return {"success": False, "error": f"Erreur MTN: {str(e)}"}

    def _initiate_moov_payment(
        self, amount: Decimal, phone_number: str, order_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Initier un paiement Moov Money avec le SDK officiel
        """
        try:
            # Initialisation du SDK Moov
            moov = Moov(api_key=self.moov_config["api_key"])

            # Formatage du numéro de téléphone
            formatted_phone = self._format_phone_number(phone_number, "CI")

            # Création du paiement
            payment_data = {
                "amount": {"value": str(amount), "currency": "XOF"},
                "payer": {"type": "phone", "phone": formatted_phone},
                "description": description or f"Paiement commande #{order_id}",
                "external_id": order_id,
                "metadata": {"order_id": order_id, "merchant": "KefyStore"},
            }

            # Envoi du paiement
            payment = moov.payments.create(payment_data)

            return {
                "success": True,
                "transaction_id": payment.id,
                "status": "pending",
                "message": "Paiement Moov initié avec succès",
                "provider": "Moov",
                "phone_number": formatted_phone,
                "amount": str(amount),
            }

        except Exception as e:
            logger.error(f"Erreur Moov payment: {str(e)}")
            return {"success": False, "error": f"Erreur Moov: {str(e)}"}

    def _initiate_orange_payment(
        self, amount: Decimal, phone_number: str, order_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Initier un paiement Orange Money
        """
        try:
            # Formatage du numéro de téléphone
            formatted_phone = self._format_phone_number(phone_number, "CI")

            # Obtention du token d'accès
            access_token = self._get_orange_token()

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            payload = {
                "merchant": {"id": self.orange_config["merchant_id"]},
                "order": {
                    "id": order_id,
                    "amount": str(amount),
                    "currency": "XOF",
                    "description": description or f"Paiement commande #{order_id}",
                },
                "customer": {"msisdn": formatted_phone},
                "returnUrl": f"{settings.SITE_URL}/payment/orange/callback/",
                "cancelUrl": f"{settings.SITE_URL}/payment/orange/cancel/",
            }

            response = requests.post(
                f"{self.orange_config['api_url']}/orange-money-webpay/ci/v1/webpayment",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 201:
                response_data = response.json()
                return {
                    "success": True,
                    "transaction_id": response_data.get("payToken"),
                    "status": "pending",
                    "message": "Paiement Orange Money initié avec succès",
                    "provider": "Orange",
                    "phone_number": formatted_phone,
                    "amount": str(amount),
                    "payment_url": response_data.get("paymentUrl"),
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "error": f'Erreur Orange: {error_data.get("message", "Erreur inconnue")}',
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"Erreur Orange payment: {str(e)}")
            return {"success": False, "error": f"Erreur Orange: {str(e)}"}

    def _initiate_wave_payment(
        self, amount: Decimal, phone_number: str, order_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Initier un paiement Wave
        """
        try:
            headers = {
                "Authorization": f'Bearer {self.wave_config["api_key"]}',
                "Content-Type": "application/json",
            }

            payload = {
                "amount": str(amount),
                "currency": "XOF",
                "client_reference": order_id,
                "description": description or f"Paiement commande #{order_id}",
                "customer": {"phone_number": phone_number},
                "merchant_reference": f"KefyStore-{order_id}",
                "callback_url": f"{settings.SITE_URL}/payment/wave/callback/",
                "redirect_url": f"{settings.SITE_URL}/payment/wave/redirect/",
            }

            response = requests.post(
                f"{self.wave_config['api_url']}/v1/checkout/sessions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 201:
                response_data = response.json()
                return {
                    "success": True,
                    "transaction_id": response_data.get("id"),
                    "status": "pending",
                    "message": "Paiement Wave initié avec succès",
                    "provider": "Wave",
                    "phone_number": phone_number,
                    "amount": str(amount),
                    "checkout_url": response_data.get("checkout_url"),
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "error": f'Erreur Wave: {error_data.get("message", "Erreur inconnue")}',
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"Erreur Wave payment: {str(e)}")
            return {"success": False, "error": f"Erreur Wave: {str(e)}"}

    def check_payment_status(
        self, provider: str, transaction_id: str
    ) -> Dict[str, Any]:
        """
        Vérifier le statut d'un paiement
        """
        try:
            if provider.lower() == "mtn":
                return self._check_mtn_status(transaction_id)
            elif provider.lower() == "moov":
                return self._check_moov_status(transaction_id)
            elif provider.lower() == "orange":
                return self._check_orange_status(transaction_id)
            elif provider.lower() == "wave":
                return self._check_wave_status(transaction_id)
            else:
                return {"success": False, "error": f"Provider {provider} non supporté"}
        except Exception as e:
            logger.error(
                f"Erreur lors de la vérification du statut {provider}: {str(e)}"
            )
            return {"success": False, "error": f"Erreur technique: {str(e)}"}

    def _check_mtn_status(self, transaction_id: str) -> Dict[str, Any]:
        """Vérifier le statut MTN"""
        try:
            headers = {
                "Authorization": f"Bearer {self._get_mtn_token()}",
                "X-Target-Environment": self.mtn_config["environment"],
                "Ocp-Apim-Subscription-Key": self.mtn_config["subscription_key"],
            }

            response = requests.get(
                f"{self.mtn_config['api_url']}/collection/v1_0/requesttopay/{transaction_id}",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status", "unknown"),
                    "amount": data.get("amount"),
                    "currency": data.get("currency"),
                    "payer": data.get("payer", {}),
                    "transaction_id": transaction_id,
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur lors de la vérification MTN: {response.status_code}",
                }
        except Exception as e:
            return {"success": False, "error": f"Erreur MTN status: {str(e)}"}

    def _check_moov_status(self, transaction_id: str) -> Dict[str, Any]:
        """Vérifier le statut Moov"""
        try:
            moov = Moov(api_key=self.moov_config["api_key"])

            payment = moov.payments.get(transaction_id)

            return {
                "success": True,
                "status": payment.status,
                "amount": payment.amount.value,
                "currency": payment.amount.currency,
                "transaction_id": transaction_id,
            }
        except Exception as e:
            return {"success": False, "error": f"Erreur Moov status: {str(e)}"}

    def _check_orange_status(self, transaction_id: str) -> Dict[str, Any]:
        """Vérifier le statut Orange"""
        try:
            headers = {
                "Authorization": f"Bearer {self._get_orange_token()}",
                "Accept": "application/json",
            }

            response = requests.get(
                f"{self.orange_config['api_url']}/orange-money-webpay/ci/v1/webpayment/{transaction_id}",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status", "unknown"),
                    "amount": data.get("amount"),
                    "currency": data.get("currency"),
                    "transaction_id": transaction_id,
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur lors de la vérification Orange: {response.status_code}",
                }
        except Exception as e:
            return {"success": False, "error": f"Erreur Orange status: {str(e)}"}

    def _check_wave_status(self, transaction_id: str) -> Dict[str, Any]:
        """Vérifier le statut Wave"""
        try:
            headers = {
                "Authorization": f'Bearer {self.wave_config["api_key"]}',
                "Accept": "application/json",
            }

            response = requests.get(
                f"{self.wave_config['api_url']}/v1/checkout/sessions/{transaction_id}",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status", "unknown"),
                    "amount": data.get("amount"),
                    "currency": data.get("currency"),
                    "transaction_id": transaction_id,
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur lors de la vérification Wave: {response.status_code}",
                }
        except Exception as e:
            return {"success": False, "error": f"Erreur Wave status: {str(e)}"}

    def _format_phone_number(self, phone_number: str, country_code: str = "CI") -> str:
        """
        Formater le numéro de téléphone selon le standard du pays
        """
        # Nettoyer le numéro
        cleaned = phone_number.replace(" ", "").replace("-", "").replace("+", "")

        # Ajouter le code pays si nécessaire
        if country_code == "CI":
            if cleaned.startswith("225"):
                return cleaned
            elif cleaned.startswith("0"):
                return "225" + cleaned[1:]
            else:
                return "225" + cleaned

        return cleaned

    def _get_mtn_token(self) -> str:
        """
        Obtenir le token d'accès MTN
        """
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.mtn_config["subscription_key"]}

            response = requests.post(
                f"{self.mtn_config['api_url']}/collection/token/",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json().get("access_token", "")
            else:
                logger.error(f"Erreur obtention token MTN: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Erreur token MTN: {str(e)}")
            return ""

    def _get_orange_token(self) -> str:
        """
        Obtenir le token d'accès Orange
        """
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            data = {
                "grant_type": "client_credentials",
                "client_id": self.orange_config["client_id"],
                "client_secret": self.orange_config["client_secret"],
            }

            response = requests.post(
                f"{self.orange_config['api_url']}/oauth/v2/token",
                headers=headers,
                data=data,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json().get("access_token", "")
            else:
                logger.error(f"Erreur obtention token Orange: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Erreur token Orange: {str(e)}")
            return ""


class PaymentWebhookHandler:
    """
    Gestionnaire des webhooks de paiement
    """

    def __init__(self):
        self.mobile_money_service = MobileMoneyService()

    def handle_webhook(self, provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traiter un webhook de paiement
        """
        try:
            if provider.lower() == "mtn":
                return self._handle_mtn_webhook(payload)
            elif provider.lower() == "moov":
                return self._handle_moov_webhook(payload)
            elif provider.lower() == "orange":
                return self._handle_orange_webhook(payload)
            elif provider.lower() == "wave":
                return self._handle_wave_webhook(payload)
            else:
                return {"success": False, "error": f"Provider {provider} non supporté"}
        except Exception as e:
            logger.error(f"Erreur webhook {provider}: {str(e)}")
            return {"success": False, "error": f"Erreur technique: {str(e)}"}

    def _handle_mtn_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter webhook MTN"""
        # Logique de traitement du webhook MTN
        return {
            "success": True,
            "message": "Webhook MTN traité avec succès",
            "transaction_id": payload.get("externalId"),
            "status": payload.get("status"),
        }

    def _handle_moov_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter webhook Moov"""
        # Logique de traitement du webhook Moov
        return {
            "success": True,
            "message": "Webhook Moov traité avec succès",
            "transaction_id": payload.get("id"),
            "status": payload.get("status"),
        }

    def _handle_orange_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter webhook Orange"""
        # Logique de traitement du webhook Orange
        return {
            "success": True,
            "message": "Webhook Orange traité avec succès",
            "transaction_id": payload.get("payToken"),
            "status": payload.get("status"),
        }

    def _handle_wave_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter webhook Wave"""
        # Logique de traitement du webhook Wave
        return {
            "success": True,
            "message": "Webhook Wave traité avec succès",
            "transaction_id": payload.get("id"),
            "status": payload.get("status"),
        }
