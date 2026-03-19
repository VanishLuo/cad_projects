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
