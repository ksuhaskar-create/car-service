PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    model TEXT NOT NULL,
    year INTEGER CHECK (year > 1900),
    current_mileage INTEGER NOT NULL DEFAULT 0
        CHECK (current_mileage >= 0)
);

CREATE TABLE IF NOT EXISTS service_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id INTEGER NOT NULL,
    service_date TEXT NOT NULL,
    mileage INTEGER NOT NULL CHECK (mileage >= 0),
    description TEXT NOT NULL,
    cost REAL NOT NULL DEFAULT 0 CHECK (cost >= 0),
    oil_change INTEGER NOT NULL DEFAULT 0
        CHECK (oil_change IN (0, 1)),
    FOREIGN KEY (car_id)
        REFERENCES cars(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_record_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    FOREIGN KEY (service_record_id)
        REFERENCES service_records(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_service_records_car_id
    ON service_records(car_id);

CREATE INDEX IF NOT EXISTS idx_service_records_date
    ON service_records(service_date);

CREATE INDEX IF NOT EXISTS idx_parts_service_record_id
    ON parts(service_record_id);
