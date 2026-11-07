"""Подготовка базы перед запуском приложения."""
from dao import database


def prepare_database():
    database.init_db()
