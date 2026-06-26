# Script pour préparer le déploiement WhatsApp bot sur Render
# 1. Lance le bot localement pour scanner le QR
# 2. Commit la session WhatsApp dans git
# 3. Push sur GitHub → Render déploie automatiquement

Write-Host "=== BNC-OTAKU WhatsApp - Déploiement Render ===" -ForegroundColor Cyan
Write-Host ""

$sessionDir = "whatsapp_bot\sessions\whatsapp_session"
$gitignore = ".gitignore"

# Vérifier si la session existe déjà
if (Test-Path $sessionDir) {
    Write-Host "✅ Session existante détectée" -ForegroundColor Green
    
    # Vérifier si la session est déjà dans git
    $tracked = git ls-files "$sessionDir\*" 2>$null
    if ($tracked) {
        Write-Host "   Session déjà suivie par git → push simple suffit" -ForegroundColor Green
    } else {
        Write-Host "   Session non suivie → ajout à git..." -ForegroundColor Yellow
        git add "$sessionDir\*.json" "$sessionDir\*\*.json" "$sessionDir\*\*.bin" "$sessionDir\*\*Local Storage*" "$sessionDir\*\*Cookies*" 2>$null
    }
} else {
    Write-Host "⚠️  Aucune session trouvée !" -ForegroundColor Yellow
    Write-Host "   Lance d'abord : python run_whatsapp.py" -ForegroundColor Yellow
    Write-Host "   Scanne le QR code, puis relance ce script." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "📦 Commit et push..." -ForegroundColor Cyan
git add whatsapp_bot/render_bot.py
git commit -m "WhatsApp Render Worker — session + bot" --allow-empty
git push origin main

Write-Host ""
Write-Host "✅ Déploiement déclenché !" -ForegroundColor Green
Write-Host "   Vérifie sur https://dashboard.render.com" -ForegroundColor Green
