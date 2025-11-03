"""
Commande pour créer des popups par défaut pour KefyStore
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from popups.models import (
    AgeVerification,
    CookieConsent,
    Popup,
    PrivacyPolicy,
    TermsOfService,
)


class Command(BaseCommand):
    help = "Créer des popups et configurations par défaut pour KefyStore"

    def handle(self, *args, **options):
        # Supprimer les anciens popups
        Popup.objects.all().delete()

        # 1. Popup de bienvenue
        Popup.objects.create(
            name="Bienvenue KefyStore",
            popup_type="welcome",
            title="Bienvenue sur KefyStore ! 🛍️",
            content="Découvrez notre sélection de produits de qualité à des prix imbattables. Livraison rapide et sécurisée partout en Côte d'Ivoire.",
            button_text="Commencer mes achats",
            button_url="/products/",
            trigger_type="delay",
            trigger_delay=3,
            show_to_authenticated=True,
            show_to_anonymous=True,
            user_types=[],
            pages=[],
            background_color="#ffffff",
            text_color="#333333",
            button_color="#667eea",
            overlay_opacity=0.5,
            is_active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )

        # 2. Popup de newsletter
        Popup.objects.create(
            name="Newsletter KefyStore",
            popup_type="newsletter",
            title="Restez informé ! 📧",
            content="Abonnez-vous à notre newsletter et recevez 10% de réduction sur votre première commande. Offres exclusives et nouveautés en avant-première !",
            button_text="S'abonner",
            button_url="/newsletter/",
            trigger_type="scroll",
            trigger_scroll=70,
            show_to_authenticated=True,
            show_to_anonymous=True,
            user_types=[],
            pages=[],
            background_color="#f8f9fa",
            text_color="#333333",
            button_color="#28a745",
            overlay_opacity=0.6,
            is_active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=60),
        )

        # 3. Popup de promotion
        Popup.objects.create(
            name="Promotion Flash",
            popup_type="promotion",
            title="Promotion Flash ! ⚡",
            content="Profitez de -20% sur tous les produits électroniques. Offre valable jusqu'à la fin de la semaine. Ne manquez pas cette occasion !",
            button_text="Voir les offres",
            button_url="/products/?category=electronique",
            trigger_type="exit_intent",
            show_to_authenticated=True,
            show_to_anonymous=True,
            user_types=[],
            pages=[],
            background_color="#fff3cd",
            text_color="#856404",
            button_color="#ffc107",
            overlay_opacity=0.7,
            is_active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
        )

        # 4. Popup de preuve sociale
        Popup.objects.create(
            name="Avis Clients",
            popup_type="social_proof",
            title="Nos clients nous font confiance ! ⭐",
            content="Plus de 10,000 clients satisfaits. Découvrez pourquoi nos clients nous recommandent avec une note moyenne de 4.8/5.",
            button_text="Voir les avis",
            button_url="/reviews/",
            trigger_type="time_on_page",
            trigger_time=60,
            show_to_authenticated=True,
            show_to_anonymous=True,
            user_types=[],
            pages=[],
            background_color="#d4edda",
            text_color="#155724",
            button_color="#28a745",
            overlay_opacity=0.5,
            is_active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=90),
        )

        # 5. Configuration des cookies
        CookieConsent.objects.all().delete()

        CookieConsent.objects.create(
            name="Cookies Nécessaires",
            description="Ces cookies sont essentiels au fonctionnement du site et ne peuvent pas être désactivés.",
            consent_type="necessary",
            is_required=True,
            is_active=True,
            cookie_name="sessionid",
            cookie_domain="kefystore.com",
            cookie_duration=30,
        )

        CookieConsent.objects.create(
            name="Cookies Analytiques",
            description="Ces cookies nous aident à comprendre comment les visiteurs interagissent avec notre site.",
            consent_type="analytics",
            is_required=False,
            is_active=True,
            cookie_name="analytics",
            cookie_domain="kefystore.com",
            cookie_duration=365,
        )

        CookieConsent.objects.create(
            name="Cookies Marketing",
            description="Ces cookies sont utilisés pour afficher des publicités pertinentes.",
            consent_type="marketing",
            is_required=False,
            is_active=True,
            cookie_name="marketing",
            cookie_domain="kefystore.com",
            cookie_duration=90,
        )

        CookieConsent.objects.create(
            name="Cookies de Préférences",
            description="Ces cookies mémorisent vos préférences et paramètres.",
            consent_type="preferences",
            is_required=False,
            is_active=True,
            cookie_name="preferences",
            cookie_domain="kefystore.com",
            cookie_duration=180,
        )

        CookieConsent.objects.create(
            name="Cookies Réseaux Sociaux",
            description="Ces cookies permettent l'intégration des réseaux sociaux.",
            consent_type="social",
            is_required=False,
            is_active=True,
            cookie_name="social",
            cookie_domain="kefystore.com",
            cookie_duration=30,
        )

        # 6. Configuration de la vérification d'âge
        AgeVerification.objects.all().delete()

        AgeVerification.objects.create(
            title="Vérification d'Âge",
            message="Vous devez avoir au moins 18 ans pour accéder à ce site. Veuillez confirmer votre âge.",
            min_age=18,
            is_active=False,  # Désactivé par défaut
            show_on_all_pages=True,
            pages=[],
            background_color="#000000",
            text_color="#ffffff",
            button_color="#667eea",
        )

        # 7. Politique de confidentialité
        PrivacyPolicy.objects.all().delete()

        PrivacyPolicy.objects.create(
            title="Politique de Confidentialité - KefyStore",
            content="""
            <h2>1. Introduction</h2>
            <p>Cette politique de confidentialité décrit comment KefyStore collecte, utilise et protège vos informations personnelles.</p>

            <h2>2. Informations collectées</h2>
            <p>Nous collectons :</p>
            <ul>
                <li>Nom et prénom</li>
                <li>Adresse email</li>
                <li>Numéro de téléphone</li>
                <li>Adresse de livraison</li>
                <li>Informations de paiement (sécurisées)</li>
            </ul>

            <h2>3. Utilisation des informations</h2>
            <p>Vos informations sont utilisées pour :</p>
            <ul>
                <li>Traiter vos commandes</li>
                <li>Vous contacter concernant vos commandes</li>
                <li>Améliorer notre site et nos services</li>
                <li>Vous envoyer des communications marketing (avec votre consentement)</li>
            </ul>

            <h2>4. Contact</h2>
            <p>Pour toute question : kouayavana18@gmail.com</p>
            """,
            version="1.0",
            version_type="published",
            language="fr",
            effective_date=timezone.now(),
        )

        # 8. Conditions d'utilisation
        TermsOfService.objects.all().delete()

        TermsOfService.objects.create(
            title="Conditions d'Utilisation - KefyStore",
            content="""
            <h2>1. Acceptation des conditions</h2>
            <p>En utilisant KefyStore, vous acceptez ces conditions d'utilisation.</p>

            <h2>2. Description du service</h2>
            <p>KefyStore est une plateforme e-commerce permettant :</p>
            <ul>
                <li>La vente de produits en ligne</li>
                <li>La création de comptes utilisateur</li>
                <li>Le passage de commandes</li>
                <li>Le paiement sécurisé</li>
                <li>La livraison de produits</li>
            </ul>

            <h2>3. Commandes et paiements</h2>
            <p>Nous acceptons :</p>
            <ul>
                <li>Paiement à la livraison</li>
                <li>Moov Money</li>
                <li>Orange Money</li>
                <li>MTN Money</li>
                <li>Wave</li>
                <li>Cartes bancaires</li>
            </ul>

            <h2>4. Contact</h2>
            <p>Pour toute question : kouayavana18@gmail.com</p>
            """,
            version="1.0",
            version_type="published",
            language="fr",
            effective_date=timezone.now(),
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Popups et configurations par defaut crees avec succes !\n"
                "Email configure : kouayavana18@gmail.com\n"
                "Design KefyStore applique\n"
                "Securite et confidentialite configurees\n"
                "Pret pour la production !"
            )
        )
