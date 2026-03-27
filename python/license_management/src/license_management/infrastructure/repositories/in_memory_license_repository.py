from __future__ import annotations

from license_management.domain.models.license_record import LicenseRecord


class InMemoryLicenseRepository:
    """Simple in-memory repository for early development and tests."""

    def __init__(self) -> None:
        self._committed_records: dict[str, LicenseRecord] = {}
        self._staging_records: dict[str, LicenseRecord] = {}
        self._current_workspace = "committed"

    @property
    def current_workspace(self) -> str:
        return self._current_workspace

    def switch_workspace(self, workspace: str) -> None:
        if workspace not in {"staging", "committed"}:
            raise ValueError(f"Unsupported workspace: {workspace}")
        self._current_workspace = workspace

    def enter_staging_workspace(self) -> None:
        if self._current_workspace != "staging":
            self._staging_records = dict(self._committed_records)
            self._current_workspace = "staging"

    def publish_staging_to_committed(self) -> int:
        self._committed_records = dict(self._staging_records)
        self._staging_records = {}
        self._current_workspace = "committed"
        return len(self._committed_records)

    def _active_records(self) -> dict[str, LicenseRecord]:
        return self._staging_records if self._current_workspace == "staging" else self._committed_records

    def upsert(self, record: LicenseRecord) -> None:
        self._active_records()[record.record_id] = record

    def get(self, record_id: str) -> LicenseRecord | None:
        return self._active_records().get(record_id)

    def list_all(self) -> list[LicenseRecord]:
        return list(self._active_records().values())

    def delete(self, record_id: str) -> bool:
        return self._active_records().pop(record_id, None) is not None
