-- Migration 015: Faza F — Top 10 Features P1
-- F2: Prompt Templates, F3: Invoice Series, F4: Payment tracking,
-- F5: ITP Appointments, F6: Notifications, F10: Glossary per client

-- F10: Add client_id to glossary_terms for per-client glossaries
ALTER TABLE glossary_terms ADD COLUMN client_id INTEGER REFERENCES clients(id);

-- F2: AI Prompt Templates with variables
CREATE TABLE IF NOT EXISTS ai_prompt_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    variables   TEXT, -- JSON array of variable names e.g. ["lang","topic"]
    category    TEXT DEFAULT 'general',
    usage_count INTEGER DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- F3: Configurable invoice series
CREATE TABLE IF NOT EXISTS invoice_series (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prefix      TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT,
    next_number INTEGER DEFAULT 1,
    is_default  INTEGER DEFAULT 0,
    active      INTEGER DEFAULT 1,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default series
INSERT OR IGNORE INTO invoice_series (prefix, name, description, is_default)
VALUES ('RCC', 'Roland Command Center', 'Serie implicita facturi', 1);

-- F4: Payment date on invoices
ALTER TABLE invoices ADD COLUMN payment_date TEXT;

-- F5: ITP Appointments/Scheduling
CREATE TABLE IF NOT EXISTS itp_appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number    TEXT NOT NULL,
    owner_name      TEXT,
    owner_phone     TEXT,
    scheduled_date  TEXT NOT NULL,
    scheduled_time  TEXT DEFAULT '08:00',
    duration_min    INTEGER DEFAULT 30,
    status          TEXT DEFAULT 'scheduled', -- scheduled, confirmed, completed, cancelled, no_show
    notes           TEXT,
    inspection_id   INTEGER REFERENCES itp_inspections(id),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_itp_appt_date ON itp_appointments(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_itp_appt_plate ON itp_appointments(plate_number);

-- F6: Unified Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    message     TEXT NOT NULL,
    type        TEXT DEFAULT 'info', -- info, warning, error, success
    source      TEXT, -- module that created it: itp, invoice, translator, ai, system
    link        TEXT, -- optional route to navigate to
    is_read     INTEGER DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

INSERT INTO schema_version (version, name) VALUES (15, '015_faza_f');
