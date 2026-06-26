-- Table de persistance de session WhatsApp (cookies + localStorage)
-- Permet de survivre aux redémarrages Render

CREATE TABLE IF NOT EXISTS wa_sessions (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_key   VARCHAR(64) NOT NULL UNIQUE,
    session_data  MEDIUMTEXT NOT NULL,         -- base64 JSON des cookies + localStorage
    checksum      VARCHAR(32) NOT NULL,        -- pour éviter les écritures redondantes
    created_at    DATETIME DEFAULT NOW(),
    updated_at    DATETIME DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_key (session_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
