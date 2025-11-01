# 🔑 Comment créer un Personal Access Token GitHub

GitHub ne permet plus l'authentification par mot de passe. Vous devez utiliser un **Personal Access Token (PAT)**.

## 📝 Étapes pour créer un PAT

### 1. Aller sur la page des tokens GitHub

Allez sur : **https://github.com/settings/tokens**

Ou suivez ce chemin :
1. Cliquez sur votre photo de profil (en haut à droite)
2. Cliquez sur **"Settings"**
3. Dans le menu de gauche, cliquez sur **"Developer settings"**
4. Cliquez sur **"Personal access tokens"**
5. Cliquez sur **"Tokens (classic)"**

### 2. Générer un nouveau token

1. Cliquez sur **"Generate new token"**
2. Sélectionnez **"Generate new token (classic)"**

### 3. Configurer le token

- **Note** : Donnez un nom descriptif, ex: `e-commerce-deployment`
- **Expiration** : Choisissez une durée (90 jours recommandé pour la sécurité)
- **Scopes** : Cochez **uniquement** :
  - ✅ **`repo`** (toutes les options sous repo seront cochées automatiquement)
    - Cela donne accès aux repositories

### 4. Générer et copier le token

1. Cliquez sur **"Generate token"** en bas de la page
2. **⚠️ IMPORTANT** : Copiez le token immédiatement ! Vous ne pourrez plus le voir après.
3. Le token ressemblera à : `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 5. Utiliser le token

Lorsque vous exécutez `git push`, GitHub vous demandera :
- **Username** : `yvan2007` (votre nom d'utilisateur GitHub)
- **Password** : Collez le token que vous venez de copier (pas votre mot de passe GitHub !)

## 🔒 Sécurité

- ✅ Ne partagez JAMAIS votre token
- ✅ Ne le commitez JAMAIS dans votre code
- ✅ Régénérez-le si vous pensez qu'il a été compromis
- ✅ Supprimez-le quand vous n'en avez plus besoin

## 📋 Résumé rapide

1. **https://github.com/settings/tokens**
2. **Generate new token (classic)**
3. Cocher **`repo`**
4. **Generate token**
5. **Copier le token**
6. Utiliser comme mot de passe lors du `git push`

