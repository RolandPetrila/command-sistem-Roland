-- Migration 006: Translator module tables
-- Translation Memory + Glossary + Translation history

CREATE TABLE IF NOT EXISTS translations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_text     TEXT NOT NULL,
    target_text     TEXT NOT NULL,
    source_lang     TEXT NOT NULL DEFAULT 'en',
    target_lang     TEXT NOT NULL DEFAULT 'ro',
    provider        TEXT NOT NULL,
    chars_count     INTEGER DEFAULT 0,
    file_name       TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS translation_memory (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_segment  TEXT NOT NULL,
    target_segment  TEXT NOT NULL,
    source_lang     TEXT NOT NULL DEFAULT 'en',
    target_lang     TEXT NOT NULL DEFAULT 'ro',
    domain          TEXT DEFAULT 'general',
    confidence      REAL DEFAULT 1.0,
    usage_count     INTEGER DEFAULT 1,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS tm_fts USING fts5(
    source_segment,
    target_segment,
    content=translation_memory,
    content_rowid=id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS tm_ai AFTER INSERT ON translation_memory BEGIN
    INSERT INTO tm_fts(rowid, source_segment, target_segment)
    VALUES (new.id, new.source_segment, new.target_segment);
END;

CREATE TRIGGER IF NOT EXISTS tm_ad AFTER DELETE ON translation_memory BEGIN
    INSERT INTO tm_fts(tm_fts, rowid, source_segment, target_segment)
    VALUES ('delete', old.id, old.source_segment, old.target_segment);
END;

CREATE TRIGGER IF NOT EXISTS tm_au AFTER UPDATE ON translation_memory BEGIN
    INSERT INTO tm_fts(tm_fts, rowid, source_segment, target_segment)
    VALUES ('delete', old.id, old.source_segment, old.target_segment);
    INSERT INTO tm_fts(rowid, source_segment, target_segment)
    VALUES (new.id, new.source_segment, new.target_segment);
END;

CREATE TABLE IF NOT EXISTS glossary_terms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    term_source     TEXT NOT NULL,
    term_target     TEXT NOT NULL,
    source_lang     TEXT NOT NULL DEFAULT 'en',
    target_lang     TEXT NOT NULL DEFAULT 'ro',
    domain          TEXT DEFAULT 'general',
    notes           TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tm_source ON translation_memory(source_lang, target_lang);
CREATE INDEX IF NOT EXISTS idx_glossary_domain ON glossary_terms(domain);
CREATE INDEX IF NOT EXISTS idx_translations_created ON translations(created_at DESC);

INSERT INTO schema_version (version, name) VALUES (6, '006_translator');
