-- Migration 003: Notepad — note rapide cu auto-save
-- Data: 2026-03-18

CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL DEFAULT 'Notă nouă',
    content     TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);

-- Marchează migrarea ca aplicată
INSERT OR IGNORE INTO schema_version (version, name) VALUES (3, '003_notepad');
