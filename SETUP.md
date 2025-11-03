# Guide d'Installation et de Configuration - KefyStore E-Commerce

Ce guide vous aidera à configurer et lancer le projet KefyStore depuis GitHub sur une nouvelle machine.

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Python 3.10 ou supérieur** ([Télécharger Python](https://www.python.org/downloads/))
- **Git** ([Télécharger Git](https://git-scm.com/downloads))
- **Un éditeur de code** (VS Code, PyCharm, etc.)

### Vérification de l'installation

Ouvrez un terminal (PowerShell sur Windows, Terminal sur Mac/Linux) et vérifiez :

```bash
python --version
# Doit afficher Python 3.10.x ou supérieur

git --version
# Doit afficher une version de Git
```

## 🚀 Installation étape par étape

### 1. Cloner le projet depuis GitHub

```bash
# Cloner le dépôt
git clone https://github.com/yvan2007/e_commerce.git

# Entrer dans le dossier du projet
cd e_commerce
```

### 2. Créer un environnement virtuel (Virtual Environment)

#### Sur Windows (PowerShell) :

```powershell
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Si vous avez une erreur d'exécution de script, exécutez d'abord :
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Sur Windows (CMD) :

```cmd
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
venv\Scripts\activate.bat
```

#### Sur Mac/Linux :

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate
```

**✅ Vérification :** Vous devriez voir `(venv)` au début de votre ligne de commande.

### 3. Installer les dépendances

```bash
# Mettre à jour pip
python -m pip install --upgrade pip

# Installer toutes les dépendances
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet en copiant le fichier exemple :

```bash
# Sur Windows (PowerShell)
Copy-Item env.example .env

# Sur Windows (CMD)
copy env.example .env

# Sur Mac/Linux
cp env.example .env
```

**Modifiez le fichier `.env`** et configurez les variables suivantes (minimum requis) :

```env
# Configuration Django
DEBUG=True
SECRET_KEY=votre-secret-key-generee-aleatoirement

# Base de données (SQLite par défaut en développement)
# Pour PostgreSQL : postgresql://user:password@localhost:5432/dbname
# Pour MySQL : mysql://user:password@localhost:3306/dbname
DATABASE_URL=sqlite:///db.sqlite3

# Configuration Email (optionnel pour le développement)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-application

# Configuration de paiement (optionnel - voir payment_api_config.env.example)
PAYMENT_API_KEY=votre-cle-api
PAYMENT_API_SECRET=votre-secret-api

# Allowed hosts (pour la production)
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Pour générer un SECRET_KEY Django :**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Appliquer les migrations de la base de données

```bash
# Créer les migrations (si nécessaire)
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate
```

### 6. Créer un superutilisateur (admin)

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer votre compte administrateur :
- Nom d'utilisateur
- Email
- Mot de passe (il sera masqué lors de la saisie)

### 7. Collecter les fichiers statiques (pour le développement)

```bash
python manage.py collectstatic --noinput
```

### 8. (Optionnel) Charger des données de test

```bash
# Créer des catégories et tags
python manage.py create_categories_and_tags

# Créer des produits d'exemple
python manage.py create_sample_products
```

## ▶️ Lancer le serveur de développement

```bash
python manage.py runserver
```

Le serveur démarre généralement sur **http://127.0.0.1:8000/**

Ouvrez votre navigateur et accédez à :
- **Site web :** http://127.0.0.1:8000/
- **Administration :** http://127.0.0.1:8000/admin/

## 🛠️ Configuration Pre-commit (Recommandé)

Pour maintenir la qualité du code, le projet utilise pre-commit pour formater automatiquement le code avant chaque commit.

### Installation de pre-commit :

```bash
# Installer pre-commit (si pas déjà fait)
pip install pre-commit

# Installer les hooks Git
pre-commit install
```

Désormais, à chaque `git commit`, le code sera automatiquement formaté et vérifié.

### Exécuter pre-commit manuellement :

```bash
# Sur tous les fichiers
pre-commit run --all-files

# Sur les fichiers modifiés uniquement
pre-commit run
```

## 📦 Structure du projet

```
e_commerce/
├── accounts/          # Gestion des utilisateurs et authentification
├── products/          # Gestion des produits
├── orders/            # Gestion des commandes et panier
├── payment_system/     # Système de paiement
├── delivery_system/   # Système de livraison
├── reviews/           # Avis et commentaires
├── notifications/      # Système de notifications
├── dashboard/          # Tableaux de bord (admin/vendeur)
├── static/            # Fichiers statiques (CSS, JS, images)
├── templates/         # Templates HTML
├── media/             # Fichiers uploadés (images produits, etc.)
├── ecommerce_site/    # Configuration Django principale
├── manage.py          # Script de gestion Django
├── requirements.txt   # Dépendances Python
├── .env               # Variables d'environnement (à créer)
├── .pre-commit-config.yaml  # Configuration pre-commit
└── SETUP.md           # Ce fichier
```

## 🔧 Commandes utiles

### Gestion de la base de données

```bash
# Créer de nouvelles migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Accéder à la console Django
python manage.py shell
```

### Gestion des utilisateurs et données

```bash
# Créer un superutilisateur
python manage.py createsuperuser

# Créer des catégories et tags
python manage.py create_categories_and_tags

# Créer des produits d'exemple
python manage.py create_sample_products

# Renouveler le stock des produits
python manage.py renew_stock
```

### Développement

```bash
# Lancer le serveur de développement
python manage.py runserver

# Lancer le serveur sur un port spécifique
python manage.py runserver 8080

# Vérifier les erreurs du projet
python manage.py check

# Collecter les fichiers statiques
python manage.py collectstatic
```

## 🌍 Configuration de la langue

Le projet supporte le français (par défaut) et l'anglais.

```bash
# Générer les fichiers de traduction
python manage.py makemessages -l en

# Compiler les traductions
python manage.py compilemessages
```

## 🔒 Sécurité

### Pour la production :

1. **Modifiez `DEBUG = False`** dans `settings.py`
2. **Générez une nouvelle `SECRET_KEY`** et gardez-la secrète
3. **Utilisez une base de données PostgreSQL** ou MySQL au lieu de SQLite
4. **Configurez HTTPS**
5. **Définissez `ALLOWED_HOSTS`** dans `.env`
6. **Utilisez un serveur web** (nginx + gunicorn) au lieu du serveur de développement

## ❓ Problèmes courants

### Erreur : "ModuleNotFoundError: No module named 'X'"

**Solution :** Vérifiez que votre environnement virtuel est activé et installez les dépendances :
```bash
pip install -r requirements.txt
```

### Erreur : "django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty"

**Solution :** Créez un fichier `.env` avec un `SECRET_KEY` valide (voir étape 4).

### Erreur : "Port already in use"

**Solution :** Utilisez un autre port :
```bash
python manage.py runserver 8080
```

### Erreur lors de l'activation du venv (Windows PowerShell)

**Solution :** Exécutez :
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Puis réessayez d'activer le venv.

### Erreur : "pre-commit: command not found"

**Solution :** Installez pre-commit :
```bash
pip install pre-commit
pre-commit install
```

## 📝 Contribution au projet

### Workflow Git recommandé :

```bash
# 1. Créer une nouvelle branche
git checkout -b feature/nom-de-la-fonctionnalite

# 2. Faire vos modifications
# ... modifier les fichiers ...

# 3. Vérifier le code avant de committer
pre-commit run --all-files

# 4. Ajouter les fichiers modifiés
git add .

# 5. Committer (pre-commit s'exécutera automatiquement)
git commit -m "Description de vos modifications"

# 6. Pousser vers GitHub
git push origin feature/nom-de-la-fonctionnalite
```

### Standards de code :

- Le code est automatiquement formaté avec **Black** et **isort**
- Respectez les conventions PEP 8 (vérifiées par flake8)
- Ajoutez des commentaires pour le code complexe
- Utilisez des noms de variables et fonctions explicites

## 📚 Ressources supplémentaires

- [Documentation Django](https://docs.djangoproject.com/)
- [Documentation pre-commit](https://pre-commit.com/)
- [Documentation Black](https://black.readthedocs.io/)

## 🆘 Besoin d'aide ?

Si vous rencontrez des problèmes :

1. Vérifiez que toutes les étapes de ce guide sont suivies
2. Consultez les logs dans le dossier `logs/`
3. Vérifiez la console du navigateur pour les erreurs JavaScript
4. Consultez la documentation Django pour les erreurs spécifiques

## 📄 Licence

[Indiquez ici la licence du projet]

---

**Bon développement ! 🚀**
