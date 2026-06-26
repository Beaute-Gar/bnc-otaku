(function() {
  'use strict';

  const STEPS = [
    {
      title: '👋 Bienvenue sur BNC-Otaku !',
      text: 'Je suis ton guide personnel. Je vais t\'accompagner pas à pas pour utiliser le site. Clique sur "Suivant" pour commencer !',
      speak: 'Bienvenue sur BNC-Otaku ! Je suis ton guide personnel. Je vais t accompagner pas à pas.',
    },
    {
      title: '🔑 Étape 1 : Créer un compte',
      text: 'Clique sur "Connexion" en haut à droite. Crée ton compte avec un pseudo, un email et un mot de passe. C\'est gratuit !',
      speak: 'Étape 1 : Crée ton compte en cliquant sur Connexion en haut à droite.',
      highlight: 'login-link',
    },
    {
      title: '🎯 Étape 2 : Choisis ton niveau',
      text: 'Une fois connecté, va dans la section "Examen". Tu verras 4 niveaux : Junior Otaku, Senior Otaku, Master Otaku et Otaku Légendaire. Commence par le Junior !',
      speak: 'Étape 2 : Va dans la section Examen et choisis ton premier niveau.',
    },
    {
      title: '📝 Les niveaux expliqués',
      text: '🌟 Junior Otaku → Les bases de la culture anime.\n⭐ Senior Otaku → Connaissances approfondies.\n🏆 Master Otaku → Maîtrise des univers.\n👑 Otaku Légendaire → Réservé aux vrais experts !',
      speak: 'Il y a 4 niveaux progressifs, du Junior au Légendaire.',
    },
    {
      title: '📋 Étape 3 : Passe l\'examen',
      text: 'Chaque niveau contient 20 questions. Tu dois avoir au moins 55% pour valider et débloquer le niveau suivant. Prends ton temps, il n\'y a pas de limite !',
      speak: 'Étape 3 : Réponds aux 20 questions. Il faut 55% pour valider le niveau.',
    },
    {
      title: '⚠️ Attention au personnage !',
      text: 'Si tu restes inactif plus de 15 secondes, un personnage d\'anime apparaîtra pour te secouer ! Alors reste concentré !',
      speak: 'Attention ! Si tu restes inactif trop longtemps, un personnage va se fâcher !',
    },
    {
      title: '🎓 Étape 4 : Télécharge ton diplôme',
      text: 'Après avoir validé un niveau, tu peux télécharger ton certificat officiel signé par BeauteGar, Directeur de Djousse Tech Evolution.',
      speak: 'Étape 4 : Télécharge ton certificat officiel après chaque niveau réussi.',
    },
    {
      title: '📱 Rejoins la communauté',
      text: 'Rejoins-nous sur Telegram et WhatsApp ! Les liens sont en bas de chaque page. Partage ton exploit avec tes amis !',
      speak: 'Rejoins la communauté sur Telegram et WhatsApp !',
    },
    {
      title: '✅ Prêt à commencer ?',
      text: 'Tu sais tout ! Va créer ton compte et commence ton aventure d\'Otaku. Bonne chance, candidat ! 🍀',
      speak: 'Tu es prêt ! Va créer ton compte et bonne chance pour l examen !',
    },
  ];

  const ASSISTANT_STORAGE_KEY = 'bnc_assistant_done';

  let currentStep = 0;
  let isOpen = false;
  let isMinimized = false;
  let speechSynth = window.speechSynthesis;
  let utter = null;

  function getChar() {
    const user = getUser();
    const initial = user && user.username ? user.username.charAt(0).toUpperCase() : 'N';
    const chars = {
      A: { emoji: '👧', name: 'Arale' }, B: { emoji: '👩', name: 'Bulma' }, C: { emoji: '🦌', name: 'Chopper' },
      D: { emoji: '🧑', name: 'Deku' }, E: { emoji: '⚔', name: 'Eren' }, F: { emoji: '🧙', name: 'Frieren' },
      G: { emoji: '🐉', name: 'Goku' }, H: { emoji: '👧', name: 'Hinata' }, I: { emoji: '🗡', name: 'Itachi' },
      J: { emoji: '👊', name: 'Jotaro' }, K: { emoji: '⚔', name: 'Kirito' }, L: { emoji: '👑', name: 'Lelouch' },
      M: { emoji: '⚔', name: 'Mikasa' }, N: { emoji: '🍜', name: 'Naruto' }, O: { emoji: '🌀', name: 'Obito' },
      P: { emoji: '⚡', name: 'Pikachu' }, Q: { emoji: '👦', name: 'Quatre' }, R: { emoji: '👩', name: 'Rukia' },
      S: { emoji: '🗡', name: 'Sasuke' }, T: { emoji: '⚔', name: 'Tanjiro' }, U: { emoji: '🎯', name: 'Usopp' },
      V: { emoji: '💪', name: 'Vegeta' }, W: { emoji: '👴', name: 'Watari' }, X: { emoji: '⚔', name: 'Xenovia' },
      Y: { emoji: '🐱', name: 'Yoruichi' }, Z: { emoji: '⚔', name: 'Zoro' },
    };
    return chars[initial] || { emoji: '🍜', name: 'Naruto' };
  }

  function speak(text, callback) {
    if (!window.speechSynthesis) { if (callback) callback(); return; }
    window.speechSynthesis.cancel();
    utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'fr-FR';
    utter.rate = 0.9;
    utter.pitch = 1.1;
    if (callback) utter.onend = callback;
    window.speechSynthesis.speak(utter);
  }

  function stopSpeaking() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  }

  function createAssistant() {
    if (document.getElementById('bnc-assistant')) return;

    const char = getChar();

    const container = document.createElement('div');
    container.id = 'bnc-assistant';

    // Bubble
    const bubble = document.createElement('div');
    bubble.className = 'bnc-assistant__bubble';
    bubble.innerHTML = `
      <div class="bnc-assistant__header">
        <span class="bnc-assistant__name">${char.name} 🎙️</span>
        <div class="bnc-assistant__controls">
          <button class="bnc-assistant__btn" id="assistantSound" title="Activer/Désactiver le son">🔊</button>
          <button class="bnc-assistant__btn" id="assistantMinimize" title="Réduire">🗕</button>
          <button class="bnc-assistant__btn" id="assistantClose" title="Fermer">✕</button>
        </div>
      </div>
      <div class="bnc-assistant__step-indicator" id="assistantStepIndicator"></div>
      <div class="bnc-assistant__title" id="assistantTitle"></div>
      <div class="bnc-assistant__text" id="assistantText"></div>
      <div class="bnc-assistant__actions">
        <button class="bnc-assistant__btn" id="assistantPrev" disabled>◀ Précédent</button>
        <button class="bnc-assistant__btn bnc-assistant__btn--primary" id="assistantNext">Suivant ▶</button>
      </div>
      <button class="bnc-assistant__skip" id="assistantSkip">⏭ Passer le tutoriel</button>
    `;

    // Character avatar
    const avatar = document.createElement('div');
    avatar.className = 'bnc-assistant__avatar';
    avatar.innerHTML = `<span class="bnc-assistant__emoji">${char.emoji}</span>`;
    avatar.title = `Clique pour ${isOpen ? 'fermer' : 'ouvrir'} le guide`;

    container.appendChild(bubble);
    container.appendChild(avatar);
    document.body.appendChild(container);

    // Events
    avatar.addEventListener('click', toggleAssistant);
    document.getElementById('assistantClose').addEventListener('click', closeAssistant);
    document.getElementById('assistantMinimize').addEventListener('click', minimizeAssistant);
    document.getElementById('assistantNext').addEventListener('click', nextStep);
    document.getElementById('assistantPrev').addEventListener('click', prevStep);
    document.getElementById('assistantSkip').addEventListener('click', skipTutorial);
    document.getElementById('assistantSound').addEventListener('click', toggleSound);

    // State
    window._bncAssistantSound = true;
    currentStep = 0;
    showStep(0);
    isOpen = true;
    container.classList.add('open');

    // Auto-show on first visit
    if (!localStorage.getItem(ASSISTANT_STORAGE_KEY)) {
      setTimeout(() => {
        if (!isOpen) toggleAssistant();
      }, 2000);
    }
  }

  function toggleAssistant() {
    const container = document.getElementById('bnc-assistant');
    if (!container) return;
    isOpen = !isOpen;
    container.classList.toggle('open', isOpen);
    if (!isOpen) stopSpeaking();
  }

  function closeAssistant() {
    const container = document.getElementById('bnc-assistant');
    if (!container) return;
    stopSpeaking();
    container.classList.remove('open');
    isOpen = false;
    localStorage.setItem(ASSISTANT_STORAGE_KEY, 'true');
  }

  function minimizeAssistant() {
    const container = document.getElementById('bnc-assistant');
    if (!container) return;
    isMinimized = !isMinimized;
    container.classList.toggle('minimized', isMinimized);
    if (isMinimized) stopSpeaking();
  }

  function toggleSound() {
    window._bncAssistantSound = !window._bncAssistantSound;
    const btn = document.getElementById('assistantSound');
    if (btn) btn.textContent = window._bncAssistantSound ? '🔊' : '🔇';
    if (!window._bncAssistantSound) stopSpeaking();
  }

  function showStep(index) {
    const step = STEPS[index];
    if (!step) return;

    document.getElementById('assistantTitle').textContent = step.title;
    document.getElementById('assistantText').textContent = step.text;

    const prev = document.getElementById('assistantPrev');
    const next = document.getElementById('assistantNext');
    prev.disabled = index === 0;
    if (index >= STEPS.length - 1) {
      next.textContent = '✅ Terminer';
    } else {
      next.textContent = 'Suivant ▶';
    }

    // Step indicator
    const indicator = document.getElementById('assistantStepIndicator');
    indicator.innerHTML = STEPS.map((_, i) =>
      `<span class="bnc-assistant__dot${i === index ? ' active' : (i < index ? ' done' : '')}"></span>`
    ).join('');

    // Speech
    stopSpeaking();
    if (window._bncAssistantSound !== false) {
      speak(step.speak);
    }

    // Highlight element
    if (step.highlight) {
      const el = document.querySelector(`[href="${step.highlight}"], #${step.highlight}`);
      if (el) {
        el.style.transition = 'all 0.3s';
        el.style.boxShadow = '0 0 20px rgba(255,215,0,0.8)';
        el.style.borderRadius = '4px';
        setTimeout(() => {
          if (el) {
            el.style.boxShadow = 'none';
          }
        }, 3000);
      }
    }
  }

  function nextStep() {
    if (currentStep < STEPS.length - 1) {
      currentStep++;
      showStep(currentStep);
    } else {
      closeAssistant();
    }
  }

  function prevStep() {
    if (currentStep > 0) {
      currentStep--;
      showStep(currentStep);
    }
  }

  function skipTutorial() {
    localStorage.setItem(ASSISTANT_STORAGE_KEY, 'true');
    closeAssistant();
  }

  // Init
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createAssistant);
  } else {
    createAssistant();
  }

  // Style
  const style = document.createElement('style');
  style.textContent = `
    #bnc-assistant {
      position: fixed;
      bottom: 100px;
      left: 20px;
      z-index: 9999;
      font-family: 'Segoe UI', system-ui, sans-serif;
    }
    #bnc-assistant .bnc-assistant__bubble {
      display: none;
      width: 340px;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      border: 1px solid rgba(255,215,0,0.3);
      border-radius: 16px;
      padding: 1rem;
      box-shadow: 0 8px 40px rgba(0,0,0,0.8), 0 0 30px rgba(255,215,0,0.1);
      margin-bottom: 10px;
      animation: bncSlideIn 0.4s ease;
    }
    @keyframes bncSlideIn {
      from { opacity: 0; transform: translateY(20px) scale(0.95); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    #bnc-assistant.open .bnc-assistant__bubble { display: block; }
    #bnc-assistant.minimized .bnc-assistant__bubble { display: none; }

    .bnc-assistant__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .bnc-assistant__name {
      font-size: 0.85rem;
      color: var(--gold, #ffd700);
      font-weight: 600;
    }
    .bnc-assistant__controls { display: flex; gap: 0.3rem; }
    .bnc-assistant__step-indicator {
      display: flex;
      gap: 0.3rem;
      justify-content: center;
      margin-bottom: 0.8rem;
    }
    .bnc-assistant__dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      transition: all 0.3s;
    }
    .bnc-assistant__dot.active { background: var(--gold, #ffd700); transform: scale(1.3); }
    .bnc-assistant__dot.done { background: #4caf50; }
    .bnc-assistant__title {
      font-size: 1rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 0.5rem;
    }
    .bnc-assistant__text {
      font-size: 0.85rem;
      color: rgba(255,255,255,0.85);
      line-height: 1.5;
      margin-bottom: 1rem;
      white-space: pre-line;
    }
    .bnc-assistant__actions {
      display: flex;
      gap: 0.5rem;
    }
    .bnc-assistant__btn {
      padding: 0.4rem 0.8rem;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 8px;
      background: rgba(255,255,255,0.05);
      color: #fff;
      cursor: pointer;
      font-size: 0.78rem;
      transition: all 0.2s;
    }
    .bnc-assistant__btn:hover:not(:disabled) { background: rgba(255,215,0,0.15); border-color: var(--gold, #ffd700); }
    .bnc-assistant__btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .bnc-assistant__btn--primary { background: var(--gold, #ffd700); color: #000; border-color: var(--gold, #ffd700); font-weight: 600; }
    .bnc-assistant__btn--primary:hover { background: #ffe44d; }
    .bnc-assistant__skip {
      margin-top: 0.5rem;
      background: none;
      border: none;
      color: rgba(255,255,255,0.4);
      cursor: pointer;
      font-size: 0.72rem;
      width: 100%;
      text-align: center;
    }
    .bnc-assistant__skip:hover { color: rgba(255,255,255,0.7); }

    .bnc-assistant__avatar {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: linear-gradient(135deg, #1a1a2e, #0f3460);
      border: 2px solid var(--gold, #ffd700);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.3s;
      box-shadow: 0 4px 20px rgba(255,215,0,0.3);
      animation: bncFloat 3s ease-in-out infinite;
    }
    .bnc-assistant__avatar:hover {
      transform: scale(1.1);
      box-shadow: 0 4px 30px rgba(255,215,0,0.5);
    }
    .bnc-assistant__emoji {
      font-size: 1.8rem;
      line-height: 1;
      animation: bncWave 2s ease-in-out infinite;
    }
    @keyframes bncFloat {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }
    @keyframes bncWave {
      0%, 100% { transform: rotate(0deg); }
      25% { transform: rotate(-10deg); }
      75% { transform: rotate(10deg); }
    }
  `;
  document.head.appendChild(style);
})();
