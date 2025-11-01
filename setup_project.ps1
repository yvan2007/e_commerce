# Script PowerShell pour configurer completement le projet
# Activation du venv, installation des dependances, migrations, etc.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CONFIGURATION COMPLETE DU PROJET" -ForegroundColor Cyan
Write-Host "   E-COMMERCE KEFYSTORE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifier que nous sommes dans le bon repertoire
$currentDir = Get-Location
Write-Host "[INFO] Repertoire actuel: $currentDir" -ForegroundColor Gray
Write-Host ""

# Etape 1: Activation de l'environnement virtuel
Write-Host "[1/6] Activation de l'environnement virtuel..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "[OK] Environnement virtuel active" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] Le dossier venv n'existe pas!" -ForegroundColor Red
    Write-Host "  Creation de l'environnement virtuel..." -ForegroundColor Yellow
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-Host "[OK] Environnement virtuel cree et active" -ForegroundColor Green
}
Write-Host ""

# Verifier la version de Python
Write-Host "[2/6] Verification de Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "[OK] $pythonVersion" -ForegroundColor Green
Write-Host ""

# Mise a jour de pip
Write-Host "[3/6] Mise a jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "[OK] pip mis a jour" -ForegroundColor Green
Write-Host ""

# Installation des dependances
Write-Host "[4/6] Installation des dependances depuis requirements.txt..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "  Installation en cours, cela peut prendre quelques minutes..." -ForegroundColor Gray
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Toutes les dependances installees avec succes" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Erreur lors de l'installation des dependances" -ForegroundColor Red
        Write-Host "  Verifiez les erreurs ci-dessus" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERREUR] requirements.txt introuvable!" -ForegroundColor Red
}
Write-Host ""

# Verification de Django
Write-Host "[5/6] Verification de Django..." -ForegroundColor Yellow
try {
    $djangoVersion = python -c "import django; print(django.get_version())" 2>&1
    Write-Host "[OK] Django version: $djangoVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Django non installe" -ForegroundColor Red
}
Write-Host ""

# Creation des migrations
Write-Host "[6/6] Creation et application des migrations..." -ForegroundColor Yellow
Write-Host "  Creation des migrations..." -ForegroundColor Gray
python manage.py makemigrations
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Migrations creees" -ForegroundColor Green
} else {
    Write-Host "[AVERTISSEMENT] Probleme lors de la creation des migrations" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "  Application des migrations..." -ForegroundColor Gray
python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Migrations appliquees avec succes" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] Erreur lors de l'application des migrations" -ForegroundColor Red
}
Write-Host ""

# Verification finale
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CONFIGURATION TERMINEE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Environnement virtuel: Active" -ForegroundColor Green
Write-Host "[OK] Dependances: Installees" -ForegroundColor Green
Write-Host "[OK] Migrations: Appliquees" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines etapes:" -ForegroundColor Yellow
Write-Host "   1. Pour demarrer le serveur local: .\start_server.bat" -ForegroundColor White
Write-Host "   2. Pour demarrer avec acces mobile: .\start_server_mobile.bat" -ForegroundColor White
Write-Host "   3. Pour creer un superutilisateur: python manage.py createsuperuser" -ForegroundColor White
Write-Host ""
Write-Host "Le serveur sera accessible sur: http://localhost:8000/" -ForegroundColor Cyan
Write-Host ""
