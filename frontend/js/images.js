(function() {
  'use strict';

  const IMG_CACHE = {};

  const ANIME_IMAGES = [
    'https://cdn.pixabay.com/photo/2023/04/26/08/26/anime-7951551_960_720.jpg',
    'https://cdn.pixabay.com/photo/2022/12/01/18/19/anime-7629358_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/05/16/13/19/anime-7997703_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/04/21/09/03/anime-7940835_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/07/28/16/22/anime-8155178_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/04/11/01/10/anime-7915966_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/05/14/21/39/anime-7993355_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/06/26/05/00/anime-8089281_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/08/04/11/09/anime-8169592_960_720.jpg',
    'https://cdn.pixabay.com/photo/2023/02/13/14/47/anime-7787918_960_720.jpg',
  ];

  let currentIdx = 0;

  async function fetchImage() {
    const url = ANIME_IMAGES[currentIdx % ANIME_IMAGES.length];
    currentIdx++;
    return url;
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
          el.style.backgroundSize = 'cover';
          el.style.backgroundPosition = 'center';
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
    getImagePool: () => ANIME_IMAGES.slice(),
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
