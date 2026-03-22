-- Migration 019: Calculator templates for reusable price quotes
-- Allows saving calculation results as templates for quick reuse

CREATE TABLE IF NOT EXISTS calculation_templates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    word_count     INTEGER NOT NULL,
    document_type  TEXT NOT NULL DEFAULT 'general',
    complexity     TEXT NOT NULL DEFAULT 'medium',
    source_lang    TEXT NOT NULL DEFAULT 'en',
    target_lang    TEXT NOT NULL DEFAULT 'ro',
    price          REAL NOT NULL,
    notes          TEXT DEFAULT '',
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_calc_templates_name ON calculation_templates(name);
CREATE INDEX IF NOT EXISTS idx_calc_templates_doc_type ON calculation_templates(document_type);

INSERT INTO schema_version (version, name) VALUES (19, '019_calculator_templates');
