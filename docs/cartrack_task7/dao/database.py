"""Подключение и транзакции SQLite."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DBError = sqlite3.Error
_DEFAULT_DB = Path(__file__).resolve().parents[2] / "cartrack.db"
_DB_PATH = _DEFAULT_DB


def configure(db_path):
    global _DB_PATH
    _DB_PATH = Path(db_path)


def get_db_path():
    return _DB_PATH


def get_connection():
    connection = sqlite3.connect(_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(sql_path=None):
    script = Path(sql_path) if sql_path else Path(__file__).resolve().parents[2] / "init.sql"
    if not script.exists():
        # При автономном запуске тестов используем схему, совпадающую с init.sql проекта.
        schema = '''
        CREATE TABLE IF NOT EXISTS cars (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
        CREATE TABLE IF NOT EXISTS service_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, car_id INTEGER NOT NULL, date TEXT NOT NULL,
            mileage INTEGER NOT NULL CHECK(mileage >= 0), description TEXT NOT NULL,
            cost REAL NOT NULL CHECK(cost >= 0),
            FOREIGN KEY(car_id) REFERENCES cars(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, service_record_id INTEGER NOT NULL,
            name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity > 0),
            price REAL NOT NULL CHECK(price >= 0),
            FOREIGN KEY(service_record_id) REFERENCES service_records(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_service_records_car_id ON service_records(car_id);
        CREATE INDEX IF NOT EXISTS idx_service_records_date ON service_records(date);
        CREATE INDEX IF NOT EXISTS idx_parts_service_record_id ON parts(service_record_id);
        '''
    else:
        schema = script.read_text(encoding="utf-8")
    with connection() as conn:
        conn.executescript(schema)
        conn.executemany("INSERT OR IGNORE INTO cars(name) VALUES (?)", [
            ("Skoda Octavia A5",), ("Lada Priora 2011",), ("BMW M5",)
        ])
        conn.commit()
