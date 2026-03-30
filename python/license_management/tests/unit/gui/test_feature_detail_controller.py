from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.controllers.feature_detail_controller import FeatureDetailController


def _record(record_id: str, feature_name: str, path: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv",
        provider="FlexNet",
        prot="27000",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
        vendor="ansys",
        start_executable_path="/opt/lmgrd",
        license_file_path=path,
    )


class _Repo:
    def __init__(self) -> None:
        self.records = [
            _record("r1", "f1", "/a.lic"),
            _record("r2", "f2", "/a.lic"),
        ]

    def get(self, record_id: str) -> LicenseRecord | None:
        for record in self.records:
            if record.record_id == record_id:
                return record
        return None

    def list_all(self) -> list[LicenseRecord]:
        return list(self.records)


@dataclass(slots=True, frozen=True)
class _SyncResult:
    license_missing: bool


class _Catalog:
    def __init__(self) -> None:
        self.rows: dict[str, list[tuple[str, str, int]]] = {}
        self.missing = False

    def list_for_record(self, record: LicenseRecord) -> list[tuple[str, str, int]]:
        return list(self.rows.get(record.record_id, []))

    def sync_from_record(self, record: LicenseRecord) -> _SyncResult:
        _ = record
        return _SyncResult(license_missing=self.missing)


def test_build_for_record_id_returns_not_found_when_missing() -> None:
    controller = FeatureDetailController(repository=_Repo(), feature_catalog=_Catalog())
    result = controller.build_for_record_id("missing")

    assert result.found is False
    assert result.reason == "record_not_found"


def test_build_for_record_id_uses_catalog_rows_when_available() -> None:
    repo = _Repo()
    catalog = _Catalog()
    catalog.rows["r1"] = [("feat", "2026-06-01", 3)]
    controller = FeatureDetailController(repository=repo, feature_catalog=catalog)
    result = controller.build_for_record_id("r1")

    assert result.found is True
    assert result.record_count == 3
    assert len(result.grouped_rows) == 1


def test_build_for_record_id_falls_back_to_same_file_grouping() -> None:
    repo = _Repo()
    catalog = _Catalog()
    controller = FeatureDetailController(repository=repo, feature_catalog=catalog)
    result = controller.build_for_record_id("r1")

    assert result.found is True
    assert result.record_count == 2
    assert len(result.grouped_rows) == 2
