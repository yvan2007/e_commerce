# 🚀 Guide Complet de Déploiement - De GitHub à Render

Ce guide vous accompagne étape par étape pour déployer votre application e-commerce sur Render.

## 📋 Prérequis

- ✅ Git installé sur votre ordinateur
- ✅ Compte GitHub créé (https://github.com/yvan2007/e_commerce.git)
- ✅ Compte Render (gratuit) - [S'inscrire ici](https://render.com)

---

## ÉTAPE 1 : Initialiser Git dans votre projet local

### 1.1 Ouvrir PowerShell dans le dossier du projet

```powershell
cd "C:\Users\YVXN20\Conception de site e-commerce"
```

### 1.2 Initialiser Git (si pas déjà fait)

```powershell
git init
```

### 1.3 Vérifier que .gitignore existe

Assurez-vous que le fichier `.gitignore` est présent (il existe déjà dans votre projet).

---

## ÉTAPE 2 : Configurer Git (si pas déjà fait)

```powershell
git config --global user.name "Votre Nom"
git config --global user.email "votre-email@example.com"
```

---

## ÉTAPE 3 : Ajouter tous les fichiers au repository

### 3.1 Vérifier l'état de Git

```powershell
git status
```

### 3.2 Ajouter tous les fichiers

```powershell
git add .
```

### 3.3 Faire le commit initial

```powershell
git commit -m "Initial commit - Application e-commerce KefyStore prête pour déploiement"
```

---

## ÉTAPE 4 : Connecter votre repository local à GitHub

### 4.1 Ajouter le remote GitHub

```powershell
git remote add origin https://github.com/yvan2007/e_commerce.git
```

### 4.2 Vérifier le remote

```powershell
git remote -v
```

Vous devriez voir :
```
origin  https://github.com/yvan2007/e_commerce.git (fetch)
origin  https://github.com/yvan2007/e_commerce.git (push)
```

---

## ÉTAPE 5 : Pousser le code sur GitHub

### 5.1 Renommer la branche principale (si nécessaire)

```powershell
git branch -M main
```

### 5.2 Pousser le code

```powershell
git push -u origin main
```

**Note** : Si c'est la première fois, GitHub vous demandera de vous authentifier. Utilisez votre nom d'utilisateur GitHub et un Personal Access Token (PAT) comme mot de passe.

### 5.3 Vérifier sur GitHub

Allez sur https://github.com/yvan2007/e_commerce et vérifiez que tous vos fichiers sont présents.

---

## ÉTAPE 6 : Créer un compte Render (si pas déjà fait)

1. Allez sur [render.com](https://render.com)
2. Cliquez sur **"Get Started for Free"**
3. Cliquez sur **"Sign up with GitHub"**
4. Autorisez Render à accéder à votre compte GitHub

---

## ÉTAPE 7 : Créer un nouveau Blueprint sur Render

### 7.1 Créer le Blueprint

1. Dans le dashboard Render, cliquez sur **"New +"** en haut à droite
2. Sélectionnez **"Blueprint"**
3. Si vous voyez "Connect a repository", cliquez dessus
4. Sélectionnez votre repository : **yvan2007/e_commerce**
5. Cliquez sur **"Apply"**

### 7.2 Render détectera automatiquement render.yaml

Render va :
- ✅ Créer un service Web Django
- ✅ Créer une base de données PostgreSQL gratuite
- ✅ Configurer toutes les variables d'environnement
- ✅ Démarrer le déploiement automatiquement

### 7.3 Attendre le déploiement

Le premier déploiement peut prendre 5-10 minutes. Vous verrez les logs en temps réel.

---

## ÉTAPE 8 : Configurer les variables d'environnement (optionnel)

Si vous avez besoin d'ajouter des variables personnalisées :

1. Allez dans votre service Web sur Render
2. Cliquez sur **"Environment"** dans le menu latéral
3. Ajoutez les variables si nécessaire :
   - `SITE_URL` = `https://votre-app.onrender.com`
   - `EMAIL_HOST_USER` = votre email (si vous utilisez l'envoi d'emails)
   - etc.

---

## ÉTAPE 9 : Créer un superutilisateur Django

### 9.1 Ouvrir le Shell Render

1. Dans votre service Web sur Render
2. Cliquez sur **"Shell"** dans le menu latéral
3. Cliquez sur **"Open Shell"**

### 9.2 Créer le superutilisateur

Dans le shell Render, exécutez :

```bash
python manage.py createsuperuser
```

Suivez les instructions :
- Username : `admin` (ou votre choix)
- Email : votre email
- Password : créez un mot de passe fort

### 9.3 Vérifier que c'est créé

```bash
python manage.py shell -c "from accounts.models import User; print(User.objects.filter(is_superuser=True).count())"
```

---

## ÉTAPE 10 : Accéder à votre application

### 10.1 URL de votre application

Une fois déployé, votre application sera accessible sur :
```
https://kefystore-ecommerce.onrender.com
```

(Le nom exact dépendra du nom que Render a généré)

### 10.2 Interface d'administration

```
https://votre-app.onrender.com/admin/
```

Connectez-vous avec les identifiants du superutilisateur créé à l'étape 9.

---

## ÉTAPE 11 : Vérifier que tout fonctionne

### 11.1 Test de la page d'accueil

1. Ouvrez votre navigateur
2. Allez sur l'URL de votre application
3. Vérifiez que la page d'accueil s'affiche

### 11.2 Test de l'admin

1. Allez sur `/admin/`
2. Connectez-vous
3. Vérifiez que vous pouvez accéder au tableau de bord admin

### 11.3 Vérifier les logs

1. Dans Render, allez dans **"Logs"**
2. Vérifiez qu'il n'y a pas d'erreurs critiques

---

## 🔧 Dépannage

### Erreur lors du push Git

**Problème** : "remote: Support for password authentication was removed"

**Solution** : Utilisez un Personal Access Token :
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Sélectionnez les scopes : `repo`
4. Copiez le token
5. Utilisez-le comme mot de passe lors du `git push`

### Erreur de build sur Render

**Vérifier** :
1. Les logs dans Render → Logs
2. Que `requirements.txt` contient toutes les dépendances
3. Que `build.sh` a les permissions d'exécution (devrait être automatique)

### Erreur de base de données

**Vérifier** :
1. Que la base de données PostgreSQL est créée
2. Que `DATABASE_URL` est bien configurée dans les variables d'environnement
3. Les logs pour voir les erreurs de connexion

### Les fichiers statiques ne s'affichent pas

**Vérifier** :
1. Que `DISABLE_COLLECTSTATIC=0` dans les variables d'environnement
2. Que `whitenoise` est dans `requirements.txt`
3. Que WhiteNoise middleware est dans `settings.py`

---

## 📝 Checklist finale

- [ ] Code poussé sur GitHub
- [ ] Repository visible sur GitHub avec tous les fichiers
- [ ] Blueprint créé sur Render
- [ ] Service Web déployé avec succès
- [ ] Base de données PostgreSQL créée
- [ ] Superutilisateur créé
- [ ] Application accessible sur l'URL Render
- [ ] Interface admin fonctionnelle
- [ ] Pas d'erreurs dans les logs

---

## 🎉 Félicitations !

Votre application e-commerce est maintenant déployée et accessible en ligne !

### Prochaines étapes possibles :

1. **Configurer un domaine personnalisé** (optionnel, payant)
2. **Configurer les emails** pour les notifications
3. **Configurer un stockage cloud** pour les fichiers média (AWS S3, Cloudinary)
4. **Ajouter un monitoring** (Sentry, etc.)
5. **Configurer les backups** de la base de données

---

## 📞 Support

- Documentation Render : https://render.com/docs
- Documentation Django : https://docs.djangoproject.com
- Support Render : support@render.com

