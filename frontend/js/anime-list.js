(function () {
  'use strict';

  var section = document.querySelector('.anime-list');
  var cursor = document.getElementById('animeCursor');
  var hoverImg = document.getElementById('animeHoverImg');
  var hoverImgEl = hoverImg.querySelector('img');
  var items = document.querySelectorAll('.anime-list__item');

  if (!section || !cursor || !hoverImg || !items.length) return;

  items.forEach(function (item) {
    var title = item.querySelector('.anime-list__title');
    if (title && !title.dataset.text) title.dataset.text = title.textContent;
  });

  var isInside = false;
  var mouseX = 0, mouseY = 0;
  var imgX = 0, imgY = 0;
  var cursorX = 0, cursorY = 0;
  var rafId = null;

  var chars = '!<>-_\\/[]{}—=+*^?#________';

  function scramble(el, text) {
    var oldText = el.textContent;
    var length = Math.max(oldText.length, text.length);
    var frame = 0;
    var maxFrames = 20;
    var queue = [];
    for (var i = 0; i < length; i++) {
      var from = oldText[i] || '';
      var to = text[i] || '';
      var start = Math.floor(Math.random() * maxFrames);
      var end = start + Math.floor(Math.random() * maxFrames);
      queue.push({ from: from, to: to, start: start, end: end });
    }
    function tick() {
      frame++;
      var output = '';
      for (var i = 0; i < queue.length; i++) {
        var q = queue[i];
        var ch;
        if (frame < q.start) ch = q.from;
        else if (frame < q.end) ch = chars[Math.floor(Math.random() * chars.length)];
        else ch = q.to;
        output += ch;
      }
      el.textContent = output;
      if (frame < maxFrames) requestAnimationFrame(tick);
    }
    tick();
  }

  if (typeof gsap !== 'undefined') {
    gsap.from('.anime-list__item', {
      y: 60, opacity: 0, duration: 0.8, stagger: 0.08, ease: 'power3.out',
      scrollTrigger: { trigger: '.anime-list', start: 'top 85%', toggleActions: 'play none none none' }
    });
  }

  function onMouseMove(e) { mouseX = e.clientX; mouseY = e.clientY; }
  function onMouseEnter() {
    isInside = true;
    cursor.classList.add('active');
    if (!rafId) rafId = requestAnimationFrame(loop);
  }
  function onMouseLeave() {
    isInside = false;
    cursor.classList.remove('active', 'hovering');
    hoverImg.classList.remove('visible');
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    items.forEach(function (item) {
      var t = item.querySelector('.anime-list__title');
      if (t && t.dataset.text) t.textContent = t.dataset.text;
    });
  }

  section.addEventListener('mouseenter', onMouseEnter);
  section.addEventListener('mouseleave', onMouseLeave);
  document.addEventListener('mousemove', onMouseMove);

  items.forEach(function (item) {
    item.addEventListener('mouseenter', function () {
      cursor.classList.add('hovering');
      var src = item.dataset.image;
      if (src) {
        hoverImgEl.src = src;
        hoverImgEl.onload = function () { hoverImg.classList.add('visible'); };
        hoverImgEl.onerror = function () { hoverImg.classList.remove('visible'); };
      }
      var title = item.querySelector('.anime-list__title');
      if (title && title.dataset.text) scramble(title, title.dataset.text);
    });
    item.addEventListener('mouseleave', function () {
      cursor.classList.remove('hovering');
      hoverImg.classList.remove('visible');
      var title = item.querySelector('.anime-list__title');
      if (title && title.dataset.text) title.textContent = title.dataset.text;
    });
  });

  function loop() {
    cursorX += (mouseX - cursorX) * 0.15;
    cursorY += (mouseY - cursorY) * 0.15;
    cursor.style.left = cursorX + 'px';
    cursor.style.top = cursorY + 'px';
    imgX += (mouseX - imgX) * 0.1;
    imgY += (mouseY - imgY) * 0.1;
    hoverImg.style.left = (imgX + 30) + 'px';
    hoverImg.style.top = (imgY - 140) + 'px';
    if (isInside) rafId = requestAnimationFrame(loop);
    else rafId = null;
  }

})();
