let sessionId = null;
let questions = [];
let currentIndex = 0;
let answers = [];
let score = 0;
let correctCount = 0;
let totalPoints = 0;

const DIFFICULTY_COLORS = {
  'Junior Otaku': '#4caf50',
  'Senior Otaku': '#ff9800',
  'Master Otaku': '#f44336',
  'Otaku Legendaire': '#9c27b0',
};

function getDifficultyPoints(d) {
  const map = { 'Junior Otaku': 5, 'Senior Otaku': 10, 'Master Otaku': 15, 'Otaku Legendaire': 20 };
  return map[d] || 10;
}

let angerTimer = null;
let angerOverlay = null;

function initAngerFeature() {
  if (document.getElementById('anger-overlay')) return;

  angerOverlay = document.createElement('div');
  angerOverlay.id = 'anger-overlay';
  angerOverlay.style.cssText = `
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 9998;
    background: rgba(0,0,0,0.7);
    justify-content: center;
    align-items: center;
    flex-direction: column;
    cursor: pointer;
  `;

  const user = getUser();
  const initial = user && user.username ? user.username.charAt(0).toUpperCase() : 'O';
  const chars = {
    A: { name: 'Arale', emoji: '👧' },
    B: { name: 'Bulma', emoji: '👩' },
    C: { name: 'Chopper', emoji: '🦌' },
    D: { name: 'Deku', emoji: '🧑' },
    E: { name: 'Eren', emoji: '⚔' },
    F: { name: 'Frieren', emoji: '🧙' },
    G: { name: 'Goku', emoji: '🐉' },
    H: { name: 'Hinata', emoji: '👧' },
    I: { name: 'Itachi', emoji: '🗡' },
    J: { name: 'Jotaro', emoji: '👊' },
    K: { name: 'Kirito', emoji: '⚔' },
    L: { name: 'Lelouch', emoji: '👑' },
    M: { name: 'Mikasa', emoji: '⚔' },
    N: { name: 'Naruto', emoji: '🍜' },
    O: { name: 'Obito', emoji: '🌀' },
    P: { name: 'Pikachu', emoji: '⚡' },
    Q: { name: 'Quatre', emoji: '👦' },
    R: { name: 'Rukia', emoji: '👩' },
    S: { name: 'Sasuke', emoji: '🗡' },
    T: { name: 'Tanjiro', emoji: '⚔' },
    U: { name: 'Usopp', emoji: '🎯' },
    V: { name: 'Vegeta', emoji: '💪' },
    W: { name: 'Watari', emoji: '👴' },
    X: { name: 'Xenovia', emoji: '⚔' },
    Y: { name: 'Yoruichi', emoji: '🐱' },
    Z: { name: 'Zoro', emoji: '⚔' },
  };

  const char = chars[initial] || { name: 'Sensei', emoji: '👨' };

  angerOverlay.innerHTML = `
    <div style="text-align:center;animation:angerPulse 1s infinite alternate;">
      <div style="font-size:6rem;line-height:1;">${char.emoji}</div>
      <div style="font-size:1.5rem;color:#ff4444;font-weight:bold;margin:1rem 0;">
        ${char.name} est FÂCHÉ !!
      </div>
      <div style="font-size:1.2rem;color:#ffd700;">
        "BOUGE-TOI !! La question t'attend !"
      </div>
      <div style="margin-top:1rem;font-size:0.9rem;color:rgba(255,255,255,0.5);">
        (Clique pour continuer)
      </div>
    </div>
  `;

  angerOverlay.addEventListener('click', () => {
    hideAnger();
  });

  document.body.appendChild(angerOverlay);

  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes angerPulse {
      0% { transform: scale(1); }
      100% { transform: scale(1.05); }
    }
  `;
  document.head.appendChild(styleSheet);
}

function showAnger() {
  if (angerOverlay) angerOverlay.style.display = 'flex';
}

function hideAnger() {
  if (angerOverlay) angerOverlay.style.display = 'none';
}

function resetAngerTimer() {
  if (angerTimer) clearTimeout(angerTimer);
  hideAnger();
  angerTimer = setTimeout(() => {
    showAnger();
  }, 15000);
}

function clearAngerTimer() {
  if (angerTimer) {
    clearTimeout(angerTimer);
    angerTimer = null;
  }
  hideAnger();
}

function updateProgress() {
  const total = questions.length;
  const pct = total > 0 ? Math.round((currentIndex / total) * 100) : 0;
  const bar = document.getElementById('quizProgressBar');
  if (bar) {
    bar.style.setProperty('--progress', `${pct}%`);
    bar.style.background = `linear-gradient(90deg, var(--success), var(--gold), var(--accent))`;
    bar.style.backgroundSize = `${pct}% 100%`;
    bar.style.backgroundRepeat = 'no-repeat';
    bar.style.backgroundColor = 'rgba(255,255,255,0.1)';
  }
  document.getElementById('quizProgressText').textContent = `${pct}%`;
}

async function startQuiz() {
  if (!requireAuth()) return;

  // Arrêter l'opening brusquement
  if (window._bncAudio) {
    window._bncAudio.stop();
  }

  const intro = document.getElementById('quizIntro');
  const quizScreen = document.getElementById('quizScreen');
  const theme = document.getElementById('themeInput').value.trim();
  intro.style.display = 'none';

  try {
    const url = theme ? `/api/quiz/start?theme=${encodeURIComponent(theme)}` : '/api/quiz/start';
    const res = await apiFetch(url, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur serveur');
    }
    const data = await res.json();
    if (!data.questions || !data.questions.length) {
      throw new Error('Aucune question reçue');
    }

    sessionId = data.session_id;
    questions = data.questions;
    answers = [];
    currentIndex = 0;
    score = 0;
    correctCount = 0;
    totalPoints = 0;

    questions.forEach(q => { totalPoints += getDifficultyPoints(q.difficulty); });

    quizScreen.style.display = 'block';
    updateProgress();
    initAngerFeature();
    showQuestion(0);
  } catch (err) {
    intro.style.display = 'block';
    intro.innerHTML += `<p class="error" style="color:var(--error);margin-top:1rem;">
      ❌ Erreur de chargement : ${err.message}
    </p>`;
  }
}

function showQuestion(index) {
  if (index >= questions.length) {
    showResults();
    return;
  }

  const q = questions[index];
  document.getElementById('questionCounter').textContent = `Question ${index + 1}/${questions.length}`;
  document.getElementById('questionText').textContent = q.question;
  document.getElementById('scoreDisplay').textContent = `Score: ${score}`;

  const badge = document.getElementById('difficultyBadge');
  badge.textContent = q.difficulty;
  badge.style.background = DIFFICULTY_COLORS[q.difficulty] || '#666';

  // Changer la musique selon la difficulté
  if (window._bncAudio) {
    window._bncAudio.playQuizMusic(q.difficulty);
  }

  const container = document.getElementById('optionsContainer');
  container.innerHTML = '';

  const labels = ['A', 'B', 'C', 'D'];
  q.options.forEach((opt, i) => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.textContent = `${labels[i]}. ${opt}`;
    btn.onclick = () => selectOption(i);
    btn.dataset.index = i;
    container.appendChild(btn);
  });

  document.getElementById('nextBtn').style.display = 'none';

  // Lancer le timer du personnage fâché
  resetAngerTimer();
}

function selectOption(index) {
  const buttons = document.querySelectorAll('.option-btn');
  const q = questions[currentIndex];

  buttons.forEach((btn, i) => {
    btn.disabled = true;
    if (i === index) btn.classList.add('selected');
  });

  answers.push(index);
  score += getDifficultyPoints(q.difficulty);
  correctCount++;

  document.getElementById('scoreDisplay').textContent = `Score: ${score}`;

  document.getElementById('nextBtn').style.display = 'inline-block';
  if (currentIndex === questions.length - 1) {
    document.getElementById('nextBtn').textContent = '🎓 Voir mes Résultats';
  }

  clearAngerTimer();
}

function nextQuestion() {
  currentIndex++;
  updateProgress();
  if (currentIndex < questions.length) {
    showQuestion(currentIndex);
  } else {
    document.getElementById('quizProgressText').textContent = '100%';
    const bar = document.getElementById('quizProgressBar');
    if (bar) {
      bar.style.backgroundSize = '100% 100%';
    }
    showResults();
  }
}

async function showResults() {
  document.getElementById('quizScreen').style.display = 'none';

  // Arrêter la musique du quiz
  if (window._bncAudio) {
    window._bncAudio.stop();
  }

  try {
    const res = await apiFetch('/api/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, answers }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Erreur soumission');

    document.getElementById('resultScreen').style.display = 'none';
    await showAdGate();
    document.getElementById('adGateScreen').style.display = 'none';

    const pct = data.score;
    let level, emoji, grade;
    if (pct >= 90) { level = 'Otaku Légendaire'; grade = 'SS'; emoji = '👑'; }
    else if (pct >= 75) { level = 'Master Otaku'; grade = 'S'; emoji = '🏆'; }
    else if (pct >= 55) { level = 'Senior Otaku'; grade = 'A'; emoji = '⭐'; }
    else { level = 'Junior Otaku'; grade = 'B'; emoji = '🌟'; }

    document.getElementById('resultEmoji').textContent = emoji;
    document.getElementById('resultLevel').textContent = `${level} [Grade ${grade}]`;
    document.getElementById('resultScoreText').textContent = `${pct}%`;
    document.getElementById('resultBarFill').style.width = `${pct}%`;

    const user = getUser();
    try {
      const r2 = await apiFetch('/api/quiz/congratulate', {
        method: 'POST',
        body: JSON.stringify({
          username: user ? user.username : 'Candidat',
          level: data.level,
          score: pct,
        }),
      });
      const msg = await r2.json();
      document.getElementById('resultMessage').textContent = msg.message;
    } catch {
      document.getElementById('resultMessage').textContent =
        `Félicitations ! Tu as obtenu le niveau ${level} avec ${pct}% de bonnes réponses !`;
    }

    window._bncResult = { level, score: pct, emoji, sessionId };
    document.getElementById('resultScreen').style.display = 'block';
  } catch (err) {
    document.getElementById('resultScreen').style.display = 'block';
    document.getElementById('resultEmoji').textContent = '❌';
    document.getElementById('resultLevel').textContent = 'Erreur';
    document.getElementById('resultScoreText').textContent = '0%';
    document.getElementById('resultBarFill').style.width = '0%';
    document.getElementById('resultMessage').textContent = err.message;
  }
}

async function generateCertificate() {
  document.getElementById('resultScreen').style.display = 'none';
  await showAdGate();
  document.getElementById('adGateScreen').style.display = 'none';
  if (typeof downloadCertificate === 'function') {
    downloadCertificate();
  }
}

// Jouer l'opening au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
  if (window._bncAudio) {
    window._bncAudio.playOpening();
  }
});
