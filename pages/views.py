import json

from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView


class ContactView(TemplateView):
    template_name = "pages/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Contactez-nous"
        return context

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # AJAX request
            try:
                send_mail(
                    subject=f"Nouveau message de contact - {subject}",
                    message=f"De: {name} ({email})\n\n{message}",
                    from_email="noreply@kefystore.com",
                    recipient_list=["contact@kefystore.com"],
                    fail_silently=False,
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Votre message a été envoyé avec succès!",
                    }
                )
            except Exception as e:
                return JsonResponse(
                    {"success": False, "message": f"Erreur lors de l'envoi: {str(e)}"}
                )
        else:
            messages.success(request, "Votre message a été envoyé avec succès!")
            return render(request, self.template_name)


class LivraisonView(TemplateView):
    template_name = "pages/livraison.html"


class RetoursView(TemplateView):
    template_name = "pages/retours.html"


class FAQView(TemplateView):
    template_name = "pages/faq.html"


class PromotionsView(TemplateView):
    template_name = "pages/promotions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Promotions"

        # Récupérer tous les produits actuellement en promotion
        from django.db.models import Q

        from products.models import Product

        now = timezone.now()

        # Produits en promotion actuellement (is_on_sale = True et dates valides)
        products_on_sale = (
            Product.objects.filter(status="published", is_on_sale=True)
            .filter(
                Q(sale_start_date__lte=now) | Q(sale_start_date__isnull=True),
                Q(sale_end_date__gte=now) | Q(sale_end_date__isnull=True),
            )
            .select_related("category", "vendor")[:12]
        )  # Limiter à 12 produits

        context["products_on_sale"] = products_on_sale
        context["products_count"] = products_on_sale.count()

        return context
