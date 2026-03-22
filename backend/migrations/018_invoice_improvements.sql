-- Migration 018: Invoice module improvements
-- 1. Predefined invoice items (presets)
-- 2. Recurring invoices configuration
-- 3. Partial payments tracking

CREATE TABLE IF NOT EXISTS invoice_item_presets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    unit_price  REAL NOT NULL DEFAULT 0,
    unit        TEXT DEFAULT 'buc',
    category    TEXT DEFAULT 'general',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recurring_invoices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  INTEGER NOT NULL REFERENCES invoices(id),
    frequency   TEXT DEFAULT 'monthly',
    next_due    TEXT,
    enabled     INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recurring_invoice ON recurring_invoices(invoice_id);
CREATE INDEX IF NOT EXISTS idx_recurring_enabled ON recurring_invoices(enabled);

CREATE TABLE IF NOT EXISTS invoice_payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id    INTEGER NOT NULL REFERENCES invoices(id),
    amount        REAL NOT NULL,
    payment_date  TEXT NOT NULL,
    method        TEXT DEFAULT 'transfer',
    notes         TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_invoice ON invoice_payments(invoice_id);

INSERT INTO schema_version (version, name) VALUES (18, '018_invoice_improvements');
