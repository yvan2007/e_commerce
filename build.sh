#!/usr/bin/env bash
# Script de build pour Render

set -o errexit  # Exit on error

echo "🚀 Démarrage du build..."

# Installer les dépendances Python
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Collecter les fichiers statiques
echo "📁 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer les migrations si nécessaire
echo "🗄️  Création des migrations..."
python manage.py makemigrations --noinput || true

echo "✅ Build terminé avec succès!"
