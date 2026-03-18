-- Migration 002: Activity log — migrare de la JSON la SQLite
-- Data: 2026-03-18
-- Descriere: Tabel activity_log pentru logarea centralizata a actiunilor

CREATE TABLE IF NOT EXISTS activity_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    action      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'success',
    summary     TEXT NOT NULL DEFAULT '',
    details     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_action ON activity_log(action);

-- Marchează migrarea ca aplicată
INSERT OR IGNORE INTO schema_version (version, name) VALUES (2, '002_activity_log');
