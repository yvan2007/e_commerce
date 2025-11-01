# Guide de déploiement sur Render (Gratuit)

Ce guide vous explique comment déployer votre application Django e-commerce sur Render gratuitement.

## 📋 Prérequis

1. Un compte GitHub (gratuit)
2. Un compte Render (gratuit) - [S'inscrire ici](https://render.com)
3. Votre code sur GitHub

## 🚀 Étapes de déploiement

### 1. Préparer votre code

Assurez-vous que tous les fichiers suivants sont présents dans votre projet :
- ✅ `render.yaml` - Configuration Render
- ✅ `build.sh` - Script de build
- ✅ `start.sh` - Script de démarrage
- ✅ `requirements.txt` - Dépendances Python
- ✅ `.gitignore` - Fichiers à ignorer

### 2. Pousser votre code sur GitHub

```bash
git add .
git commit -m "Préparation pour déploiement Render"
git push origin main
```

### 3. Créer un compte Render

1. Allez sur [render.com](https://render.com)
2. Cliquez sur "Get Started for Free"
3. Connectez-vous avec votre compte GitHub

### 4. Créer un nouveau service Web

1. Dans le dashboard Render, cliquez sur **"New +"**
2. Sélectionnez **"Blueprint"** (ou "Web Service" si Blueprint n'est pas disponible)
3. Connectez votre repository GitHub
4. Render détectera automatiquement le fichier `render.yaml`

### 5. Configuration automatique (avec render.yaml)

Si vous utilisez `render.yaml`, Render créera automatiquement :
- ✅ Un service Web Django
- ✅ Une base de données PostgreSQL gratuite
- ✅ Toutes les variables d'environnement nécessaires

### 6. Configuration manuelle (si nécessaire)

Si vous préférez configurer manuellement :

#### Service Web Django :
- **Name**: `kefystore-ecommerce`
- **Environment**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `./start.sh`
- **Plan**: `Free`

#### Variables d'environnement :
```
PYTHON_VERSION=3.12.5
SECRET_KEY=<généré automatiquement ou votre clé>
DEBUG=False
ALLOWED_HOSTS=kefystore-ecommerce.onrender.com
DATABASE_URL=<généré automatiquement depuis la base de données>
DISABLE_COLLECTSTATIC=0
```

#### Base de données PostgreSQL :
- **Name**: `kefystore-db`
- **Plan**: `Free`
- **Database**: `kefystore_db`
- **User**: `kefystore_user`

**Important**: Copiez la variable `DATABASE_URL` depuis la base de données et ajoutez-la aux variables d'environnement du service Web.

### 7. Créer un superutilisateur

Une fois le déploiement terminé :

1. Ouvrez le **Shell** dans le dashboard Render (ou utilisez SSH)
2. Exécutez :
```bash
python manage.py createsuperuser
```

### 8. Accéder à votre application

Votre application sera accessible sur :
```
https://kefystore-ecommerce.onrender.com
```

L'interface admin sera sur :
```
https://kefystore-ecommerce.onrender.com/admin/
```

## ⚙️ Configuration des fichiers

### Fichiers déjà configurés

Tous les fichiers nécessaires sont déjà créés et configurés :

1. **render.yaml** - Configuration complète du déploiement
2. **build.sh** - Script qui installe les dépendances et collecte les fichiers statiques
3. **start.sh** - Script qui applique les migrations et démarre Gunicorn
4. **requirements.txt** - Mise à jour avec `dj-database-url` et `gunicorn`
5. **settings.py** - Modifié pour utiliser les variables d'environnement et PostgreSQL

### Variables d'environnement importantes

Vous pouvez ajouter ces variables dans le dashboard Render :

```env
# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
DEFAULT_FROM_EMAIL=KefyStore <votre-email@gmail.com>

# Site URL
SITE_URL=https://kefystore-ecommerce.onrender.com
```

## 🔧 Dépannage

### Les fichiers statiques ne s'affichent pas

Assurez-vous que :
- `DISABLE_COLLECTSTATIC=0` dans les variables d'environnement
- `whitenoise` est dans `requirements.txt`
- `whitenoise.middleware.WhiteNoiseMiddleware` est dans `MIDDLEWARE`

### Erreur de connexion à la base de données

Vérifiez que :
- La base de données PostgreSQL est créée
- `DATABASE_URL` est correctement configurée dans les variables d'environnement
- La base de données est dans le même compte Render que le service Web

### Erreur 500

Vérifiez les logs dans le dashboard Render :
1. Allez dans votre service Web
2. Cliquez sur "Logs"
3. Recherchez les erreurs

### Migrations non appliquées

Le script `start.sh` applique automatiquement les migrations. Si cela ne fonctionne pas :
1. Ouvrez le Shell dans Render
2. Exécutez : `python manage.py migrate`

## 📝 Notes importantes

### Limitations du plan gratuit

- ⏱️ **Spin down après 15 minutes d'inactivité** : Le service se met en veille après 15 minutes sans trafic
- 💾 **Base de données limitée** : 1 GB de stockage PostgreSQL gratuit
- 🌐 **URL personnalisée** : Vous pouvez utiliser votre propre domaine (optionnel)

### Migrations automatiques

Les migrations sont appliquées automatiquement au démarrage grâce au script `start.sh`.

### Fichiers média

Pour les fichiers média (images uploadées), vous devrez :
1. Utiliser un service de stockage externe (AWS S3, Cloudinary, etc.)
2. Ou configurer `django-storages` pour un stockage cloud

## 🎉 C'est tout !

Votre application devrait maintenant être déployée sur Render gratuitement !

Pour toute question, consultez la [documentation Render](https://render.com/docs).

