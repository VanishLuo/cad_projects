from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.feature_search import FeatureSearchController
from license_management.gui.view_model import MainListViewModel


def _record(
    record_id: str,
    server_name: str,
    feature_name: str,
    provider: str,
    expires_on: date,
) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name=server_name,
        provider=provider,
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=expires_on,
    )


@pytest.mark.parametrize(
    ("search_kwargs", "expected_ids"),
    [
        ({"feature_name": "ANSYS"}, ["rec-001", "rec-002"]),
        ({"keyword": "CFD"}, ["rec-002"]),
        ({"provider": "FlexNet", "server_name": "prod"}, ["rec-001", "rec-002"]),
        ({"status": "expired"}, ["rec-004"]),
        ({"expires_before": date(2026, 5, 5)}, ["rec-004"]),
    ],
)
def test_e2e_search_filter_matrix(search_kwargs: dict[str, Any], expected_ids: list[str]) -> None:
    vm = MainListViewModel(warning_days=30)
    vm.load(
        [
            _record("rec-001", "prod-a", "ANSYS-MECH", "FlexNet", date(2026, 6, 1)),
            _record("rec-002", "prod-b", "ANSYS-CFD", "FlexNet", date(2026, 6, 10)),
            _record("rec-003", "dev-a", "MATLAB", "MathWorks", date(2026, 6, 15)),
            _record("rec-004", "qa-a", "LEGACY", "FlexNet", date(2026, 4, 30)),
        ],
        today=date(2026, 5, 1),
    )

    result = FeatureSearchController(vm).search(today=date(2026, 5, 1), **search_kwargs)
    found_ids = sorted(row.record_id for row in result.rows)
    assert found_ids == sorted(expected_ids)
