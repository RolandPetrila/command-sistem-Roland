-- Migration 017: Adauga coloana 'category' la tabela notes
-- Data: 2026-03-22

ALTER TABLE notes ADD COLUMN category TEXT NOT NULL DEFAULT 'general';

-- Marchează migrarea ca aplicată
INSERT OR IGNORE INTO schema_version (version, name) VALUES (17, '017_notes_category');
