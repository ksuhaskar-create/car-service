"""Подготовка общей информации для страницы автомобиля."""
from .car_service import resolve_car
from .history_service import get_service_history
from .expense_service import calculate_total_expenses
from .oil_service import check_oil_reminder


def get_car_overview(car_id=None, current_mileage=None):
    car = resolve_car(car_id)
    return {"car": car, "history": get_service_history(car["id"]),
            "total_expenses": calculate_total_expenses(car["id"]),
            "oil_status": check_oil_reminder(car["id"], current_mileage)}
