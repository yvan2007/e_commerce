#!/usr/bin/env bash
# Script de démarrage pour Render

set -o errexit  # Exit on error

echo "🚀 Démarrage de l'application..."

# Appliquer les migrations
echo "🗄️  Application des migrations..."
python manage.py migrate --noinput

# Créer un superutilisateur si nécessaire (optionnel)
# python manage.py shell -c "from accounts.models import User; User.objects.filter(is_superuser=True).exists() or User.objects.create_superuser('admin', 'admin@example.com', 'changeme')"

# Démarrer Gunicorn
echo "🌐 Démarrage du serveur Gunicorn..."
gunicorn ecommerce_site.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
