# Instructions pour accéder au site depuis votre iPhone

## Prérequis
1. Votre iPhone et votre ordinateur doivent être sur le **même réseau WiFi**
2. Le pare-feu Windows doit autoriser les connexions sur le port 8000

## Méthode 1 : Utiliser le script automatique (Recommandé)

### Windows (BAT)
1. Double-cliquez sur `start_server_mobile.bat`
2. Le script affichera automatiquement votre adresse IP locale
3. Utilisez cette adresse sur votre iPhone

### Windows PowerShell
1. Ouvrez PowerShell dans le dossier du projet
2. Exécutez : `.\start_server_mobile.ps1`
3. Utilisez l'adresse IP affichée sur votre iPhone

## Méthode 2 : Trouver l'IP manuellement

### Sur Windows :
1. Ouvrez l'invite de commande (CMD)
2. Tapez : `ipconfig`
3. Cherchez "Adresse IPv4" sous votre connexion WiFi
4. Notez cette adresse (ex: 192.168.1.100)

### Démarrer le serveur avec l'IP :
```bash
python manage.py runserver 0.0.0.0:8000
```

## Accéder depuis votre iPhone

1. **Ouvrez Safari** sur votre iPhone
2. **Assurez-vous d'être sur le même WiFi** que votre ordinateur
3. **Tapez l'adresse** : `http://VOTRE_IP:8000/`
   - Exemple : `http://192.168.1.100:8000/`

## Autoriser le pare-feu Windows

Si vous ne pouvez pas accéder depuis votre iPhone :

1. Ouvrez "Pare-feu Windows Defender"
2. Cliquez sur "Paramètres avancés"
3. Cliquez sur "Règles de trafic entrant" → "Nouvelle règle"
4. Sélectionnez "Port" → Suivant
5. TCP → Ports spécifiques : 8000 → Suivant
6. Autoriser la connexion → Suivant
7. Cochez les trois profils → Suivant
8. Nommez la règle "Django Development Server" → Terminer

## Dépannage

### Le site ne charge pas sur l'iPhone :
- ✅ Vérifiez que vous êtes sur le même WiFi
- ✅ Vérifiez que le serveur est bien démarré avec `0.0.0.0:8000`
- ✅ Vérifiez que le pare-feu autorise le port 8000
- ✅ Essayez de redémarrer le serveur

### Erreur "DisallowedHost" :
- Le fichier `settings.py` doit avoir `ALLOWED_HOSTS` avec `'*'` en développement
- Redémarrez le serveur après modification

### Connexion lente :
- Normal en développement, les fichiers statiques peuvent prendre du temps
- En production, utilisez un serveur web professionnel (Nginx + Gunicorn)

## Sécurité

⚠️ **Important** : Cette configuration est uniquement pour le développement local.
- Ne jamais utiliser `ALLOWED_HOSTS = ['*']` en production
- Ne jamais exposer votre serveur de développement sur Internet
- Utilisez uniquement sur un réseau local privé

