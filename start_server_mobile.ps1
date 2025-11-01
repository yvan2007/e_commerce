# Script PowerShell pour démarrer le serveur Django avec accès réseau local
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DEMARRAGE DU SERVEUR E-COMMERCE" -ForegroundColor Cyan
Write-Host "   ACCES RESEAU LOCAL (MOBILE)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Activation de l'environnement virtuel..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "[2/4] Vérification des dépendances..." -ForegroundColor Yellow
python -c "import django; print('Django version:', django.get_version())"

Write-Host ""
Write-Host "[3/4] Recherche de l'adresse IP locale..." -ForegroundColor Yellow

# Obtenir l'adresse IP locale
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*"} | Select-Object -First 1).IPAddress

if (-not $localIP) {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"} | Select-Object -First 1).IPAddress
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   SERVEUR ACCESSIBLE SUR:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Ordinateur local: http://localhost:8000/" -ForegroundColor White
Write-Host "📱 Mobile (iPhone): http://$localIP:8000/" -ForegroundColor Cyan
Write-Host "🔧 Interface admin: http://$localIP:8000/admin/" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 INSTRUCTIONS POUR IPHONE:" -ForegroundColor Yellow
Write-Host "   1. Assurez-vous que votre iPhone est sur le même réseau WiFi" -ForegroundColor White
Write-Host "   2. Ouvrez Safari sur votre iPhone" -ForegroundColor White
Write-Host "   3. Entrez l'adresse: http://$localIP:8000/" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: Assurez-vous que le pare-feu Windows autorise les connexions sur le port 8000" -ForegroundColor Red
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter le serveur" -ForegroundColor Yellow
Write-Host ""

Write-Host "[4/4] Démarrage du serveur..." -ForegroundColor Yellow
python manage.py runserver 0.0.0.0:8000

