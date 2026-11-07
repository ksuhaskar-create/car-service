"""Ошибки бизнес-логики."""
import sqlite3

class ServiceError(Exception):
    """Базовая ошибка сервиса."""

class ValidationError(ServiceError):
    pass

class NotFoundError(ServiceError):
    pass

class DatabaseError(ServiceError):
    pass


def handle_db_errors(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Ошибка базы данных: {exc}") from exc
    return wrapper
