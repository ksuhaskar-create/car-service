"""Проверка необходимости замены масла."""
from dao import cars_dao, records_dao
from .errors import NotFoundError
from .validators import validate_car_id

OIL_INTERVAL = 10000
NO_DATA_MESSAGE = "Недостаточно данных для расчёта."


def calculate_oil_status(current_mileage, last_oil_mileage):
    if current_mileage is None or last_oil_mileage is None:
        return {"needed": False, "message": NO_DATA_MESSAGE, "remaining": None}
    current = int(current_mileage)
    last = int(last_oil_mileage)
    remaining = OIL_INTERVAL - (current - last)
    if remaining <= 0:
        return {"needed": True, "message": "Пора заменить масло.", "remaining": 0}
    return {"needed": False, "message": f"До замены масла осталось {remaining} км.", "remaining": remaining}


def check_oil_reminder(car_id, current_mileage):
    car_id = validate_car_id(car_id)
    if not cars_dao.car_exists(car_id):
        raise NotFoundError(f"Автомобиль с ID {car_id} не найден.")
    return calculate_oil_status(current_mileage, records_dao.get_last_oil_mileage(car_id))
