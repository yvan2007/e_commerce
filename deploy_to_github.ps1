# Script PowerShell pour automatiser le déploiement sur GitHub
# Ce script vous guide étape par étape

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DEPLOIEMENT SUR GITHUB" -ForegroundColor Cyan
Write-Host "   E-COMMERCE KEFYSTORE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que Git est installé
Write-Host "[1/8] Verification de Git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version
    Write-Host "[OK] $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Git n'est pas installe!" -ForegroundColor Red
    Write-Host "  Installez Git depuis: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Vérifier que nous sommes dans le bon répertoire
Write-Host "[2/8] Verification du repertoire..." -ForegroundColor Yellow
$currentDir = Get-Location
Write-Host "[INFO] Repertoire actuel: $currentDir" -ForegroundColor Gray

if (-not (Test-Path "manage.py")) {
    Write-Host "[ERREUR] manage.py introuvable!" -ForegroundColor Red
    Write-Host "  Assurez-vous d'etre dans le dossier du projet Django" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Repertoire correct" -ForegroundColor Green
Write-Host ""

# Initialiser Git si nécessaire
Write-Host "[3/8] Initialisation de Git..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    Write-Host "  Initialisation du repository Git..." -ForegroundColor Gray
    git init
    Write-Host "[OK] Repository Git initialise" -ForegroundColor Green
} else {
    Write-Host "[OK] Repository Git deja initialise" -ForegroundColor Green
}
Write-Host ""

# Vérifier la configuration Git
Write-Host "[4/8] Verification de la configuration Git..." -ForegroundColor Yellow
$gitUser = git config --global user.name
$gitEmail = git config --global user.email

if (-not $gitUser -or -not $gitEmail) {
    Write-Host "[ATTENTION] Configuration Git incomplete" -ForegroundColor Yellow
    Write-Host "  Nom d'utilisateur: $gitUser" -ForegroundColor Gray
    Write-Host "  Email: $gitEmail" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Voulez-vous configurer Git maintenant? (O/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "O" -or $response -eq "o") {
        $name = Read-Host "Entrez votre nom"
        $email = Read-Host "Entrez votre email"
        git config --global user.name $name
        git config --global user.email $email
        Write-Host "[OK] Configuration Git mise a jour" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] Configuration Git: $gitUser <$gitEmail>" -ForegroundColor Green
}
Write-Host ""

# Vérifier le remote GitHub
Write-Host "[5/8] Verification du remote GitHub..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin 2>$null

if ($remoteUrl) {
    Write-Host "[OK] Remote existant: $remoteUrl" -ForegroundColor Green
    Write-Host "Voulez-vous le changer? (O/N)" -ForegroundColor Yellow
    $changeRemote = Read-Host
    if ($changeRemote -eq "O" -or $changeRemote -eq "o") {
        git remote remove origin
        $remoteUrl = $null
    }
}

if (-not $remoteUrl) {
    Write-Host "  Ajout du remote GitHub..." -ForegroundColor Gray
    git remote add origin https://github.com/yvan2007/e_commerce.git
    Write-Host "[OK] Remote GitHub ajoute" -ForegroundColor Green
}
Write-Host ""

# Vérifier l'état de Git
Write-Host "[6/8] Verification de l'etat Git..." -ForegroundColor Yellow
git status
Write-Host ""

# Ajouter tous les fichiers
Write-Host "[7/8] Ajout des fichiers..." -ForegroundColor Yellow
Write-Host "  Ajout de tous les fichiers au staging..." -ForegroundColor Gray
git add .
Write-Host "[OK] Fichiers ajoutes" -ForegroundColor Green
Write-Host ""

# Faire le commit
Write-Host "[8/8] Creation du commit..." -ForegroundColor Yellow
$commitMessage = "Initial commit - Application e-commerce KefyStore prête pour déploiement"
Write-Host "  Message de commit: $commitMessage" -ForegroundColor Gray
git commit -m $commitMessage
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Commit cree avec succes" -ForegroundColor Green
} else {
    Write-Host "[ATTENTION] Aucun changement a commiter" -ForegroundColor Yellow
}
Write-Host ""

# Résumé et instructions
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ETAPES SUIVANTES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Renommer la branche principale (si necessaire):" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor White
Write-Host ""
Write-Host "2. Pousser le code sur GitHub:" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "   Note: Si c'est la premiere fois, GitHub vous demandera:" -ForegroundColor Gray
Write-Host "   - Username: votre nom d'utilisateur GitHub" -ForegroundColor Gray
Write-Host "   - Password: un Personal Access Token (PAT)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Creer un Personal Access Token:" -ForegroundColor Yellow
Write-Host "   https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host "   -> Generate new token (classic)" -ForegroundColor Gray
Write-Host "   -> Selectionnez 'repo' scope" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Apres le push, allez sur Render:" -ForegroundColor Yellow
Write-Host "   https://render.com" -ForegroundColor Cyan
Write-Host "   -> New + -> Blueprint" -ForegroundColor Gray
Write-Host "   -> Connecter votre repository" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

