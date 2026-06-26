(function() {
  'use strict';

  const OVERLAY_ID = 'anime-bg-overlay';
  const VIDEO_ID = 'anime-bg-video';

  let currentIndex = 0;
  let cycleInterval = null;
  let isPlaying = false;
  let videoElement = null;
  let overlay = null;

  // Délai avant retour au défaut (30s après la fin du cycle)
  const CYCLE_DELAY = 10000;
  const VIDEO_DURATION = 6000;

  // Images/videos anime depuis des sources externes (CDN publics)
  const WALLPAPERS = [
    'https://cdn.pixabay.com/video/2021/08/14/85345-591648036_large.mp4',
    'https://cdn.pixabay.com/video/2023/09/09/180066-864428197_large.mp4',
    'https://cdn.pixabay.com/video/2020/04/29/36911-424522214_large.mp4',
    'https://cdn.pixabay.com/video/2019/06/24/24591-346334447_large.mp4',
    'https://cdn.pixabay.com/video/2021/12/22/103095-615946841_large.mp4',
  ];

  const GRADIENT_FALLBACKS = [
    'linear-gradient(135deg, #0f0c29, #302b63, #24243e)',
    'linear-gradient(135deg, #1a0a00, #e65c00, #ff8c00)',
    'linear-gradient(135deg, #0a3d2c, #1a6b4a, #4caf7a)',
    'linear-gradient(135deg, #0b0b2b, #1a1a4e, #2d1b69)',
    'linear-gradient(135deg, #0d0221, #3a0ca3, #f72585)',
  ];

  function createOverlay() {
    if (document.getElementById(OVERLAY_ID)) return;

    overlay = document.createElement('div');
    overlay.id = OVERLAY_ID;
    overlay.style.cssText = `
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: -1;
      background: #1a1a2e;
      opacity: 0;
      transition: opacity 1.5s ease;
      overflow: hidden;
    `;

    const video = document.createElement('video');
    video.id = VIDEO_ID;
    video.muted = true;
    video.loop = false;
    video.playsInline = true;
    video.style.cssText = `
      position: absolute;
      top: 50%; left: 50%;
      min-width: 100%; min-height: 100%;
      width: auto; height: auto;
      transform: translate(-50%, -50%);
      object-fit: cover;
      opacity: 0;
      transition: opacity 1.5s ease;
    `;

    overlay.appendChild(video);
    document.body.insertBefore(overlay, document.body.firstChild);

    videoElement = video;
    requestAnimationFrame(() => { overlay.style.opacity = '0.85'; });
  }

  function playVideo(src) {
    return new Promise((resolve) => {
      if (!videoElement) return resolve(false);

      videoElement.style.opacity = '0';
      videoElement.pause();
      videoElement.src = '';
      videoElement.load();

      setTimeout(() => {
        videoElement.src = src;
        videoElement.load();

        const timeout = setTimeout(() => {
          videoElement.style.opacity = '0';
          resolve(false);
        }, 5000);

        videoElement.oncanplay = () => {
          clearTimeout(timeout);
          videoElement.style.opacity = '1';
          videoElement.play().then(() => resolve(true)).catch(() => resolve(false));
        };

        videoElement.onerror = () => {
          clearTimeout(timeout);
          videoElement.style.opacity = '0';
          resolve(false);
        };
      }, 200);
    });
  }

  function setGradientBg(index) {
    overlay.style.background = GRADIENT_FALLBACKS[index % GRADIENT_FALLBACKS.length];
    if (videoElement) {
      videoElement.style.opacity = '0';
      videoElement.pause();
      videoElement.src = '';
    }
  }

  function returnToDefault() {
    if (cycleInterval) clearInterval(cycleInterval);
    cycleInterval = null;
    isPlaying = false;

    if (videoElement) {
      videoElement.style.opacity = '0';
      videoElement.pause();
      videoElement.src = '';
    }
    overlay.style.opacity = '0';
    setTimeout(() => {
      overlay.style.background = '#1a1a2e';
    }, 1500);

    // Redémarre après CYCLE_DELAY
    setTimeout(() => {
      if (!isPlaying) startAnimation();
    }, CYCLE_DELAY);
  }

  async function nextWallpaper() {
    if (currentIndex >= WALLPAPERS.length) {
      returnToDefault();
      return;
    }

    overlay.style.opacity = '0.85';
    const success = await playVideo(WALLPAPERS[currentIndex]);
    if (!success) {
      setGradientBg(currentIndex);
    }
    currentIndex++;
  }

  function startAnimation() {
    if (isPlaying) return;
    isPlaying = true;
    currentIndex = 0;
    overlay.style.opacity = '0.85';
    nextWallpaper();
    cycleInterval = setInterval(nextWallpaper, VIDEO_DURATION);
  }

  function stopAnimation() {
    if (cycleInterval) clearInterval(cycleInterval);
    cycleInterval = null;
    isPlaying = false;
    if (videoElement) {
      videoElement.style.opacity = '0';
      videoElement.pause();
      videoElement.src = '';
    }
    overlay.style.opacity = '0';
    setTimeout(() => {
      overlay.style.background = '#1a1a2e';
    }, 1500);
  }

  function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        createOverlay();
        setTimeout(startAnimation, 1000);
      });
    } else {
      createOverlay();
      setTimeout(startAnimation, 1000);
    }

    document.addEventListener('click', () => {
      if (!isPlaying) {
        setTimeout(startAnimation, 500);
      }
    });

    window._bncBg = {
      start: startAnimation,
      stop: stopAnimation,
      next: nextWallpaper,
      WALLPAPERS,
    };
  }

  init();
})();
