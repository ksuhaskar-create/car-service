"""Расчёты стоимости."""


def calculate_parts_cost(parts):
    return sum(float(part["quantity"]) * float(part["price"]) for part in parts)


def calculate_record_total(record_cost, parts):
    return float(record_cost) + calculate_parts_cost(parts)
