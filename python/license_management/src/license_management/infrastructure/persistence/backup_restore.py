from __future__ import annotations

import shutil
import sqlite3
from collections.abc import Callable
from pathlib import Path


def backup_sqlite(db_path: Path, backup_dir: Path, *, backup_name: str | None = None) -> Path:
    """Creates a SQLite backup copy and returns the backup file path."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / (backup_name or f"{db_path.stem}.backup.sqlite")

    with sqlite3.connect(db_path) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
    return target


def restore_sqlite(backup_path: Path, db_path: Path) -> None:
    """Restores database file from a backup copy."""
    shutil.copy2(backup_path, db_path)


def run_with_rollback(db_path: Path, backup_dir: Path, operation: Callable[[], None]) -> None:
    """Runs an operation and restores database from backup if it fails."""
    backup_path = backup_sqlite(db_path, backup_dir)
    try:
        operation()
    except Exception:
        restore_sqlite(backup_path, db_path)
        raise
