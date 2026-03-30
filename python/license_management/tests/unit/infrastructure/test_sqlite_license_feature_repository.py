from __future__ import annotations

from datetime import date
from pathlib import Path

from license_management.application.license_file_parser import ParsedLicenseFeature
from license_management.domain.models.license_record import LicenseRecord
from license_management.infrastructure.repositories.sqlite_license_feature_repository import (
    SqliteLicenseFeatureRepository,
)
from license_management.application.license_feature_catalog import LicenseFeatureCatalogService


def _record(record_id: str, license_file_path: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv-a",
        provider="FlexNet",
        vendor="cadence",
        prot="27000",
        feature_name="",
        process_name="lmgrd",
        expires_on=date(2026, 1, 1),
        license_file_path=license_file_path,
    )


def test_replace_for_record_keeps_duplicate_rows_without_aggregation(tmp_path: Path) -> None:
    repo = SqliteLicenseFeatureRepository(tmp_path / "feature.sqlite3")
    record = _record("r1", "C:/demo/a.lic")

    repo.replace_for_record(
        record,
        [
            ParsedLicenseFeature(feature_name="FEAT-A", expires_on=date(2026, 12, 31), quantity=1),
            ParsedLicenseFeature(feature_name="FEAT-A", expires_on=date(2026, 12, 31), quantity=1),
            ParsedLicenseFeature(feature_name="FEAT-A", expires_on=date(2026, 12, 31), quantity=5),
        ],
    )

    rows = repo.list_for_record(record)
    assert len(rows) == 3
    assert rows[0] == ("FEAT-A", "2026-12-31", 1)
    assert rows[1] == ("FEAT-A", "2026-12-31", 1)
    assert rows[2] == ("FEAT-A", "2026-12-31", 5)


def test_list_for_record_matches_after_path_normalization(tmp_path: Path) -> None:
    repo = SqliteLicenseFeatureRepository(tmp_path / "feature.sqlite3")
    stored = _record("r1", "\u202aC:/demo/a.lic")

    repo.replace_for_record(
        stored,
        [
            ParsedLicenseFeature(feature_name="FEAT-N", expires_on=date(2027, 1, 1), quantity=2),
        ],
    )

    lookup = _record("r1", "C:/demo/a.lic")
    rows = repo.list_for_record(lookup)
    assert rows == [("FEAT-N", "2027-01-01", 2)]


def test_feature_catalog_remove_for_record_deletes_rows(tmp_path: Path) -> None:
    repo = SqliteLicenseFeatureRepository(tmp_path / "feature.sqlite3")
    service = LicenseFeatureCatalogService(repository=repo)
    record = _record("r1", "C:/demo/remove.lic")

    repo.replace_for_record(
        record,
        [ParsedLicenseFeature(feature_name="FEAT-R", expires_on=date(2028, 2, 2), quantity=1)],
    )
    assert repo.list_for_record(record) == [("FEAT-R", "2028-02-02", 1)]

    service.remove_for_record(record)
    assert repo.list_for_record(record) == []


def test_feature_rows_are_isolated_by_record_id(tmp_path: Path) -> None:
    repo = SqliteLicenseFeatureRepository(tmp_path / "feature.sqlite3")
    record_a = _record("r1", "C:/demo/shared.lic")
    record_b = _record("r2", "C:/demo/shared.lic")

    repo.replace_for_record(
        record_a,
        [ParsedLicenseFeature(feature_name="FEAT-A", expires_on=date(2028, 1, 1), quantity=1)],
    )
    repo.replace_for_record(
        record_b,
        [ParsedLicenseFeature(feature_name="FEAT-B", expires_on=date(2029, 1, 1), quantity=2)],
    )

    assert repo.list_for_record(record_a) == [("FEAT-A", "2028-01-01", 1)]
    assert repo.list_for_record(record_b) == [("FEAT-B", "2029-01-01", 2)]


def test_feature_repository_staging_publish_and_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "feature.sqlite3"
    repo = SqliteLicenseFeatureRepository(db_path)
    committed = _record("r1", "C:/demo/committed.lic")
    staged = _record("r2", "C:/demo/staged.lic")

    repo.replace_for_record(
        committed,
        [ParsedLicenseFeature(feature_name="FEAT-C", expires_on=date(2026, 1, 1), quantity=1)],
    )

    repo.enter_staging_workspace()
    repo.replace_for_record(
        staged,
        [ParsedLicenseFeature(feature_name="FEAT-S", expires_on=date(2026, 2, 2), quantity=2)],
    )

    repo.switch_workspace("committed")
    committed_rows = repo.list_for_record(committed)
    assert committed_rows == [("FEAT-C", "2026-01-01", 1)]
    assert repo.list_for_record(staged) == []

    repo.switch_workspace("staging")
    published = repo.publish_staging_to_committed()
    assert published == 2
    assert repo.current_workspace == "committed"
    assert repo.list_for_record(committed) == [("FEAT-C", "2026-01-01", 1)]
    assert repo.list_for_record(staged) == [("FEAT-S", "2026-02-02", 2)]

    reloaded = SqliteLicenseFeatureRepository(db_path)
    assert reloaded.current_workspace == "committed"
    assert reloaded.list_for_record(committed) == [("FEAT-C", "2026-01-01", 1)]
    assert reloaded.list_for_record(staged) == [("FEAT-S", "2026-02-02", 2)]
