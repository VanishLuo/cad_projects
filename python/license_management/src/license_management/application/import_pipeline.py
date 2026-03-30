from __future__ import annotations

import json
import importlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import cast

from license_management.domain.models.license_record import LicenseRecord
from license_management.domain.ports.license_repository import LicenseRepository
from license_management.infrastructure.config.table_header_config import load_table_header_config
from license_management.application.license_feature_catalog import LicenseFeatureCatalogService
from license_management.shared.path_normalization import normalize_local_path_text


@dataclass(slots=True)
class ImportReport:
    total: int
    succeeded: int
    failed: int
    deduplicated: int
    invalid: int
    errors: list[str]
    warnings: list[str]


class ImportPipelineService:
    """Implements T5.1/T5.2 import pipelines with validation and deduplication."""

    def __init__(
        self,
        repository: LicenseRepository,
        feature_catalog_service: LicenseFeatureCatalogService | None = None,
    ) -> None:
        self._repository = repository
        self._feature_catalog_service = feature_catalog_service
        self._cfg = load_table_header_config()
        self._json_controlled_fields = set(self._cfg.sqlite_columns.keys())
        self._field_whitelist = set(self._cfg.field_whitelist)
        self._header_aliases = self._build_header_aliases()

    def import_single_file(self, file_path: Path) -> ImportReport:
        records = self._load_records(file_path)
        return self._persist_records(records, source_label=str(file_path))

    def import_batch_files(self, file_paths: list[Path]) -> ImportReport:
        all_records: list[dict[str, object]] = []
        errors: list[str] = []

        for file_path in file_paths:
            try:
                all_records.extend(self._load_records(file_path))
            except ValueError as exc:
                errors.append(f"{file_path}: {exc}")

        report = self._persist_records(all_records, source_label="batch")
        report.errors.extend(errors)
        report.failed += len(errors)
        report.invalid += len(errors)
        report.total += len(errors)
        return report

    def _load_records(self, file_path: Path) -> list[dict[str, object]]:
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            return self._load_json_records(file_path)
        if suffix in {".xlsx", ".xlsm"}:
            return self._load_excel_records(file_path)
        raise ValueError(f"unsupported import format: {file_path.suffix}")

    def _load_json_records(self, file_path: Path) -> list[dict[str, object]]:
        raw: object = json.loads(file_path.read_text(encoding="utf-8"))

        if isinstance(raw, dict):
            typed = cast(dict[object, object], raw)
            payload = {str(key): value for key, value in typed.items()}
            return [self._normalize_payload_keys(payload)]
        if isinstance(raw, list):
            raw_list = cast(list[object], raw)
            payloads: list[dict[str, object]] = []
            for item in raw_list:
                if not isinstance(item, dict):
                    raise ValueError("list items must be JSON objects")
                typed = cast(dict[object, object], item)
                payload = {str(key): value for key, value in typed.items()}
                payloads.append(self._normalize_payload_keys(payload))
            return payloads
        raise ValueError("JSON payload must be an object or array")

    def _load_excel_records(self, file_path: Path) -> list[dict[str, object]]:
        try:
            openpyxl = importlib.import_module("openpyxl")
            load_workbook = getattr(openpyxl, "load_workbook")
        except ImportError as exc:
            raise ValueError("openpyxl is required for Excel import") from exc

        workbook = load_workbook(file_path, read_only=True, data_only=True)
        sheet = workbook.active
        if sheet is None:
            return []
        rows = sheet.iter_rows(values_only=True)

        try:
            header_row = next(rows)
        except StopIteration:
            return []

        headers = [str(cell).strip() if cell is not None else "" for cell in header_row]
        if not any(headers):
            return []

        payloads: list[dict[str, object]] = []
        for row in rows:
            payload: dict[str, object] = {}
            has_value = False
            for index, cell in enumerate(row):
                if index >= len(headers):
                    continue
                raw_key = headers[index]
                key = self._resolve_header(raw_key)
                if not key:
                    continue
                if cell is not None and str(cell).strip() != "":
                    has_value = True
                payload[key] = "" if cell is None else str(cell)
            if has_value:
                payloads.append(payload)

        return payloads

    def _persist_records(
        self, payloads: list[dict[str, object]], *, source_label: str
    ) -> ImportReport:
        succeeded = 0
        deduplicated = 0
        invalid = 0
        warnings: list[str] = []
        errors: list[str] = []
        existing_records = self._repository.list_all()
        seen_ids: set[str] = {item.record_id for item in existing_records}
        seen_business_keys: set[tuple[str, ...]] = {
            self._build_business_key(item) for item in existing_records
        }
        next_auto_id = self._next_auto_record_id(existing_records)

        for payload in payloads:
            try:
                record_id = self._resolve_record_id(payload, next_auto_id)
                parsed_id = self._parse_positive_int(record_id)
                if parsed_id is None:
                    next_auto_id += 1
                else:
                    next_auto_id = max(next_auto_id, parsed_id + 1)

                record = self._build_record(payload, record_id=record_id)
                display_path = normalize_local_path_text(record.license_file_path)
                business_key = self._build_business_key(record)

                if record.record_id in seen_ids:
                    deduplicated += 1
                    warnings.append(
                        f"{source_label}: duplicate record_id skipped "
                        f"(server={record.server_name}, provider={record.provider}, "
                        f"license={display_path or record.license_file_path})"
                    )
                    continue

                if self._has_business_identity(record) and business_key in seen_business_keys:
                    deduplicated += 1
                    warnings.append(
                        f"{source_label}: duplicate business row skipped "
                        f"(server={record.server_name}, provider={record.provider}, "
                        f"license={display_path or record.license_file_path})"
                    )
                    continue

                seen_ids.add(record.record_id)
                seen_business_keys.add(business_key)
                self._repository.upsert(record)
                succeeded += 1

                if self._feature_catalog_service is not None:
                    sync = self._feature_catalog_service.sync_from_record(record)
                    if sync.license_missing:
                        warnings.append(
                            f"{source_label}: license file not found, feature catalog skipped "
                            f"({display_path or record.license_file_path})"
                        )
            except (KeyError, ValueError) as exc:
                invalid += 1
                errors.append(f"{source_label}: invalid record payload ({exc})")

        total = len(payloads)
        failed = invalid
        return ImportReport(
            total=total,
            succeeded=succeeded,
            failed=failed,
            deduplicated=deduplicated,
            invalid=invalid,
            errors=errors,
            warnings=warnings,
        )

    def _build_record(self, payload: dict[str, object], *, record_id: str) -> LicenseRecord:
        required = self._cfg.sqlite_required_fields
        normalized: dict[str, str] = {}
        for key in required:
            value = payload.get(key)
            if value is None:
                if key == "prot":
                    raise ValueError("port/prot must be a non-empty string")
                raise ValueError(f"{key} must be a non-empty string")
            text = str(value).strip()
            if text == "":
                if key == "prot":
                    raise ValueError("port/prot must be a non-empty string")
                raise ValueError(f"{key} must be a non-empty string")
            normalized[key] = text

        return LicenseRecord(
            record_id=record_id,
            server_name=normalized["server_name"],
            provider=normalized["provider"],
            prot=normalized["prot"],
            feature_name="",
            process_name="",
            expires_on=date.today(),
            vendor=self._get_controlled_text(payload, "vendor"),
            start_executable_path=self._get_controlled_text(payload, "start_executable_path"),
            license_file_path=self._get_controlled_text(payload, "license_file_path"),
            start_option_override="",
        )

    def _build_header_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for internal_field, column_name in self._cfg.sqlite_columns.items():
            aliases[internal_field.strip().lower()] = internal_field
            aliases[column_name.strip().lower()] = internal_field

        # Accept GUI display headers in imported files.
        for key, label in self._cfg.gui_headers.items():
            aliases[key.strip().lower()] = key
            aliases[label.strip().lower()] = key

        # Backward-compatible alias used by users in spreadsheets.
        aliases["port"] = "prot"

        return aliases

    def _resolve_header(self, header: str) -> str:
        key = header.strip().lower()
        if not key:
            return ""
        return self._header_aliases.get(key, "")

    def _normalize_payload_keys(self, payload: dict[str, object]) -> dict[str, object]:
        normalized: dict[str, object] = {}
        for key, value in payload.items():
            mapped = self._resolve_header(str(key))
            if not mapped:
                continue
            normalized[mapped] = value
        return normalized

    def _get_controlled_text(self, payload: dict[str, object], key: str) -> str:
        if key not in self._json_controlled_fields or key not in self._field_whitelist:
            return ""
        value = payload.get(key)
        if value is None:
            return ""
        return str(value).strip()

    def _resolve_record_id(self, payload: dict[str, object], next_auto_id: int) -> str:
        value = payload.get("record_id")
        if value is None:
            return str(next_auto_id)
        text = str(value).strip()
        return text or str(next_auto_id)

    def _next_auto_record_id(self, records: list[LicenseRecord]) -> int:
        max_id = 0
        for item in records:
            parsed = self._parse_positive_int(item.record_id)
            if parsed is None:
                continue
            max_id = max(max_id, parsed)
        return max_id + 1

    def _parse_positive_int(self, value: str) -> int | None:
        text = value.strip()
        if not text.isdigit():
            return None
        parsed = int(text)
        if parsed <= 0:
            return None
        return parsed

    def _build_business_key(self, record: LicenseRecord) -> tuple[str, ...]:
        return (
            record.server_name.strip().lower(),
            record.feature_name.strip().lower(),
            record.process_name.strip().lower(),
            record.expires_on.isoformat(),
            record.provider.strip().lower(),
            record.vendor.strip().lower(),
            record.prot.strip().lower(),
            record.start_executable_path.strip().lower(),
            record.license_file_path.strip().lower(),
            record.start_option_override.strip().lower(),
        )

    def _has_business_identity(self, record: LicenseRecord) -> bool:
        return any(
            (
                record.feature_name.strip(),
                record.process_name.strip(),
                record.start_executable_path.strip(),
                record.license_file_path.strip(),
            )
        )
