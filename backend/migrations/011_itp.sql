CREATE TABLE IF NOT EXISTS itp_inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL,
    vin TEXT,
    brand TEXT,
    model TEXT,
    year INTEGER,
    fuel_type TEXT, -- benzina, diesel, GPL, electric, hybrid
    owner_name TEXT,
    owner_phone TEXT,
    inspection_date TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    result TEXT NOT NULL, -- admis, respins
    rejection_reasons TEXT, -- JSON array if respins
    price REAL DEFAULT 0,
    inspector_name TEXT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_itp_plate ON itp_inspections(plate_number);
CREATE INDEX IF NOT EXISTS idx_itp_date ON itp_inspections(inspection_date);
CREATE INDEX IF NOT EXISTS idx_itp_expiry ON itp_inspections(expiry_date);

INSERT INTO schema_version (version, name) VALUES (11, '011_itp');
