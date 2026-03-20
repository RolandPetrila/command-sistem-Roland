-- Migration 008: Lightweight invoice module (minimal Faza 10 for 15B.7)

CREATE TABLE IF NOT EXISTS clients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    cui         TEXT,
    reg_com     TEXT,
    address     TEXT,
    email       TEXT,
    phone       TEXT,
    notes       TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id       INTEGER REFERENCES clients(id),
    invoice_number  TEXT NOT NULL UNIQUE,
    series          TEXT DEFAULT 'RCC',
    date            TEXT NOT NULL,  -- YYYY-MM-DD
    due_date        TEXT,
    items_json      TEXT NOT NULL,  -- JSON array of {description, quantity, unit_price, total}
    subtotal        REAL NOT NULL DEFAULT 0,
    vat_percent     REAL DEFAULT 0,
    vat_amount      REAL DEFAULT 0,
    total           REAL NOT NULL DEFAULT 0,
    currency        TEXT DEFAULT 'RON',
    status          TEXT DEFAULT 'draft',  -- draft, sent, paid, cancelled
    notes           TEXT,
    pdf_path        TEXT,
    calculation_id  INTEGER,  -- link to price calculation if generated from calc
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);

INSERT INTO schema_version (version, name) VALUES (8, '008_invoice_lite');
