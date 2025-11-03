"""
Modèles pour les analytics et rapports avancés
"""
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class AnalyticsEvent(models.Model):
    """Modèle pour les événements d'analytics"""

    EVENT_TYPES = [
        ("page_view", "Vue de page"),
        ("product_view", "Vue de produit"),
        ("add_to_cart", "Ajout au panier"),
        ("remove_from_cart", "Suppression du panier"),
        ("checkout_start", "Début de commande"),
        ("checkout_complete", "Commande terminée"),
        ("search", "Recherche"),
        ("filter", "Filtrage"),
        ("wishlist_add", "Ajout aux favoris"),
        ("wishlist_remove", "Suppression des favoris"),
        ("review_submit", "Soumission d'avis"),
        ("newsletter_signup", "Inscription newsletter"),
        ("login", "Connexion"),
        ("logout", "Déconnexion"),
        ("registration", "Inscription"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_events",
        verbose_name="Utilisateur",
    )
    session_id = models.CharField(max_length=100, verbose_name="ID de session")
    event_type = models.CharField(
        max_length=30, choices=EVENT_TYPES, verbose_name="Type d'événement"
    )

    # Données de l'événement
    page_url = models.URLField(blank=True, verbose_name="URL de la page")
    referrer = models.URLField(blank=True, verbose_name="Référent")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")

    # Données spécifiques
    product_id = models.IntegerField(null=True, blank=True, verbose_name="ID Produit")
    category_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID Catégorie"
    )
    search_query = models.CharField(
        max_length=200, blank=True, verbose_name="Requête de recherche"
    )
    value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valeur"
    )

    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Événement Analytics"
        verbose_name_plural = "Événements Analytics"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["session_id", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.created_at}"


class SalesReport(models.Model):
    """Modèle pour les rapports de vente"""

    REPORT_PERIODS = [
        ("daily", "Quotidien"),
        ("weekly", "Hebdomadaire"),
        ("monthly", "Mensuel"),
        ("quarterly", "Trimestriel"),
        ("yearly", "Annuel"),
        ("custom", "Personnalisé"),
    ]

    report_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200, verbose_name="Titre du rapport")
    period = models.CharField(
        max_length=20, choices=REPORT_PERIODS, verbose_name="Période"
    )
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(verbose_name="Date de fin")

    # Données du rapport
    total_orders = models.IntegerField(default=0, verbose_name="Total commandes")
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Chiffre d'affaires total",
    )
    total_products_sold = models.IntegerField(
        default=0, verbose_name="Total produits vendus"
    )
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Valeur moyenne des commandes",
    )

    # Métriques avancées
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Taux de conversion (%)",
    )
    cart_abandonment_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Taux d'abandon de panier (%)",
    )
    customer_acquisition_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Coût d'acquisition client",
    )
    customer_lifetime_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Valeur vie client",
    )

    # Données détaillées
    data = models.JSONField(default=dict, blank=True, verbose_name="Données détaillées")

    # Métadonnées
    generated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sales_reports",
        verbose_name="Généré par",
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False, verbose_name="Public")

    class Meta:
        verbose_name = "Rapport de vente"
        verbose_name_plural = "Rapports de vente"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%d/%m/%Y')}"


class ProductAnalytics(models.Model):
    """Modèle pour les analytics de produits"""

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="analytics",
        verbose_name="Produit",
    )

    # Métriques de vue
    total_views = models.IntegerField(default=0, verbose_name="Total vues")
    unique_views = models.IntegerField(default=0, verbose_name="Vues uniques")
    views_today = models.IntegerField(default=0, verbose_name="Vues aujourd'hui")
    views_this_week = models.IntegerField(default=0, verbose_name="Vues cette semaine")
    views_this_month = models.IntegerField(default=0, verbose_name="Vues ce mois")

    # Métriques de conversion
    add_to_cart_count = models.IntegerField(default=0, verbose_name="Ajouts au panier")
    purchase_count = models.IntegerField(default=0, verbose_name="Achats")
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Taux de conversion (%)",
    )

    # Métriques de performance
    revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Chiffre d'affaires",
    )
    profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Marge bénéficiaire (%)",
    )

    # Métriques de satisfaction
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Note moyenne",
    )
    review_count = models.IntegerField(default=0, verbose_name="Nombre d'avis")

    # Métriques de popularité
    wishlist_count = models.IntegerField(default=0, verbose_name="Ajouts aux favoris")
    comparison_count = models.IntegerField(default=0, verbose_name="Comparaisons")

    # Dernière mise à jour
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Analytics de produit"
        verbose_name_plural = "Analytics de produits"

    def __str__(self):
        return f"Analytics - {self.product.name}"

    def update_conversion_rate(self):
        """Mettre à jour le taux de conversion"""
        if self.total_views > 0:
            self.conversion_rate = (self.purchase_count / self.total_views) * 100
        else:
            self.conversion_rate = Decimal("0.00")
        self.save()


