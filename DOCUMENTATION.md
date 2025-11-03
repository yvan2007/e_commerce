# Documentation Complète - Application E-Commerce KefyStore

## 📋 Table des matières

1. [Présentation Générale](#présentation-générale)
2. [Architecture Technique](#architecture-technique)
3. [Installation et Configuration](#installation-et-configuration)
4. [Modèles de Données](#modèles-de-données)
5. [Applications Django](#applications-django)
6. [Système d'Authentification](#système-dauthentification)
7. [Gestion des Produits](#gestion-des-produits)
8. [Système de Commandes](#système-de-commandes)
9. [Système de Paiement](#système-de-paiement)
10. [Notifications](#notifications)
11. [API REST](#api-rest)
12. [Interface Utilisateur](#interface-utilisateur)
13. [Sécurité](#sécurité)
14. [Tests](#tests)
15. [Déploiement](#déploiement)

---

## 🎯 Présentation Générale

### Description du Projet

**KefyStore** est une plateforme e-commerce complète et moderne développée avec Django 4.2.7. Elle permet la gestion de produits, de commandes, de paiements multiples (Mobile Money, cartes bancaires, Wave), et offre une expérience utilisateur riche avec des fonctionnalités avancées.

### Fonctionnalités Principales

- **Gestion multi-vendeurs** : Plusieurs vendeurs peuvent proposer leurs produits
- **Système de produits riche** : Catégories, tags, variantes, images multiples
- **Panier et commandes** : Gestion complète du processus d'achat
- **Paiements multiples** : Moov Money, Orange Money, MTN Money, Wave, cartes bancaires
- **Authentification renforcée** : Authentification à deux facteurs (2FA)
- **Notifications** : Email, SMS, notifications push
- **Avis et évaluations** : Système complet d'avis clients
- **Gestion d'inventaire** : Suivi des stocks, alertes, rapports
- **Système de livraison** : Gestion des zones, calcul des frais
- **Dashboard** : Tableaux de bord pour admins et vendeurs
- **API REST** : Interface API complète
- **Recherche avancée** : Filtres multiples, tri
- **Wishlist** : Liste de souhaits personnalisée

### Technologies Utilisées

- **Backend** : Django 4.2.7, Python 3.x
- **Base de données** : SQLite (développement), PostgreSQL (production)
- **Frontend** : HTML5, CSS3, JavaScript, Bootstrap 5
- **Éditeur WYSIWYG** : TinyMCE, CKEditor 5
- **Authentification** : Django Allauth, OAuth 2.0 (Google)
- **API** : Django REST Framework
- **Tâches asynchrones** : Celery, Redis
- **Notifications** : Django Email, SMS (Twilio)
- **Sécurité** : 2FA, CSP, Rate limiting

---

## 🏗️ Architecture Technique

### Structure du Projet

```
ecommerce_site/
├── accounts/          # Gestion des utilisateurs et authentification
├── products/          # Gestion des produits
├── orders/            # Commandes et panier
├── payment_system/    # Système de paiement
├── notifications/     # Système de notifications
├── dashboard/         # Tableaux de bord
├── search/            # Recherche de produits
├── wishlist/          # Liste de souhaits
├── pages/             # Pages statiques
├── analytics/         # Analyses et statistiques
├── api/               # API REST
├── popups/            # Popups et modals
├── two_factor_auth/   # Authentification 2FA
├── inventory/         # Gestion d'inventaire
├── delivery_system/   # Système de livraison
├── reviews/           # Avis et évaluations
├── loyalty/           # Programme de fidélité
├── chat/              # Chat en temps réel
├── i18n/              # Internationalisation
├── returns/           # Retours et remboursements
├── promotions/        # Promotions
├── ecommerce_site/    # Configuration principale
├── templates/         # Templates HTML
├── static/            # Fichiers statiques
├── media/             # Médias uploadés
└── logs/              # Logs de l'application
```

### Configuration Django

Le fichier `ecommerce_site/settings.py` contient toutes les configurations :

```python
# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... applications tierces
    'accounts',
    'products',
    'orders',
    # ... applications locales
]

# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'accounts.User'

# Configuration de la base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

---

## 🔧 Installation et Configuration

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git
- Un environnement virtuel (venv)

### Installation

#### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd "Conception de site e-commerce"
```

#### 2. Créer et activer un environnement virtuel

**Windows (PowerShell) :**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac :**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

#### 4. Configuration de l'environnement

Copier le fichier `env.example` vers `.env` et remplir les variables :

```bash
cp env.example .env
```

Éditer `.env` avec vos clés API et configuration :

```env
SECRET_KEY=votre-clé-secrète-ici
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe
```

#### 5. Migrations de la base de données

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 6. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

#### 7. Collecter les fichiers statiques

```bash
python manage.py collectstatic
```

#### 8. Démarrer le serveur

**Option 1 - Script automatique (Windows) :**
```bash
start_server.bat
```

**Option 2 - Commande manuelle :**
```bash
python manage.py runserver
```

Le serveur sera accessible à l'adresse : **http://localhost:8000/**

### Interfaces d'Administration

- **Interface publique** : http://localhost:8000/
- **Interface admin** : http://localhost:8000/admin/
- **API** : http://localhost:8000/api/
- **Dashboard** : http://localhost:8000/dashboard/

---

## 📊 Modèles de Données

### 1. Comptes Utilisateurs (`accounts`)

#### User (Modèle Utilisateur Personnalisé)

**Hérite de** : `django.contrib.auth.models.AbstractUser`

**Champs principaux** :
- `user_type` : Type d'utilisateur (client, vendeur, admin)
- `phone_number` : Numéro de téléphone
- `country_code` : Code pays (+225, +33, etc.)
- `address`, `city`, `postal_code` : Coordonnées
- `profile_picture` : Photo de profil
- `date_of_birth` : Date de naissance
- `is_verified` : Compte vérifié
- `two_factor_enabled` : 2FA activé
- `two_factor_secret` : Secret 2FA
- `backup_codes` : Codes de secours

**Méthodes principales** :
- `get_display_name()` : Nom d'affichage
- `is_vendor()` : Vérifie si vendeur
- `is_client()` : Vérifie si client
- `get_full_phone_number()` : Numéro complet

#### UserProfile

**Champs** : `bio`, `website`, `social_facebook`, `social_twitter`, `social_instagram`

#### VendorProfile

**Champs** :
- `business_name` : Nom de l'entreprise
- `business_description` : Description
- `business_license` : Numéro de licence
- `tax_id` : Numéro fiscal
- `bank_name`, `bank_account` : Informations bancaires
- `is_approved` : Vendeur approuvé

### 2. Produits (`products`)

#### Category

**Champs** :
- `name` : Nom de la catégorie
- `slug` : Slug URL
- `description` : Description
- `image` : Image de la catégorie
- `parent` : Catégorie parente (hiérarchique)
- `is_active` : Active

**Méthodes** : `get_absolute_url()`

#### Tag

**Champs** : `name`, `slug`, `color`

#### Product

**Champs principaux** :

**Informations de base** :
- `name` : Nom du produit
- `slug` : Slug URL
- `sku` : Code SKU unique
- `description` : Description riche (CKEditor)
- `short_description` : Description courte
- `features`, `specifications`, `usage_instructions`, `warranty_info` : Détails

**Relations** :
- `vendor` : Vendeur (ForeignKey)
- `category` : Catégorie (ForeignKey)
- `tags` : Étiquettes (ManyToMany)

**Prix et promotions** :
- `price` : Prix actuel
- `original_price` : Prix original
- `discount_percentage` : Pourcentage de remise
- `is_on_sale` : En promotion
- `sale_start_date`, `sale_end_date` : Dates promotion
- `compare_price` : Prix de comparaison

**Stock** :
- `stock` : Quantité en stock
- `min_stock` : Stock minimum

**Images et statut** :
- `main_image` : Image principale
- `status` : Statut (draft, published, archived)
- `is_featured` : Produit vedette
- `is_digital` : Produit numérique

**Métriques** :
- `views` : Nombre de vues
- `sales_count` : Nombre de ventes
- `rating` : Note moyenne
- `review_count` : Nombre d'avis

**Dates** : `created_at`, `updated_at`, `published_at`

**Méthodes principales** :
- `get_discount_percentage()` : Calcul remise
- `is_currently_on_sale()` : Vérifie promotion active
- `is_in_stock()` : Vérifie disponibilité
- `is_low_stock()` : Vérifie stock faible
- `update_rating()` : Met à jour la note

#### ProductImage

**Champs** : `product`, `image`, `alt_text`, `order`, `is_active`

#### ProductVariant

**Champs** : `product`, `name`, `sku`, `price`, `stock`, `is_active`

#### ProductReview

**Champs** :
- `product`, `user` : Relations
- `rating` : Note (1-5)
- `title`, `comment` : Contenu
- `is_verified_purchase` : Achat vérifié
- `is_approved` : Approuvé
- `helpful_votes` : Votes utiles

#### ProductViewHistory

**Champs** : `user`, `product`, `ip_address`, `session_key`, `viewed_at`

### 3. Commandes (`orders`)

#### Order

**Champs principaux** :

**Identification** :
- `order_number` : Numéro unique (format CMD-XXXXXXXX)
- `user` : Client

**Statuts** :
- `status` : pending, confirmed, processing, shipped, delivered, cancelled, refunded
- `payment_method` : cash, moovmoney, orangemoney, mtnmoney, wave, carte
- `payment_status` : pending, paid, failed, refunded

**Adresse de livraison** :
- `shipping_first_name`, `shipping_last_name`
- `shipping_phone`, `shipping_address`
- `shipping_city`, `shipping_postal_code`, `shipping_country`
- `billing_address` : Adresse de facturation

**Montants** :
- `subtotal` : Sous-total
- `shipping_cost` : Frais de livraison
- `tax_amount` : Taxes
- `total_amount` : Total

**Paiement** :
- `payment_reference` : Référence
- `payment_date` : Date

**Dates** : `created_at`, `updated_at`, `shipped_at`, `delivered_at`

**Méthodes** :
- `can_be_cancelled()` : Vérifie annulation possible
- `get_status_display_color()` : Couleur du statut

#### OrderItem

**Champs** : `order`, `product`, `variant`, `quantity`, `unit_price`, `total_price`

#### Cart

**Champs** : `user`

**Méthodes** :
- `get_total_items()` : Nombre total d'articles
- `get_total_price()` : Prix total
- `clear()` : Vide le panier

#### CartItem

**Champs** : `cart`, `product`, `variant`, `quantity`

**Méthodes** :
- `get_unit_price()` : Prix unitaire
- `get_total_price()` : Prix total

#### ShippingAddress

**Champs** : `user`, `first_name`, `last_name`, `phone`, `address`, `city`, `postal_code`, `country`, `is_default`

#### OrderStatusHistory

**Champs** : `order`, `status`, `notes`, `created_by`, `created_at`

### 4. Paiements (`payment_system`)

#### PaymentMethod

**Champs** :
- `name` : Nom de la méthode
- `type` : mobile_money, bank_card, wave, cash_on_delivery
- `logo` : Logo
- `is_active` : Active
- `fees_percentage` : Frais (%)
- `min_amount`, `max_amount` : Limites

#### PaymentTransaction

**Champs** :
- `id` : UUID
- `transaction_id` : ID unique
- `order`, `user`, `payment_method` : Relations
- `amount` : Montant
- `fees` : Frais
- `total_amount` : Total
- `status` : pending, processing, completed, failed, cancelled, refunded
- `payment_reference` : Référence
- `external_transaction_id` : ID transaction externe
- `metadata` : Métadonnées JSON
- `completed_at` : Date de complétion

**Méthodes** :
- `is_successful()` : Vérifie succès
- `can_be_refunded()` : Vérifie remboursement possible

#### MobileMoneyAccount

**Champs** : `user`, `provider` (moov, orange, mtn), `phone_number`, `is_verified`, `is_primary`

#### BankCard

**Champs** : `user`, `card_type`, `last_four_digits`, `expiry_month`, `expiry_year`, `cardholder_name`, `is_verified`

#### RefundRequest

**Champs** :
- `transaction`, `user` : Relations
- `reason` : defective, wrong_item, not_delivered, cancelled, other
- `description` : Détails
- `status` : pending, approved, rejected, processed
- `admin_notes` : Notes admin

### 5. Notifications (`notifications`)

#### NotificationTemplate

**Champs** :
- `name` : Nom du modèle
- `type` : email, sms, push, in_app
- `trigger_type` : Type de déclencheur
- `subject` : Sujet
- `content` : Contenu
- `is_active` : Actif

#### Notification

**Champs** :
- `id` : UUID
- `user`, `template` : Relations
- `type` : email, sms, push, in_app
- `subject`, `content` : Contenu
- `status` : pending, sent, delivered, failed, read
- `is_read` : Lu
- `sent_at`, `read_at` : Dates
- `metadata` : Métadonnées

**Méthodes** : `mark_as_read()`

#### NotificationPreference

**Champs** : Préférences de notification par type (email, sms, push, in_app)

#### EmailQueue

**Champs** :
- `to_email`, `subject`, `content`, `html_content`
- `status` : pending, processing, sent, failed
- `priority` : 1 (très haute) à 5 (très basse)
- `retry_count`, `max_retries` : Tentatives
- `scheduled_at`, `sent_at` : Dates

#### SMSQueue

**Champs** : `to_phone`, `message`, `status`, `retry_count`, `scheduled_at`, `sent_at`

### 6. Livraison (`delivery_system`)

#### Region

**Champs** : `name`, `code`, `is_active`

#### City

**Champs** : `name`, `region`, `postal_code`, `is_active`

#### DeliveryZone

**Champs** :
- `name` : Nom de la zone
- `zone_type` : abidjan, bassam, civ_other, international
- `delivery_fee` : Frais de livraison (FCFA)
- `estimated_days` : Délai (jours)
- `city`, `city_list` : Villes
- `is_active` : Active

#### DeliveryAddress

**Champs** : Adresse complète de livraison avec zone

**Méthodes** : `get_full_address()`

#### DeliveryCalculation

**Champs** : `order`, `zone`, `base_fee`, `additional_fees`, `total_delivery_fee`, `estimated_delivery_date`

### 7. Inventaire (`inventory`)

#### Supplier

**Champs** :
- `name`, `contact_person`
- `email`, `phone`, `address`, `city`, `country`
- `tax_id`, `payment_terms`
- `status` : active, inactive, suspended
- `rating` : Note (0-5)

**Méthodes** : `get_total_products()`, `get_average_rating()`

#### StockAlert

**Champs** :
- `product` : Produit
- `alert_type` : low_stock, out_of_stock, overstock, expiring
- `priority` : low, medium, high, urgent
- `threshold_value` : Seuil
- `current_stock` : Stock actuel
- `message` : Message
- `is_resolved` : Résolu
- `resolved_at`, `resolved_by` : Résolution

**Méthodes** : `resolve(user)`

#### InventoryTransaction

**Champs** :
- `transaction_id` : UUID
- `product`, `supplier` : Relations
- `transaction_type` : in, out, adjustment, transfer, return
- `quantity` : Quantité
- `unit_cost`, `total_cost` : Coûts
- `reference`, `notes` : Infos
- `created_by` : Créateur

#### ProductSupplier

**Champs** :
- `product`, `supplier` : Relations
- `supplier_sku` : SKU fournisseur
- `cost_price` : Prix d'achat
- `minimum_order_quantity` : Quantité min
- `lead_time_days` : Délai (jours)
- `is_primary` : Principal
- `is_active` : Actif

#### StockMovement

**Champs** :
- `product`, `created_by` : Relations
- `movement_type` : sale, return, adjustment, transfer, damage, expired
- `quantity` : Quantité
- `previous_stock`, `new_stock` : Stocks
- `reference`, `notes` : Infos

#### InventoryReport

**Champs** :
- `report_type` : Type de rapport
- `title`, `description` : Infos
- `data` : Données JSON
- `generated_by` : Générateur
- `generated_at` : Date

### 8. Authentification 2FA (`two_factor_auth`)

#### TwoFactorAuth

**Champs** :
- `user` : Utilisateur
- `is_enabled` : 2FA activé
- `primary_method` : totp, sms, email, backup
- `totp_secret` : Secret TOTP
- `totp_verified` : TOTP vérifié
- `phone_number`, `sms_verified` : SMS
- `email_verified` : Email
- `backup_codes` : Codes de secours
- `last_used` : Dernière utilisation

**Méthodes** :
- `generate_totp_secret()` : Génère secret
- `get_totp_qr_code()` : Génère QR code
- `verify_totp_code(code)` : Vérifie code
- `generate_backup_codes(count)` : Génère codes
- `enable_2fa()`, `disable_2fa()` : Activation/désactivation

#### TwoFactorCode

**Champs** :
- `user` : Utilisateur
- `code_type` : totp, sms, email, backup
- `code` : Code
- `expires_at` : Expiration
- `is_used` : Utilisé
- `ip_address`, `user_agent` : Métadonnées

**Méthodes** :
- `is_expired()` : Vérifie expiration
- `is_valid()` : Vérifie validité
- `use_code()` : Utilise le code
- `generate_sms_code()` : Génère code SMS
- `generate_email_code()` : Génère code email

#### TwoFactorSession

**Champs** :
- `user` : Utilisateur
- `session_key` : Clé de session
- `is_verified` : Vérifié
- `ip_address`, `user_agent` : Métadonnées
- `device_info` : Infos appareil
- `expires_at`, `last_activity` : Dates

**Méthodes** :
- `is_expired()` : Vérifie expiration
- `is_valid()` : Vérifie validité
- `create_session()` : Crée session

#### TwoFactorDevice

**Champs** :
- `user` : Utilisateur
- `device_name` : Nom
- `device_type` : mobile, tablet, desktop, other
- `device_fingerprint` : Empreinte
- `ip_address`, `user_agent` : Métadonnées
- `location` : Localisation
- `is_trusted` : Appareil de confiance
- `is_active` : Actif
- `last_used` : Dernière utilisation

**Méthodes** : `create_device_fingerprint()`

### 9. Avis (`reviews`)

#### DeliveryProductReview

**Champs** :
- `user`, `product`, `order`, `order_item` : Relations
- `rating` : Note (1-5)
- `title`, `comment` : Contenu
- `image_1`, `image_2`, `image_3` : Photos
- `is_verified_purchase` : Achat vérifié
- `is_helpful` : Votes utiles
- `is_public` : Public

**Propriétés** : `rating_stars`, `has_images`

#### DeliveryReview

**Champs** :
- `user`, `order` : Relations
- `delivery_rating` : Note livraison
- `delivery_comment` : Commentaire
- `delivery_speed_rating` : Rapidité
- `packaging_rating` : Emballage
- `delivery_person_rating` : Livreur

**Propriétés** : `average_rating`

#### ReviewHelpful

**Champs** : `user`, `review`, `is_helpful`

#### ReviewResponse

**Champs** : `review`, `vendor`, `response_text`, `created_at`, `updated_at`

### 10. Wishlist (`wishlist`)

#### Wishlist

**Champs** : `user`, `products` (ManyToMany)

**Méthodes** :
- `add_product(product)` : Ajoute produit
- `remove_product(product)` : Retire produit
- `is_in_wishlist(product)` : Vérifie présence
- `get_products()` : Récupère produits

#### WishlistItem

**Champs** : `wishlist`, `product`, `added_at`

**Limite** : 50 produits maximum

#### WishlistShare

**Champs** : `wishlist`, `shared_by`, `shared_with_email`, `message`, `is_active`, `viewed_at`

---

## 📱 Applications Django

### 1. accounts - Gestion des Comptes

**Responsabilité** : Authentification, inscriptions, profils utilisateurs

**Vues principales** :
- `UserRegistrationView` : Inscription
- `UserLoginView` : Connexion
- `UserLogoutView` : Déconnexion
- `ProfileView` : Profil utilisateur
- `PasswordResetView` : Réinitialisation mot de passe
- `PasswordChangeView` : Changement mot de passe

**Formulaires** :
- `UserRegistrationForm`
- `VendorRegistrationForm`
- `UserLoginForm`
- `UserProfileForm`
- `VendorProfileForm`
- `PasswordChangeForm`

**URLs** : `/accounts/login/`, `/accounts/register/`, `/accounts/profile/`, etc.

### 2. products - Gestion des Produits

**Responsabilité** : Catalogue, détails produits, recherche

**Vues principales** :
- `ProductListView` : Liste produits (avec pagination dynamique)
- `ProductDetailView` : Détails produit
- `CategoryDetailView` : Détails catégorie
- `ProductCreateView` : Création produit
- `ProductUpdateView` : Modification produit
- `ProductReviewCreateView` : Ajout avis

**Formulaires** :
- `ProductForm`
- `ProductImageForm`
- `ProductVariantForm`
- `ProductSearchForm`
- `ProductReviewForm`
- `CategoryForm`
- `TagForm`

**Context Processors** :
- `categories` : Liste des catégories actives
- `cart_context` : Contexte du panier

**URLs** : `/`, `/products/`, `/products/<slug>/`, etc.

### 3. orders - Commandes

**Responsabilité** : Panier, checkout, gestion des commandes

**Vues principales** :
- `CartView` : Gestion du panier
- `CheckoutView` : Processus de commande
- `OrderListView` : Liste des commandes
- `OrderDetailView` : Détails commande
- `ShippingAddressListView` : Adresses de livraison
- `ShippingAddressCreateView` : Nouvelle adresse

**Signaux** :
- Création de panier automatique
- Mise à jour stock après commande
- Notifications

**URLs** : `/orders/cart/`, `/orders/checkout/`, `/orders/`, etc.

### 4. payment_system - Paiements

**Responsabilité** : Processus de paiement multiples

**Vues principales** :
- `PaymentMethodListView` : Méthodes disponibles
- `PaymentInitiationView` : Initiation paiement
- `PaymentCallbackView` : Callback paiement
- `RefundRequestView` : Demande remboursement

**Services** :
- `MobileMoneyService` : Gestion Mobile Money
- `HybridPaymentService` : Service hybride

**URLs** : `/payment/`, `/payment/initiate/`, `/payment/callback/`, etc.

### 5. notifications - Notifications

**Responsabilité** : Envoi de notifications

**Services** :
- `EmailService` : Service email
- `SMSService` : Service SMS
- `PushNotificationService` : Notifications push

**Types** :
- Email de bienvenue
- Confirmation de commande
- Mise à jour statut
- Alertes stock faible
- Promotions

### 6. dashboard - Tableaux de Bord

**Responsabilité** : Dashboards admins et vendeurs

**Vues** :
- `AdminDashboardView` : Dashboard admin
- `VendorDashboardView` : Dashboard vendeur
- `ProductManagementView` : Gestion produits
- `OrderManagementView` : Gestion commandes

**Statistiques** :
- Revenus
- Commandes
- Produits
- Utilisateurs
- Taux de conversion

**URLs** : `/dashboard/`, `/dashboard/admin/`, `/dashboard/vendor/`, etc.

### 7. search - Recherche

**Responsabilité** : Recherche avancée

**Vues** :
- `SearchResultsView` : Résultats

**Filtres** :
- Catégorie
- Prix
- Tags
- Tri multiple

**URLs** : `/search/?query=`, etc.

### 8. wishlist - Liste de Souhaits

**Responsabilité** : Liste de souhaits utilisateur

**Vues** :
- `WishlistView` : Liste
- `AddToWishlistView` : Ajout
- `RemoveFromWishlistView` : Retrait
- `ShareWishlistView` : Partage

**URLs** : `/wishlist/`, etc.

### 9. analytics - Analyses

**Responsabilité** : Analyses et rapports

**Vues** :
- `AnalyticsDashboardView` : Dashboard

**Métriques** :
- Ventes par période
- Produits populaires
- Segmentation clients
- Taux de conversion

### 10. two_factor_auth - 2FA

**Responsabilité** : Authentification à deux facteurs

**Vues** :
- `Setup2FAView` : Configuration
- `Verify2FASetupView` : Vérification
- `Disable2FAView` : Désactivation
- `TwoFactorRequiredView` : Login avec 2FA

**Méthodes supportées** :
- TOTP (Google Authenticator)
- SMS
- Email
- Codes de sauvegarde

**URLs** : `/2fa/setup/`, `/2fa/verify/`, etc.

### 11. inventory - Inventaire

**Responsabilité** : Gestion avancée des stocks

**Vues** :
- `SupplierListView` : Fournisseurs
- `StockAlertListView` : Alertes
- `InventoryReportView` : Rapports

**Fonctionnalités** :
- Suivi des stocks
- Alertes automatiques
- Rapports détaillés
- Gestion fournisseurs

### 12. delivery_system - Livraison

**Responsabilité** : Gestion des livraisons

**Vues** :
- `DeliveryZoneListView` : Zones
- `CalculateDeliveryFeeView` : Calcul frais
- `TrackDeliveryView` : Suivi livraison

**Fonctionnalités** :
- Zones géographiques
- Calcul automatique des frais
- Délais de livraison
- Suivi en temps réel

### 13. reviews - Avis

**Responsabilité** : Système d'avis détaillés

**Vues** :
- `ProductReviewCreateView` : Création avis
- `DeliveryReviewCreateView` : Avis livraison
- `MyReviewsView` : Mes avis

**Fonctionnalités** :
- Avis produits avec photos
- Avis livraison
- Votes "utile"
- Réponses vendeurs

### 14. api - API REST

**Responsabilité** : Interface API

**Endpoints principaux** :
- `/api/products/` : Produits
- `/api/orders/` : Commandes
- `/api/cart/` : Panier
- `/api/users/` : Utilisateurs
- `/api/categories/` : Catégories

**Authentification** : Token, Session

**Fonctionnalités** :
- CRUD complet
- Filtres avancés
- Pagination
- Recherche

---

## 🔐 Système d'Authentification

### Inscription

**URL** : `/accounts/register/`

**Types d'utilisateurs** :
- Client : Acheteur standard
- Vendeur : Vendeur avec boutique
- Administrateur : Gestionnaire plateforme

**Processus** :
1. Choix du type d'utilisateur
2. Remplissage du formulaire
3. Vérification email (optionnelle)
4. Connexion automatique
5. Email de bienvenue

### Connexion

**URL** : `/accounts/login/`

**Méthodes** :
- Username/Email + Mot de passe
- Google OAuth (django-allauth)

**Fonctionnalités** :
- "Se souvenir de moi"
- Réinitialisation mot de passe
- Authentification 2FA optionnelle

### Authentification 2FA

**Activation** :
1. Accéder à `/2fa/setup/`
2. Choisir la méthode (TOTP, SMS, Email)
3. Suivre les instructions de configuration
4. Vérification avec code

**Méthodes disponibles** :

1. **TOTP (Google Authenticator)** :
   - Scan QR code
   - Codes à 6 chiffres
   - Renouvellement toutes les 30 secondes

2. **SMS** :
   - Code à 6 chiffres
   - Durée de validité : 10 minutes
   - Renvoi limité

3. **Email** :
   - Code à 6 chiffres
   - Durée de validité : 15 minutes
   - Lien de vérification

4. **Codes de sauvegarde** :
   - 10 codes uniques
   - À conserver en sécurité
   - Usage unique

**Appareils de confiance** :
- Mémorisation appareil
- Validation automatique (24h)
- Gestion des appareils

### OAuth Google

**Configuration** :
- Client ID configuré
- Client Secret configuré
- Scopes : profile, email

**Processus** :
1. Clic sur "Se connecter avec Google"
2. Redirection Google
3. Autorisation
4. Retour application
5. Création/connexion compte

### Mot de passe

**Réinitialisation** :
- `/accounts/password/reset/`
- Envoi email avec lien
- Validation token
- Nouveau mot de passe

**Changement** :
- `/accounts/password/change/`
- Mot de passe actuel requis
- Validation force

---

## 🛍️ Gestion des Produits

### Création d'un Produit

**URL** : `/products/add/` (vendeur)

**Processus** :
1. Informations de base (nom, description, catégorie)
2. Prix et promotion
3. Stock et variantes
4. Images (principale + multiples)
5. Tags et caractéristiques
6. Publication

**Validations** :
- SKU unique automatique
- Slug unique
- Prix > 0
- Stock >= 0
- Dates promotion valides

### Catégories

**Structure** : Hiérarchique (parent/enfant)

**Exemple** :
```
Électronique
├── Téléphones
│   ├── Smartphones
│   └── Téléphones basiques
├── Ordinateurs
│   ├── Portables
│   └── Desktops
└── Accessoires
```

### Tags

**Utilisation** :
- Classification secondaire
- Couleur personnalisable
- Filtrage avancé

### Images

**Spécifications** :
- Formats : JPG, PNG, WebP
- Taille : Min 400x400px
- Compression automatique
- Minification TinyMCE

**Gestion** :
- Image principale obligatoire
- Images additionnelles (optionnelles)
- Ordre personnalisable
- Texte alternatif (SEO)

### Variantes

**Types** :
- Taille
- Couleur
- Matière
- Capacité

**Chaque variante** :
- SKU unique
- Prix spécifique
- Stock indépendant

### Promotions

**Types** :
1. **Pourcentage fixe** : -20%
2. **Montant fixe** : -5 000 FCFA
3. **Avec dates** : Début/Fin
4. **Sans dates** : Permanent jusqu'à modification

**Calcul automatique** :
- Prix promotionnel
- Affichage du pourcentage
- Barre de comparaison

### Évaluation

**Système de notation** :
- Note de 1 à 5 étoiles
- Moyenne automatique
- Nombre d'avis
- Affichage des étoiles

**Fonctionnalités** :
- Avis vérifiés (achat requis)
- Photos dans les avis
- Votes "utile"
- Réponses vendeurs

---

## 🛒 Système de Commandes

### Panier

**URL** : `/orders/cart/`

**Fonctionnalités** :
- Ajout/Retrait articles
- Modification quantités
- Sélection variantes
- Calcul automatique du total
- Persistance (session)

**Gestion** :
- Panier unique par utilisateur
- Stock vérifié en temps réel
- Prix mis à jour automatiquement

### Checkout

**URL** : `/orders/checkout/`

**Étapes** :

1. **Adresse de livraison** :
   - Sélection parmi adresses sauvegardées
   - Ou saisie nouvelle adresse
   - Vérification champs obligatoires

2. **Méthode de livraison** :
   - Sélection de la zone
   - Calcul automatique des frais
   - Délai estimé

3. **Méthode de paiement** :
   - Moov Money
   - Orange Money
   - MTN Money
   - Wave
   - Carte bancaire
   - Cash à la livraison

4. **Récapitulatif** :
   - Articles
   - Sous-total
   - Frais de livraison
   - Total

5. **Confirmation** :
   - Création de la commande
   - Initiation du paiement
   - Envoi email de confirmation

### Statuts des Commandes

**État** :
1. **pending** (En attente) : Commande créée, en attente de paiement
2. **confirmed** (Confirmée) : Paiement reçu
3. **processing** (En traitement) : Préparation
4. **shipped** (Expédiée) : En cours de livraison
5. **delivered** (Livrée) : Livrée avec succès
6. **cancelled** (Annulée) : Annulée avant livraison
7. **refunded** (Remboursée) : Remboursement effectué

**Transitions** :
- pending → confirmed (paiement)
- confirmed → processing (début préparation)
- processing → shipped (expédition)
- shipped → delivered (livraison)
- * → cancelled (annulation)
- * → refunded (remboursement)

### Suivi

**URL** : `/orders/<order_number>/`

**Informations** :
- Numéro de commande
- Statut actuel
- Historique des statuts
- Adresse de livraison
- Articles commandés
- Montants
- Référence de paiement
- Dates importantes

**Notifications** :
- Email à chaque changement de statut
- SMS optionnel
- Notification in-app

### Adresses de livraison

**Gestion** : `/orders/shipping-addresses/`

**Fonctionnalités** :
- Création multiple
- Modification
- Suppression
- Adresse par défaut
- Validation automatique

---

## 💳 Système de Paiement

### Méthodes supportées

#### 1. Mobile Money
- **Moov Money** (Côte d'Ivoire)
- **Orange Money** (Côte d'Ivoire)
- **MTN Money** (Côte d'Ivoire)

**Processus** :
1. Sélection de la méthode
2. Saisie du numéro de téléphone
3. Validation
4. Redirection vers l'application du fournisseur
5. Confirmation du paiement
6. Callback vers la plateforme

#### 2. Wave
**Processus** : Similaire à Mobile Money

#### 3. Carte Bancaire
**Support** : Stripe (configurable)

**Types** : Visa, Mastercard, American Express

**Processus** :
1. Saisie des informations
2. Validation
3. Tokenisation
4. Paiement sécurisé
5. Confirmation

#### 4. Cash à la Livraison
**Processus** :
- Pas de paiement avant livraison
- Paiement au livreur
- Validation manuelle

### Création de Transaction

**Étapes** :
1. Récupération de la méthode choisie
2. Vérification des limites (min/max)
3. Calcul des frais
4. Création de la transaction
5. Initiation du paiement
6. Attente de la confirmation

### Callback et Webhooks

**URLs** :
- `/payment/callback/<transaction_id>/`
- `/payment/webhook/<provider>/`

**Validation** :
- Signature vérifiée
- Montant confirmé
- Statut mis à jour
- Notification envoyée

### Remboursements

**URL** : `/payment/refund-request/`

**Conditions** :
- Commande livrée ou annulée
- Transaction réussie
- Raison justifiée

**Processus** :
1. Demande du client
2. Examen par l'admin
3. Approbation/Rejet
4. Traitement du remboursement
5. Notification

---

## 🔔 Notifications

### Types

#### 1. Email
**Configuration** : SMTP Gmail
**Templates** : 8 templates HTML

**Types** :
- Bienvenue
- Confirmation de commande
- Mise à jour de statut
- Livraison confirmée
- Code 2FA
- Réinitialisation mot de passe
- Notification vendeur
- Newsletter

#### 2. SMS
**Provider** : Twilio
**Limite** : 160 caractères

**Types** :
- Confirmation de commande
- Alertes de stock
- Notifications importantes

#### 3. Push (In-App)
**Technologie** : Web Push API

**Types** :
- Commandes
- Promotions
- Messages personnalisés

### Envoi

**Service** : `EmailService`, `SMSService`

**Processus** :
1. Création de la notification
2. Ajout à la file d'attente
3. Traitement asynchrone (Celery)
4. Envoi
5. Mise à jour du statut

### Préférences

**URL** : `/accounts/notification-preferences/`

**Options** :
- Activer/Désactiver par type
- Fréquence
- Contenu préféré

---

## 🌐 API REST

### Authentification

**Méthodes** :
1. **Token** :
   ```http
   POST /api/auth/token/
   Content-Type: application/json

   {
     "username": "user@example.com",
     "password": "password123"
   }
   ```

   **Réponse** :
   ```json
   {
     "token": "your-token-here",
     "user": {...}
   }
   ```

2. **Session** : Cookie de session Django

### Endpoints

#### Produits

**Liste** :
```http
GET /api/products/?page=1&page_size=20&category=1&min_price=1000&max_price=50000
```

**Détails** :
```http
GET /api/products/1/
```

**Création** (Vendeur) :
```http
POST /api/products/
Content-Type: application/json
Authorization: Token your-token-here

{
  "name": "Produit",
  "description": "...",
  "price": 5000,
  "stock": 100,
  "category": 1
}
```

**Mise à jour** :
```http
PUT /api/products/1/
PATCH /api/products/1/
```

**Suppression** :
```http
DELETE /api/products/1/
```

#### Commandes

**Liste** :
```http
GET /api/orders/
```

**Création** :
```http
POST /api/orders/
```

**Détails** :
```http
GET /api/orders/1/
```

#### Panier

**Récupérer** :
```http
GET /api/cart/
```

**Ajouter article** :
```http
POST /api/cart/items/
{
  "product": 1,
  "quantity": 2,
  "variant": null
}
```

**Modifier quantité** :
```http
PATCH /api/cart/items/1/
{
  "quantity": 3
}
```

**Supprimer** :
```http
DELETE /api/cart/items/1/
```

#### Utilisateurs

**Profil** :
```http
GET /api/users/profile/
PUT /api/users/profile/
```

#### Catégories

**Liste** :
```http
GET /api/categories/
```

**Détails** :
```http
GET /api/categories/1/
```

### Filtres et Recherche

**Paramètres** :
- `search` : Recherche texte
- `category` : ID catégorie
- `min_price`, `max_price` : Fourchette prix
- `tags` : IDs tags
- `sort_by` : Tri (-price, name, created_at, etc.)
- `page` : Numéro de page
- `page_size` : Taille de page

### Pagination

**Format** :
```json
{
  "count": 100,
  "next": "http://...?page=2",
  "previous": null,
  "results": [...]
}
```

---

## 🎨 Interface Utilisateur

### Templates

**Structure** :
```
templates/
├── base/          # Templates de base
├── accounts/      # Authentification
├── products/      # Produits
├── orders/        # Commandes
├── dashboard/     # Tableaux de bord
└── emails/        # Emails HTML
```

**Base Template** :
- `base.html` : Template principal
- `base_simple.html` : Version simplifiée
- `auth_base.html` : Authentification

### Composants

**Header** :
- Logo
- Navigation principale
- Recherche
- Compte utilisateur
- Panier

**Footer** :
- Liens utiles
- Newsletter
- Réseaux sociaux
- Informations légales

**Produits** :
- Grille responsive
- Images lazy loading
- Badges (promo, nouveau, etc.)
- Overlay hover

**Détails produit** :
- Image principale + galerie
- Description enrichie
- Variantes
- Avis
- Bouton ajout panier

**Panier** :
- Articles
- Calculs automatiques
- Bouton checkout
- Persistance

### Responsive Design

**Breakpoints** :
- Mobile : < 768px
- Tablet : 768px - 991px
- Desktop : > 992px

**Adaptations** :
- Menu hamburger (mobile)
- Grille flexible
- Images adaptatives
- Touches tactiles optimisées

### JavaScript

**Fichiers principaux** :
- `cart.js` : Gestion panier AJAX
- `products.js` : Produits dynamiques
- `payment.js` : Processus paiement
- `search.js` : Recherche instantanée

**Frameworks** :
- jQuery (compatibilité)
- Bootstrap 5 JS
- Popper.js

---

## 🔒 Sécurité

### Authentification

**Protection** :
- Mots de passe hashés (PBKDF2)
- Cookies sécurisés (HttpOnly, Secure)
- CSRF tokens
- Rate limiting

**2FA** :
- TOTP (base32)
- Codes sauvegarde
- Appareils de confiance

### Autorisation

**Permissions** :
- Vendeurs : Gestion de leurs produits
- Admins : Accès complet
- Clients : Consultation, achat

**Décorateurs** :
- `@login_required`
- `@user_passes_test`
- `@permission_required`

### Données Sensibles

**Protection** :
- Clés API dans `.env`
- Secrets 2FA cryptés
- Informations bancaires tokenisées
- Logs masqués

### Validation

**Formulaires** :
- Validation côté client et serveur
- Sanitization
- Validation de types
- Contraintes d'intégrité

### Headers Sécurité

**Configuration** :
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`

### Sanitization

**CKEditor** :
- Filtrage HTML
- Limitation des tags
- Nettoyage automatique

---

## 🧪 Tests

### Configuration

**Outils** :
- pytest
- pytest-django
- pytest-cov
- factory-boy
- faker

### Exécution

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov

# Tests spécifiques
pytest products/tests.py
pytest accounts/tests.py::TestUserRegistration
```

### Types de Tests

**Unitaires** :
- Modèles
- Formulaires
- Utilitaires

**Intégration** :
- Vues
- API
- Processus complets

**End-to-End** :
- Parcours utilisateur
- Workflows critiques

### Coverage

**Objectif** : > 80%

**Rapport** :
```bash
pytest --cov --cov-report=html
```

---

## 🚀 Déploiement

### Préparation

**Variables** :
- `DEBUG=False`
- `SECRET_KEY` fort
- `ALLOWED_HOSTS` configurés
- Base de données PostgreSQL
- Redis pour cache et Celery

### Collecte Statique

```bash
python manage.py collectstatic --noinput
```

### Migrations

```bash
python manage.py migrate
```

### Serveur WSGI

**Gunicorn** :
```bash
gunicorn ecommerce_site.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Configuration Web Serveur (Nginx)

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Celery & Redis

**Workers** :
```bash
celery -A ecommerce_site worker -l info
```

**Beat** (tâches périodiques) :
```bash
celery -A ecommerce_site beat -l info
```

### HTTPS

**Certificat SSL** :
- Let's Encrypt
- Configuration automatique (Certbot)

### Monitoring

**Outils** :
- Sentry (erreurs)
- New Relic (performance)
- Logging structuré

### Sauvegardes

**Stratégie** :
- Base de données : Quotidien
- Médias : Quotidien
- Rétention : 30 jours

---

## 📈 Performances

### Optimisations

**Base de données** :
- Index
- `select_related()` et `prefetch_related()`
- Requêtes optimisées

**Cache** :
- Redis
- Cache query
- Cache de template

**Assets** :
- Minification CSS/JS
- Compression images
- CDN

### Monitoring

**Métriques** :
- Temps de réponse
- Taux d'erreur
- Utilisation CPU/Mémoire
- Requêtes base de données

---

## 🐛 Dépannage

### Problèmes Courants

#### 1. Erreur de migration

```bash
python manage.py makemigrations
python manage.py migrate --fake
```

#### 2. Fichiers statiques manquants

```bash
python manage.py collectstatic --noinput
```

#### 3. Erreur d'import

```bash
pip install -r requirements.txt
```

#### 4. Erreur base de données

```bash
python manage.py dbshell
```

### Logs

**Emplacement** : `logs/django.log`

**Niveaux** :
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

---

## 📚 Ressources

### Documentation Django

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Allauth](https://django-allauth.readthedocs.io/)

### Outils

- [TinyMCE](https://www.tiny.cloud/)
- [Bootstrap 5](https://getbootstrap.com/)
- [Stripe](https://stripe.com/docs)

### Support

- Issues GitHub
- Documentation interne
- Wiki du projet

---

## 📝 Licence

Ce projet est sous licence propriétaire. Tous droits réservés.

---

## 👥 Équipe

Développé par l'équipe KefyStore.

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2024  
**Statut** : Production

---

*Documentation complète de l'application e-commerce KefyStore*
