from __future__ import annotations

import json
from pathlib import Path

from license_management.application.import_pipeline import ImportPipelineService
from license_management.infrastructure.repositories.in_memory_license_repository import (
    InMemoryLicenseRepository,
)


def _single_payload() -> dict[str, str]:
    return {
        "record_id": "r1",
        "server_name": "srv-a",
        "provider": "FlexNet",
        "feature_name": "F1",
        "process_name": "lmgrd",
        "expires_on": "2026-12-31",
    }


def test_import_single_file_succeeds(tmp_path: Path) -> None:
    file_path = tmp_path / "single.json"
    file_path.write_text(json.dumps(_single_payload()), encoding="utf-8")

    repo = InMemoryLicenseRepository()
    service = ImportPipelineService(repo)

    report = service.import_single_file(file_path)

    assert report.total == 1
    assert report.succeeded == 1
    assert report.failed == 0
    assert report.deduplicated == 0
    assert report.invalid == 0
    assert report.errors == []
    assert report.warnings == []
    assert repo.get("r1") is not None


def test_import_batch_files_succeeds_for_two_files(tmp_path: Path) -> None:
    payload1 = _single_payload()
    payload2 = {**_single_payload(), "record_id": "r2", "feature_name": "F2"}

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(payload1), encoding="utf-8")
    second.write_text(json.dumps(payload2), encoding="utf-8")

    repo = InMemoryLicenseRepository()
    service = ImportPipelineService(repo)

    report = service.import_batch_files([first, second])

    assert report.total == 2
    assert report.succeeded == 2
    assert report.failed == 0
    assert report.deduplicated == 0
    assert report.invalid == 0
    assert report.errors == []
    assert report.warnings == []
    assert repo.get("r1") is not None
    assert repo.get("r2") is not None


def test_import_batch_files_records_errors_for_invalid_payload(tmp_path: Path) -> None:
    ok_file = tmp_path / "ok.json"
    bad_file = tmp_path / "bad.json"

    ok_file.write_text(json.dumps(_single_payload()), encoding="utf-8")
    bad_file.write_text(json.dumps({"record_id": "bad"}), encoding="utf-8")

    repo = InMemoryLicenseRepository()
    service = ImportPipelineService(repo)

    report = service.import_batch_files([ok_file, bad_file])

    assert report.total == 2
    assert report.succeeded == 1
    assert report.failed == 1
    assert report.deduplicated == 0
    assert report.invalid == 1
    assert len(report.errors) == 1
    assert report.warnings == []


def test_import_batch_files_skips_duplicate_record_ids_in_payload(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    first.write_text(json.dumps(_single_payload()), encoding="utf-8")
    second.write_text(json.dumps(_single_payload()), encoding="utf-8")

    repo = InMemoryLicenseRepository()
    service = ImportPipelineService(repo)

    report = service.import_batch_files([first, second])

    assert report.total == 2
    assert report.succeeded == 1
    assert report.failed == 0
    assert report.deduplicated == 1
    assert report.invalid == 0
    assert report.errors == []
    assert len(report.warnings) == 1


def test_import_single_file_skips_duplicate_record_id_already_in_repo(tmp_path: Path) -> None:
    file_path = tmp_path / "single.json"
    file_path.write_text(json.dumps(_single_payload()), encoding="utf-8")

    repo = InMemoryLicenseRepository()
    service = ImportPipelineService(repo)
    first = service.import_single_file(file_path)
    second = service.import_single_file(file_path)

    assert first.succeeded == 1
    assert second.succeeded == 0
    assert second.failed == 0
    assert second.deduplicated == 1
    assert second.invalid == 0
    assert len(second.warnings) == 1
