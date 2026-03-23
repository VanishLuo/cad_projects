from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.application.compare_service import CrossTargetCompareService
from license_management.application.import_pipeline import ImportPipelineService
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.dialog_flows import DialogFlowBinder
from license_management.gui.models import FeedbackCenter
from license_management.infrastructure.repositories.in_memory_license_repository import (
    InMemoryLicenseRepository,
)


class StubSshExecutor:
    def __init__(self, exit_code: int = 0) -> None:
        self._exit_code = exit_code

    def run(
        self,
        *,
        host: str,
        username: str,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        if self._exit_code == 0:
            return 0, "ok", ""
        return 1, "", "failed"


def _record(record_id: str, feature_name: str, expires_on: date) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv-a",
        provider="FlexNet",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=expires_on,
    )


def test_add_or_edit_returns_validation_error() -> None:
    binder = DialogFlowBinder(
        repository=InMemoryLicenseRepository(),
        feedback_center=FeedbackCenter(),
    )

    result = binder.add_or_edit({"record_id": ""})

    assert result.success is False
    assert result.feedback.level == "error"


def test_add_or_edit_import_start_stop_compare_export_flow(tmp_path: Path) -> None:
    repository = InMemoryLicenseRepository()
    feedback = FeedbackCenter()
    import_service = ImportPipelineService(repository)
    adapter = FlexNetAdapter(StubSshExecutor(), retry_times=0)
    compare_service = CrossTargetCompareService()

    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
        import_service=import_service,
        flexnet_adapter=adapter,
        compare_service=compare_service,
    )

    add_result = binder.add_or_edit(
        {
            "record_id": "r1",
            "server_name": "srv-a",
            "provider": "FlexNet",
            "feature_name": "ANSYS-MECH",
            "process_name": "lmgrd",
            "expires_on": "2026-12-31",
        }
    )
    assert add_result.success is True

    import_file = tmp_path / "import.json"
    import_file.write_text(
        json.dumps(
            {
                "record_id": "r2",
                "server_name": "srv-b",
                "provider": "FlexNet",
                "prot": "27000",
                "feature_name": "ANSYS-CFD",
                "process_name": "lmgrd",
                "expires_on": "2026-12-01",
            }
        ),
        encoding="utf-8",
    )

    import_result, import_report = binder.import_files([import_file])
    assert import_result.success is True
    assert import_report is not None
    assert import_report.succeeded == 1

    start_result = binder.start_stop(action="start", host="srv-a", username="ops")
    assert start_result.success is True

    compare_result, compare_report = binder.compare(
        left_target="left",
        left_records=[_record("r1", "ANSYS-MECH", date(2026, 12, 31))],
        right_target="right",
        right_records=[_record("r1", "ANSYS-MECH", date(2027, 1, 1))],
    )
    assert compare_result.success is True
    assert compare_report is not None
    assert compare_report.has_differences is True

    export_file = tmp_path / "export.json"
    export_result = binder.export_records(file_path=export_file, records=repository.list_all())
    assert export_result.success is True
    assert export_file.exists()
