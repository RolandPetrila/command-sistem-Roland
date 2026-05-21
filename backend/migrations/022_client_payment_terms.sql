-- Migration 022: Add default_payment_terms to clients (R4-29)

ALTER TABLE clients ADD COLUMN default_payment_terms TEXT;

INSERT INTO schema_version (version, name) VALUES (22, '022_client_payment_terms');
