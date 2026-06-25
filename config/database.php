<?php
/**
 * BNC-Otaku — Configuration DB (PHP Admin)
 * WampServer : root sans mot de passe, bnc_otaku_db
 */

define('DB_HOST', 'localhost');
define('DB_PORT', '3306');
define('DB_USER', 'root');
define('DB_PASSWORD', '');
define('DB_NAME', 'bnc_otaku_db');

try {
    $pdo = new PDO(
        "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4",
        DB_USER,
        DB_PASSWORD,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );
} catch (PDOException $e) {
    error_log("DB Connection failed: " . $e->getMessage());
    die("Erreur de connexion à la base de données.");
}
