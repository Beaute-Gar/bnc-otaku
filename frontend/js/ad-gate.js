let _adGateResolve = null;

const AD_VIDEOS = [
  { src: 'https://cdn.pixabay.com/video/2023/09/09/180066-864428197_large.mp4', label: 'Anime World — Découvre l\'univers' },
  { src: 'https://cdn.pixabay.com/video/2024/05/30/214500_large.mp4', label: 'Otaku Paradise — Rejoins l\'aventure' },
  { src: 'https://cdn.pixabay.com/video/2025/03/26/267601_large.mp4', label: 'Sakura Dreams — Édition limitée' },
];

function triggerAd() {
  var s = document.createElement('script');
  s.src = 'https://pl29903942.effectivecpmnetwork.com/46/d3/ce/46d3ce455b49126e94fb4c7762125af8.js';
  s.async = true;
  document.head.appendChild(s);
}

function showAdGate() {
  return new Promise((resolve) => {
    _adGateResolve = resolve;

    const screen = document.getElementById('adGateScreen');
    if (screen) screen.style.display = 'flex';

    try { triggerAd(); } catch(e) { console.warn('[AdGate] Erreur déclenchement pub:', e); }

    const adVideo = document.getElementById('adVideo');
    const adLabel = document.getElementById('adLabel');
    if (adVideo && adLabel) {
      const pick = AD_VIDEOS[Math.floor(Math.random() * AD_VIDEOS.length)];
      adVideo.src = pick.src;
      adVideo.load();
      adVideo.play().catch(() => {});
      adLabel.textContent = pick.label;
    }

    let countdown = 5;
    const timerEl = document.getElementById('adTimer');
    const skipBtn = document.getElementById('adSkipBtn');
    if (skipBtn) skipBtn.disabled = true;

    if (timerEl) timerEl.textContent = countdown;

    fetch('/api/admin/ad/view', { method: 'POST', headers: {'Content-Type':'application/json'} })
      .catch(() => {});

    const interval = setInterval(() => {
      countdown--;
      if (timerEl) timerEl.textContent = countdown;
      if (countdown <= 0) {
        clearInterval(interval);
        if (timerEl) timerEl.textContent = '✅';
        if (skipBtn) skipBtn.disabled = false;
        if (adVideo) adVideo.pause();
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
