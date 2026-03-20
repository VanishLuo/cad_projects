from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.application.compare_service import CrossTargetCompareService
from license_management.application.import_pipeline import ImportPipelineService
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.dialog_flows import DialogFlowBinder
from license_management.gui.feature_search import FeatureSearchController
from license_management.gui.models import FeedbackCenter
from license_management.gui.view_model import MainListViewModel
from license_management.infrastructure.repositories.in_memory_license_repository import (
    InMemoryLicenseRepository,
)


class HappyPathExecutor:
    def run(
        self,
        *,
        host: str,
        username: str,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        return 0, "ok", ""


def _record(record_id: str, feature_name: str, expires_on: date) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv-a",
        provider="FlexNet",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=expires_on,
    )


def test_e2e_core_flow_import_filter_compare_export(tmp_path: Path) -> None:
    repository = InMemoryLicenseRepository()
    feedback = FeedbackCenter()
    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
        import_service=ImportPipelineService(repository),
        flexnet_adapter=FlexNetAdapter(HappyPathExecutor(), retry_times=0),
        compare_service=CrossTargetCompareService(),
    )

    import_file = tmp_path / "import.json"
    import_file.write_text(
        json.dumps(
            [
                {
                    "record_id": "r-001",
                    "server_name": "srv-a",
                    "provider": "FlexNet",
                    "feature_name": "ANSYS-MECH",
                    "process_name": "lmgrd",
                    "expires_on": "2026-12-31",
                },
                {
                    "record_id": "r-002",
                    "server_name": "srv-b",
                    "provider": "FlexNet",
                    "feature_name": "ANSYS-CFD",
                    "process_name": "lmgrd",
                    "expires_on": "2026-11-30",
                },
            ]
        ),
        encoding="utf-8",
    )

    import_result, _ = binder.import_files([import_file])
    assert import_result.success is True

    vm = MainListViewModel()
    vm.load(repository.list_all(), today=date(2026, 6, 1))
    search = FeatureSearchController(vm).search(
        today=date(2026, 6, 1),
        feature_name="ANSYS",
        keyword="MECH",
    )
    assert [row.record_id for row in search.rows] == ["r-001"]

    compare_result, compare_report = binder.compare(
        left_target="left",
        left_records=[_record("r-001", "ANSYS-MECH", date(2026, 12, 31))],
        right_target="right",
        right_records=[_record("r-001", "ANSYS-MECH", date(2027, 1, 1))],
    )
    assert compare_result.success is True
    assert compare_report is not None
    assert compare_report.has_differences is True

    export_file = tmp_path / "export.json"
    export_result = binder.export_records(file_path=export_file, records=repository.list_all())
    assert export_result.success is True
    assert export_file.exists()


def test_e2e_invalid_form_shows_recoverable_feedback() -> None:
    binder = DialogFlowBinder(
        repository=InMemoryLicenseRepository(),
        feedback_center=FeedbackCenter(),
    )

    invalid_result = binder.add_or_edit(
        {
            "record_id": "",
            "server_name": "",
            "provider": "",
            "feature_name": "",
            "process_name": "",
            "expires_on": "bad-date",
        }
    )

    assert invalid_result.success is False
    assert invalid_result.feedback.level == "error"
    assert invalid_result.feedback.action == "fix_input"

    valid_result = binder.add_or_edit(
        {
            "record_id": "r-100",
            "server_name": "srv-a",
            "provider": "FlexNet",
            "feature_name": "ANSYS-MECH",
            "process_name": "lmgrd",
            "expires_on": "2026-12-31",
        }
    )
    assert valid_result.success is True
