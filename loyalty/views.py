"""
Vues pour le système de fidélité
"""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from orders.models import Order

from .models import LoyaltyPoints, LoyaltyPointsHistory, LoyaltyReward, UserReward


class LoyaltyDashboardView(LoginRequiredMixin, ListView):
    """Vue du tableau de bord de fidélité"""

    template_name = "loyalty/dashboard.html"
    context_object_name = "rewards"

    def get_queryset(self):
        return LoyaltyReward.objects.filter(is_active=True).order_by("points_cost")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer ou créer les points de fidélité
        loyalty_points, created = LoyaltyPoints.objects.get_or_create(
            user=self.request.user
        )

        # Historique des points (30 derniers jours)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_history = LoyaltyPointsHistory.objects.filter(
            user=self.request.user, created_at__gte=thirty_days_ago
        ).order_by("-created_at")[:10]

        # Récompenses disponibles
        available_rewards = LoyaltyReward.objects.filter(
            is_active=True, points_cost__lte=loyalty_points.points
        ).order_by("points_cost")

        # Récompenses utilisées
        user_rewards = UserReward.objects.filter(user=self.request.user).order_by(
            "-used_at"
        )[:10]

        context.update(
            {
                "loyalty_points": loyalty_points,
                "recent_history": recent_history,
                "available_rewards": available_rewards,
                "user_rewards": user_rewards,
                "benefits": loyalty_points.get_level_benefits(),
            }
        )

        return context


@login_required
def claim_reward(request, reward_id):
    """Réclamer une récompense"""
    reward = get_object_or_404(LoyaltyReward, id=reward_id, is_active=True)
    loyalty_points, created = LoyaltyPoints.objects.get_or_create(user=request.user)

    if loyalty_points.points < reward.points_cost:
        messages.error(
            request, "Vous n'avez pas assez de points pour cette récompense."
        )
        return redirect("loyalty:dashboard")

    # Créer la récompense utilisateur
    user_reward = UserReward.objects.create(user=request.user, reward=reward)

    # Dépenser les points
    if loyalty_points.spend_points(reward.points_cost, f"Récompense: {reward.name}"):
        messages.success(request, f'Récompense "{reward.name}" réclamée avec succès!')
    else:
        messages.error(request, "Erreur lors de la réclamation de la récompense.")
        user_reward.delete()

    return redirect("loyalty:dashboard")


@login_required
def loyalty_history(request):
    """Historique des points de fidélité"""
    history = LoyaltyPointsHistory.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    context = {
        "history": history,
    }

    return render(request, "loyalty/history.html", context)


@login_required
def loyalty_stats_api(request):
    """API pour les statistiques de fidélité"""
    loyalty_points, created = LoyaltyPoints.objects.get_or_create(user=request.user)

    # Statistiques des 12 derniers mois
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_stats = (
        LoyaltyPointsHistory.objects.filter(
            user=request.user,
            created_at__gte=twelve_months_ago,
            points__gt=0,  # Seulement les gains
        )
        .extra(select={"month": "strftime('%%Y-%%m', created_at)"})
        .values("month")
        .annotate(total_points=Sum("points"))
        .order_by("month")
    )

    return JsonResponse(
        {
            "current_points": loyalty_points.points,
            "level": loyalty_points.level,
            "total_earned": loyalty_points.total_earned,
            "total_spent": loyalty_points.total_spent,
            "monthly_stats": list(monthly_stats),
            "benefits": loyalty_points.get_level_benefits(),
        }
    )
