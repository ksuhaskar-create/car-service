"""Запросы к записям обслуживания."""
from .database import connection


def add_record(car_id, date, mileage, description, cost, conn=None):
    if conn is not None:
        cur = conn.execute("INSERT INTO service_records(car_id,date,mileage,description,cost) VALUES(?,?,?,?,?)",
                           (car_id, date, mileage, description, cost))
        return cur.lastrowid
    with connection() as db:
        cur = db.execute("INSERT INTO service_records(car_id,date,mileage,description,cost) VALUES(?,?,?,?,?)",
                         (car_id, date, mileage, description, cost))
        return cur.lastrowid


def get_record_by_id(record_id):
    with connection() as conn:
        row = conn.execute("SELECT * FROM service_records WHERE id=?", (record_id,)).fetchone()
        return dict(row) if row else None


def get_records_by_car(car_id):
    with connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM service_records WHERE car_id=? ORDER BY date DESC, id DESC", (car_id,))]


def get_last_oil_mileage(car_id):
    with connection() as conn:
        row = conn.execute("""SELECT mileage FROM service_records
            WHERE car_id=? AND lower(description) LIKE '%масл%'
            ORDER BY mileage DESC, date DESC LIMIT 1""", (car_id,)).fetchone()
        return row["mileage"] if row else None


def get_total_cost(car_id):
    with connection() as conn:
        row = conn.execute("SELECT COALESCE(SUM(cost),0) AS total FROM service_records WHERE car_id=?", (car_id,)).fetchone()
        return float(row["total"])
