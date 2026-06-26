/**
 * BNC-Otaku — Anime Wallpaper Background Animator
 * Affiche des fonds d'écran animés style anime qui défilent
 * puis reviennent au style par défaut après un cycle.
 */
(function() {
  'use strict';

  const WALLPAPERS = [
    // 1 — Ciel crépuscule anime (Kimino Nami)
    'linear-gradient(135deg, #0f0c29, #302b63, #24243e)',
    // 2 — Lever de soleil sur Konoha (orange/or)
    'linear-gradient(135deg, #1a0a00, #e65c00, #ff8c00)',
    // 3 — Forêt de bambous (Violette Evergarden)
    'linear-gradient(135deg, #0a3d2c, #1a6b4a, #4caf7a)',
    // 4 — Ciel étoilé (Your Name)
    'linear-gradient(135deg, #0b0b2b, #1a1a4e, #2d1b69)',
    // 5 — Ville néon (Akihabara / Psycho-Pass)
    'linear-gradient(135deg, #0d0221, #3a0ca3, #f72585)',
    // 6 — Cerisiers en fleurs (Sakura)
    'linear-gradient(135deg, #2d1b3d, #ff6b9d, #ffb3c6)',
    // 7 — Océan au coucher du soleil (One Piece)
    'linear-gradient(135deg, #001f3f, #0074d9, #ff851b)',
    // 8 — Montagnes brumeuses (Mononoke)
    'linear-gradient(135deg, #1a2a1a, #3a5a3a, #6a9a6a)',
    // 9 — Temple japonais (Inuyasha)
    'linear-gradient(135deg, #1a0a00, #4a2a0a, #cc8844)',
    // 10 — Aurore boréale (anime fantastique)
    'linear-gradient(135deg, #000428, #004e92, #00d4aa, #7b2ff7)',
  ];

  let currentIndex = 0;
  let interval = null;
  let isAnimating = false;

  // Crée l'overlay de fond
  const overlay = document.createElement('div');
  overlay.id = 'anime-bg-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: -1;
    transition: background 1.5s ease;
    background: var(--primary, #1a1a2e);
    opacity: 0;
  `;
  document.body.insertBefore(overlay, document.body.firstChild);

  // Fade in after DOM ready
  requestAnimationFrame(() => { overlay.style.opacity = '0.85'; });

  function setWallpaper(index) {
    const grad = WALLPAPERS[index % WALLPAPERS.length];
    overlay.style.background = grad;
  }

  function nextWallpaper() {
    if (currentIndex >= WALLPAPERS.length) {
      stopAnimation();
      return;
    }
    setWallpaper(currentIndex);
    currentIndex++;
  }

  function startAnimation() {
    if (isAnimating) return;
    isAnimating = true;
    currentIndex = 0;
    overlay.style.opacity = '0.85';
    nextWallpaper();
    interval = setInterval(nextWallpaper, 3500); // 3.5s par wallpaper
  }

  function stopAnimation() {
    if (interval) clearInterval(interval);
    interval = null;
    isAnimating = false;
    // Retour au style par défaut (fade out)
    overlay.style.opacity = '0';
    setTimeout(() => {
      overlay.style.background = 'var(--primary, #1a1a2e)';
    }, 1500);
  }

  // Démarre automatiquement après 1 seconde (le temps que la page charge)
  setTimeout(startAnimation, 1000);

  // Redémarre si l'utilisateur clique n'importe où (touche l'écran)
  document.addEventListener('click', () => {
    if (!isAnimating) {
      // Petit délai pour pas surcharger
      setTimeout(startAnimation, 500);
    }
  });

  // Expose pour debug
  window._bncBg = { start: startAnimation, stop: stopAnimation, WALLPAPERS };
})();
