"""Проверка пользовательских данных."""
from datetime import date
from .errors import ValidationError


def parse_int(value, field_name):
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"Поле «{field_name}» должно быть целым числом.")
    return result


def parse_number(value, field_name):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"Поле «{field_name}» должно быть числом.")
    return result


def validate_car_id(car_id):
    value = parse_int(car_id, "ID автомобиля")
    if value <= 0:
        raise ValidationError("ID автомобиля должен быть положительным.")
    return value


def validate_service_record(data):
    if not isinstance(data, dict):
        raise ValidationError("Данные записи должны быть переданы в виде словаря.")
    car_id = validate_car_id(data.get("car_id"))
    mileage = parse_int(data.get("mileage"), "Пробег")
    cost = parse_number(data.get("cost"), "Стоимость")
    record_date = str(data.get("date", "")).strip()
    description = str(data.get("description", "")).strip()
    if mileage < 0:
        raise ValidationError("Пробег не может быть отрицательным.")
    if cost < 0:
        raise ValidationError("Стоимость не может быть отрицательной.")
    try:
        date.fromisoformat(record_date)
    except ValueError:
        raise ValidationError("Дата должна быть в формате ГГГГ-ММ-ДД.")
    if not description:
        raise ValidationError("Описание работ не должно быть пустым.")
    parts = data.get("parts", []) or []
    if not isinstance(parts, list):
        raise ValidationError("Список запчастей заполнен некорректно.")
    clean_parts = []
    for part in parts:
        name = str(part.get("name", "")).strip()
        quantity = parse_int(part.get("quantity"), "Количество")
        price = parse_number(part.get("price"), "Цена")
        if not name:
            raise ValidationError("У запчасти должно быть название.")
        if quantity <= 0:
            raise ValidationError("Количество запчастей должно быть больше нуля.")
        if price < 0:
            raise ValidationError("Цена запчасти не может быть отрицательной.")
        clean_parts.append({"name": name, "quantity": quantity, "price": price})
    return {"car_id": car_id, "date": record_date, "mileage": mileage,
            "description": description, "cost": cost, "parts": clean_parts}
