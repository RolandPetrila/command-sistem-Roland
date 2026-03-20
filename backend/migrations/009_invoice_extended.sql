-- Migration 009: Extended invoice module (Faza 10.3–10.8)
-- received_invoices: facturi primite scanate OCR
-- document_templates: template-uri documente (contract, oferta, chitanta)

CREATE TABLE IF NOT EXISTS received_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT,
    supplier_cui TEXT,
    invoice_number TEXT,
    invoice_date TEXT,
    amount REAL DEFAULT 0,
    vat REAL DEFAULT 0,
    total REAL DEFAULT 0,
    currency TEXT DEFAULT 'RON',
    file_path TEXT,
    raw_text TEXT,
    extracted_data TEXT, -- JSON
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    template_type TEXT NOT NULL, -- contract, offer, receipt
    fields_json TEXT NOT NULL, -- JSON array of field definitions
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO document_templates (name, display_name, description, template_type, fields_json)
VALUES
    ('contract_traducere', 'Contract Traducere', 'Contract standard pentru servicii de traducere', 'contract',
     '[{"name":"client_name","label":"Nume client","type":"text"},{"name":"client_cui","label":"CUI client","type":"text"},{"name":"client_address","label":"Adresa client","type":"text"},{"name":"description","label":"Descriere servicii","type":"textarea"},{"name":"price","label":"Preț (RON)","type":"number"},{"name":"deadline","label":"Termen livrare","type":"date"},{"name":"date","label":"Data contract","type":"date"}]'),
    ('oferta_pret', 'Ofertă de Preț', 'Ofertă de preț pentru servicii traducere', 'offer',
     '[{"name":"client_name","label":"Nume client","type":"text"},{"name":"description","label":"Descriere servicii","type":"textarea"},{"name":"items","label":"Articole","type":"items"},{"name":"validity","label":"Valabilitate ofertă (zile)","type":"number"},{"name":"date","label":"Data ofertă","type":"date"}]'),
    ('chitanta', 'Chitanță', 'Chitanță pentru plata cash', 'receipt',
     '[{"name":"client_name","label":"Nume client","type":"text"},{"name":"amount","label":"Suma (RON)","type":"number"},{"name":"description","label":"Descriere plată","type":"text"},{"name":"date","label":"Data","type":"date"}]');

INSERT INTO schema_version (version, name) VALUES (9, '009_invoice_extended');
