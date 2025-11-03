@echo off
setlocal enabledelayedexpansion
echo ========================================
echo    DEMARRAGE DU SERVEUR E-COMMERCE
echo    ACCES RESEAU LOCAL (MOBILE)
echo ========================================
echo.

echo [1/4] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo [2/4] Vérification des dépendances...
python -c "import django; print('Django version:', django.get_version())"

echo.
echo [3/4] Recherche de l'adresse IP locale...
set LOCAL_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set TEMP_IP=%%a
    set TEMP_IP=!TEMP_IP: =!
    if "!LOCAL_IP!"=="" set LOCAL_IP=!TEMP_IP!
)

if "!LOCAL_IP!"=="" (
    echo ⚠️  Impossible de trouver l'adresse IP automatiquement
    echo.
    echo Veuillez trouver votre IP manuellement:
    echo   1. Ouvrez CMD et tapez: ipconfig
    echo   2. Cherchez "Adresse IPv4" sous votre connexion WiFi
    echo   3. Utilisez cette adresse sur votre iPhone
    echo.
    set LOCAL_IP=192.168.1.XXX
)

echo.
echo ========================================
echo    SERVEUR ACCESSIBLE SUR:
echo ========================================
echo.
echo 🌐 Ordinateur local: http://localhost:8000/
echo 📱 Mobile (iPhone): http://!LOCAL_IP!:8000/
echo 🔧 Interface admin: http://!LOCAL_IP!:8000/admin/
echo.
echo 📋 INSTRUCTIONS POUR IPHONE:
echo    1. Assurez-vous que votre iPhone est sur le meme reseau WiFi
echo    2. Ouvrez Safari sur votre iPhone
echo    3. Entrez l'adresse: http://!LOCAL_IP!:8000/
echo.
echo ⚠️  IMPORTANT: Assurez-vous que le pare-feu Windows autorise les connexions sur le port 8000
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur
echo.

echo [4/4] Démarrage du serveur...
python manage.py runserver 0.0.0.0:8000
