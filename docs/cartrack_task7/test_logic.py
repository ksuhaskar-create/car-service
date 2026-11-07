"""Консольная проверка бизнес-логики CarTrack."""
import tempfile
from pathlib import Path
from dao import database, cars_dao, records_dao, parts_dao
from services.validators import validate_service_record
from services.errors import ValidationError, NotFoundError
from services.record_service import add_service_record
from services.history_service import get_service_history
from services.expense_service import calculate_total_expenses
from services.oil_service import calculate_oil_status


def run_test(name, function):
    try:
        function()
        print(f"[УСПЕХ] {name}")
        return True
    except Exception as error:
        print(f"[ОШИБКА] {name}: {error}")
        return False


def main():
    with tempfile.TemporaryDirectory() as folder:
        database.configure(Path(folder) / "test.db")
        database.init_db()
        car_id = cars_dao.get_all_cars()[0]["id"]

        def valid_add():
            rid = add_service_record({"car_id": car_id, "date": "2026-11-07", "mileage": 50000,
                "description": "Замена масла", "cost": 1500,
                "parts": [{"name": "Масло", "quantity": 4, "price": 800}]})
            assert rid > 0
            assert len(parts_dao.get_parts_by_record(rid)) == 1

        def invalid_cost():
            try:
                validate_service_record({"car_id": car_id, "date": "2026-11-07", "mileage": 1,
                    "description": "Проверка", "cost": -1})
            except ValidationError:
                return
            raise AssertionError("Отрицательная стоимость не отклонена")

        def missing_car():
            try:
                add_service_record({"car_id": 999, "date": "2026-11-07", "mileage": 1,
                    "description": "Проверка", "cost": 0})
            except NotFoundError:
                return
            raise AssertionError("Несуществующий автомобиль не отклонён")

        def history_and_expenses():
            history = get_service_history(car_id)
            assert len(history) == 1
            assert history[0]["total"] == 4700
            assert calculate_total_expenses(car_id) == 4700

        def oil_calculation():
            status = calculate_oil_status(60000, 50000)
            assert status["needed"] is True

        tests = [
            ("Добавление записи и запчасти", valid_add),
            ("Отклонение отрицательной стоимости", invalid_cost),
            ("Отклонение несуществующего автомобиля", missing_car),
            ("История и общая сумма расходов", history_and_expenses),
            ("Напоминание о замене масла", oil_calculation),
        ]
        passed = sum(run_test(name, func) for name, func in tests)
        print(f"\nРезультат: {passed} из {len(tests)} проверок пройдено.")
        return passed == len(tests)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
