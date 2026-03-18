-- Migration 001: Schema inițială — Calculator Preț Traduceri
-- Data: 2026-03-18
-- Descriere: Captură schema existentă ca punct de plecare pentru sistemul de migrare

-- Tabel de tracking versiune schema
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabel: uploads — fișierele încărcate pentru analiză
CREATE TABLE IF NOT EXISTS uploads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL,
    filepath        TEXT NOT NULL,
    file_type       TEXT NOT NULL CHECK(file_type IN ('pdf', 'docx')),
    file_size       INTEGER NOT NULL DEFAULT 0,
    upload_date     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabel: calculations — rezultatele calculelor de preț per fișier
CREATE TABLE IF NOT EXISTS calculations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id       INTEGER NOT NULL,
    market_price    REAL NOT NULL,
    invoice_price   REAL NOT NULL,
    invoice_percent REAL NOT NULL DEFAULT 75.0,
    confidence      REAL NOT NULL DEFAULT 0.0,
    method_details  TEXT NOT NULL DEFAULT '{}',
    features        TEXT NOT NULL DEFAULT '{}',
    warnings        TEXT NOT NULL DEFAULT '[]',
    validated_price REAL,
    validated_at    TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
);

-- Tabel: settings — setări cheie-valoare persistente
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index-uri pentru performanță
CREATE INDEX IF NOT EXISTS idx_uploads_date ON uploads(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_calculations_upload_id ON calculations(upload_id);
CREATE INDEX IF NOT EXISTS idx_calculations_created_at ON calculations(created_at DESC);

-- View: history — combinare uploads + calculations
CREATE VIEW IF NOT EXISTS history AS
SELECT
    c.id            AS calculation_id,
    u.id            AS upload_id,
    u.filename,
    u.file_type,
    u.file_size,
    u.upload_date,
    c.market_price,
    c.invoice_price,
    c.invoice_percent,
    c.confidence,
    c.method_details,
    c.features,
    c.warnings,
    c.validated_price,
    c.validated_at,
    c.created_at    AS calculated_at
FROM calculations c
JOIN uploads u ON u.id = c.upload_id
ORDER BY c.created_at DESC;

-- Marchează migrarea ca aplicată
INSERT OR IGNORE INTO schema_version (version, name) VALUES (1, '001_initial');
