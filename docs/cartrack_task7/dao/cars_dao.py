"""Запросы к таблице автомобилей."""
from .database import connection


def get_all_cars():
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT id, name FROM cars ORDER BY id")]


def get_car_by_id(car_id):
    with connection() as conn:
        row = conn.execute("SELECT id, name FROM cars WHERE id = ?", (car_id,)).fetchone()
        return dict(row) if row else None


def car_exists(car_id):
    return get_car_by_id(car_id) is not None
