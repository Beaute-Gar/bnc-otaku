# ============================================================
# BNC-OTAKU — Script de lancement Windows (PowerShell)
# Utilise WampServer pour MySQL
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   BNC-OTAKU - Bureau National de"       -ForegroundColor Cyan
Write-Host "      Certification Otaku"                -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# === 1. Vérifier Python ===
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python 3.11+ non trouvé. Installe-le depuis python.org" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python : $pyVersion" -ForegroundColor Green

# === 2. Vérifier WampServer ===
$wampPath = @("C:\wamp64", "C:\wamp") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $wampPath) {
    Write-Host "[WARN] WampServer non trouvé. Assure-toi que MySQL tourne sur localhost:3306" -ForegroundColor Yellow
} else {
    Write-Host "[OK] WampServer trouvé : $wampPath" -ForegroundColor Green
}

# === 3. Installer les dépendances Python ===
Write-Host ""
Write-Host "[...] Installation des dépendances Python..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Échec de l'installation des dépendances" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dépendances installées" -ForegroundColor Green

# === 4. Installer Chromium pour Playwright ===
Write-Host ""
Write-Host "[...] Installation de Chromium pour Playwright..." -ForegroundColor Yellow
python -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Échec installation Chromium (utilisable sans WhatsApp Playwright)" -ForegroundColor Yellow
}

# === 5. Créer la base de données MySQL ===
Write-Host ""
Write-Host "[...] Création de la base de données MySQL..." -ForegroundColor Yellow
$mysqlPath = Join-Path $wampPath "bin\mysql\mysql5.7.31\bin\mysql.exe"
if (Test-Path $mysqlPath) {
    & $mysqlPath -u root < database\schema.sql 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Base de données créée" -ForegroundColor Green
    } else {
        Write-Host "[WARN] La base existe peut-être déjà" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] mysql.exe non trouvé dans WampServer. Crée la DB manuellement via phpMyAdmin :" -ForegroundColor Yellow
    Write-Host "       1. Ouvre http://localhost/phpmyadmin" -ForegroundColor Yellow
    Write-Host "       2. Exécute le contenu de database\schema.sql" -ForegroundColor Yellow
}

# === 6. Vérifier .env ===
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "[WARN] Fichier .env non trouvé !" -ForegroundColor Yellow
    Write-Host "       Copie .env.example vers .env et configure GEMINI_API_KEY" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] .env créé depuis .env.example — modifie-le avec ta clé Gemini" -ForegroundColor Green
}

# === 7. Lancer le serveur ===
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Démarrage du serveur BNC-OTAKU..."    -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   API :      http://localhost:8000"       -ForegroundColor White
Write-Host "   Docs :     http://localhost:8000/docs"  -ForegroundColor White
Write-Host "   Frontend : http://localhost:8000"       -ForegroundColor White
Write-Host ""
Write-Host "   Appuie sur Ctrl+C pour arrêter"        -ForegroundColor Gray
Write-Host ""

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
