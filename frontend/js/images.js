(function() {
  'use strict';

  const IMG_CACHE = {};

  // APIs publiques pour images anime
  const API_SOURCES = [
    {
      name: 'waifu',
      url: 'https://api.waifu.im/search?included_tags=landscape&is_nsfw=false',
      parse: (data) => data.images?.[0]?.url,
    },
    {
      name: 'nekos',
      url: 'https://nekos.best/api/v2/wallpaper',
      parse: (data) => data.results?.[0]?.url,
    },
    {
      name: 'anime-api',
      url: 'https://api.nekosapi.com/v3/images/random?limit=1&rating=safe',
      parse: (data) => data.data?.[0]?.image?.url || data.data?.[0]?.attributes?.file,
    },
  ];

  let currentApiIndex = 0;

  async function fetchImage() {
    for (let attempt = 0; attempt < API_SOURCES.length; attempt++) {
      const api = API_SOURCES[currentApiIndex % API_SOURCES.length];
      currentApiIndex++;

      try {
        const res = await fetch(api.url, { signal: AbortSignal.timeout(5000) });
        if (!res.ok) continue;
        const data = await res.json();
        const url = api.parse(data);
        if (url) {
          // Vérifier que l'URL est accessible
          const test = await fetch(url, { method: 'HEAD', signal: AbortSignal.timeout(3000) });
          if (test.ok) return url;
        }
      } catch(e) {
        continue;
      }
    }
    return null;
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

  // Précharger et appliquer une image
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

  // Images système : image_1.png, image_3.png, image_5.png
  // Chargées depuis les APIs externes, accessibles via window._bncImages.getImage()
  const SYSTEM_IMAGES = {
    'image_1.png': null,
    'image_3.png': null,
    'image_5.png': null,
  };

  async function loadSystemImages() {
    const keys = Object.keys(SYSTEM_IMAGES);
    for (const key of keys) {
      const url = await fetchImage();
      if (url) {
        SYSTEM_IMAGES[key] = url;
        IMG_CACHE[key] = url;
      }
    }
  }

  function getSystemImage(name) {
    return SYSTEM_IMAGES[name] || null;
  }

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

  // Exposer l'API
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

  // Charger les images au démarrage
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
      const url = await fetchImage();
      if (url) setBackgroundImage(url);
      await loadSystemImages();
      loadGalleryImages();
    });
  } else {
    setTimeout(async () => {
      const url = await fetchImage();
      if (url) setBackgroundImage(url);
      await loadSystemImages();
      loadGalleryImages();
    }, 2000);
  }
})();
