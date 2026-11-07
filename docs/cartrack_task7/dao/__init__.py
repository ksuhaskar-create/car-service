"""Работа с базой данных CarTrack."""
from .database import configure, get_connection, get_db_path, init_db, transaction
from .database import DBError
