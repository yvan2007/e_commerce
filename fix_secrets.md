# 🔒 Comment supprimer les secrets de l'historique Git

GitHub a détecté des secrets dans votre premier commit. Il faut les supprimer de l'historique Git.

## Solution : Réécrire l'historique Git

### Option 1 : Utiliser git rebase (Recommandé)

```bash
# 1. Commencer un rebase interactif depuis le début
git rebase -i --root

# 2. Dans l'éditeur qui s'ouvre, changez "pick" en "edit" pour le premier commit
# (celui qui contient les secrets)

# 3. Une fois le rebase commencé, modifier le fichier settings.py
# (déjà fait, le fichier est corrigé)

# 4. Ajouter les changements
git add ecommerce_site/settings.py

# 5. Amender le commit
git commit --amend --no-edit

# 6. Continuer le rebase
git rebase --continue

# 7. Forcer le push (ATTENTION: cela réécrit l'historique)
git push -f origin main
```

### Option 2 : Créer un nouveau commit qui supprime les secrets

Si le rebase est trop complexe, vous pouvez utiliser `git filter-branch` ou simplement forcer le push après avoir corrigé :

```bash
# 1. Modifier le commit précédent
git commit --amend

# 2. Forcer le push (ATTENTION: cela réécrit l'historique)
git push -f origin main
```

### Option 3 : Utiliser BFG Repo-Cleaner (plus simple)

1. Téléchargez BFG : https://rtyley.github.io/bfg-repo-cleaner/
2. Exécutez :
```bash
java -jar bfg.jar --replace-text passwords.txt
```

## ⚠️ ATTENTION

**Forcer le push réécrit l'historique Git**. Si d'autres personnes ont déjà cloné le repository, cela peut causer des problèmes.

Comme c'est un nouveau repository, c'est sans risque.

## Solution rapide : Recommencer avec un nouveau commit

La solution la plus simple pour vous :

1. Les secrets sont déjà retirés du code (fait ✅)
2. Créer un nouveau commit
3. Forcer le push pour remplacer l'ancien commit

```bash
git push -f origin main
```

