<?php
/**
 * BNC-OTAKU — Admin Dashboard (PHP)
 * Interface de gestion sécurisée avec authentification.
 * Dashboard temps réel via Socket.IO.
 */

session_start();
require_once __DIR__ . '/../config/database.php';

// Vérification simple d'authentification
$isLoggedIn = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    if ($username === 'admin' && password_verify($password, '$2b$12$JBdUjjqpTJofUsbSNq7J0uJXfkcBess/HCqf6ZTqc/7Ma6e6zR3c2')) {
        $_SESSION['admin_logged_in'] = true;
        $_SESSION['admin_username'] = $username;
        $isLoggedIn = true;
    } else {
        $error = "Identifiants invalides";
    }
}

if (!$isLoggedIn):
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>BNC-Otaku — Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .login-card {
            background: #16213e;
            padding: 3rem;
            border-radius: 16px;
            border: 1px solid #ffd700;
            width: 100%;
            max-width: 400px;
        }
        .login-card h1 { color: #ffd700; margin-bottom: 2rem; text-align: center; }
        .login-card input {
            width: 100%;
            padding: 0.8rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            border: 2px solid rgba(255,255,255,0.2);
            background: #1a1a2e;
            color: white;
            font-size: 1rem;
        }
        .login-card button {
            width: 100%;
            padding: 0.8rem;
            background: #e94560;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
        }
        .error { color: #f44336; text-align: center; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>🔐 BNC-Otaku Admin</h1>
        <?php if (isset($error)): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
        <form method="POST">
            <input type="text" name="username" placeholder="Nom d'utilisateur" required>
            <input type="password" name="password" placeholder="Mot de passe" required>
            <button type="submit" name="login">Connexion</button>
        </form>
    </div>
</body>
</html>
<?php else: ?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BNC-Otaku — Dashboard Admin</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #f0f0f0;
        }
        .header {
            background: #16213e;
            border-bottom: 3px solid #ffd700;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
        }
        .header h1 { color: #ffd700; font-size: 1.3rem; }
        .header a { color: #e94560; text-decoration: none; }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        .card {
            background: #0f3460;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(255,215,0,0.2);
        }
        .card h3 { color: #ffd700; margin-bottom: 0.5rem; }
        .card .stat { font-size: 2rem; font-weight: 700; }
        .card .label { opacity: 0.7; font-size: 0.9rem; }
        .logs {
            grid-column: 1 / -1;
            max-height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85rem;
        }
        .logs .log-entry { padding: 0.3rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .status-online { color: #4caf50; }
        .status-offline { color: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 BNC-Otaku — Administration</h1>
        <div>
            <span id="connectionStatus" class="status-offline">● Déconnecté</span>
            <a href="?logout=1" style="margin-left:1rem;">Déconnexion</a>
        </div>
    </div>

    <div class="dashboard" id="dashboard">
        <div class="card">
            <h3>🎓 Certificats Émis</h3>
            <div class="stat" id="statCertificates">0</div>
            <div class="label">Total</div>
        </div>
        <div class="card">
            <h3>📝 Examens Passés</h3>
            <div class="stat" id="statExams">0</div>
            <div class="label">Aujourd'hui</div>
        </div>
        <div class="card">
            <h3>🤖 Bots Actifs</h3>
            <div class="stat" id="statBots">0/0</div>
            <div class="label">Telegram / WhatsApp</div>
        </div>
        <div class="card">
            <h3>👥 Utilisateurs</h3>
            <div class="stat" id="statUsers">0</div>
            <div class="label">Inscrits</div>
        </div>
        <div class="card logs" id="logsContainer">
            <h3>📋 Logs Temps Réel</h3>
            <div id="logEntries"></div>
        </div>
    </div>

    <script>
        // Connexion Socket.IO au backend FastAPI
        const socket = io('http://localhost:8000', {
            transports: ['websocket', 'polling'],
        });

        socket.on('connect', () => {
            document.getElementById('connectionStatus').textContent = '● Connecté';
            document.getElementById('connectionStatus').className = 'status-online';
            addLog('✅ Dashboard connecté au backend');
        });

        socket.on('disconnect', () => {
            document.getElementById('connectionStatus').textContent = '● Déconnecté';
            document.getElementById('connectionStatus').className = 'status-offline';
            addLog('❌ Connexion perdue');
        });

        socket.on('stats', (data) => {
            document.getElementById('statCertificates').textContent = data.certificates || 0;
            document.getElementById('statExams').textContent = data.exams_today || 0;
            document.getElementById('statBots').textContent = `${data.bots_active || 0}/${data.bots_total || 0}`;
            document.getElementById('statUsers').textContent = data.users || 0;
        });

        socket.on('log', (data) => {
            addLog(data.message);
        });

        function addLog(msg) {
            const container = document.getElementById('logEntries');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            const time = new Date().toLocaleTimeString('fr-FR');
            entry.textContent = `[${time}] ${msg}`;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
<?php endif; ?>
<?php if (isset($_GET['logout'])) { session_destroy(); header('Location: index.php'); exit; } ?>
