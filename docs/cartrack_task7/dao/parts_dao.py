"""Запросы к запчастям."""
from .database import connection


def add_part(record_id, name, quantity, price, conn=None):
    if conn is not None:
        cur = conn.execute("INSERT INTO parts(service_record_id,name,quantity,price) VALUES(?,?,?,?)",
                           (record_id, name, quantity, price))
        return cur.lastrowid
    with connection() as db:
        cur = db.execute("INSERT INTO parts(service_record_id,name,quantity,price) VALUES(?,?,?,?)",
                         (record_id, name, quantity, price))
        return cur.lastrowid


def get_parts_by_record(record_id):
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM parts WHERE service_record_id=? ORDER BY id", (record_id,))]


def get_parts_total_by_car(car_id):
    with connection() as conn:
        row = conn.execute("""SELECT COALESCE(SUM(p.quantity*p.price),0) AS total
            FROM parts p JOIN service_records r ON r.id=p.service_record_id WHERE r.car_id=?""", (car_id,)).fetchone()
        return float(row["total"])
