from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from license_management.domain.models.license_record import LicenseRecord
from license_management.domain.ports.license_repository import LicenseRepository


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

    def __init__(self, repository: LicenseRepository) -> None:
        self._repository = repository

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
        raw = json.loads(file_path.read_text(encoding="utf-8"))

        if isinstance(raw, dict) and all(isinstance(k, str) for k in raw):
            return [raw]
        if isinstance(raw, list):
            payloads: list[dict[str, object]] = []
            for item in raw:
                if not (isinstance(item, dict) and all(isinstance(k, str) for k in item)):
                    raise ValueError("list items must be JSON objects")
                payloads.append(item)
            return payloads
        raise ValueError("JSON payload must be an object or array")

    def _persist_records(
        self, payloads: list[dict[str, object]], *, source_label: str
    ) -> ImportReport:
        succeeded = 0
        deduplicated = 0
        invalid = 0
        warnings: list[str] = []
        errors: list[str] = []
        seen_ids: set[str] = set()

        for payload in payloads:
            try:
                record = self._build_record(payload)

                if (
                    record.record_id in seen_ids
                    or self._repository.get(record.record_id) is not None
                ):
                    deduplicated += 1
                    warnings.append(
                        f"{source_label}: duplicate record_id skipped ({record.record_id})"
                    )
                    continue

                seen_ids.add(record.record_id)
                self._repository.upsert(record)
                succeeded += 1
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

    def _build_record(self, payload: dict[str, object]) -> LicenseRecord:
        required = (
            "record_id",
            "server_name",
            "provider",
            "feature_name",
            "process_name",
            "expires_on",
        )
        for key in required:
            value = payload.get(key)
            if not isinstance(value, str) or value.strip() == "":
                raise ValueError(f"{key} must be a non-empty string")

        return LicenseRecord(
            record_id=str(payload["record_id"]),
            server_name=str(payload["server_name"]),
            provider=str(payload["provider"]),
            feature_name=str(payload["feature_name"]),
            process_name=str(payload["process_name"]),
            expires_on=date.fromisoformat(str(payload["expires_on"])),
        )
