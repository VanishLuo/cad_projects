from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.application.import_pipeline import ImportPipelineService
from license_management.gui.dialog_flows import DialogFlowBinder
from license_management.gui.models import FeedbackCenter
from license_management.infrastructure.repositories.in_memory_license_repository import (
    InMemoryLicenseRepository,
)


class StableExecutor:
    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        _ = password
        return 0, "ok", ""


def _record_payload(index: int) -> dict[str, str]:
    expires = date(2026, 12, 1).isoformat()
    return {
        "record_id": f"rec-{index:03d}",
        "server_name": f"srv-{index % 4}",
        "provider": "FlexNet",
        "prot": str(27000 + (index % 6)),
        "feature_name": f"FEATURE-{index % 6}",
        "process_name": "lmgrd",
        "expires_on": expires,
    }


def _write_payloads(file_path: Path, count: int) -> None:
    payloads = [_record_payload(i) for i in range(count)]
    file_path.write_text(json.dumps(payloads), encoding="utf-8")


def test_capacity_baseline_20_and_expansion_24_import(tmp_path: Path) -> None:
    repo = InMemoryLicenseRepository()
    import_service = ImportPipelineService(repo)

    baseline_file = tmp_path / "baseline_20.json"
    expansion_file = tmp_path / "expansion_24.json"
    _write_payloads(baseline_file, 20)
    _write_payloads(expansion_file, 24)

    baseline_report = import_service.import_single_file(baseline_file)
    assert baseline_report.succeeded == 20
    assert baseline_report.failed == 0

    repo = InMemoryLicenseRepository()
    import_service = ImportPipelineService(repo)
    expansion_report = import_service.import_single_file(expansion_file)
    assert expansion_report.succeeded == 24
    assert expansion_report.failed == 0


def test_start_stop_stability_for_8_cycles() -> None:
    binder = DialogFlowBinder(
        repository=InMemoryLicenseRepository(),
        feedback_center=FeedbackCenter(),
        flexnet_adapter=FlexNetAdapter(StableExecutor(), retry_times=0),
    )

    for _ in range(8):
        start_result = binder.start_stop(action="start", host="srv-a", username="ops")
        stop_result = binder.start_stop(action="stop", host="srv-a", username="ops")
        assert start_result.success is True
        assert stop_result.success is True
