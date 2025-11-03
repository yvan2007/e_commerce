"""
Service de simulation des paiements Mobile Money pour les tests
"""
import random
import time
from decimal import Decimal
from typing import Any, Dict

from django.utils import timezone


class MobileMoneySimulator:
    """
    Simulateur de paiements Mobile Money pour les tests
    """

    def __init__(self):
        self.simulated_transactions = {}

    def simulate_payment(
        self,
        provider: str,
        amount: Decimal,
        phone_number: str,
        order_id: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Simuler un paiement Mobile Money
        """
        transaction_id = f"SIM_{provider.upper()}_{order_id}_{int(time.time())}"

        # Simuler différents scénarios
        success_rate = 0.8  # 80% de succès
        is_successful = random.random() < success_rate

        if is_successful:
            status = "pending"
            message = f"Paiement {provider.upper()} initié avec succès ! Vérifiez votre téléphone."
        else:
            status = "failed"
            message = f"Erreur lors de l'initiation du paiement {provider.upper()}. Veuillez réessayer."

        # Stocker la transaction simulée
        self.simulated_transactions[transaction_id] = {
            "provider": provider,
            "amount": str(amount),
            "phone_number": phone_number,
            "order_id": order_id,
            "status": status,
            "created_at": timezone.now(),
            "description": description,
        }

        return {
            "success": is_successful,
            "transaction_id": transaction_id,
            "status": status,
            "message": message,
            "provider": provider.upper(),
            "phone_number": phone_number,
            "amount": str(amount),
            "simulation": True,
        }

    def simulate_status_check(
        self, provider: str, transaction_id: str
    ) -> Dict[str, Any]:
        """
        Simuler la vérification du statut
        """
        if transaction_id not in self.simulated_transactions:
            return {"success": False, "error": "Transaction non trouvée"}

        transaction = self.simulated_transactions[transaction_id]

        # Simuler l'évolution du statut
        current_status = transaction["status"]

        if current_status == "pending":
            # Après 30 secondes, passer à 'successful' ou 'failed'
            time_elapsed = (timezone.now() - transaction["created_at"]).total_seconds()

            if time_elapsed > 30:
                # Simuler 90% de succès
                if random.random() < 0.9:
                    transaction["status"] = "successful"
                    status = "successful"
                else:
                    transaction["status"] = "failed"
                    status = "failed"
            else:
                status = "pending"
        else:
            status = current_status

        return {
            "success": True,
            "status": status,
            "amount": transaction["amount"],
            "currency": "XOF",
            "transaction_id": transaction_id,
            "simulation": True,
        }

    def simulate_webhook(self, provider: str, transaction_id: str) -> Dict[str, Any]:
        """
        Simuler un webhook de paiement
        """
        if transaction_id not in self.simulated_transactions:
            return {"success": False, "error": "Transaction non trouvée"}

        transaction = self.simulated_transactions[transaction_id]

        # Simuler la notification de paiement réussi
        if transaction["status"] == "pending":
            transaction["status"] = "successful"

        return {
            "success": True,
            "message": f"Webhook {provider.upper()} simulé avec succès",
            "transaction_id": transaction_id,
            "status": transaction["status"],
            "simulation": True,
        }


# Instance globale du simulateur
mobile_money_simulator = MobileMoneySimulator()
