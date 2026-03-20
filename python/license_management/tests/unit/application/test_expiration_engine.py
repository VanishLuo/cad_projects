from __future__ import annotations

from datetime import date

from license_management.application.expiration_engine import ExpirationStateEngine
from license_management.domain.models.license_record import LicenseRecord


def _record(expires_on: date) -> LicenseRecord:
    return LicenseRecord(
        record_id="r1",
        server_name="srv-a",
        provider="FlexNet",
        feature_name="F1",
        process_name="lmgrd",
        expires_on=expires_on,
    )


def test_evaluate_returns_active_when_far_from_expiration() -> None:
    engine = ExpirationStateEngine(warning_days=30)
    state = engine.evaluate(_record(date(2026, 6, 30)), today=date(2026, 5, 1))

    assert state.status == "active"
    assert state.days_to_expire == 60


def test_evaluate_returns_expiring_soon_within_warning_window() -> None:
    engine = ExpirationStateEngine(warning_days=30)
    state = engine.evaluate(_record(date(2026, 5, 20)), today=date(2026, 5, 1))

    assert state.status == "expiring_soon"
    assert state.days_to_expire == 19


def test_evaluate_returns_expired_after_expiry_date() -> None:
    engine = ExpirationStateEngine(warning_days=30)
    state = engine.evaluate(_record(date(2026, 4, 30)), today=date(2026, 5, 1))

    assert state.status == "expired"
    assert state.days_to_expire == -1
