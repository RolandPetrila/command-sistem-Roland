-- Migration 025: Document Templates (doc_templates)
-- Separate table from calculator's document_templates
-- Used for general-purpose document templates with variable rendering

CREATE TABLE IF NOT EXISTS doc_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'general',
    content     TEXT NOT NULL,
    variables   TEXT DEFAULT '[]',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO schema_version (version, name) VALUES (25, '025_doc_templates');
