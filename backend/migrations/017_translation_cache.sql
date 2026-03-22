-- Migration 017: Translation cache table
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

INSERT INTO schema_version (version, name) VALUES (17, '017_translation_cache');
