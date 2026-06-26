-- =============================================================================
-- BNC-OTAKU - Schéma MySQL (Requêtes préparées, anti-SQL Injection)
-- Bureau National de Certification Otaku
-- =============================================================================

CREATE DATABASE IF NOT EXISTS bnc_otaku_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE bnc_otaku_db;

-- =============================================================================
-- 1. UTILISATEURS
-- =============================================================================
CREATE TABLE users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,              -- bcrypt
    full_name       VARCHAR(100) DEFAULT NULL,
    role            ENUM('admin','candidate','viewer') NOT NULL DEFAULT 'candidate',
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- =============================================================================
-- 2. SESSIONS / TOKENS (refresh tokens stockés côté serveur)
-- =============================================================================
CREATE TABLE auth_tokens (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    token_hash      VARCHAR(255) NOT NULL,
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash)
) ENGINE=InnoDB;

-- =============================================================================
-- 3. EXAMENS / SESSIONS DE QUIZ
-- =============================================================================
CREATE TABLE exam_sessions (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    started_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME DEFAULT NULL,
    status          ENUM('in_progress','completed','abandoned') NOT NULL DEFAULT 'in_progress',
    score           DECIMAL(5,2) DEFAULT NULL,           -- sur 100
    level           ENUM('junior','senior','master','legendary') DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_exam_user (user_id),
    INDEX idx_exam_status (status)
) ENGINE=InnoDB;

-- =============================================================================
-- 4. QUESTIONS GÉNÉRÉES PAR L'IA (cache / historique)
-- =============================================================================
CREATE TABLE quiz_questions (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    exam_session_id INT UNSIGNED NOT NULL,
    question_text   TEXT NOT NULL,
    options         JSON NOT NULL,                       -- ["opt1","opt2","opt3","opt4"]
    correct_index   TINYINT UNSIGNED NOT NULL,           -- 0-3
    difficulty      VARCHAR(30) NOT NULL,
    category        VARCHAR(50) DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_session_id) REFERENCES exam_sessions(id) ON DELETE CASCADE,
    INDEX idx_quiz_exam (exam_session_id)
) ENGINE=InnoDB;

-- =============================================================================
-- 5. RÉPONSES UTILISATEUR
-- =============================================================================
CREATE TABLE user_answers (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    question_id     INT UNSIGNED NOT NULL,
    selected_index  TINYINT UNSIGNED NOT NULL,
    is_correct      TINYINT(1) NOT NULL,
    answered_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE,
    INDEX idx_answers_user (user_id),
    INDEX idx_answers_question (question_id)
) ENGINE=InnoDB;

-- =============================================================================
-- 6. CERTIFICATS ÉMIS
-- =============================================================================
CREATE TABLE certificates (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    exam_session_id INT UNSIGNED NOT NULL,
    cert_number     VARCHAR(20) NOT NULL UNIQUE,         -- BNC-2026-0001
    full_name       VARCHAR(100) NOT NULL,
    level           ENUM('junior','senior','master','legendary') NOT NULL,
    score           DECIMAL(5,2) NOT NULL,
    issued_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    download_count  INT UNSIGNED NOT NULL DEFAULT 0,
    is_verified     TINYINT(1) NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_session_id) REFERENCES exam_sessions(id) ON DELETE CASCADE,
    INDEX idx_cert_user (user_id),
    INDEX idx_cert_number (cert_number),
    UNIQUE KEY uk_exam_cert (exam_session_id)
) ENGINE=InnoDB;

-- =============================================================================
-- 7. LOGS D'ACTIVITÉ (traçabilité)
-- =============================================================================
CREATE TABLE activity_logs (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED DEFAULT NULL,
    action          VARCHAR(100) NOT NULL,
    details         JSON DEFAULT NULL,
    ip_address      VARCHAR(45) DEFAULT NULL,
    user_agent      VARCHAR(255) DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_logs_user (user_id),
    INDEX idx_logs_action (action),
    INDEX idx_logs_created (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- 8. ÉVÉNEMENTS BOTS (WhatsApp/Telegram)
-- =============================================================================
CREATE TABLE bot_events (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    platform        ENUM('telegram','whatsapp') NOT NULL,
    event_type      VARCHAR(50) NOT NULL,
    sender_id       VARCHAR(100) NOT NULL,
    sender_name     VARCHAR(100) DEFAULT NULL,
    message_body    TEXT DEFAULT NULL,
    metadata        JSON DEFAULT NULL,
    processed       TINYINT(1) NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bot_platform (platform),
    INDEX idx_bot_processed (processed),
    INDEX idx_bot_created (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- 9. PAIEMENTS MOBILE MONEY (CinetPay / NotchPay)
-- =============================================================================
CREATE TABLE payments (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED DEFAULT NULL,
    montant_fcfa    INT UNSIGNED NOT NULL,
    devise          VARCHAR(10) NOT NULL DEFAULT 'XAF',
    operateur       ENUM('MTN','ORANGE','WAVE','MOOV','AIRTEL') NOT NULL,
    transaction_id  VARCHAR(100) DEFAULT NULL,
    reference       VARCHAR(100) NOT NULL UNIQUE,
    statut          ENUM('pending','success','failed','expired') NOT NULL DEFAULT 'pending',
    produit         VARCHAR(50) NOT NULL,
    description     TEXT DEFAULT NULL,
    phone           VARCHAR(20) DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at    DATETIME DEFAULT NULL,
    raw_webhook     TEXT DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_pay_user (user_id),
    INDEX idx_pay_statut (statut),
    INDEX idx_pay_created (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- 10. PRODUITS PREMIUM
-- =============================================================================
CREATE TABLE premium_products (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    slug            VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT DEFAULT NULL,
    prix_fcfa       INT UNSIGNED NOT NULL,
    badge_label     VARCHAR(50) DEFAULT NULL,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =============================================================================
-- INDEX PLEINTEXTE pour recherche rapide
-- =============================================================================
ALTER TABLE quiz_questions ADD FULLTEXT INDEX ft_question (question_text);
ALTER TABLE activity_logs ADD FULLTEXT INDEX ft_log_action (action);
