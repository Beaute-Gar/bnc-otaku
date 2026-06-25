const API_BASE = '';

function getToken() {
  return localStorage.getItem('bnc_token');
}

function getUser() {
  const raw = localStorage.getItem('bnc_user');
  return raw ? JSON.parse(raw) : null;
}

function isLoggedIn() {
  return !!getToken();
}

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem('bnc_token');
    localStorage.removeItem('bnc_user');
    window.location.href = '/login.html';
  }
  return res;
}

function logout() {
  localStorage.removeItem('bnc_token');
  localStorage.removeItem('bnc_user');
  window.location.href = '/login.html';
}

function updateNavbar() {
  const user = getUser();
  const nav = document.querySelector('.gov-nav');
  if (!nav) return;
  const existing = document.querySelector('.auth-status');
  if (existing) existing.remove();

  const el = document.createElement('span');
  el.className = 'auth-status';
  el.style.cssText = 'margin-left:auto;font-size:0.85rem;display:flex;align-items:center;gap:0.5rem;';

  if (user) {
    el.innerHTML = `<span style="color:#ffd700;">👤 ${user.username}</span>
      <a href="#" onclick="logout();return false;" style="color:#e94560;text-decoration:none;">Déconnexion</a>`;
  } else {
    el.innerHTML = `<a href="/login.html" style="color:#4caf50;text-decoration:none;font-weight:600;">🔑 Connexion</a>`;
  }
  nav.appendChild(el);
}

document.addEventListener('DOMContentLoaded', updateNavbar);
