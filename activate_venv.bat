@echo off
echo Activation de l'environnement virtuel pour le projet e-commerce...
call venv\Scripts\activate.bat
echo.
echo Environnement virtuel activé !
echo Vous pouvez maintenant utiliser les commandes Django :
echo   - python manage.py runserver
echo   - python manage.py migrate
echo   - python manage.py collectstatic
echo   - python manage.py test
echo.
echo Pour désactiver l'environnement virtuel, tapez : deactivate
echo.
