-- BNC-OTAKU WHATSAPP BOT — Tables MySQL additionnelles

CREATE TABLE IF NOT EXISTS wa_users (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    wa_id_hash        VARCHAR(64) NOT NULL UNIQUE,
    display_name      VARCHAR(100),
    ref_code          VARCHAR(20) UNIQUE,
    referred_by_code  VARCHAR(20),
    last_interaction  DATETIME,
    opt_out           TINYINT(1) DEFAULT 0,
    created_at        DATETIME DEFAULT NOW(),
    INDEX idx_ref_code (ref_code),
    INDEX idx_last_interaction (last_interaction)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS referrals (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    referrer_id     INT UNSIGNED NOT NULL,
    referred_wa_hash VARCHAR(64) NOT NULL,
    confirmed       TINYINT(1) DEFAULT 0,
    confirmed_at    DATETIME,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (referrer_id) REFERENCES wa_users(id) ON DELETE CASCADE,
    INDEX idx_referrer (referrer_id),
    INDEX idx_confirmed (confirmed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_wa_interactions (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sender_id_hash  VARCHAR(64) NOT NULL,
    sender_name     VARCHAR(100),
    message_type    ENUM('text', 'image', 'command') DEFAULT 'text',
    is_group        TINYINT(1) DEFAULT 0,
    handler_used    VARCHAR(50),
    created_at      DATETIME DEFAULT NOW(),
    INDEX idx_sender (sender_id_hash),
    INDEX idx_created (created_at),
    INDEX idx_type (message_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_broadcasts (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    broadcast_type  ENUM('daily_question', 'weekly_leaderboard', 'manual') NOT NULL,
    message_preview TEXT,
    recipients_count INT UNSIGNED DEFAULT 0,
    sent_at         DATETIME DEFAULT NOW(),
    INDEX idx_type (broadcast_type),
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
