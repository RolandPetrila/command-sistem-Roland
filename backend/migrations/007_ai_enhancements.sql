-- Migration 007: AI enhancements — token tracking, document index, classify cache

-- Token usage tracking per provider per day
CREATE TABLE IF NOT EXISTS ai_token_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT NOT NULL,
    date            TEXT NOT NULL,  -- YYYY-MM-DD
    requests_count  INTEGER DEFAULT 0,
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    chars_count     INTEGER DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, date)
);

-- Provider limits (pre-populated)
CREATE TABLE IF NOT EXISTS ai_provider_limits (
    provider            TEXT PRIMARY KEY,
    daily_requests      INTEGER,
    monthly_chars       INTEGER,
    monthly_tokens      INTEGER,
    notes               TEXT
);

INSERT OR IGNORE INTO ai_provider_limits (provider, daily_requests, monthly_chars, monthly_tokens, notes)
VALUES
    ('gemini',   1500,  NULL,       NULL,       'Google Gemini free tier: 1500 req/day'),
    ('openai',   NULL,  NULL,       NULL,       'OpenAI: pay-per-token, free $5 credit'),
    ('groq',     14400, NULL,       NULL,       'Groq free tier: 14400 req/day'),
    ('deepl',    NULL,  500000,     NULL,       'DeepL free: 500K chars/month'),
    ('azure',    NULL,  2000000,    NULL,       'Azure Translator free: 2M chars/month');

-- Document index for RAG / semantic search
CREATE TABLE IF NOT EXISTS document_index (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL UNIQUE,
    file_name       TEXT NOT NULL,
    content_text    TEXT,
    file_type       TEXT,
    classification  TEXT,
    tags            TEXT,  -- JSON array
    language        TEXT,
    file_size       INTEGER DEFAULT 0,
    indexed_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
    file_name,
    content_text,
    classification,
    tags,
    content=document_index,
    content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS doc_ai AFTER INSERT ON document_index BEGIN
    INSERT INTO document_fts(rowid, file_name, content_text, classification, tags)
    VALUES (new.id, new.file_name, new.content_text, new.classification, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS doc_ad AFTER DELETE ON document_index BEGIN
    INSERT INTO document_fts(document_fts, rowid, file_name, content_text, classification, tags)
    VALUES ('delete', old.id, old.file_name, old.content_text, old.classification, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS doc_au AFTER UPDATE ON document_index BEGIN
    INSERT INTO document_fts(document_fts, rowid, file_name, content_text, classification, tags)
    VALUES ('delete', old.id, old.file_name, old.content_text, old.classification, old.tags);
    INSERT INTO document_fts(rowid, file_name, content_text, classification, tags)
    VALUES (new.id, new.file_name, new.content_text, new.classification, new.tags);
END;

-- File classification cache
CREATE TABLE IF NOT EXISTS file_classifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL UNIQUE,
    file_hash       TEXT,
    classification  TEXT,
    suggested_name  TEXT,
    tags_json       TEXT,  -- JSON array
    language        TEXT,
    classified_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- AI insights cache
CREATE TABLE IF NOT EXISTS ai_insights_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key       TEXT NOT NULL UNIQUE,
    content         TEXT NOT NULL,  -- JSON
    generated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_token_usage_date ON ai_token_usage(provider, date);
CREATE INDEX IF NOT EXISTS idx_doc_index_path ON document_index(file_path);
CREATE INDEX IF NOT EXISTS idx_classify_path ON file_classifications(file_path);

INSERT INTO schema_version (version, name) VALUES (7, '007_ai_enhancements');
