from __future__ import annotations

from dataclasses import dataclass
from datetime import date

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
        "record_id",
        "server_name",
        "provider",
        "feature_name",
        "process_name",
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

    return ValidationResult(is_valid=not issues, issues=tuple(issues))


def to_license_record(payload: dict[str, str]) -> LicenseRecord:
    return LicenseRecord(
        record_id=payload["record_id"].strip(),
        server_name=payload["server_name"].strip(),
        provider=payload["provider"].strip(),
        feature_name=payload["feature_name"].strip(),
        process_name=payload["process_name"].strip(),
        expires_on=date.fromisoformat(payload["expires_on"].strip()),
    )
