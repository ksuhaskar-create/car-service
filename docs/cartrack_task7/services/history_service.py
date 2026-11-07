"""Получение истории обслуживания."""
from dao import cars_dao, records_dao, parts_dao
from .errors import NotFoundError
from .calculations import calculate_parts_cost, calculate_record_total
from .validators import validate_car_id


def get_service_history(car_id):
    car_id = validate_car_id(car_id)
    if not cars_dao.car_exists(car_id):
        raise NotFoundError(f"Автомобиль с ID {car_id} не найден.")
    result = []
    for record in records_dao.get_records_by_car(car_id):
        parts = parts_dao.get_parts_by_record(record["id"])
        result.append({**record, "parts": parts,
                       "parts_cost": calculate_parts_cost(parts),
                       "total": calculate_record_total(record["cost"], parts)})
    return result
