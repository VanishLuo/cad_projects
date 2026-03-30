from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from license_management.domain.models.license_record import LicenseRecord
from license_management.infrastructure.repositories.sqlite_license_repository import (
    SqliteLicenseRepository,
)


def _record(record_id: str, server_name: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name=server_name,
        provider="FlexNet",
        prot="27000",
        feature_name="feat",
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
        vendor="ansys",
        start_executable_path="/opt/lmgrd",
        license_file_path="/opt/license.dat",
    )


def test_sqlite_repository_staging_publish_and_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "licenses.sqlite3"
    repo = SqliteLicenseRepository(db_path)
    repo.upsert(_record("r1", "srv-a"))

    repo.enter_staging_workspace()
    repo.upsert(_record("r2", "srv-b"))

    repo.switch_workspace("committed")
    assert [record.record_id for record in repo.list_all()] == ["r1"]

    repo.switch_workspace("staging")
    published = repo.publish_staging_to_committed()

    assert published == 2
    assert repo.current_workspace == "committed"
    assert [record.record_id for record in repo.list_all()] == ["r1", "r2"]

    reloaded = SqliteLicenseRepository(db_path)
    assert reloaded.current_workspace == "committed"
    assert [record.record_id for record in reloaded.list_all()] == ["r1", "r2"]


def test_sqlite_repository_drops_legacy_initial_table(tmp_path: Path) -> None:
    db_path = tmp_path / "licenses.sqlite3"
    SqliteLicenseRepository(db_path)
    table_name = "license_records_initial"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (record_id TEXT PRIMARY KEY, server_name TEXT)"
        )
        conn.commit()

    reloaded = SqliteLicenseRepository(db_path)
    assert reloaded.current_workspace == "committed"

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()

    assert row is not None
    assert int(row[0]) == 0


def test_sqlite_repository_text_snapshot_persists_initial_and_updates_current(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "licenses.sqlite3"
    repo = SqliteLicenseRepository(db_path)
    repo.upsert(_record("r1", "srv-a"))

    repo.upsert_license_text_snapshot("r1", initial_text="init", current_text="current-1")
    repo.upsert_license_text_snapshot("r1", initial_text="ignored", current_text="current-2")

    snapshot = repo.get_license_text_snapshot("r1")
    assert snapshot is not None
    assert snapshot[0] == "init"
    assert snapshot[1] == "current-2"


def test_sqlite_repository_delete_committed_removes_text_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "licenses.sqlite3"
    repo = SqliteLicenseRepository(db_path)
    repo.upsert(_record("r1", "srv-a"))
    repo.upsert_license_text_snapshot("r1", initial_text="init", current_text="current")

    deleted = repo.delete("r1")
    assert deleted is True
    assert repo.get_license_text_snapshot("r1") is None
