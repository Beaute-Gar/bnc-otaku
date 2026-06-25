# 🎌 BNC-Otaku — Bureau National de Certification Otaku

**Plateforme web gamifiée** pour passer l'*Examen National Otaku* avec génération de diplômes,
intégrée à un **système multi-bots unifié (Telegram + WhatsApp)** piloté par l'IA Gemini.

---

## Architecture

```
BNC-OTAKU/
├── backend/                  # API FastAPI (Python 3.11)
│   ├── main.py               # Point d'entrée FastAPI
│   ├── config.py             # Configuration Pydantic (.env)
│   ├── database.py           # SQLAlchemy async (MySQL)
│   ├── security.py           # Rate limiting + CSRF
│   ├── routers/
│   │   ├── quiz.py           # Module 1 : Quiz IA Gemini
│   │   ├── auth.py           # Authentification admin
│   │   ├── certificate.py    # Certification endpoints
│   │   └── webhooks.py       # Webhooks Telegram/Meta
│   ├── models/
│   │   ├── user.py           # Modèle utilisateur
│   │   ├── quiz.py           # Modèles quiz/examen
│   │   └── certificate.py    # Modèle certificat
│   └── services/
│       └── gemini_service.py # IA Gemini (quiz + félicitations)
├── bots/                     # Module 3 : Bots unifiés
│   ├── core.py               # Orchestrateur multi-plateforme
│   ├── telegram_handler.py   # Bot Telegram (polling/webhook)
│   ├── whatsapp_playwright.py# WhatsApp via Playwright
│   └── whatsapp_meta.py      # WhatsApp via Meta Business API
├── frontend/                 # Client web HTML/JS
│   ├── index.html            # Landing page gouvernementale
│   ├── quiz.html             # Page d'examen
│   ├── css/style.css         # Styles complets
│   └── js/
│       ├── quiz.js           # Moteur de quiz frontend
│       └── certificate.js    # Module 2 : Canvas + Ad-Gate
├── admin/                    # Dashboard admin (PHP)
│   └── index.php             # Interface Socket.IO temps réel
├── database/
│   └── schema.sql            # Schéma MySQL complet
├── run.ps1                   # Script de lancement Windows
├── .env                      # Configuration (NE PAS COMMIT)
├── .env.example              # Template sécurisé
└── requirements.txt          # Dépendances Python
```

## Stack Technique

| Couche | Technologie |
|--------|-------------|
| **Backend** | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| **IA** | Google Gemini 2.0 Flash |
| **Base de données** | MySQL 8.0 (WampServer) + SQLAlchemy 2.0 Async |
| **Bot Telegram** | `python-telegram-bot` 21.x (webhook/polling) |
| **Bot WhatsApp** | Playwright (WhatsApp Web) + Meta Business API |
| **Frontend** | HTML5, CSS3, Vanilla JS, Canvas API |
| **Dashboard** | PHP 8.2 (WampServer), Socket.IO (temps réel) |
| **Sécurité** | bcrypt, JWT, Rate Limiting (slowapi), CSRF, requêtes préparées |

## Prérequis (Windows)

- **Python 3.11+** — installé
- **WampServer** (MySQL + PHP + Apache) — installé
- **Clé API Google Gemini** — [obtenir ici](https://aistudio.google.com/apikey)

## Installation & Démarrage

```powershell
# 1. Aller dans le projet
cd BNC-OTAKU

# 2. Configurer les clés API
#    Édite .env et mets GEMINI_API_KEY="ta_cle"

# 3. Lancer le script (fait tout automatiquement)
.\run.ps1
```

Le script `run.ps1` va :
1. ✅ Vérifier Python
2. ✅ Vérifier WampServer
3. ✅ Installer les dépendances Python
4. ✅ Installer Chromium (Playwright)
5. ✅ Créer la base de données MySQL
6. ✅ Lancer le serveur sur `http://localhost:8000`

### Ou manuellement

```powershell
# Installation des dépendances
pip install -r requirements.txt
python -m playwright install chromium

# Créer la base (via phpMyAdmin ou ligne de commande)
mysql -u root < database\schema.sql

# Lancer le serveur
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Accès

| Service | URL |
|---------|-----|
| **API + Frontend** | http://localhost:8000 |
| **Documentation API** | http://localhost:8000/docs |
| **Admin Dashboard** | http://localhost/bnc-otaku/admin/ (via WampServer) |

## Dashboard PHP (via WampServer)

Pour que le dashboard admin PHP fonctionne :

1. Copie le dossier `BNC-OTAKU/admin/` dans `C:\wamp\www\bnc-otaku\`
2. Copie `config/database.php` dans `C:\wamp\www\bnc-otaku\config\`
3. Accède à `http://localhost/bnc-otaku/admin/index.php`

## Sécurité

- **Aucune clé API en dur** dans le code — tout passe par `.env`
- **Rate limiting** (slowapi) sur les endpoints sensibles
- **CSRF tokens** pour les mutations
- **bcrypt** pour les hash de mots de passe
- **Requêtes préparées** (anti SQL Injection)
- **Utilisateur MySQL dédié** recommandé (pas de root en prod)

## Modules clés

### Module 1 — Moteur de Quiz IA (`backend/services/gemini_service.py`)
- Génère 10 questions uniques via Gemini 2.0 Flash
- 4 niveaux de difficulté (facile → légendaire)
- Score pondéré par difficulté
- Félicitations personnalisées par l'IA

### Module 2 — Générateur de Certificat (`frontend/js/certificate.js`)
- Dessin du diplôme sur Canvas (800×600)
- Ad-Gate de 5 secondes avant téléchargement
- Numéro de certificat unique (BNC-2026-XXXX)

### Module 3 — Bot Multi-Plateforme (`bots/core.py`)
- Écoute Telegram + WhatsApp simultanément
- Détecte les certificats BNC-Otaku
- Répond avec messages personnalisés par Gemini
- Architecture extensible (facile d'ajouter Discord, Messenger...)

## Licence

Projet parodique. Aucune affiliation avec des institutions réelles.
