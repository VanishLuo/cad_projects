from __future__ import annotations

import sqlite3
from pathlib import Path

from license_management.infrastructure.migrations.schema_migrator import SchemaMigrator


def test_apply_baseline_v1_creates_table_and_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    migrator = SchemaMigrator(db_path)

    assert migrator.apply_baseline_v1()
    assert not migrator.apply_baseline_v1()

    with sqlite3.connect(db_path) as conn:
        table_row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='license_records'"
        ).fetchone()
        assert table_row is not None

        index_names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='license_records'"
            ).fetchall()
        }

    assert "idx_license_records_provider" in index_names
    assert "idx_license_records_expires_on" in index_names


def test_applied_migrations_reports_baseline_id(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    migrator = SchemaMigrator(db_path)

    migrator.apply_baseline_v1()

    assert "0001_baseline" in migrator.applied_migrations()
