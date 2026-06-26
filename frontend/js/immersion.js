(function() {
  'use strict';

  // Mapping lettre → personnage anime (emoji + nom, l'image se charge depuis un CDN public si disponible)
  const CHARACTER_MAP = {
    A: { name: 'Arale', emoji: '👧', src: '' },
    B: { name: 'Bulma', emoji: '👩', src: '' },
    C: { name: 'Chopper', emoji: '🦌', src: '' },
    D: { name: 'Deku', emoji: '🧑', src: '' },
    E: { name: 'Eren', emoji: '⚔', src: '' },
    F: { name: 'Frieren', emoji: '🧙', src: '' },
    G: { name: 'Goku', emoji: '🐉', src: '' },
    H: { name: 'Hinata', emoji: '👧', src: '' },
    I: { name: 'Itachi', emoji: '🗡', src: '' },
    J: { name: 'Jotaro', emoji: '👊', src: '' },
    K: { name: 'Kirito', emoji: '⚔', src: '' },
    L: { name: 'Lelouch', emoji: '👑', src: '' },
    M: { name: 'Mikasa', emoji: '⚔', src: '' },
    N: { name: 'Naruto', emoji: '🍜', src: '' },
    O: { name: 'Obito', emoji: '🌀', src: '' },
    P: { name: 'Pikachu', emoji: '⚡', src: '' },
    Q: { name: 'Quatre', emoji: '👦', src: '' },
    R: { name: 'Rukia', emoji: '👩', src: '' },
    S: { name: 'Sasuke', emoji: '🗡', src: '' },
    T: { name: 'Tanjiro', emoji: '⚔', src: '' },
    U: { name: 'Usopp', emoji: '🎯', src: '' },
    V: { name: 'Vegeta', emoji: '💪', src: '' },
    W: { name: 'Watari', emoji: '👴', src: '' },
    X: { name: 'Xenovia', emoji: '⚔', src: '' },
    Y: { name: 'Yoruichi', emoji: '🐱', src: '' },
    Z: { name: 'Zoro', emoji: '⚔', src: '' },
  };

  const DEFAULT_CHAR = { name: 'Otaku', emoji: '🎌', src: '' };

  // Éléments DOM
  let charPreview = null;
  let passwordField = null;
  let charNameEl = null;
  let combatContainer = null;

  function init() {
    createCharPreview();
    createCombatEffects();
    bindEvents();
  }

  function createCharPreview() {
    const usernameField = document.getElementById('loginUsername') || document.getElementById('regUsername');
    if (!usernameField) return;

    // Conteneur preview personnage
    charPreview = document.createElement('div');
    charPreview.id = 'char-preview';
    charPreview.style.cssText = `
      display: none;
      text-align: center;
      margin-bottom: 1rem;
      padding: 1rem;
      background: rgba(0,0,0,0.3);
      border-radius: 12px;
      border: 2px solid rgba(255,215,0,0.3);
      transition: all 0.5s ease;
    `;

    const emojiEl = document.createElement('div');
    emojiEl.id = 'char-emoji';
    emojiEl.style.cssText = `
      font-size: 3rem;
      line-height: 1.2;
      margin-bottom: 0.3rem;
      opacity: 0;
      transition: opacity 0.5s ease;
      filter: drop-shadow(0 0 10px rgba(255,215,0,0.5));
    `;

    charNameEl = document.createElement('div');
    charNameEl.id = 'char-name';
    charNameEl.style.cssText = `
      font-size: 0.9rem;
      color: #ffd700;
      font-weight: 600;
      opacity: 0;
      transition: opacity 0.5s ease;
    `;

    charPreview.appendChild(emojiEl);
    charPreview.appendChild(charNameEl);

    // Insérer après le champ username
    usernameField.parentNode.insertBefore(charPreview, usernameField.nextSibling);
  }

  function createCombatEffects() {
    passwordField = document.getElementById('loginPassword') || document.getElementById('regPassword');
    if (!passwordField) return;

    combatContainer = document.createElement('div');
    combatContainer.id = 'combat-effects';
    combatContainer.style.cssText = `
      position: relative;
      height: 0;
      overflow: visible;
      pointer-events: none;
    `;
    passwordField.parentNode.style.position = 'relative';
    passwordField.parentNode.appendChild(combatContainer);
  }

  function showCharacter(letter) {
    if (!charPreview) return;
    const key = letter.toUpperCase();
    const char = CHARACTER_MAP[key] || DEFAULT_CHAR;
    const emojiEl = document.getElementById('char-emoji');
    const name = document.getElementById('char-name');

    charPreview.style.display = 'block';
    emojiEl.textContent = char.emoji;
    name.textContent = `⚔ ${char.name}`;

    setTimeout(() => {
      emojiEl.style.opacity = '1';
      name.style.opacity = '1';
    }, 100);
  }

  function hideCharacter() {
    if (!charPreview) return;
    const emojiEl = document.getElementById('char-emoji');
    const name = document.getElementById('char-name');
    emojiEl.style.opacity = '0';
    name.style.opacity = '0';
    setTimeout(() => { charPreview.style.display = 'none'; }, 500);
  }

  function triggerCombatEffect() {
    if (!combatContainer || !passwordField || passwordField.value.length === 0) return;

    const effects = [
      { emoji: '⚡', color: '#ffff00', size: 24 + Math.random() * 20 },
      { emoji: '🔥', color: '#ff4500', size: 20 + Math.random() * 24 },
      { emoji: '💥', color: '#ff0000', size: 28 + Math.random() * 16 },
      { emoji: '✨', color: '#00ffff', size: 16 + Math.random() * 20 },
      { emoji: '🌊', color: '#4169e1', size: 22 + Math.random() * 18 },
    ];

    const effect = effects[Math.floor(Math.random() * effects.length)];
    const el = document.createElement('span');
    el.textContent = effect.emoji;
    el.style.cssText = `
      position: absolute;
      font-size: ${effect.size}px;
      color: ${effect.color};
      left: ${5 + Math.random() * 90}%;
      top: ${-20 - Math.random() * 40}px;
      opacity: 0;
      pointer-events: none;
      z-index: 10;
      filter: drop-shadow(0 0 8px ${effect.color});
      animation: combatBurst 0.6s ease-out forwards;
    `;

    combatContainer.appendChild(el);

    // Éclairs sur le champ
    passwordField.style.borderColor = effect.color;
    passwordField.style.boxShadow = `0 0 20px ${effect.color}`;
    setTimeout(() => {
      passwordField.style.borderColor = 'rgba(255,255,255,0.15)';
      passwordField.style.boxShadow = 'none';
    }, 300);

    setTimeout(() => el.remove(), 800);
  }

  function bindEvents() {
    const usernameField = document.getElementById('loginUsername') || document.getElementById('regUsername');
    if (usernameField) {
      usernameField.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        if (val.length > 0) {
          showCharacter(val[0]);
        } else {
          hideCharacter();
        }
      });

      usernameField.addEventListener('blur', () => {
        // Petite persistence, ne cache pas immédiatement
      });
    }

    if (passwordField) {
      passwordField.addEventListener('keydown', (e) => {
        if (e.key.length === 1) {
          triggerCombatEffect();
        }
      });
    }
  }

  // Injecter les keyframes une fois
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes combatBurst {
      0% {
        opacity: 1;
        transform: translateY(0) scale(0.5) rotate(0deg);
      }
      50% {
        opacity: 1;
        transform: translateY(-30px) scale(1.2) rotate(180deg);
      }
      100% {
        opacity: 0;
        transform: translateY(-60px) scale(0.8) rotate(360deg);
      }
    }
  `;
  document.head.appendChild(styleSheet);

  // Init au DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
