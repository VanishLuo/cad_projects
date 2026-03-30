from __future__ import annotations

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
