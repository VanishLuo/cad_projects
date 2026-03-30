from __future__ import annotations

from datetime import date
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.state.view_model import MainListViewModel, SearchFilters


def _record(
    *,
    record_id: str,
    server_name: str,
    feature_name: str,
    expires_on: date,
    provider: str = "FlexNet",
) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name=server_name,
        provider=provider,
        prot="27000",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=expires_on,
    )


def test_load_assigns_status_and_highlight_levels() -> None:
    vm = MainListViewModel(warning_days=30)
    rows = vm.load(
        [
            _record(
                record_id="r-expired",
                server_name="srv-a",
                feature_name="F1",
                expires_on=date(2026, 4, 30),
            ),
            _record(
                record_id="r-soon",
                server_name="srv-a",
                feature_name="F2",
                expires_on=date(2026, 5, 15),
            ),
            _record(
                record_id="r-active",
                server_name="srv-b",
                feature_name="F3",
                expires_on=date(2026, 7, 1),
            ),
        ],
        today=date(2026, 5, 1),
    )

    by_id = {row.record_id: row for row in rows}
    assert by_id["r-expired"].status == "unknown"
    assert by_id["r-expired"].highlight_level == "normal"
    assert by_id["r-soon"].status == "unknown"
    assert by_id["r-soon"].highlight_level == "normal"
    assert by_id["r-active"].status == "unknown"
    assert by_id["r-active"].highlight_level == "normal"


def test_search_and_filter_supports_combined_strict_filters() -> None:
    vm = MainListViewModel(warning_days=30)
    vm.load(
        [
            _record(
                record_id="lic-001",
                server_name="prod-a",
                feature_name="ANSYS-MECH",
                expires_on=date(2026, 6, 1),
            ),
            _record(
                record_id="lic-002",
                server_name="prod-a",
                feature_name="ANSYS-CFD",
                expires_on=date(2026, 6, 1),
            ),
            _record(
                record_id="lic-100",
                server_name="dev-a",
                feature_name="MATLAB",
                expires_on=date(2026, 6, 1),
            ),
        ],
        today=date(2026, 5, 1),
    )

    rows = vm.search_and_filter(
        filters=SearchFilters(
            server_name="prod",
            keyword="lic-001",
        ),
        today=date(2026, 5, 1),
    )

    assert [row.record_id for row in rows] == ["lic-001"]
    assert rows[0].matched_terms == ("lic-001",)


def test_reset_filters_restores_full_result_set() -> None:
    vm = MainListViewModel(warning_days=30)
    vm.load(
        [
            _record(
                record_id="r1",
                server_name="srv-a",
                feature_name="F1",
                expires_on=date(2026, 6, 1),
            ),
            _record(
                record_id="r2",
                server_name="srv-b",
                feature_name="F2",
                expires_on=date(2026, 6, 1),
            ),
        ],
        today=date(2026, 5, 1),
    )

    vm.search_and_filter(filters=SearchFilters(server_name="srv-a"), today=date(2026, 5, 1))
    assert len(vm.rows) == 1

    rows = vm.reset_filters(today=date(2026, 5, 1))
    assert len(rows) == 2


def test_runtime_status_override_controls_status_and_highlight() -> None:
    vm = MainListViewModel(warning_days=30)
    rows = vm.load(
        [
            LicenseRecord(
                record_id="r-1",
                server_name="srv-a",
                provider="FlexNet",
                prot="27000",
                feature_name="F1",
                process_name="lmgrd",
                expires_on=date(2027, 1, 1),
                license_file_path="/opt/demo/license.dat",
            )
        ],
        today=date(2026, 5, 1),
    )

    assert len(rows) == 1
    assert rows[0].status == "unknown"
    assert rows[0].highlight_level == "normal"

    vm.set_runtime_statuses({"r-1": "active"})
    rows = vm.search_and_filter(filters=SearchFilters(), today=date(2026, 5, 1))

    assert len(rows) == 1
    assert rows[0].status == "active"
    assert rows[0].highlight_level == "success"

    vm.set_runtime_statuses({"r-1": "expired"})
    rows = vm.search_and_filter(filters=SearchFilters(), today=date(2026, 5, 1))

    assert len(rows) == 1
    assert rows[0].status == "expired"
    assert rows[0].highlight_level == "danger"
