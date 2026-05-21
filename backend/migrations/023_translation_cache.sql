-- Migration 023: Translation cache table (renumbered from duplicate 017)
-- Caches identical translations to avoid redundant API calls

CREATE TABLE IF NOT EXISTS translation_cache (
    hash        TEXT PRIMARY KEY,
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    provider    TEXT NOT NULL,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_langs ON translation_cache(source_lang, target_lang);

INSERT OR IGNORE INTO schema_version (version, name) VALUES (23, '023_translation_cache');
