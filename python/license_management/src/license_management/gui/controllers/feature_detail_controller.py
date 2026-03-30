from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from license_management.domain.models.license_record import LicenseRecord


class FeatureDetailRepositoryProtocol(Protocol):
    def get(self, record_id: str) -> LicenseRecord | None: ...

    def list_all(self) -> list[LicenseRecord]: ...


class FeatureCatalogSyncResultProtocol(Protocol):
    @property
    def license_missing(self) -> bool: ...


class FeatureDetailCatalogProtocol(Protocol):
    def list_for_record(self, record: LicenseRecord) -> list[tuple[str, str, int]]: ...

    def sync_from_record(self, record: LicenseRecord) -> FeatureCatalogSyncResultProtocol: ...


@dataclass(slots=True, frozen=True)
class FeatureDetailData:
    found: bool
    reason: str = ""
    selected_record: LicenseRecord | None = None
    license_file_path: str = ""
    grouped_rows: tuple[tuple[str, str, int], ...] = ()
    record_count: int = 0
    sync_license_missing: bool = False


class FeatureDetailController:
    """Build feature detail presentation data for row double-click actions."""

    def __init__(
        self,
        *,
        repository: FeatureDetailRepositoryProtocol,
        feature_catalog: FeatureDetailCatalogProtocol,
    ) -> None:
        self._repository = repository
        self._feature_catalog = feature_catalog

    def build_for_record_id(self, record_id: str) -> FeatureDetailData:
        selected_record = self._repository.get(record_id)
        if selected_record is None:
            return FeatureDetailData(found=False, reason="record_not_found")

        license_file_path = selected_record.license_file_path.strip()
        grouped_rows = self._feature_catalog.list_for_record(selected_record)
        sync_license_missing = False
        if not grouped_rows:
            sync = self._feature_catalog.sync_from_record(selected_record)
            grouped_rows = self._feature_catalog.list_for_record(selected_record)
            sync_license_missing = sync.license_missing

        if not grouped_rows:
            all_records = self._repository.list_all()
            same_file_records = [
                record
                for record in all_records
                if record.license_file_path.strip() == license_file_path
            ]
            grouped_rows = self._build_feature_expiry_rows(same_file_records)
            record_count = len(same_file_records)
        else:
            record_count = sum(item[2] for item in grouped_rows)

        if not grouped_rows:
            return FeatureDetailData(
                found=False,
                reason="no_feature_data",
                selected_record=selected_record,
                license_file_path=license_file_path,
                sync_license_missing=sync_license_missing,
            )

        return FeatureDetailData(
            found=True,
            selected_record=selected_record,
            license_file_path=license_file_path,
            grouped_rows=tuple(grouped_rows),
            record_count=record_count,
            sync_license_missing=sync_license_missing,
        )

    def _build_feature_expiry_rows(
        self,
        records: list[LicenseRecord],
    ) -> list[tuple[str, str, int]]:
        grouped: dict[tuple[str, str], int] = {}
        for record in records:
            feature = record.feature_name.strip() or "(empty)"
            expires_on = record.expires_on.isoformat()
            key = (feature, expires_on)
            grouped[key] = grouped.get(key, 0) + 1

        rows = [(feature, expires_on, count) for (feature, expires_on), count in grouped.items()]
        rows.sort(key=lambda item: (item[1], item[0].lower()))
        return rows
