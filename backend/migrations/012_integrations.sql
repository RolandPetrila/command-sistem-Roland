-- Migration 012: Integrations — stocare token-uri pentru servicii externe
-- Gmail, Google Drive, Google Calendar, GitHub

CREATE TABLE IF NOT EXISTS integration_tokens (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    provider    TEXT NOT NULL DEFAULT '',
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version, name) VALUES (12, '012_integrations');
