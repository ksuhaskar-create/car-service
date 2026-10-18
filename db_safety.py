import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

KEEP_BACKUPS = 10

def _is_healthy(db_file):
    try:
        connection = sqlite3.connect(db_file)
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()
        finally:
            connection.close()
        return result is not None and result[0] == "ok"
    except sqlite3.Error:
        return False

def _make_backup(db_file, backups_dir):
    backups_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    target = backups_dir / f"cartrack_{stamp}.db"

    source = sqlite3.connect(db_file)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    copies = sorted(backups_dir.glob("cartrack_*.db"))
    for old in copies[:-KEEP_BACKUPS]:
        old.unlink()

def prepare_database(db_path):
    db_file = Path(db_path)
    backups_dir = db_file.parent / "backups"

    if not db_file.exists():
        return

    if _is_healthy(db_file):
        _make_backup(db_file, backups_dir)
        return

    broken_dir = db_file.parent / "broken"
    broken_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    shutil.move(str(db_file), str(broken_dir / f"cartrack_{stamp}.db"))
    for suffix in ("-journal", "-wal", "-shm"):
        extra = Path(str(db_file) + suffix)
        if extra.exists():
            extra.unlink()

    for copy in sorted(backups_dir.glob("cartrack_*.db"), reverse=True):
        if _is_healthy(copy):
            shutil.copy2(copy, db_file)
            print(f"[CarTrack] База была повреждена. Восстановлена копия: {copy.name}")
            return

    print("[CarTrack] База была повреждена, копий нет. Будет создана новая пустая база.")