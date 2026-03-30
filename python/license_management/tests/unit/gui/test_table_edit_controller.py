from __future__ import annotations

from datetime import date

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.controllers.table_edit_controller import TableEditController


def _record() -> LicenseRecord:
    return LicenseRecord(
        record_id="r1",
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


def test_apply_returns_invalid_for_empty_required_field() -> None:
    controller = TableEditController()
    decision = controller.apply(record=_record(), column_name="server_name", value="")

    assert decision.action == "invalid"
    assert "cannot be empty" in decision.log_message


def test_apply_returns_invalid_for_bad_date() -> None:
    controller = TableEditController()
    decision = controller.apply(record=_record(), column_name="expires_on", value="2026/01/01")

    assert decision.action == "invalid"
    assert "invalid date format" in decision.user_feedback


def test_apply_returns_updated_record() -> None:
    controller = TableEditController()
    decision = controller.apply(record=_record(), column_name="vendor", value="synopsys")

    assert decision.action == "updated"
    assert decision.updated_record is not None
    assert decision.updated_record.vendor == "synopsys"