class CustomerAnalytics(models.Model):
    """Modèle pour les analytics de clients"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_analytics",
        verbose_name="Utilisateur",
    )

    # Métriques d'engagement
    total_sessions = models.IntegerField(default=0, verbose_name="Total sessions")
    total_page_views = models.IntegerField(default=0, verbose_name="Total pages vues")
    average_session_duration = models.DurationField(
        null=True, blank=True, verbose_name="Durée moyenne de session"
    )

    # Métriques d'achat
    total_orders = models.IntegerField(default=0, verbose_name="Total commandes")
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total dépensé",
    )
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Valeur moyenne des commandes",
    )

    # Métriques de fidélité
    days_since_first_order = models.IntegerField(
        null=True, blank=True, verbose_name="Jours depuis la première commande"
    )
    days_since_last_order = models.IntegerField(
        null=True, blank=True, verbose_name="Jours depuis la dernière commande"
    )
    customer_lifetime_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Valeur vie client",
    )

    # Segmentation
    customer_segment = models.CharField(
        max_length=50, blank=True, verbose_name="Segment client"
    )
    risk_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Score de risque",
    )

    # Dernière mise à jour
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Analytics de client"
        verbose_name_plural = "Analytics de clients"

    def __str__(self):
        return f"Analytics - {self.user.get_display_name()}"

    def calculate_customer_segment(self):
        """Calculer le segment du client"""
        if self.total_spent >= 100000:  # 100,000 FCFA
            return "VIP"
        elif self.total_spent >= 50000:  # 50,000 FCFA
            return "Premium"
        elif self.total_spent >= 20000:  # 20,000 FCFA
            return "Standard"
        else:
            return "Nouveau"

    def calculate_risk_score(self):
        """Calculer le score de risque"""
        score = 0

        # Facteurs de risque
        if self.days_since_last_order and self.days_since_last_order > 90:
            score += 30

        if self.total_orders == 0:
            score += 20

        if self.average_order_value < 5000:  # 5,000 FCFA
            score += 10

        return min(score, 100)  # Max 100


class GoogleAnalytics(models.Model):
    """Modèle pour l'intégration Google Analytics"""

    property_id = models.CharField(
        max_length=50, unique=True, verbose_name="ID de propriété"
    )
    property_name = models.CharField(max_length=200, verbose_name="Nom de la propriété")
    view_id = models.CharField(max_length=50, verbose_name="ID de vue")
    credentials = models.JSONField(verbose_name="Identifiants")

    # Configuration
    is_active = models.BooleanField(default=True, verbose_name="Active")
    track_ecommerce = models.BooleanField(default=True, verbose_name="Suivi e-commerce")
    track_enhanced_ecommerce = models.BooleanField(
        default=True, verbose_name="Suivi e-commerce amélioré"
    )

    # Métriques
    last_sync = models.DateTimeField(
        null=True, blank=True, verbose_name="Dernière synchronisation"
    )
    sync_frequency = models.IntegerField(
        default=24, verbose_name="Fréquence de synchronisation (heures)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Google Analytics"
        verbose_name_plural = "Google Analytics"

    def __str__(self):
        return f"Google Analytics - {self.property_name}"


class DashboardWidget(models.Model):
    """Modèle pour les widgets de tableau de bord"""

    WIDGET_TYPES = [
        ("chart", "Graphique"),
        ("metric", "Métrique"),
        ("table", "Tableau"),
        ("list", "Liste"),
        ("gauge", "Jauge"),
        ("map", "Carte"),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom du widget")
    widget_type = models.CharField(
        max_length=20, choices=WIDGET_TYPES, verbose_name="Type de widget"
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")

    # Configuration
    data_source = models.CharField(max_length=100, verbose_name="Source de données")
    query = models.JSONField(verbose_name="Requête")
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuration")

    # Position et taille
    position_x = models.IntegerField(default=0, verbose_name="Position X")
    position_y = models.IntegerField(default=0, verbose_name="Position Y")
    width = models.IntegerField(default=4, verbose_name="Largeur")
    height = models.IntegerField(default=3, verbose_name="Hauteur")

    # Visibilité
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_public = models.BooleanField(default=False, verbose_name="Public")

    # Permissions
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="dashboard_widgets",
        verbose_name="Utilisateurs autorisés",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Widget de tableau de bord"
        verbose_name_plural = "Widgets de tableau de bord"
        ordering = ["position_y", "position_x"]

    def __str__(self):
        return f"{self.name} - {self.get_widget_type_display()}"


class ReportTemplate(models.Model):
    """Modèle pour les templates de rapports"""

    name = models.CharField(max_length=100, verbose_name="Nom du template")
    description = models.TextField(blank=True, verbose_name="Description")

    # Configuration du rapport
    report_type = models.CharField(max_length=50, verbose_name="Type de rapport")
    query = models.JSONField(verbose_name="Requête")
    format = models.CharField(
        max_length=20,
        choices=[
            ("pdf", "PDF"),
            ("excel", "Excel"),
            ("csv", "CSV"),
            ("json", "JSON"),
        ],
        default="pdf",
        verbose_name="Format",
    )

    # Paramètres
    parameters = models.JSONField(default=dict, blank=True, verbose_name="Paramètres")

    # Visibilité
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_public = models.BooleanField(default=False, verbose_name="Public")

    # Permissions
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="report_templates",
        verbose_name="Utilisateurs autorisés",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_report_templates",
        verbose_name="Créé par",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Template de rapport"
        verbose_name_plural = "Templates de rapports"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.get_format_display()}"
