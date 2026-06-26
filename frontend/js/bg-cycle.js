(function() {
  'use strict';

  var bg = document.getElementById('bg-image');
  if (!bg) return;

  var images = [];
  for (var i = 1; i <= 20; i++) {
    images.push('wallpapers/wp_' + String(i).padStart(2, '0') + '.jpg');
  }

  var DELAY = 4000;
  var idx = 0;
  var timer = null;

  function setBg(src) {
    bg.style.backgroundImage = 'url(' + src + ')';
  }

  function next() {
    idx = (idx + 1) % images.length;
    setBg(images[idx]);
  }

  function scheduleNext() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(next, DELAY);
  }

  setBg(images[0]);

  document.addEventListener('mousemove', scheduleNext);
})();
