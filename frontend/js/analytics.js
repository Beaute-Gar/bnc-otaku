(function() {
  const params = new URLSearchParams(window.location.search);
  const utmData = {
    utm_source: params.get('utm_source') || '',
    utm_medium: params.get('utm_medium') || '',
    utm_campaign: params.get('utm_campaign') || '',
    utm_content: params.get('utm_content') || '',
    utm_term: params.get('utm_term') || '',
    ref: params.get('ref') || '',
  };

  const hasUtm = Object.values(utmData).some(v => v);
  if (!hasUtm) return;

  try {
    localStorage.setItem('bnc_utm', JSON.stringify(utmData));
  } catch (e) {}

  try {
    const payload = { ...utmData, url: window.location.pathname };
    navigator.sendBeacon('/api/stats/visit', JSON.stringify(payload));
  } catch (e) {}

  const ref = utmData.utm_term || utmData.ref;
  if (ref) {
    try { localStorage.setItem('bnc_ref', ref); } catch (e) {}
  }
})();

function getStoredUtm() {
  try {
    return JSON.parse(localStorage.getItem('bnc_utm')) || {};
  } catch { return {}; }
}

function getReferralCode() {
  try {
    return localStorage.getItem('bnc_ref') || '';
  } catch { return ''; }
}
