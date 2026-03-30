from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.adapters.provider_adapter import CommandAttemptLog
from license_management.application.compare_service import (
    CompareReport,
    CrossTargetCompareService,
    TargetSnapshot,
)
from license_management.application.import_pipeline import ImportPipelineService, ImportReport
from license_management.application.license_feature_catalog import LicenseFeatureCatalogService
from license_management.domain.models.license_record import LicenseRecord
from license_management.domain.ports.license_repository import LicenseRepository
from license_management.gui.state.models import FeedbackCenter, FeedbackMessage
from license_management.gui.validation_feedback import to_license_record, validate_license_form
from license_management.infrastructure.config.table_header_config import load_table_header_config


# DialogFlowBinder is responsible for handling user interactions from the GUI and invoking the appropriate service-layer APIs.
# DialogFlowBinder 负责处理来自 GUI 的用户交互并调用适当的服务层 API。
@dataclass(slots=True, frozen=True)
class DialogResult:
    success: bool
    feedback: FeedbackMessage
    operation_logs: tuple[CommandAttemptLog, ...] = ()


class DialogFlowBinder:
    """M06 T6.2/T6.3 dialog actions bound to service-layer APIs."""

    def __init__(
        self,
        *,
        repository: LicenseRepository,
        feedback_center: FeedbackCenter,
        import_service: ImportPipelineService | None = None,
        feature_catalog_service: LicenseFeatureCatalogService | None = None,
        flexnet_adapter: FlexNetAdapter | None = None,
        compare_service: CrossTargetCompareService | None = None,
    ) -> None:
        self._repository = repository
        self._feedback = feedback_center
        self._import_service = import_service
        self._feature_catalog_service = feature_catalog_service
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
        saved_count = 1
        catalog_suffix = ""
        if self._feature_catalog_service is not None:
            sync = self._feature_catalog_service.sync_from_record(record)
            if sync.license_missing:
                catalog_suffix = " feature_catalog=missing_license"
            else:
                catalog_suffix = (
                    f" feature_catalog_groups={sync.feature_groups}"
                    f" feature_catalog_quantity={sync.total_quantity}"
                )
        message = FeedbackMessage(
            level="success",
            title="Record saved",
            detail=(
                f"Record {record.record_id} saved successfully. "
                f"rows={saved_count}{catalog_suffix}"
            ),
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

    def start_stop(
        self,
        *,
        action: str,
        host: str,
        username: str,
        password: str | None = None,
        provider: str = "",
        start_executable_path: str | None = None,
        license_file_path: str | None = None,
        start_option_override: str | None = None,
    ) -> DialogResult:
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
            self._flexnet_adapter.start(
                host=host,
                username=username,
                password=password,
                provider=provider,
                executable_path=start_executable_path,
                license_file_path=license_file_path,
                start_option_override=start_option_override,
            )
            if action == "start"
            else self._flexnet_adapter.stop(host=host, username=username, password=password)
        )
        level = "success" if result.succeeded else "error"
        status_text = "succeeded" if result.succeeded else "failed"
        preview = ""
        if result.command_logs:
            first = result.command_logs[0]
            output = first.stdout.strip() or first.stderr.strip() or "(no output)"
            preview = (
                f"\ncommand={first.command}"
                f"\nexit_code={first.exit_code}"
                f"\noutput_preview={output[:240]}"
            )
        message = FeedbackMessage(
            level=level,
            title=f"{action.title()} completed",
            detail=(
                f"{action} {status_text}; attempts={result.attempts}; "
                f"rollback={result.rollback_attempted}. See logs for details.{preview}"
            ),
            action="view_operation_log",
        )
        self._feedback.add(message)
        return DialogResult(
            success=result.succeeded,
            feedback=message,
            operation_logs=result.command_logs,
        )

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
        serialized: list[dict[str, object]] = [
            {
                "record_id": record.record_id,
                "server_name": record.server_name,
                "prot": record.prot,
                "provider": record.provider,
                "vendor": record.vendor,
                "feature_name": record.feature_name,
                "process_name": record.process_name,
                "expires_on": record.expires_on.isoformat(),
                "start_executable_path": record.start_executable_path,
                "license_file_path": record.license_file_path,
                "start_option_override": record.start_option_override,
            }
            for record in sorted(records, key=lambda item: item.record_id)
        ]
        feature_rows = self._collect_feature_rows(records)
        if feature_rows:
            feature_index: dict[str, list[dict[str, str | int]]] = {}
            for feature_row in feature_rows:
                record_id = str(feature_row.get("record_id", "")).strip()
                feature_index.setdefault(record_id, []).append(feature_row)
            for serialized_row in serialized:
                serialized_row["features"] = feature_index.get(
                    str(serialized_row.get("record_id", "")).strip(), []
                )

        suffix = file_path.suffix.lower()
        try:
            if suffix in {".xlsx", ".xlsm"}:
                self._export_excel(file_path=file_path, rows=serialized, feature_rows=feature_rows)
            else:
                file_path.write_text(
                    json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except (OSError, ValueError) as exc:
            message = FeedbackMessage(
                level="error",
                title="Export failed",
                detail=f"Failed to export records to {file_path}: {exc}",
                action="retry_export",
            )
            self._feedback.add(message)
            return DialogResult(success=False, feedback=message)

        message = FeedbackMessage(
            level="success",
            title="Export completed",
            detail=f"Exported {len(serialized)} records to {file_path}",
            action="open_export_file",
        )
        self._feedback.add(message)
        return DialogResult(success=True, feedback=message)

    def _export_excel(
        self,
        *,
        file_path: Path,
        rows: list[dict[str, object]],
        feature_rows: list[dict[str, str | int]],
    ) -> None:
        try:
            openpyxl = importlib.import_module("openpyxl")
            workbook_cls = getattr(openpyxl, "Workbook")
            font_cls = getattr(importlib.import_module("openpyxl.styles"), "Font")
            alignment_cls = getattr(importlib.import_module("openpyxl.styles"), "Alignment")
            get_column_letter = getattr(
                importlib.import_module("openpyxl.utils"), "get_column_letter"
            )
        except ImportError as exc:
            raise ValueError("openpyxl is required for Excel export") from exc

        workbook = workbook_cls()
        sheet = workbook.active
        if sheet is None:
            raise ValueError("Unable to create Excel worksheet")
        headers = [
            key for key in load_table_header_config().sqlite_columns.keys() if key != "record_id"
        ]

        grouped_rows: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            vendor = str(row.get("vendor", "")).strip() or "UNKNOWN_VENDOR"
            grouped_rows.setdefault(vendor, []).append(row)
        if not grouped_rows:
            grouped_rows["UNKNOWN_VENDOR"] = []

        grouped_feature_rows: dict[str, list[dict[str, str | int]]] = {}
        for feature_row in feature_rows:
            vendor = str(feature_row.get("vendor", "")).strip() or "UNKNOWN_VENDOR"
            grouped_feature_rows.setdefault(vendor, []).append(feature_row)

        workbook.remove(sheet)
        used_sheet_names: set[str] = set()
        for vendor in sorted(grouped_rows.keys(), key=lambda item: item.lower()):
            worksheet_name = self._to_unique_sheet_name(vendor=vendor, used=used_sheet_names)
            used_sheet_names.add(worksheet_name)
            worksheet = workbook.create_sheet(title=worksheet_name)
            vendor_features = grouped_feature_rows.get(vendor, [])
            feature_header_mapping = [
                ("feature_name", "feature_name"),
                ("feature_expires_on", "expires_on"),
                ("feature_quantity", "quantity"),
            ]
            feature_headers = [name for name, _ in feature_header_mapping]
            worksheet.append(headers + feature_headers)

            vendor_rows = sorted(
                grouped_rows[vendor], key=lambda item: str(item.get("record_id", ""))
            )
            vendor_features = sorted(
                vendor_features,
                key=lambda item: (
                    str(item.get("server_name", "")),
                    str(item.get("feature_name", "")),
                    str(item.get("expires_on", "")),
                ),
            )
            row_count = max(len(vendor_rows), len(vendor_features))
            for idx in range(row_count):
                left_values = (
                    [vendor_rows[idx].get(key, "") for key in headers]
                    if idx < len(vendor_rows)
                    else [""] * len(headers)
                )
                right_values = (
                    [
                        vendor_features[idx].get(source_key, "")
                        for _, source_key in feature_header_mapping
                    ]
                    if idx < len(vendor_features)
                    else [""] * len(feature_headers)
                )
                worksheet.append(left_values + right_values)

            # Fill down stable columns to improve readability when one side has more rows.
            stable_cols = list(range(1, len(headers) + 1))
            for col in stable_cols:
                for row_idx in range(3, worksheet.max_row + 1):
                    current = worksheet.cell(row=row_idx, column=col).value
                    previous = worksheet.cell(row=row_idx - 1, column=col).value
                    if (current is None or str(current).strip() == "") and previous not in (
                        None,
                        "",
                    ):
                        worksheet.cell(row=row_idx, column=col, value=previous)

            # Apply Arial font and auto-fit widths for all populated columns.
            arial_font = font_cls(name="Arial")
            left_align = alignment_cls(horizontal="left", vertical="center")
            max_width_by_col: dict[int, int] = {}
            for row in worksheet.iter_rows(
                min_row=1,
                max_row=worksheet.max_row,
                min_col=1,
                max_col=worksheet.max_column,
            ):
                for cell in row:
                    cell.font = arial_font
                    cell.alignment = left_align
                    text = "" if cell.value is None else str(cell.value)
                    max_width_by_col[cell.column] = max(
                        max_width_by_col.get(cell.column, 0), len(text)
                    )

            for col, width in max_width_by_col.items():
                worksheet.column_dimensions[get_column_letter(col)].width = min(
                    max(10, width + 2), 60
                )

        workbook.save(file_path)

    def _collect_feature_rows(self, records: list[LicenseRecord]) -> list[dict[str, str | int]]:
        if self._feature_catalog_service is None:
            return []

        rows: list[dict[str, str | int]] = []
        for record in records:
            features = self._feature_catalog_service.list_for_record(record)
            for feature_name, expires_on, quantity in features:
                rows.append(
                    {
                        "record_id": record.record_id,
                        "server_name": record.server_name,
                        "provider": record.provider,
                        "vendor": record.vendor,
                        "license_file_path": record.license_file_path,
                        "feature_name": feature_name,
                        "expires_on": expires_on,
                        "quantity": int(quantity),
                    }
                )
        return rows

    def _to_unique_sheet_name(self, *, vendor: str, used: set[str]) -> str:
        sanitized = re.sub(r"[:\\/?*\[\]]", "_", vendor).strip()
        base = sanitized[:31] or "UNKNOWN_VENDOR"
        if base not in used:
            return base

        index = 2
        while True:
            suffix = f"_{index}"
            candidate = f"{base[: 31 - len(suffix)]}{suffix}"
            if candidate not in used:
                return candidate
            index += 1
