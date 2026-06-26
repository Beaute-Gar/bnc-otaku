(function() {
  'use strict';

  const VIDEO_URLS = [
    'videos/anime-bg.mp4',
    'videos/sakura-bg.mp4',
    'https://cdn.pixabay.com/video/2024/05/30/214500_large.mp4',
    'https://cdn.pixabay.com/video/2022/03/26/111977-692666934_large.mp4',
    'https://cdn.pixabay.com/video/2025/03/26/267601_large.mp4',
  ];

  const CYCLE_MS = 4000;
  let currentIdx = 0;
  const video = document.getElementById('bg-video');
  if (!video) return;

  const preloader = document.createElement('video');
  preloader.muted = true;
  preloader.preload = 'auto';
  preloader.style.display = 'none';
  document.body.appendChild(preloader);

  function preloadNext(idx) {
    const src = VIDEO_URLS[idx % VIDEO_URLS.length];
    preloader.src = src;
    preloader.load();
  }

  function switchToNext() {
    currentIdx = (currentIdx + 1) % VIDEO_URLS.length;
    const src = VIDEO_URLS[currentIdx];
    video.src = src;
    video.play().catch(() => {});
    preloadNext(currentIdx + 1);
  }

  video.addEventListener('loadeddata', () => {
    video.play().catch(() => {});
  });

  video.src = VIDEO_URLS[0];
  video.play().catch(() => {});
  preloadNext(1);

  video.addEventListener('error', () => {
    switchToNext();
  });

  setInterval(switchToNext, CYCLE_MS);
})();
