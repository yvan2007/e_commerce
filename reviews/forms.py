from django import forms
from django.utils.translation import gettext_lazy as _

from .models import DeliveryProductReview, DeliveryReview, ReviewResponse


class ProductReviewForm(forms.ModelForm):
    """
    Formulaire pour créer un avis sur un produit
    """

    class Meta:
        model = DeliveryProductReview
        fields = ["rating", "title", "comment", "image_1", "image_2", "image_3"]
        widgets = {
            "rating": forms.RadioSelect(attrs={"class": "rating-input"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Donnez un titre à votre avis..."),
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Partagez votre expérience avec ce produit..."),
                }
            ),
            "image_1": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "image_2": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "image_3": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }
        labels = {
            "rating": _("Note"),
            "title": _("Titre de votre avis"),
            "comment": _("Votre commentaire"),
            "image_1": _("Photo 1 (optionnelle)"),
            "image_2": _("Photo 2 (optionnelle)"),
            "image_3": _("Photo 3 (optionnelle)"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rating"].required = True
        self.fields["title"].required = True
        self.fields["comment"].required = True


class DeliveryReviewForm(forms.ModelForm):
    """
    Formulaire pour créer un avis sur la livraison
    """

    class Meta:
        model = DeliveryReview
        fields = [
            "delivery_rating",
            "delivery_comment",
            "delivery_speed_rating",
            "packaging_rating",
            "delivery_person_rating",
        ]
        widgets = {
            "delivery_rating": forms.RadioSelect(attrs={"class": "rating-input"}),
            "delivery_speed_rating": forms.RadioSelect(attrs={"class": "rating-input"}),
            "packaging_rating": forms.RadioSelect(attrs={"class": "rating-input"}),
            "delivery_person_rating": forms.RadioSelect(
                attrs={"class": "rating-input"}
            ),
            "delivery_comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Comment s'est passée votre livraison ?"),
                }
            ),
        }
        labels = {
            "delivery_rating": _("Note générale de la livraison"),
            "delivery_comment": _("Commentaire sur la livraison"),
            "delivery_speed_rating": _("Rapidité de livraison"),
            "packaging_rating": _("Qualité de l'emballage"),
            "delivery_person_rating": _("Service du livreur"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delivery_rating"].required = True
        self.fields["delivery_speed_rating"].required = True
        self.fields["packaging_rating"].required = True
        self.fields["delivery_person_rating"].required = True


class ReviewResponseForm(forms.ModelForm):
    """
    Formulaire pour répondre à un avis (vendeurs)
    """

    class Meta:
        model = ReviewResponse
        fields = ["response_text"]
        widgets = {
            "response_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _(
                        "Répondez à cet avis de manière professionnelle..."
                    ),
                }
            ),
        }
        labels = {
            "response_text": _("Votre réponse"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["response_text"].required = True


class ReviewSearchForm(forms.Form):
    """
    Formulaire de recherche d'avis
    """

    RATING_FILTER_CHOICES = [
        ("", _("Toutes les notes")),
        ("5", _("⭐⭐⭐⭐⭐ Excellent")),
        ("4", _("⭐⭐⭐⭐ Très bien")),
        ("3", _("⭐⭐⭐ Bien")),
        ("2", _("⭐⭐ Moyen")),
        ("1", _("⭐ Décevant")),
    ]

    SORT_CHOICES = [
        ("newest", _("Plus récents")),
        ("oldest", _("Plus anciens")),
        ("highest_rating", _("Meilleures notes")),
        ("lowest_rating", _("Moins bonnes notes")),
        ("most_helpful", _("Plus utiles")),
    ]

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Rechercher dans les avis..."),
            }
        ),
        label=_("Recherche"),
    )

    rating_filter = forms.ChoiceField(
        choices=RATING_FILTER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Filtrer par note"),
    )

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Trier par"),
    )

    with_images = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Avec photos seulement"),
    )
