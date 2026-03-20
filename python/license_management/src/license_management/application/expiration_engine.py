from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from license_management.domain.models.license_record import LicenseRecord


@dataclass(slots=True)
class ExpirationState:
    record_id: str
    days_to_expire: int
    status: str


class ExpirationStateEngine:
    """Computes reminder state for license records (T5.3)."""

    def __init__(self, *, warning_days: int = 30) -> None:
        self._warning_days = warning_days

    def evaluate(self, record: LicenseRecord, *, today: date) -> ExpirationState:
        days_to_expire = (record.expires_on - today).days

        if days_to_expire < 0:
            status = "expired"
        elif days_to_expire <= self._warning_days:
            status = "expiring_soon"
        else:
            status = "active"

        return ExpirationState(
            record_id=record.record_id,
            days_to_expire=days_to_expire,
            status=status,
        )
