from __future__ import annotations

from datetime import date

from license_management.domain.models.license_record import LicenseRecord
from license_management.infrastructure.repositories.in_memory_license_repository import (
    InMemoryLicenseRepository,
)


def test_in_memory_repository_upsert_get_list_delete() -> None:
    repo = InMemoryLicenseRepository()
    record = LicenseRecord(
        record_id="r1",
        server_name="srv-a",
        provider="FlexNet",
        feature_name="f1",
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
    )

    repo.upsert(record)

    assert repo.get("r1") == record
    assert repo.list_all() == [record]
    assert repo.delete("r1")
    assert repo.get("r1") is None


def test_in_memory_repository_staging_publish_and_reset() -> None:
    repo = InMemoryLicenseRepository()
    committed = LicenseRecord(
        record_id="r1",
        server_name="srv-a",
        provider="FlexNet",
        feature_name="f1",
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
    )
    staged = LicenseRecord(
        record_id="r2",
        server_name="srv-b",
        provider="FlexNet",
        feature_name="f2",
        process_name="lmgrd",
        expires_on=date(2026, 7, 1),
    )

    repo.upsert(committed)
    assert repo.current_workspace == "committed"

    repo.enter_staging_workspace()
    repo.upsert(staged)

    assert repo.current_workspace == "staging"
    assert {record.record_id for record in repo.list_all()} == {"r1", "r2"}

    repo.switch_workspace("committed")
    assert [record.record_id for record in repo.list_all()] == ["r1"]

    repo.switch_workspace("staging")
    published = repo.publish_staging_to_committed()

    assert published == 2
    assert repo.current_workspace == "committed"
    assert {record.record_id for record in repo.list_all()} == {"r1", "r2"}
