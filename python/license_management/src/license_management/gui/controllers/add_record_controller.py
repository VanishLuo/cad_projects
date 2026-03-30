from __future__ import annotations

from dataclasses import dataclass

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.validation_feedback import validate_license_form


@dataclass(slots=True, frozen=True)
class AddRecordPrepareResult:
    ok: bool
    payload: dict[str, str]
    error_detail: str = ""


class AddRecordController:
    """Prepare add payload with validation and deterministic staging record id assignment."""

    def prepare_add_payload(
        self,
        *,
        payload: dict[str, str],
        existing_records: list[LicenseRecord],
    ) -> AddRecordPrepareResult:
        validation = validate_license_form(payload)
        if not validation.is_valid:
            detail = "; ".join(issue.message for issue in validation.issues)
            return AddRecordPrepareResult(ok=False, payload=dict(payload), error_detail=detail)

        prepared = dict(payload)
        prepared["record_id"] = self._next_staging_record_id(existing_records)
        return AddRecordPrepareResult(ok=True, payload=prepared)

    def _next_staging_record_id(self, existing_records: list[LicenseRecord]) -> str:
        existing_ids = {record.record_id.strip() for record in existing_records}
        max_numeric_id = 0
        for record_id in existing_ids:
            parsed = self._parse_positive_int(record_id)
            if parsed is None:
                continue
            max_numeric_id = max(max_numeric_id, parsed)

        candidate = max_numeric_id + 1
        while str(candidate) in existing_ids:
            candidate += 1
        return str(candidate)

    def _parse_positive_int(self, value: str) -> int | None:
        text = value.strip()
        if not text.isdigit():
            return None
        parsed = int(text)
        if parsed <= 0:
            return None
        return parsed
