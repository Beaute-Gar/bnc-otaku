let sessionId = null;
let questions = [];
let currentIndex = 0;
let answers = [];
let score = 0;

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

    quizScreen.style.display = 'block';
    showQuestion(0);
  } catch (err) {
    intro.style.display = 'block';
    intro.innerHTML += `<p class="error" style="color:var(--error);margin-top:1rem;">
      ❌ Erreur de chargement du quiz : ${err.message}
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

  const isCorrect = true;
  if (isCorrect) score += getDifficultyPoints(q.difficulty);

  answers.push(index);
  document.getElementById('scoreDisplay').textContent = `Score: ${score}`;

  document.getElementById('nextBtn').style.display = 'inline-block';
  if (currentIndex === questions.length - 1) {
    document.getElementById('nextBtn').textContent = '🎓 Voir mes Résultats';
  }
}

function nextQuestion() {
  currentIndex++;
  if (currentIndex < questions.length) {
    showQuestion(currentIndex);
  } else {
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
