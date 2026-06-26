(function() {
  'use strict';

  const IMG_CACHE = {};

  const FALLBACK_IMAGES = [
    'https://picsum.photos/seed/anime1/800/600',
    'https://picsum.photos/seed/anime2/800/600',
    'https://picsum.photos/seed/anime3/800/600',
    'https://picsum.photos/seed/anime4/800/600',
    'https://picsum.photos/seed/anime5/800/600',
  ];

  let fbIdx = 0;

  async function fetchImage() {
    const fb = FALLBACK_IMAGES[fbIdx % FALLBACK_IMAGES.length];
    fbIdx++;
    return fb;
  }

  function setBackgroundImage(url) {
    const overlay = document.getElementById('anime-bg-overlay');
    if (!overlay) return;
    if (url) {
      overlay.style.background = `url(${url}) center/cover no-repeat`;
      overlay.style.opacity = '0.85';
    }
  }

  function resetToDefault() {
    const overlay = document.getElementById('anime-bg-overlay');
    if (!overlay) return;
    overlay.style.background = '#1a1a2e';
    overlay.style.opacity = '0.85';
  }

  async function loadAndApplyImage(targetId = null) {
    const url = await fetchImage();
    if (!url) return false;
    if (targetId) {
      const el = document.getElementById(targetId);
      if (el) {
        el.style.backgroundImage = `url(${url})`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundPosition = 'center';
      }
    }
    IMG_CACHE[targetId || 'bg'] = url;
    return url;
  }

  const SYSTEM_IMAGES = { 'image_1.png': null, 'image_3.png': null, 'image_5.png': null };

  async function loadSystemImages() {
    for (const key of Object.keys(SYSTEM_IMAGES)) {
      SYSTEM_IMAGES[key] = await fetchImage();
      IMG_CACHE[key] = SYSTEM_IMAGES[key];
    }
  }

  function getSystemImage(name) { return SYSTEM_IMAGES[name] || null; }

  function applySystemImage(name, elementId) {
    const url = SYSTEM_IMAGES[name];
    if (!url) return false;
    const el = document.getElementById(elementId);
    if (!el) return false;
    el.style.backgroundImage = `url(${url})`;
    return true;
  }

  async function loadGalleryImages() {
    const targets = ['anime-image-1', 'anime-image-2', 'anime-image-3'];
    for (const id of targets) {
      const url = await fetchImage();
      if (url) {
        const el = document.getElementById(id);
        if (el) {
          el.style.backgroundImage = `url(${url})`;
          IMG_CACHE[id] = url;
        }
      }
    }
  }

  window._bncImages = {
    fetchImage,
    setBackgroundImage,
    resetToDefault,
    loadAndApplyImage,
    loadGalleryImages,
    loadSystemImages,
    getSystemImage,
    applySystemImage,
    getCache: () => IMG_CACHE,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
      await loadSystemImages();
      loadGalleryImages();
    });
  } else {
    setTimeout(async () => {
      await loadSystemImages();
      loadGalleryImages();
    }, 500);
  }
})();
