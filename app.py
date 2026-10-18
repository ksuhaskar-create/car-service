# CarTrack - учёт технического обслуживания автомобиля.
# Запуск: python app.py (или файл "Запустить CarTrack.bat")

import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, request, redirect, url_for, render_template_string

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cartrack.db"
SQL_PATH = BASE_DIR / "init.sql"

OIL_INTERVAL = 10000  # через сколько км нужно менять масло

# Фото машин: номер машины -> (имя файла в папке static/images, подпись)
CAR_PHOTOS = {
    1: ("skodaa5.webp", "Skoda Octavia A5"),
    2: ("priora1.webp", "Lada Priora, 2011"),
    3: ("bmw5.webp", "BMW M5"),
}

app = Flask(__name__)


# ---------- База данных ----------

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Создаёт таблицы из init.sql и три автомобиля (если их ещё нет)."""
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SQL_PATH.read_text(encoding="utf-8"))
        connection.executemany(
            "INSERT OR IGNORE INTO cars (id, name) VALUES (?, ?)",
            [
                (1, "Skoda Octavia A5"),
                (2, "Lada Priora 2011"),
                (3, "BMW M5"),
            ],
        )
        connection.commit()
    finally:
        connection.close()


# ---------- Вспомогательные функции ----------

def get_oil_message(records):
    """Напоминание о замене масла.
    Замена масла = запись, где в описании есть слово «масл» (масло, масла, ...).
    Текущий пробег = самый большой пробег среди записей машины."""
    if not records:
        return "Добавьте запись о замене масла, чтобы включить напоминание.", False

    current_mileage = max(r["mileage"] for r in records)
    oil_mileages = [r["mileage"] for r in records if "масл" in r["description"].lower()]

    if not oil_mileages:
        return "Добавьте запись о замене масла, чтобы включить напоминание.", False

    passed = current_mileage - max(oil_mileages)
    if passed >= OIL_INTERVAL:
        return (f"Пора менять масло! С последней замены прошло {passed} км "
                f"(интервал {OIL_INTERVAL} км)."), True
    return (f"С последней замены масла прошло {passed} км. "
            f"До замены осталось {OIL_INTERVAL - passed} км."), False


def load_page_data(car_id):
    """Достаёт из базы данные для выбранной машины."""
    connection = get_connection()
    try:
        cars = connection.execute("SELECT id, name FROM cars ORDER BY id").fetchall()
        if not cars:
            return None
        ids = [c[0] for c in cars]
        if car_id not in ids:
            car_id = ids[0]
        car_name = next(c[1] for c in cars if c[0] == car_id)

        rows = connection.execute(
            "SELECT id, date, mileage, description, cost FROM service_records "
            "WHERE car_id = ? ORDER BY date DESC, id DESC", (car_id,)
        ).fetchall()

        records = []
        total = 0.0
        for row in rows:
            parts = connection.execute(
                "SELECT name, quantity, price FROM parts WHERE service_record_id = ?",
                (row[0],)
            ).fetchall()
            parts_cost = sum(p[1] * p[2] for p in parts)
            record_total = row[4] + parts_cost
            total += record_total
            try:
                shown_date = datetime.strptime(row[1], "%Y-%m-%d").strftime("%d.%m.%Y")
            except ValueError:
                shown_date = row[1]
            records.append({
                "date": shown_date,
                "mileage": row[2],
                "description": row[3],
                "cost": row[4],
                "parts": parts,
                "total": record_total,
            })
    finally:
        connection.close()

    # для напоминания нужны пробег и описание каждой записи
    oil_source = [{"mileage": r["mileage"], "description": r["description"]} for r in records]
    oil_message, oil_overdue = get_oil_message(oil_source)

    return {
        "cars": cars, "selected_id": car_id, "selected_car": car_name,
        "records": records, "total": total,
        "oil_message": oil_message, "oil_overdue": oil_overdue,
    }


def validate_form(form):
    """Проверяет форму. Возвращает (данные, список ошибок)."""
    errors = []

    date_text = form.get("date", "").strip()
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        errors.append("Укажите дату.")

    mileage = None
    try:
        mileage = int(form.get("mileage", "").strip())
        if mileage < 0:
            errors.append("Пробег не может быть отрицательным.")
    except ValueError:
        errors.append("Пробег должен быть целым числом.")

    description = form.get("description", "").strip()
    if not description:
        errors.append("Опишите выполненные работы.")

    cost = None
    try:
        cost = float(form.get("cost", "").strip().replace(",", "."))
        if cost < 0:
            errors.append("Стоимость работ не может быть отрицательной.")
    except ValueError:
        errors.append("Стоимость работ должна быть числом.")

    parts = []
    names = form.getlist("part_name")
    quantities = form.getlist("part_quantity")
    prices = form.getlist("part_price")
    for number, (name, qty, price) in enumerate(zip(names, quantities, prices), start=1):
        name, qty, price = name.strip(), qty.strip(), price.strip()
        if not (name or qty or price):
            continue  # пустую строку запчасти пропускаем
        if not name:
            errors.append(f"Запчасть {number}: укажите название.")
            continue
        try:
            qty_value = int(qty)
            price_value = float(price.replace(",", "."))
        except ValueError:
            errors.append(f"Запчасть «{name}»: количество и цена должны быть числами.")
            continue
        if qty_value <= 0:
            errors.append(f"Запчасть «{name}»: количество должно быть больше нуля.")
        elif price_value < 0:
            errors.append(f"Запчасть «{name}»: цена не может быть отрицательной.")
        else:
            parts.append((name, qty_value, price_value))

    data = {"date": date_text, "mileage": mileage, "description": description,
            "cost": cost, "parts": parts}
    return data, errors


def save_record(car_id, data):
    """Сохраняет запись и её запчасти одной транзакцией."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO service_records (car_id, date, mileage, description, cost) "
            "VALUES (?, ?, ?, ?, ?)",
            (car_id, data["date"], data["mileage"], data["description"], data["cost"]),
        )
        record_id = cursor.lastrowid
        for name, quantity, price in data["parts"]:
            connection.execute(
                "INSERT INTO parts (service_record_id, name, quantity, price) "
                "VALUES (?, ?, ?, ?)", (record_id, name, quantity, price),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# ---------- Страница ----------

@app.route("/", methods=["GET", "POST"])
def home():
    errors = []
    form = {}
    part_rows = [{"name": "", "quantity": "", "price": ""}]

    if request.method == "POST":
        car_id = request.form.get("car_id", type=int)
        data, errors = validate_form(request.form)
        if not errors:
            save_record(car_id, data)
            return redirect(url_for("home", car_id=car_id))   # чтобы F5 не дублировал запись
        # ошибки: показываем форму снова с тем, что ввёл пользователь
        form = request.form
        names = form.getlist("part_name")
        quantities = form.getlist("part_quantity")
        prices = form.getlist("part_price")
        part_rows = [{"name": n, "quantity": q, "price": p}
                     for n, q, p in zip(names, quantities, prices)] or part_rows
    else:
        car_id = request.args.get("car_id", type=int)

    page = load_page_data(car_id)
    if page is None:
        return "В базе нет автомобилей.", 500

    # Фото выбранной машины (если файла нет, блок с фото просто не показывается)
    photo_file, photo_caption = CAR_PHOTOS.get(page["selected_id"], (None, ""))
    if photo_file and not (BASE_DIR / "static" / "images" / photo_file).exists():
        photo_file = None
    page["photo_file"] = photo_file
    page["photo_caption"] = photo_caption

    return render_template_string(PAGE, errors=errors, form=form,
                                  part_rows=part_rows, **page)


PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CarTrack — учёт обслуживания автомобилей</title>
    <style>
        /* ---------- Цветовые темы: у каждой машины своя ---------- */
        /* Skoda: синие и чёрные тона */
        .theme-1 {
            --bg: #eef2f7; --hero-from: #0b1220; --hero-to: #1f4e8c;
            --accent: #2c64a8; --accent-dark: #1f4a80; --soft: #e6edf6;
            --border: #d3dce8; --text: #17202b; --muted: #5d6b7c;
        }
        /* Lada Priora: чёрные и белые тона */
        .theme-2 {
            --bg: #f2f2f2; --hero-from: #0c0c0c; --hero-to: #454545;
            --accent: #262626; --accent-dark: #000000; --soft: #ececec;
            --border: #d8d8d8; --text: #161616; --muted: #666666;
        }
        /* BMW M5: чёрные и красные тона */
        .theme-3 {
            --bg: #f3f1f1; --hero-from: #0c0c0c; --hero-to: #6b141c;
            --accent: #a3202b; --accent-dark: #7e1820; --soft: #f4e8e9;
            --border: #ddd1d2; --text: #1a1616; --muted: #6c6162;
        }

        /* ---------- Общий вид ---------- */
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: system-ui, "Segoe UI", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
        }
        .container { max-width: 960px; margin: 0 auto; padding: 0 20px 40px; }

        /* Шапка */
        .hero {
            background: linear-gradient(135deg, var(--hero-from), var(--hero-to));
            color: #ffffff;
            padding: 30px 0 34px;
        }
        .hero h1 { margin: 0; font-size: 2rem; letter-spacing: 0.5px; }
        .hero p { margin: 4px 0 0; opacity: 0.8; }

        /* Карточки */
        .card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
        }
        .card h2 {
            margin: 0 0 14px;
            font-size: 1.15rem;
            border-left: 4px solid var(--accent);
            padding-left: 10px;
        }
        .card h3 { margin: 22px 0 10px; font-size: 1rem; }

        /* ---------- Выбор машины ---------- */
        .picker {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            align-items: center;
        }
        .car-buttons { display: flex; flex-direction: column; gap: 10px; }
        .car-btn {
            display: block;
            padding: 14px 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: #ffffff;
            color: var(--text);
            font-weight: 600;
            text-decoration: none;
            transition: all 0.15s ease;
        }
        .car-btn:hover {
            border-color: var(--accent);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        }
        .car-btn.active {
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            border-color: transparent;
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.22);
        }
        .car-photo { margin: 0; text-align: center; }
        .car-photo img {
            max-width: 100%;
            max-height: 210px;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
        }
        .car-photo figcaption { color: var(--muted); margin-top: 8px; font-size: 0.9rem; }

        /* ---------- Форма ---------- */
        .fields {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 14px;
        }
        .field { display: flex; flex-direction: column; gap: 4px; font-weight: 600; font-size: 0.9rem; }
        .field.wide { grid-column: 1 / -1; }
        input {
            font: inherit;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: #ffffff;
            color: var(--text);
            width: 100%;
            font-weight: 400;
        }
        input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
        .part-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 10px;
            margin-bottom: 10px;
        }

        /* ---------- Кнопки ---------- */
        .btn {
            font: inherit;
            font-weight: 600;
            display: inline-block;
            padding: 11px 24px;
            border: 0;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            color: #ffffff;
            cursor: pointer;
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.15s ease;
        }
        .btn:hover { transform: translateY(-1px); box-shadow: 0 6px 14px rgba(0, 0, 0, 0.25); }
        .btn:active { transform: translateY(0); box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); }
        .btn-outline {
            background: #ffffff;
            color: var(--accent);
            border: 1.5px solid var(--accent);
            box-shadow: none;
        }
        .btn-outline:hover { background: var(--soft); box-shadow: none; }
        .actions { margin-top: 18px; }

        /* ---------- Сообщения ---------- */
        .errors {
            background: #fdecea;
            border-left: 4px solid #b3261e;
            color: #8c1d18;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 16px;
        }
        .errors ul { margin: 6px 0 0; padding-left: 20px; }
        .note {
            background: var(--soft);
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            padding: 12px 16px;
            margin: 0;
        }
        .note.overdue {
            background: #fdecea;
            border-left-color: #b3261e;
            color: #8c1d18;
            font-weight: 600;
        }

        /* ---------- Таблица ---------- */
        .table-wrap { overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; }
        th {
            background: var(--hero-from);
            color: #ffffff;
            text-align: left;
            padding: 11px 12px;
            font-weight: 600;
        }
        th:first-child { border-radius: 10px 0 0 0; }
        th:last-child { border-radius: 0 10px 0 0; }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
        }
        tr:nth-child(even) td { background: var(--soft); }
        td.nowrap { white-space: nowrap; }
        .parts { margin: 0; padding-left: 18px; }

        /* ---------- Итого ---------- */
        .total-label { color: var(--muted); margin: 0; }
        .total { font-size: 2rem; font-weight: 700; color: var(--accent); margin: 0; }

        /* ---------- Узкие экраны ---------- */
        @media (max-width: 640px) {
            .picker { grid-template-columns: 1fr; }
            .part-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body class="theme-{{ selected_id }}">

    <header class="hero">
        <div class="container" style="padding-bottom: 0;">
            <h1>CarTrack</h1>
            <p>Учёт обслуживания автомобилей</p>
        </div>
    </header>

    <div class="container">

        <section class="card">
            <h2>Выбрать автомобиль</h2>
            <div class="picker">
                <div class="car-buttons">
                {% for car in cars %}
                    <a class="car-btn {% if car[0] == selected_id %}active{% endif %}"
                       href="{{ url_for('home', car_id=car[0]) }}">{{ car[1] }}</a>
                {% endfor %}
                </div>

                {% if photo_file %}
                <figure class="car-photo">
                    <img src="{{ url_for('static', filename='images/' + photo_file) }}" alt="{{ photo_caption }}">
                    <figcaption>{{ photo_caption }}</figcaption>
                </figure>
                {% endif %}
            </div>
        </section>

        <section class="card">
            <h2>Добавить обслуживание: {{ selected_car }}</h2>

            {% if errors %}
            <div class="errors">
                <strong>Запись не сохранена:</strong>
                <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
            </div>
            {% endif %}

            <form method="post">
                <input type="hidden" name="car_id" value="{{ selected_id }}">

                <div class="fields">
                    <label class="field">Дата
                        <input type="date" name="date" value="{{ form.get('date', '') }}" required>
                    </label>
                    <label class="field">Пробег (км)
                        <input type="number" name="mileage" min="0" step="1" value="{{ form.get('mileage', '') }}" required>
                    </label>
                    <label class="field">Стоимость работ (₽)
                        <input type="text" name="cost" inputmode="decimal" value="{{ form.get('cost', '') }}" required>
                    </label>
                    <label class="field wide">Описание работ
                        <input type="text" name="description" value="{{ form.get('description', '') }}" required>
                    </label>
                </div>

                <h3>Запчасти</h3>
                <div id="parts">
                {% for row in part_rows %}
                    <div class="part-row">
                        <input type="text" name="part_name" placeholder="Название" value="{{ row.name }}">
                        <input type="number" name="part_quantity" placeholder="Кол-во" min="1" step="1" value="{{ row.quantity }}">
                        <input type="text" name="part_price" inputmode="decimal" placeholder="Цена, ₽" value="{{ row.price }}">
                    </div>
                {% endfor %}
                </div>
                <button type="button" class="btn btn-outline" id="add-part">+ Добавить запчасть</button>

                <div class="actions">
                    <button type="submit" class="btn">Сохранить запись</button>
                </div>
            </form>
        </section>

        <section class="card">
            <h2>Напоминание о замене масла</h2>
            <p class="note {% if oil_overdue %}overdue{% endif %}">{{ oil_message }}</p>
        </section>

        <section class="card">
            <h2>История обслуживания</h2>
            {% if records %}
            <div class="table-wrap">
                <table>
                    <tr>
                        <th>Дата</th>
                        <th>Пробег</th>
                        <th>Работы</th>
                        <th>Запчасти</th>
                        <th>Стоимость работ</th>
                        <th>Итого</th>
                    </tr>
                    {% for r in records %}
                    <tr>
                        <td class="nowrap">{{ r.date }}</td>
                        <td class="nowrap">{{ r.mileage }} км</td>
                        <td>{{ r.description }}</td>
                        <td>
                            {% if r.parts %}
                            <ul class="parts">
                                {% for p in r.parts %}
                                <li>{{ p[0] }} — {{ p[1] }} шт. × {{ "%.2f"|format(p[2]) }} ₽</li>
                                {% endfor %}
                            </ul>
                            {% else %}—{% endif %}
                        </td>
                        <td class="nowrap">{{ "%.2f"|format(r.cost) }} ₽</td>
                        <td class="nowrap"><strong>{{ "%.2f"|format(r.total) }} ₽</strong></td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            {% else %}
            <p class="note">История обслуживания пуста. Добавьте первое обслуживание выше.</p>
            {% endif %}
        </section>

        <section class="card">
            <h2>Общие расходы на {{ selected_car }}</h2>
            <p class="total">{{ "%.2f"|format(total) }} ₽</p>
        </section>

    </div>

    <script>
        // Добавляет пустую строку для новой запчасти
        document.getElementById("add-part").addEventListener("click", function () {
            var row = document.querySelector(".part-row").cloneNode(true);
            row.querySelectorAll("input").forEach(function (input) { input.value = ""; });
            document.getElementById("parts").appendChild(row);
        });
    </script>
</body>
</html>
"""


# Подготовка базы: проверка, копия, создание таблиц.
# Выполняется при любом запуске (и локально, и на хостинге).
from db_safety import prepare_database
prepare_database(DB_PATH)
init_db()

if __name__ == "__main__":
    app.run(debug=False)