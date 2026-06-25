let selectedProduct = null;
let selectedOperateur = null;
let pollInterval = null;

async function loadProducts() {
  try {
    const res = await apiFetch('/api/payment/products');
    const products = await res.json();
    const grid = document.getElementById('productsGrid');
    if (!grid) return;
    grid.innerHTML = products.map(p => `
      <div class="product-card" data-slug="${p.slug}">
        <span class="badge">${p.badge_label || ''}</span>
        <div class="icon">${getProductIcon(p.slug)}</div>
        <h3>${p.name}</h3>
        <p>${p.description || ''}</p>
        <div class="price">${p.prix_fcfa} <small>FCFA</small></div>
        <button onclick="showPaymentForm('${p.slug}', ${p.prix_fcfa})" class="btn btn--primary" style="width:100%;">
          Acheter
        </button>
      </div>
    `).join('');
  } catch (e) {
    console.error('Erreur chargement produits:', e);
  }
}

function getProductIcon(slug) {
  const icons = {
    'diplome_gold': '🏅',
    'grade_boost': '⚡',
    'pack_legendaire': '👑',
    'ref_personnalise': '✏️',
  };
  return icons[slug] || '🎁';
}

function showPaymentForm(slug, price) {
  selectedProduct = slug;
  document.getElementById('paymentModal').style.display = 'flex';
  document.getElementById('modalProduct').textContent = slug.replace('_', ' ').toUpperCase();
  document.getElementById('modalPrice').textContent = price + ' FCFA';
  document.getElementById('payBtn').disabled = true;
  selectedOperateur = null;
  document.querySelectorAll('.operateur-btn').forEach(b => b.classList.remove('active'));
}

function selectOperateur(op, el) {
  selectedOperateur = op;
  document.querySelectorAll('.operateur-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  checkPayReady();
}

function checkPayReady() {
  const phone = document.getElementById('phoneInput').value.trim();
  document.getElementById('payBtn').disabled = !(selectedOperateur && phone.length >= 8);
}

async function pay() {
  const phone = document.getElementById('phoneInput').value.trim();
  if (!selectedProduct || !selectedOperateur || phone.length < 8) return;

  document.getElementById('paymentForm').style.display = 'none';
  document.getElementById('paymentLoading').style.display = 'block';

  try {
    const res = await apiFetch('/api/payment/initiate', {
      method: 'POST',
      body: JSON.stringify({
        produit_slug: selectedProduct,
        operateur: selectedOperateur,
        phone: phone,
      }),
    });
    const data = await res.json();

    if (data.success && data.payment_url) {
      window.open(data.payment_url, '_blank');
    }

    document.getElementById('paymentLoading').style.display = 'none';
    document.getElementById('paymentResult').style.display = 'block';

    if (data.success) {
      document.getElementById('resultIcon').className = 'check';
      document.getElementById('resultIcon').textContent = '✅';
      document.getElementById('resultTitle').textContent = 'Paiement en cours...';
      document.getElementById('resultMsg').textContent = 'Confirme sur ton téléphone MTN/Orange Money.';
      startPolling(data.reference);
    } else {
      document.getElementById('resultIcon').className = 'error-icon';
      document.getElementById('resultIcon').textContent = '❌';
      document.getElementById('resultTitle').textContent = 'Erreur';
      document.getElementById('resultMsg').textContent = data.message || 'Impossible d\'initier le paiement.';
    }
  } catch (e) {
    document.getElementById('paymentLoading').style.display = 'none';
    document.getElementById('paymentResult').style.display = 'block';
    document.getElementById('resultIcon').className = 'error-icon';
    document.getElementById('resultIcon').textContent = '❌';
    document.getElementById('resultTitle').textContent = 'Erreur';
    document.getElementById('resultMsg').textContent = e.message;
  }
}

function startPolling(reference) {
  let attempts = 0;
  pollInterval = setInterval(async () => {
    attempts++;
    if (attempts > 20) {
      clearInterval(pollInterval);
      document.getElementById('resultMsg').textContent = 'Le paiement a expiré. Réessaie.';
      return;
    }
    try {
      const res = await apiFetch(`/api/payment/status/${reference}`);
      const data = await res.json();
      if (data.statut === 'success') {
        clearInterval(pollInterval);
        document.getElementById('resultIcon').textContent = '🎉';
        document.getElementById('resultTitle').textContent = 'Paiement réussi !';
        document.getElementById('resultMsg').textContent = 'Ton achat a été activé. Merci !';
        setTimeout(() => closeModal(), 3000);
      } else if (data.statut === 'failed') {
        clearInterval(pollInterval);
        document.getElementById('resultIcon').textContent = '❌';
        document.getElementById('resultTitle').textContent = 'Paiement échoué';
        document.getElementById('resultMsg').textContent = 'La transaction a été refusée.';
      }
    } catch (e) {
      console.error('Poll error:', e);
    }
  }, 3000);
}

function closeModal() {
  if (pollInterval) clearInterval(pollInterval);
  document.getElementById('paymentModal').style.display = 'none';
  document.getElementById('paymentForm').style.display = 'block';
  document.getElementById('paymentLoading').style.display = 'none';
  document.getElementById('paymentResult').style.display = 'none';
  document.getElementById('phoneInput').value = '';
  document.querySelectorAll('.operateur-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('payBtn').disabled = true;
  loadPaymentHistory();
}

async function loadPaymentHistory() {
  try {
    const res = await apiFetch('/api/payment/history');
    const data = await res.json();
    const tbody = document.getElementById('historyBody');
    if (!tbody) return;
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;opacity:0.5;">Aucun paiement</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(p => `
      <tr>
        <td>${p.reference}</td>
        <td>${p.produit}</td>
        <td>${p.montant_fcfa} FCFA</td>
        <td>${p.operateur}</td>
        <td class="status-${p.statut}">${p.statut}</td>
      </tr>
    `).join('');
  } catch (e) {
    console.error('Erreur historique:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadProducts();
  if (isLoggedIn()) loadPaymentHistory();
});
