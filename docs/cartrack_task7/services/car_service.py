"""Операции с автомобилями."""
from dao import cars_dao
from .errors import NotFoundError
from .validators import validate_car_id


def list_cars():
    return cars_dao.get_all_cars()


def resolve_car(car_id=None):
    cars = list_cars()
    if not cars:
        raise NotFoundError("В базе нет автомобилей.")
    if car_id is None:
        return cars[0]
    car_id = validate_car_id(car_id)
    car = cars_dao.get_car_by_id(car_id)
    if car is None:
        raise NotFoundError(f"Автомобиль с ID {car_id} не найден.")
    return car
