"""Подсчёт расходов по автомобилю."""
from dao import cars_dao, records_dao, parts_dao
from .errors import NotFoundError
from .validators import validate_car_id


def calculate_total_expenses(car_id):
    car_id = validate_car_id(car_id)
    if not cars_dao.car_exists(car_id):
        raise NotFoundError(f"Автомобиль с ID {car_id} не найден.")
    return records_dao.get_total_cost(car_id) + parts_dao.get_parts_total_by_car(car_id)
