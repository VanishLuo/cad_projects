from __future__ import annotations

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


class StubSshExecutor:
    def __init__(self, *, start_exit_code: int = 0, stop_exit_code: int = 0) -> None:
        self._start_exit_code = start_exit_code
        self._stop_exit_code = stop_exit_code

    def run(
        self,
        *,
        host: str,
        username: str,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        if "lmdown" in command:
            if self._stop_exit_code == 0:
                return 0, "stopped", ""
            return self._stop_exit_code, "", "stop failed"

        if self._start_exit_code == 0:
            return 0, "started", ""
        return self._start_exit_code, "", "start failed"


def _record(record_id: str, feature_name: str, server_name: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name=server_name,
        provider="FlexNet",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=date(2026, 12, 31),
    )


def test_dialog_binder_import_and_compare_integration(tmp_path: Path) -> None:
    repository = InMemoryLicenseRepository()
    feedback = FeedbackCenter()
    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
        import_service=ImportPipelineService(repository),
        compare_service=CrossTargetCompareService(),
    )

    import_file = tmp_path / "records.json"
    import_file.write_text(
        """
        [
          {
            "record_id": "r-001",
            "server_name": "srv-a",
            "provider": "FlexNet",
                        "prot": "27000",
            "feature_name": "ANSYS-MECH",
            "process_name": "lmgrd",
            "expires_on": "2026-12-31"
          },
          {
            "record_id": "r-002",
            "server_name": "srv-b",
            "provider": "FlexNet",
                        "prot": "27001",
            "feature_name": "ANSYS-CFD",
            "process_name": "lmgrd",
            "expires_on": "2026-11-30"
          }
        ]
        """.strip(),
        encoding="utf-8",
    )

    import_result, report = binder.import_files([import_file])

    assert import_result.success is True
    assert report is not None
    assert report.succeeded == 2
    assert len(repository.list_all()) == 2

    compare_result, compare_report = binder.compare(
        left_target="left",
        left_records=[_record("r-001", "ANSYS-MECH", "srv-a")],
        right_target="right",
        right_records=[_record("r-001", "ANSYS-MECH", "srv-a")],
    )

    assert compare_result.success is True
    assert compare_report is not None
    assert compare_report.has_differences is False


def test_feature_search_consistent_with_view_model_filters() -> None:
    vm = MainListViewModel()
    vm.load(
        [
            _record("code-001", "ANSYS-MECH", "prod-a"),
            _record("code-002", "ANSYS-CFD", "prod-a"),
            _record("code-003", "MATLAB", "dev-a"),
        ],
        today=date(2026, 6, 1),
    )

    controller = FeatureSearchController(vm)
    result = controller.search(
        today=date(2026, 6, 1),
        keyword="code-00",
        server_name="prod",
    )

    ids = [row.record_id for row in result.rows]
    assert sorted(ids) == ["code-001", "code-002"]


def test_start_stop_failure_generates_traceable_feedback() -> None:
    feedback = FeedbackCenter()
    binder = DialogFlowBinder(
        repository=InMemoryLicenseRepository(),
        feedback_center=feedback,
        flexnet_adapter=FlexNetAdapter(StubSshExecutor(start_exit_code=1), retry_times=0),
    )

    result = binder.start_stop(action="start", host="srv-a", username="ops")

    assert result.success is False
    assert result.feedback.level == "error"
    assert result.feedback.action == "view_operation_log"
