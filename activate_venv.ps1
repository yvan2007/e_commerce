# Script PowerShell pour activer l'environnement virtuel
Write-Host "Activation de l'environnement virtuel pour le projet e-commerce..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Environnement virtuel activé !" -ForegroundColor Green
Write-Host "Vous pouvez maintenant utiliser les commandes Django :" -ForegroundColor Yellow
Write-Host "  - python manage.py runserver" -ForegroundColor Cyan
Write-Host "  - python manage.py migrate" -ForegroundColor Cyan
Write-Host "  - python manage.py collectstatic" -ForegroundColor Cyan
Write-Host "  - python manage.py test" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour désactiver l'environnement virtuel, tapez : deactivate" -ForegroundColor Yellow
Write-Host ""
