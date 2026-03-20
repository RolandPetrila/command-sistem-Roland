-- Migration 014: File Manager extensions — tags, favorites, fulltext search (FTS5)

CREATE TABLE IF NOT EXISTS file_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    tag TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path, tag)
);

CREATE TABLE IF NOT EXISTS file_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS file_index USING fts5(
    file_path,
    content,
    tokenize='unicode61'
);

INSERT INTO schema_version (version, name) VALUES (14, '014_filemanager_ext');
