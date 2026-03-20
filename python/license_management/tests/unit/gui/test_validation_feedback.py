from __future__ import annotations

from license_management.gui.validation_feedback import to_license_record, validate_license_form


def test_validate_license_form_reports_missing_fields() -> None:
    result = validate_license_form(
        {
            "record_id": "",
            "server_name": "",
            "provider": "",
            "feature_name": "",
            "process_name": "",
            "expires_on": "",
        }
    )

    assert result.is_valid is False
    assert len(result.issues) == 6


def test_validate_license_form_reports_bad_date_format() -> None:
    result = validate_license_form(
        {
            "record_id": "r1",
            "server_name": "srv-a",
            "provider": "FlexNet",
            "feature_name": "F1",
            "process_name": "lmgrd",
            "expires_on": "2026/12/31",
        }
    )

    assert result.is_valid is False
    assert any(issue.field == "expires_on" for issue in result.issues)


def test_to_license_record_builds_domain_model() -> None:
    record = to_license_record(
        {
            "record_id": "r1",
            "server_name": "srv-a",
            "provider": "FlexNet",
            "feature_name": "F1",
            "process_name": "lmgrd",
            "expires_on": "2026-12-31",
        }
    )

    assert record.record_id == "r1"
    assert record.expires_on.isoformat() == "2026-12-31"
