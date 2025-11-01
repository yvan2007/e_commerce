@echo off
echo ========================================
echo    DEMARRAGE DU SERVEUR E-COMMERCE
echo ========================================
echo.

echo [1/3] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo [2/3] Vérification des dépendances...
python -c "import django; print('Django version:', django.get_version())"

echo.
echo [3/3] Démarrage du serveur...
echo.
echo 🌐 Serveur accessible sur: http://localhost:8000/
echo 🔧 Interface admin: http://localhost:8000/admin/
echo.
echo 💡 Pour accéder depuis votre iPhone, utilisez: start_server_mobile.bat
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur
echo.

python manage.py runserver
