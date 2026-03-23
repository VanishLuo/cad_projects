from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from license_management.domain.models.license_record import LicenseRecord


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    field: str
    message: str
    hint: str


@dataclass(slots=True, frozen=True)
class ValidationResult:
    is_valid: bool
    issues: tuple[ValidationIssue, ...]


def validate_license_form(payload: dict[str, str]) -> ValidationResult:
    required_fields = (
        "server_name",
        "provider",
        "expires_on",
    )
    issues: list[ValidationIssue] = []

    for field in required_fields:
        value = payload.get(field, "").strip()
        if not value:
            issues.append(
                ValidationIssue(
                    field=field,
                    message=f"{field} is required",
                    hint="Provide a non-empty value.",
                )
            )

    expires_on = payload.get("expires_on", "").strip()
    if expires_on:
        try:
            date.fromisoformat(expires_on)
        except ValueError:
            issues.append(
                ValidationIssue(
                    field="expires_on",
                    message="expires_on must be ISO date (YYYY-MM-DD)",
                    hint="Use format like 2026-12-31.",
                )
            )

    executable_path = payload.get("start_executable_path", "").strip()
    license_file_path = payload.get("license_file_path", "").strip()
    if not executable_path or not license_file_path:
        issues.append(
            ValidationIssue(
                field="start_executable_path",
                message="start_executable_path and license_file_path are required",
                hint="Provide absolute executable path and license file path.",
            )
        )

    return ValidationResult(is_valid=not issues, issues=tuple(issues))


def to_license_record(payload: dict[str, str]) -> LicenseRecord:
    record_id = payload.get("record_id", "").strip() or uuid4().hex
    return LicenseRecord(
        record_id=record_id,
        server_name=payload["server_name"].strip(),
        provider=payload["provider"].strip(),
        prot=payload.get("prot", "").strip(),
        feature_name=payload.get("feature_name", "").strip(),
        process_name=payload.get("process_name", "").strip(),
        expires_on=date.fromisoformat(payload["expires_on"].strip()),
        vendor=payload.get("vendor", "").strip(),
        start_executable_path=payload.get("start_executable_path", "").strip(),
        license_file_path=payload.get("license_file_path", "").strip(),
        start_option_override=payload.get("start_option_override", "").strip(),
    )
