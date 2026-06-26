(function() {
  'use strict';

  let currentAudio = null;
  let isPlaying = false;
  let volume = 0.3;

  // Pistes audio libres depuis SoundHelix (libres de droits)
  const TRACKS = {
    opening: [
      'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
      'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
    ],
    junior: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
    senior: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
    master: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3',
    legendary: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3',
    default: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3',
  };

  const DIFFICULTY_TRACKS = {
    'Junior Otaku': 'junior',
    'Senior Otaku': 'senior',
    'Master Otaku': 'master',
    'Otaku Legendaire': 'legendary',
  };

  const DIFFICULTY_VOLUME = {
    'Junior Otaku': 0.15,
    'Senior Otaku': 0.20,
    'Master Otaku': 0.30,
    'Otaku Legendaire': 0.40,
  };

  function play(url, opts = {}) {
    stop();
    try {
      currentAudio = new Audio(url);
      currentAudio.volume = opts.volume !== undefined ? opts.volume : volume;
      if (opts.loop !== false) currentAudio.loop = true;
      currentAudio.play().catch(() => {});
      isPlaying = true;
    } catch(e) {
      isPlaying = false;
    }
  }

  function stop() {
    if (currentAudio) {
      try {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      } catch(e) {}
      currentAudio = null;
    }
    isPlaying = false;
  }

  function fadeOut(duration = 500) {
    if (!currentAudio) return;
    const startVol = currentAudio.volume;
    const step = startVol / (duration / 50);
    const interval = setInterval(() => {
      if (!currentAudio) { clearInterval(interval); return; }
      const newVol = Math.max(0, currentAudio.volume - step);
      currentAudio.volume = newVol;
      if (newVol <= 0) {
        clearInterval(interval);
        stop();
      }
    }, 50);
  }

  function playOpening() {
    const track = TRACKS.opening[Math.floor(Math.random() * TRACKS.opening.length)];
    play(track, { volume: 0.5, loop: false });
  }

  function playQuizMusic(difficulty) {
    const key = DIFFICULTY_TRACKS[difficulty] || 'default';
    const track = TRACKS[key];
    const vol = DIFFICULTY_VOLUME[difficulty] !== undefined ? DIFFICULTY_VOLUME[difficulty] : 0.2;
    play(track, { volume: vol, loop: true });
  }

  function stopMusic() {
    stop();
  }

  window._bncAudio = {
    playOpening,
    playQuizMusic,
    stopMusic,
    stop,
    fadeOut,
    play,
    TRACKS,
  };
})();
