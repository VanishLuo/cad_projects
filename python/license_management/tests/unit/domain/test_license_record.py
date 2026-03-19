from __future__ import annotations

from datetime import date

from license_management.domain.models.license_record import LicenseRecord


def test_license_record_expired_true_when_expires_before_today() -> None:
    record = LicenseRecord(
        record_id="r1",
        server_name="srv-a",
        provider="FlexNet",
        feature_name="f1",
        process_name="lmgrd",
        expires_on=date(2026, 3, 17),
    )

    assert record.is_expired(date(2026, 3, 18))


def test_license_record_expired_false_when_expires_today() -> None:
    record = LicenseRecord(
        record_id="r2",
        server_name="srv-a",
        provider="FlexNet",
        feature_name="f2",
        process_name="lmgrd",
        expires_on=date(2026, 3, 18),
    )

    assert not record.is_expired(date(2026, 3, 18))
