from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import cast

from license_management.infrastructure.persistence.backup_restore import (
    backup_sqlite,
    run_with_rollback,
)


def _init_db(db_path: Path, value: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)")
        conn.execute(
            "INSERT OR REPLACE INTO kv (k, v) VALUES ('status', ?)",
            (value,),
        )
        conn.commit()


def _read_status(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT v FROM kv WHERE k='status'").fetchone()
    assert row is not None
    return cast(str, row[0])


def test_backup_sqlite_creates_copy(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    backup_dir = tmp_path / "backup"
    _init_db(db_path, "before")

    backup_path = backup_sqlite(db_path, backup_dir)

    assert backup_path.exists()


def test_run_with_rollback_restores_on_failure(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    backup_dir = tmp_path / "backup"
    _init_db(db_path, "before")

    def failing_operation() -> None:
        _init_db(db_path, "after")
        raise RuntimeError("boom")

    try:
        run_with_rollback(db_path, backup_dir, failing_operation)
    except RuntimeError:
        pass

    assert _read_status(db_path) == "before"
