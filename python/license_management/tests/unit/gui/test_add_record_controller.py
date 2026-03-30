from __future__ import annotations

from datetime import date

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.controllers.add_record_controller import AddRecordController


def _record(record_id: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv",
        provider="FlexNet",
        prot="27000",
        feature_name="feat",
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
        vendor="ansys",
        start_executable_path="/opt/lmgrd",
        license_file_path="/opt/license.dat",
    )


def test_prepare_add_payload_assigns_next_numeric_id() -> None:
    controller = AddRecordController()
    result = controller.prepare_add_payload(
        payload={
            "server_name": "srv",
            "provider": "FlexNet",
            "prot": "27000",
            "feature_name": "feat",
            "process_name": "lmgrd",
            "expires_on": "2026-06-01",
            "vendor": "ansys",
            "start_executable_path": "/opt/lmgrd",
            "license_file_path": "/opt/license.dat",
            "start_option_override": "",
        },
        existing_records=[_record("1"), _record("2"), _record("9")],
    )

    assert result.ok is True
    assert result.payload["record_id"] == "10"


def test_prepare_add_payload_returns_validation_error() -> None:
    controller = AddRecordController()
    result = controller.prepare_add_payload(
        payload={
            "server_name": "",
            "provider": "",
            "prot": "",
            "feature_name": "",
            "process_name": "",
            "expires_on": "bad-date",
            "vendor": "",
            "start_executable_path": "",
            "license_file_path": "",
            "start_option_override": "",
        },
        existing_records=[],
    )

    assert result.ok is False
    assert result.error_detail != ""

