from __future__ import annotations

from datetime import date

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.feature_search import FeatureSearchController
from license_management.gui.state.view_model import MainListViewModel


def _record(record_id: str, feature_name: str, server_name: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name=server_name,
        provider="FlexNet",
        prot="27000",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
    )


def test_feature_search_supports_keyword_and_reset() -> None:
    vm = MainListViewModel()
    vm.load(
        [
            _record("code-a-001", "ANSYS-MECH", "prod-a"),
            _record("code-b-002", "ANSYS-CFD", "prod-a"),
            _record("code-c-003", "MATLAB", "dev-a"),
        ],
        today=date(2026, 5, 1),
    )

    controller = FeatureSearchController(vm)
    result = controller.search(
        today=date(2026, 5, 1),
        keyword="code-a-001",
        server_name="prod",
    )

    assert [row.record_id for row in result.rows] == ["code-a-001"]

    reset = controller.reset(today=date(2026, 5, 1))
    assert len(reset.rows) == 3

