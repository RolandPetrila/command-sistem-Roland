-- Vault: add expires_at column for key expiration alerts
ALTER TABLE vault_keys ADD COLUMN expires_at TEXT DEFAULT NULL;

INSERT OR IGNORE INTO schema_version (version, name) VALUES (20, '020_vault_expires');
