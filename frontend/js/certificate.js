async function downloadCertificate() {
  const result = window._bncResult;
  if (!result || !result.sessionId) return;

  const user = getUser();
  if (!user) return;

  const name = prompt('Entrez votre nom pour le certificat :', user.full_name || user.username) || user.username;

  let certNumber = '';
  try {
    const res = await apiFetch('/api/certificates/generate', {
      method: 'POST',
      body: JSON.stringify({ exam_session_id: result.sessionId, full_name: name }),
    });
    if (res.ok) {
      const data = await res.json();
      certNumber = data.cert_number;
    }
  } catch (e) {
    certNumber = `BNC-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 9999)).padStart(4, '0')}`;
  }

  const canvas = document.createElement('canvas');
  canvas.width = 800;
  canvas.height = 600;
  const ctx = canvas.getContext('2d');

  const bgGrad = ctx.createLinearGradient(0, 0, 800, 600);
  bgGrad.addColorStop(0, '#f5e6c8');
  bgGrad.addColorStop(0.5, '#f0d9a0');
  bgGrad.addColorStop(1, '#e8c878');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, 800, 600);

  ctx.strokeStyle = '#8B6914';
  ctx.lineWidth = 8;
  ctx.strokeRect(20, 20, 760, 560);

  ctx.strokeStyle = '#D4A017';
  ctx.lineWidth = 3;
  ctx.strokeRect(35, 35, 730, 530);

  const sealX = 400, sealY = 200;
  ctx.beginPath();
  ctx.arc(sealX, sealY, 80, 0, Math.PI * 2);
  ctx.fillStyle = '#D4A017';
  ctx.fill();
  ctx.strokeStyle = '#8B6914';
  ctx.lineWidth = 4;
  ctx.stroke();

  ctx.fillStyle = '#4a3000';
  ctx.font = 'bold 14px serif';
  ctx.textAlign = 'center';
  ctx.fillText('BNC-OTAKU', sealX, sealY - 10);
  ctx.font = '12px serif';
  ctx.fillText('CERTIFICATION', sealX, sealY + 10);
  ctx.fillText('OFFICIELLE', sealX, sealY + 28);

  ctx.fillStyle = '#2c1810';
  ctx.font = 'bold 36px serif';
  ctx.fillText('Bureau National de Certification Otaku', 400, 320);

  ctx.font = '24px serif';
  ctx.fillStyle = '#8B6914';
  ctx.fillText('DIPLÔME DE CERTIFICATION OTAKU', 400, 360);

  ctx.font = 'bold 28px serif';
  ctx.fillStyle = '#2c1810';
  ctx.fillText(name, 400, 420);

  ctx.font = '20px serif';
  ctx.fillStyle = '#4a3000';
  ctx.fillText(`Niveau : ${result.level}  |  Score : ${result.score}%`, 400, 470);

  ctx.font = '14px serif';
  ctx.fillStyle = '#8B6914';
  if (certNumber) ctx.fillText(`N° ${certNumber}`, 400, 510);

  const today = new Date().toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric'
  });
  ctx.font = '14px serif';
  ctx.fillText(`Délivré le ${today}`, 400, 540);

  ctx.font = '12px serif';
  ctx.fillStyle = '#666';
  ctx.fillText('Ce certificat est délivré par le BNC-Otaku. Vérifiable sur bnc-otaku.cm', 400, 570);

  canvas.toBlob((blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = certNumber ? `BNC-Certificat-${certNumber}.png` : 'BNC-Certificat.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 'image/png');
}
