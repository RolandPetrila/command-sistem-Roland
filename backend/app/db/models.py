"""
Definiții tabele SQL pentru baza de date Calculator Preț Traduceri.

Tabele:
- uploads: fișierele încărcate
- calculations: rezultatele calculelor de preț
- settings: setări cheie-valoare
- View: history (combinare uploads + calculations)
"""

# --------------------------------------------------------------------------
# Tabel: uploads — fișierele încărcate pentru analiză
# --------------------------------------------------------------------------
CREATE_UPLOADS = """
CREATE TABLE IF NOT EXISTS uploads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL,
    filepath        TEXT NOT NULL,
    file_type       TEXT NOT NULL CHECK(file_type IN ('pdf', 'docx')),
    file_size       INTEGER NOT NULL DEFAULT 0,
    upload_date     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# --------------------------------------------------------------------------
# Tabel: calculations — rezultatele calculelor de preț per fișier
# --------------------------------------------------------------------------
CREATE_CALCULATIONS = """
CREATE TABLE IF NOT EXISTS calculations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id       INTEGER NOT NULL,
    market_price    REAL NOT NULL,
    invoice_price   REAL NOT NULL,
    invoice_percent REAL NOT NULL DEFAULT 75.0,
    confidence      REAL NOT NULL DEFAULT 0.0,
    method_details  TEXT NOT NULL DEFAULT '{}',
    features        TEXT NOT NULL DEFAULT '{}',
    warnings        TEXT NOT NULL DEFAULT '[]',
    validated_price REAL,
    validated_at    TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
);
"""

# --------------------------------------------------------------------------
# Tabel: settings — setări cheie-valoare persistente
# --------------------------------------------------------------------------
CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# --------------------------------------------------------------------------
# Index-uri pentru performanță
# --------------------------------------------------------------------------
CREATE_INDEX_UPLOADS_DATE = """
CREATE INDEX IF NOT EXISTS idx_uploads_date
ON uploads(upload_date DESC);
"""

CREATE_INDEX_CALCULATIONS_UPLOAD = """
CREATE INDEX IF NOT EXISTS idx_calculations_upload_id
ON calculations(upload_id);
"""

CREATE_INDEX_CALCULATIONS_DATE = """
CREATE INDEX IF NOT EXISTS idx_calculations_created_at
ON calculations(created_at DESC);
"""

# --------------------------------------------------------------------------
# View: history — combinare uploads + calculations pentru afișare
# --------------------------------------------------------------------------
CREATE_HISTORY_VIEW = """
CREATE VIEW IF NOT EXISTS history AS
SELECT
    c.id            AS calculation_id,
    u.id            AS upload_id,
    u.filename,
    u.file_type,
    u.file_size,
    u.upload_date,
    c.market_price,
    c.invoice_price,
    c.invoice_percent,
    c.confidence,
    c.method_details,
    c.features,
    c.warnings,
    c.validated_price,
    c.validated_at,
    c.created_at    AS calculated_at
FROM calculations c
JOIN uploads u ON u.id = c.upload_id
ORDER BY c.created_at DESC;
"""

# --------------------------------------------------------------------------
# Lista completă de comenzi CREATE (în ordinea corectă de dependențe)
# --------------------------------------------------------------------------
CREATE_TABLES = [
    CREATE_UPLOADS,
    CREATE_CALCULATIONS,
    CREATE_SETTINGS,
    CREATE_INDEX_UPLOADS_DATE,
    CREATE_INDEX_CALCULATIONS_UPLOAD,
    CREATE_INDEX_CALCULATIONS_DATE,
    CREATE_HISTORY_VIEW,
]
