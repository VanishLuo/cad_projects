from __future__ import annotations

from typing import Protocol

from license_management.domain.models.license_record import LicenseRecord


class LicenseRepository(Protocol):
    """Repository contract for license records."""

    def upsert(self, record: LicenseRecord) -> None: ...

    def get(self, record_id: str) -> LicenseRecord | None: ...

    def list_all(self) -> list[LicenseRecord]: ...

    def delete(self, record_id: str) -> bool: ...
