"""Добавление записи обслуживания и запчастей одной транзакцией."""
from dao import database, cars_dao, records_dao, parts_dao
from .errors import NotFoundError, handle_db_errors
from .validators import validate_service_record


def validate_service_data(data):
    clean = validate_service_record(data)
    if not cars_dao.car_exists(clean["car_id"]):
        raise NotFoundError(f"Автомобиль с ID {clean['car_id']} не найден.")
    return clean


@handle_db_errors
def add_service_record(data):
    clean = validate_service_data(data)
    with database.transaction() as conn:
        record_id = records_dao.add_record(clean["car_id"], clean["date"], clean["mileage"],
                                           clean["description"], clean["cost"], conn=conn)
        for part in clean["parts"]:
            parts_dao.add_part(record_id, part["name"], part["quantity"], part["price"], conn=conn)
    return record_id
