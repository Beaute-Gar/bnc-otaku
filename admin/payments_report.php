<?php
session_start();
require_once __DIR__ . '/../config/database.php';

$isLoggedIn = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;
if (!$isLoggedIn) {
    header('Location: index.php');
    exit;
}

try {
    // $pdo est défini par config/database.php

    // Stats globales
    $stmt = $pdo->query("
        SELECT 
            COALESCE(SUM(CASE WHEN statut='success' THEN montant_fcfa ELSE 0 END), 0) AS total_fcfa,
            COUNT(CASE WHEN statut='success' THEN 1 END) AS total_success,
            COUNT(*) AS total_all
        FROM payments
    ");
    $globals = $stmt->fetch(PDO::FETCH_ASSOC);

    // Par opérateur
    $stmt = $pdo->query("
        SELECT operateur, 
               COUNT(*) AS nb, 
               COALESCE(SUM(CASE WHEN statut='success' THEN montant_fcfa ELSE 0 END), 0) AS total
        FROM payments 
        GROUP BY operateur
    ");
    $operateurs = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Derniers paiements
    $stmt = $pdo->query("
        SELECT p.*, u.username 
        FROM payments p 
        LEFT JOIN users u ON p.user_id = u.id 
        ORDER BY p.created_at DESC 
        LIMIT 200
    ");
    $payments = $stmt->fetchAll(PDO::FETCH_ASSOC);

} catch (Exception $e) {
    die("Erreur: " . $e->getMessage());
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>BNC-Otaku — Paiements</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #f0f0f0;
            padding: 2rem;
        }
        h1 { color: #ffd700; margin-bottom: 1.5rem; }
        .stats { display:flex; gap:1.5rem; margin-bottom:2rem; flex-wrap:wrap; }
        .stat-card {
            background: #16213e;
            padding:1.5rem;
            border-radius:12px;
            border:1px solid rgba(255,215,0,0.2);
            min-width:180px;
        }
        .stat-card h3 { color:#ffd700; font-size:0.9rem; margin-bottom:0.3rem; }
        .stat-card .value { font-size:2rem; font-weight:700; }
        .stat-card .value.green { color:#4caf50; }
        table {
            width:100%;
            border-collapse:collapse;
            font-size:0.85rem;
        }
        th, td { padding:8px 12px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.1); }
        th { color:#ffd700; background:#0f3460; position:sticky; top:0; }
        .success { color:#4caf50; font-weight:600; }
        .pending { color:#ff9800; }
        .failed { color:#f44336; }
        .nav { margin-bottom:1.5rem; }
        .nav a { color:#ffd700; text-decoration:none; margin-right:1rem; }
        .nav a:hover { text-decoration:underline; }
        .export-btn {
            background:#4caf50;
            color:white;
            border:none;
            padding:8px 16px;
            border-radius:6px;
            cursor:pointer;
            float:right;
            margin-bottom:1rem;
        }
    </style>
</head>
<body>
    <div class="nav">
        <a href="index.php">← Dashboard</a>
        <span style="color:rgba(255,255,255,0.5);">|</span>
        <a href="?logout=1">Déconnexion</a>
    </div>

    <h1>💰 Rapport des Paiements</h1>

    <div class="stats">
        <div class="stat-card">
            <h3>Total Reçu</h3>
            <div class="value green"><?= number_format($globals['total_fcfa'], 0, ',', ' ') ?> FCFA</div>
        </div>
        <div class="stat-card">
            <h3>Transactions réussies</h3>
            <div class="value"><?= $globals['total_success'] ?></div>
        </div>
        <div class="stat-card">
            <h3>Total transactions</h3>
            <div class="value"><?= $globals['total_all'] ?></div>
        </div>
        <?php foreach ($operateurs as $op): ?>
        <div class="stat-card">
            <h3><?= htmlspecialchars($op['operateur']) ?></h3>
            <div class="value"><?= number_format($op['total'], 0, ',', ' ') ?> FCFA</div>
            <div style="opacity:0.7;font-size:0.8rem;"><?= $op['nb'] ?> transactions</div>
        </div>
        <?php endforeach; ?>
    </div>

    <button class="export-btn" onclick="exportCSV()">📥 Exporter CSV</button>

    <table id="paymentsTable">
        <thead>
            <tr>
                <th>Référence</th>
                <th>Utilisateur</th>
                <th>Produit</th>
                <th>Montant</th>
                <th>Opérateur</th>
                <th>Téléphone</th>
                <th>Statut</th>
                <th>Date</th>
                <th>Confirmé le</th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($payments as $p): ?>
            <tr>
                <td style="font-family:monospace;"><?= htmlspecialchars($p['reference']) ?></td>
                <td><?= htmlspecialchars($p['username'] ?? '—') ?></td>
                <td><?= htmlspecialchars($p['produit']) ?></td>
                <td><?= number_format($p['montant_fcfa'], 0, ',', ' ') ?> FCFA</td>
                <td><?= htmlspecialchars($p['operateur']) ?></td>
                <td><?= htmlspecialchars($p['phone'] ?? '—') ?></td>
                <td class="<?= $p['statut'] ?>"><?= $p['statut'] ?></td>
                <td><?= date('d/m/Y H:i', strtotime($p['created_at'])) ?></td>
                <td><?= $p['confirmed_at'] ? date('d/m/Y H:i', strtotime($p['confirmed_at'])) : '—' ?></td>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>

    <script>
    function exportCSV() {
        const rows = document.querySelectorAll('#paymentsTable tbody tr');
        let csv = 'Référence;Utilisateur;Produit;Montant;Opérateur;Téléphone;Statut;Date;Confirmé\n';
        rows.forEach(row => {
            const cols = row.querySelectorAll('td');
            csv += Array.from(cols).map(c => '"' + c.textContent.trim() + '"').join(';') + '\n';
        });
        const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'paiements_bnc_' + new Date().toISOString().slice(0,10) + '.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    </script>
</body>
</html>
<?php if (isset($_GET['logout'])) { session_destroy(); header('Location: index.php'); exit; } ?>
