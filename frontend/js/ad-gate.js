/*
 * ad-gate.js — Système de redirection publicitaire
 * Protocole de validation Djousse Tech Evolution
 * 
 * Pour activer la monétisation :
 * 1. Crée une zone "Interstitiel" ou "Pop-under" sur Adsterra/Monetag
 * 2. Colle le script fourni dans la fonction triggerAd()
 * 3. Le téléchargement est débloqué après 5s ou après fermeture de la pub
 */

let _adGateResolve = null;

/**
 * Déclenche la publicité Adsterra (Popunder)
 */
function triggerAd() {
    var s = document.createElement('script');
    s.src = 'https://pl29903942.effectivecpmnetwork.com/46/d3/ce/46d3ce455b49126e94fb4c7762125af8.js';
    s.async = true;
    document.head.appendChild(s);
}

/**
 * Affiche l'écran de validation publicitaire et retourne
 * une promesse résolue après 5s ou interaction pub.
 */
function showAdGate() {
    return new Promise((resolve) => {
        _adGateResolve = resolve;

        const screen = document.getElementById('adGateScreen');
        if (screen) screen.style.display = 'flex';

        // Déclenche la pub
        try { triggerAd(); } catch(e) { console.warn('[AdGate] Erreur déclenchement pub:', e); }

        // Compte à rebours
        let countdown = 5;
        const timerEl = document.getElementById('adTimer');
        const skipBtn = document.getElementById('adSkipBtn');
        if (skipBtn) skipBtn.disabled = true;

        if (timerEl) timerEl.textContent = countdown;
        // Log au backend
        fetch('/api/ad/view', { method: 'POST', headers: {'Content-Type':'application/json'} })
            .catch(() => {});

        const interval = setInterval(() => {
            countdown--;
            if (timerEl) timerEl.textContent = countdown;
            if (countdown <= 0) {
                clearInterval(interval);
                if (timerEl) timerEl.textContent = '✅';
                if (skipBtn) skipBtn.disabled = false;
                resolveAdGate();
            }
        }, 1000);
    });
}

function resolveAdGate() {
    if (_adGateResolve) {
        _adGateResolve();
        _adGateResolve = null;
    }
}

function skipAd() {
    const screen = document.getElementById('adGateScreen');
    if (screen) screen.style.display = 'none';
    resolveAdGate();
}
