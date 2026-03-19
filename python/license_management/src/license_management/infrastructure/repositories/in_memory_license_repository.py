from __future__ import annotations

from license_management.domain.models.license_record import LicenseRecord


class InMemoryLicenseRepository:
    """Simple in-memory repository for early development and tests."""

    def __init__(self) -> None:
        self._records: dict[str, LicenseRecord] = {}

    def upsert(self, record: LicenseRecord) -> None:
        self._records[record.record_id] = record

    def get(self, record_id: str) -> LicenseRecord | None:
        return self._records.get(record_id)

    def list_all(self) -> list[LicenseRecord]:
        return list(self._records.values())

    def delete(self, record_id: str) -> bool:
        return self._records.pop(record_id, None) is not None
