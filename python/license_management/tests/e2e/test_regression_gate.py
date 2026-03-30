from __future__ import annotations

from datetime import date

from license_management.application.compare_service import CrossTargetCompareService, TargetSnapshot
from license_management.application.import_pipeline import ImportPipelineService
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.flows.dialog_flows import DialogFlowBinder
from license_management.gui.state.models import FeedbackCenter
from license_management.gui.state.view_model import MainListViewModel, SearchFilters
from license_management.infrastructure.repositories.in_memory_license_repository import (
    InMemoryLicenseRepository,
)


def _record(record_id: str, feature_name: str, expires_on: date) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv-a",
        provider="FlexNet",
        prot="27000",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=expires_on,
    )


def test_regression_core_flows_stay_consistent() -> None:
    repo = InMemoryLicenseRepository()
    feedback = FeedbackCenter()
    binder = DialogFlowBinder(
        repository=repo,
        feedback_center=feedback,
        import_service=ImportPipelineService(repo),
        compare_service=CrossTargetCompareService(),
    )

    saved = binder.add_or_edit(
        {
            "record_id": "r-001",
            "server_name": "srv-a",
            "provider": "FlexNet",
            "prot": "27000",
            "feature_name": "ANSYS-MECH",
            "process_name": "lmgrd",
            "expires_on": "2026-12-31",
        }
    )
    assert saved.success is True

    vm = MainListViewModel()
    vm.load(repo.list_all(), today=date(2026, 6, 1))
    filtered = vm.search_and_filter(
        filters=SearchFilters(keyword="r-001"),
        today=date(2026, 6, 1),
    )
    assert [row.record_id for row in filtered] == ["r-001"]

    report = CrossTargetCompareService().compare(
        TargetSnapshot("left", tuple(repo.list_all())),
        TargetSnapshot("right", tuple(repo.list_all())),
    )
    assert report.has_differences is False


def test_regression_validation_feedback_recovery_path() -> None:
    binder = DialogFlowBinder(
        repository=InMemoryLicenseRepository(),
        feedback_center=FeedbackCenter(),
    )

    failed = binder.add_or_edit(
        {
            "record_id": "",
            "server_name": "",
            "provider": "",
            "prot": "",
            "feature_name": "",
            "process_name": "",
            "expires_on": "bad-date",
        }
    )
    assert failed.success is False
    assert failed.feedback.level == "error"

    recovered = binder.add_or_edit(
        {
            "record_id": "r-002",
            "server_name": "srv-b",
            "provider": "FlexNet",
            "prot": "27001",
            "feature_name": "ANSYS-CFD",
            "process_name": "lmgrd",
            "expires_on": "2026-12-01",
        }
    )
    assert recovered.success is True
