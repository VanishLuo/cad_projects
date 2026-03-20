from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.application.compare_service import (
    CompareReport,
    CrossTargetCompareService,
    TargetSnapshot,
)
from license_management.application.import_pipeline import ImportPipelineService, ImportReport
from license_management.domain.models.license_record import LicenseRecord
from license_management.domain.ports.license_repository import LicenseRepository
from license_management.gui.models import FeedbackCenter, FeedbackMessage
from license_management.gui.validation_feedback import to_license_record, validate_license_form


@dataclass(slots=True, frozen=True)
class DialogResult:
    success: bool
    feedback: FeedbackMessage


class DialogFlowBinder:
    """M06 T6.2/T6.3 dialog actions bound to service-layer APIs."""

    def __init__(
        self,
        *,
        repository: LicenseRepository,
        feedback_center: FeedbackCenter,
        import_service: ImportPipelineService | None = None,
        flexnet_adapter: FlexNetAdapter | None = None,
        compare_service: CrossTargetCompareService | None = None,
    ) -> None:
        self._repository = repository
        self._feedback = feedback_center
        self._import_service = import_service
        self._flexnet_adapter = flexnet_adapter
        self._compare_service = compare_service

    def add_or_edit(self, form_payload: dict[str, str]) -> DialogResult:
        validation = validate_license_form(form_payload)
        if not validation.is_valid:
            detail = "; ".join(issue.message for issue in validation.issues)
            message = FeedbackMessage(
                level="error",
                title="Validation failed",
                detail=detail,
                action="fix_input",
            )
            self._feedback.add(message)
            return DialogResult(success=False, feedback=message)

        record = to_license_record(form_payload)
        self._repository.upsert(record)
        message = FeedbackMessage(
            level="success",
            title="Record saved",
            detail=f"Record {record.record_id} saved successfully.",
            action="refresh_list",
        )
        self._feedback.add(message)
        return DialogResult(success=True, feedback=message)

    def import_files(self, file_paths: list[Path]) -> tuple[DialogResult, ImportReport | None]:
        if self._import_service is None:
            message = FeedbackMessage(
                level="error",
                title="Import unavailable",
                detail="Import service is not configured.",
                action="configure_import_service",
            )
            self._feedback.add(message)
            return DialogResult(success=False, feedback=message), None

        report = self._import_service.import_batch_files(file_paths)
        success = report.failed == 0
        level = "success" if success else "warning"
        message = FeedbackMessage(
            level=level,
            title="Import completed",
            detail=(
                f"total={report.total}, succeeded={report.succeeded}, "
                f"failed={report.failed}, deduplicated={report.deduplicated}"
            ),
            action="show_import_report",
        )
        self._feedback.add(message)
        return DialogResult(success=success, feedback=message), report

    def start_stop(self, *, action: str, host: str, username: str) -> DialogResult:
        if self._flexnet_adapter is None:
            message = FeedbackMessage(
                level="error",
                title="Operation unavailable",
                detail="FlexNet adapter is not configured.",
                action="configure_adapter",
            )
            self._feedback.add(message)
            return DialogResult(success=False, feedback=message)

        if action not in {"start", "stop"}:
            message = FeedbackMessage(
                level="error",
                title="Invalid action",
                detail=f"Unsupported action: {action}",
                action="use_start_or_stop",
            )
            self._feedback.add(message)
            return DialogResult(success=False, feedback=message)

        result = (
            self._flexnet_adapter.start(host=host, username=username)
            if action == "start"
            else self._flexnet_adapter.stop(host=host, username=username)
        )
        level = "success" if result.succeeded else "error"
        message = FeedbackMessage(
            level=level,
            title=f"{action.title()} completed",
            detail=f"attempts={result.attempts}, rollback={result.rollback_attempted}",
            action="view_operation_log",
        )
        self._feedback.add(message)
        return DialogResult(success=result.succeeded, feedback=message)

    def compare(
        self,
        *,
        left_target: str,
        left_records: list[LicenseRecord],
        right_target: str,
        right_records: list[LicenseRecord],
    ) -> tuple[DialogResult, CompareReport | None]:
        if self._compare_service is None:
            message = FeedbackMessage(
                level="error",
                title="Compare unavailable",
                detail="Compare service is not configured.",
                action="configure_compare_service",
            )
            self._feedback.add(message)
            return DialogResult(success=False, feedback=message), None

        report = self._compare_service.compare(
            TargetSnapshot(target_name=left_target, records=tuple(left_records)),
            TargetSnapshot(target_name=right_target, records=tuple(right_records)),
        )
        level = "warning" if report.has_differences else "success"
        message = FeedbackMessage(
            level=level,
            title="Comparison completed",
            detail=f"differences={len(report.issues)}",
            action="open_compare_report",
        )
        self._feedback.add(message)
        return DialogResult(success=True, feedback=message), report

    def export_records(self, *, file_path: Path, records: list[LicenseRecord]) -> DialogResult:
        serialized = [
            {
                "record_id": record.record_id,
                "server_name": record.server_name,
                "provider": record.provider,
                "feature_name": record.feature_name,
                "process_name": record.process_name,
                "expires_on": record.expires_on.isoformat(),
            }
            for record in sorted(records, key=lambda item: item.record_id)
        ]
        file_path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")

        message = FeedbackMessage(
            level="success",
            title="Export completed",
            detail=f"Exported {len(serialized)} records to {file_path}",
            action="open_export_file",
        )
        self._feedback.add(message)
        return DialogResult(success=True, feedback=message)
