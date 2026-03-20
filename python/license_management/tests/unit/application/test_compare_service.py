from __future__ import annotations

from datetime import date

from license_management.application.compare_service import (
    CrossTargetCompareService,
    TargetSnapshot,
)
from license_management.domain.models.license_record import LicenseRecord


def _record(
    *,
    record_id: str,
    server_name: str,
    provider: str,
    feature_name: str,
    process_name: str,
    expires_on: date,
) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name=server_name,
        provider=provider,
        feature_name=feature_name,
        process_name=process_name,
        expires_on=expires_on,
    )


def test_compare_returns_no_diff_for_same_snapshots() -> None:
    records = (
        _record(
            record_id="r1",
            server_name="srv-a",
            provider="FlexNet",
            feature_name="F1",
            process_name="lmgrd",
            expires_on=date(2026, 6, 1),
        ),
    )
    service = CrossTargetCompareService()

    report = service.compare(
        TargetSnapshot(target_name="left", records=records),
        TargetSnapshot(target_name="right", records=records),
    )

    assert report.has_differences is False
    assert report.issues == ()


def test_compare_reports_missing_and_expiration_mismatch() -> None:
    left = TargetSnapshot(
        target_name="left",
        records=(
            _record(
                record_id="r1",
                server_name="srv-a",
                provider="FlexNet",
                feature_name="F1",
                process_name="lmgrd",
                expires_on=date(2026, 6, 1),
            ),
            _record(
                record_id="r2",
                server_name="srv-a",
                provider="FlexNet",
                feature_name="F2",
                process_name="lmgrd",
                expires_on=date(2026, 6, 10),
            ),
        ),
    )
    right = TargetSnapshot(
        target_name="right",
        records=(
            _record(
                record_id="x1",
                server_name="srv-a",
                provider="FlexNet",
                feature_name="F1",
                process_name="lmgrd",
                expires_on=date(2026, 7, 1),
            ),
            _record(
                record_id="x3",
                server_name="srv-b",
                provider="FlexNet",
                feature_name="F3",
                process_name="lmgrd",
                expires_on=date(2026, 8, 1),
            ),
        ),
    )

    report = CrossTargetCompareService().compare(left, right)

    assert report.has_differences is True
    assert [issue.issue_type for issue in report.issues] == [
        "expiration_mismatch",
        "missing_in_right",
        "missing_in_left",
    ]


def test_compare_uses_latest_expiration_for_duplicate_compare_keys() -> None:
    left = TargetSnapshot(
        target_name="left",
        records=(
            _record(
                record_id="r-old",
                server_name="srv-a",
                provider="FlexNet",
                feature_name="F1",
                process_name="lmgrd",
                expires_on=date(2026, 6, 1),
            ),
            _record(
                record_id="r-new",
                server_name="srv-a",
                provider="FlexNet",
                feature_name="F1",
                process_name="lmgrd",
                expires_on=date(2026, 7, 1),
            ),
        ),
    )
    right = TargetSnapshot(
        target_name="right",
        records=(
            _record(
                record_id="x1",
                server_name="srv-a",
                provider="FlexNet",
                feature_name="F1",
                process_name="lmgrd",
                expires_on=date(2026, 7, 1),
            ),
        ),
    )

    report = CrossTargetCompareService().compare(left, right)

    assert report.has_differences is False
