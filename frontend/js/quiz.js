let sessionId = null;
let questions = [];
let currentIndex = 0;
let answers = [];
let score = 0;
let correctCount = 0;
let totalPoints = 0;

const DIFFICULTY_COLORS = {
  facile: '#4caf50',
  moyen: '#ff9800',
  difficile: '#f44336',
  legendaire: '#9c27b0',
};

function getDifficultyPoints(d) {
  const map = { facile: 5, moyen: 10, difficile: 15, legendaire: 20 };
  return map[d] || 10;
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
}

function nextQuestion() {
  currentIndex++;
  updateProgress();
  if (currentIndex < questions.length) {
    showQuestion(currentIndex);
  } else {
    // At 100% progress before showing results
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

  try {
    const res = await apiFetch('/api/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, answers }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Erreur soumission');

    // Ad-gate avant résultats
    document.getElementById('resultScreen').style.display = 'none';
    await showAdGate();
    document.getElementById('adGateScreen').style.display = 'none';

    const pct = data.score;
    let level, emoji;
    if (pct >= 90) { level = 'Otaku Légendaire'; emoji = '👑'; }
    else if (pct >= 75) { level = 'Master Otaku'; emoji = '🏆'; }
    else if (pct >= 55) { level = 'Senior Otaku'; emoji = '⭐'; }
    else { level = 'Junior Otaku'; emoji = '🌟'; }

    document.getElementById('resultEmoji').textContent = emoji;
    document.getElementById('resultLevel').textContent = level;
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
