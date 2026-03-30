from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from license_management.domain.models.license_record import LicenseRecord


class ExpirationStatus(StrEnum):
    UNKNOWN = "unknown"
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    LICENSE_NOT_FOUND = "license_not_found"


@dataclass(slots=True)
class ExpirationState:
    record_id: str
    days_to_expire: int
    status: ExpirationStatus


class ExpirationStateEngine:
    """Computes reminder state for license records (T5.3)."""

    def __init__(self, *, warning_days: int = 30) -> None:
        self._warning_days = warning_days

    def evaluate(self, record: LicenseRecord, *, today: date) -> ExpirationState:
        days_to_expire = (record.expires_on - today).days

        if days_to_expire < 0:
            status = ExpirationStatus.EXPIRED
        elif days_to_expire <= self._warning_days:
            status = ExpirationStatus.EXPIRING_SOON
        else:
            status = ExpirationStatus.ACTIVE

        return ExpirationState(
            record_id=record.record_id,
            days_to_expire=days_to_expire,
            status=status,
        )
