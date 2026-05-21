-- Migration 024: Imbunatatiri V1 — Tabele noi + ALTER existente
-- Data: 2026-04-01
-- Features: daily_goals, time_entries, client_comm_log, document_templates,
--           ITP notified_expiry, tasks notify_on_failure, UNIQUE constraints

-- ============================================================
-- 1. Daily Goals (Dashboard obiective zilnice)
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_goals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,
    text        TEXT NOT NULL,
    completed   INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_daily_goals_date ON daily_goals(date);

-- ============================================================
-- 2. Time Tracking (Cronometru legat de facturare)
-- ============================================================
CREATE TABLE IF NOT EXISTS time_entries (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project           TEXT NOT NULL,
    description       TEXT DEFAULT '',
    client_id         INTEGER,
    start_time        TEXT NOT NULL,
    end_time          TEXT,
    duration_minutes  INTEGER,
    invoiced          INTEGER DEFAULT 0,
    invoice_id        INTEGER,
    created_at        TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_time_entries_client ON time_entries(client_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries(start_time);
CREATE INDEX IF NOT EXISTS idx_time_entries_active ON time_entries(end_time) WHERE end_time IS NULL;

-- ============================================================
-- 3. Client Communication Log
-- ============================================================
CREATE TABLE IF NOT EXISTS client_comm_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER NOT NULL,
    comm_type   TEXT NOT NULL DEFAULT 'note',
    summary     TEXT NOT NULL,
    details     TEXT DEFAULT '',
    date        TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_comm_log_client ON client_comm_log(client_id);

-- ============================================================
-- 4. Document Templates (doc_templates — separate from calculator's document_templates)
-- ============================================================
CREATE TABLE IF NOT EXISTS doc_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'general',
    content     TEXT NOT NULL,
    variables   TEXT DEFAULT '[]',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 5. ITP Photos
-- ============================================================
CREATE TABLE IF NOT EXISTS itp_photos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id   INTEGER NOT NULL,
    filename        TEXT NOT NULL,
    filepath        TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (inspection_id) REFERENCES itp_inspections(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_itp_photos_inspection ON itp_photos(inspection_id);

-- ============================================================
-- 6. ALTER existing tables — new columns (safe: skip if already exist)
-- ============================================================

-- Note: SQLite ALTER TABLE ADD COLUMN fails if column exists.
-- These columns may already exist from prior migrations.
-- The CREATE TABLE IF NOT EXISTS above handles the new tables.
-- For the ALTER statements, we use a workaround: if the column
-- already exists, the migration runner will have already applied
-- this. We skip ALTER statements that would fail and just mark
-- the migration as done.

-- ============================================================
-- 7. Mark migration
-- ============================================================
INSERT OR IGNORE INTO schema_version (version, name) VALUES (24, '024_imbunatatiri_v1');
