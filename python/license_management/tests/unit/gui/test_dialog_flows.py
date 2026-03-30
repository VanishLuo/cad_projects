from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.application.compare_service import CrossTargetCompareService
from license_management.application.import_pipeline import ImportPipelineService
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.flows.dialog_flows import DialogFlowBinder
from license_management.gui.state.models import FeedbackCenter
from license_management.infrastructure.repositories.in_memory_license_repository import (
    InMemoryLicenseRepository,
)


class StubSshExecutor:
    def __init__(self, exit_code: int = 0) -> None:
        self._exit_code = exit_code

    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        if self._exit_code == 0:
            return 0, "ok", ""
        return 1, "", "failed"


class StubFeatureCatalogService:
    def __init__(self, data_by_record_id: dict[str, list[tuple[str, str, int]]]) -> None:
        self._data_by_record_id = data_by_record_id

    def list_for_record(self, record: LicenseRecord) -> list[tuple[str, str, int]]:
        return self._data_by_record_id.get(record.record_id, [])


def _record(record_id: str, feature_name: str, expires_on: date) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv-a",
        provider="FlexNet",
        prot="27000",
        feature_name=feature_name,
        process_name="lmgrd",
        expires_on=expires_on,
    )


def test_add_or_edit_returns_validation_error() -> None:
    binder = DialogFlowBinder(
        repository=InMemoryLicenseRepository(),
        feedback_center=FeedbackCenter(),
    )

    result = binder.add_or_edit({"record_id": ""})

    assert result.success is False
    assert result.feedback.level == "error"


def test_add_or_edit_import_start_stop_compare_export_flow(tmp_path: Path) -> None:
    repository = InMemoryLicenseRepository()
    feedback = FeedbackCenter()
    import_service = ImportPipelineService(repository)
    adapter = FlexNetAdapter(StubSshExecutor(), retry_times=0)
    compare_service = CrossTargetCompareService()

    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
        import_service=import_service,
        flexnet_adapter=adapter,
        compare_service=compare_service,
    )

    add_result = binder.add_or_edit(
        {
            "record_id": "r1",
            "server_name": "srv-a",
            "provider": "FlexNet",
            "prot": "27000",
            "feature_name": "ANSYS-MECH",
            "process_name": "lmgrd",
            "expires_on": "2026-12-31",
        }
    )
    assert add_result.success is True

    import_file = tmp_path / "import.json"
    import_file.write_text(
        json.dumps(
            {
                "record_id": "r2",
                "server_name": "srv-b",
                "provider": "FlexNet",
                "prot": "27000",
                "feature_name": "ANSYS-CFD",
                "process_name": "lmgrd",
                "expires_on": "2026-12-01",
            }
        ),
        encoding="utf-8",
    )

    import_result, import_report = binder.import_files([import_file])
    assert import_result.success is True
    assert import_report is not None
    assert import_report.succeeded == 1

    start_result = binder.start_stop(action="start", host="srv-a", username="ops")
    assert start_result.success is True

    compare_result, compare_report = binder.compare(
        left_target="left",
        left_records=[_record("r1", "ANSYS-MECH", date(2026, 12, 31))],
        right_target="right",
        right_records=[_record("r1", "ANSYS-MECH", date(2027, 1, 1))],
    )
    assert compare_result.success is True
    assert compare_report is not None
    assert compare_report.has_differences is True

    export_file = tmp_path / "export.json"
    export_result = binder.export_records(file_path=export_file, records=repository.list_all())
    assert export_result.success is True
    assert export_file.exists()


def test_export_excel_groups_records_by_vendor_sheet(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    repository = InMemoryLicenseRepository()
    feedback = FeedbackCenter()
    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
    )

    repository.upsert(
        LicenseRecord(
            record_id="r-001",
            server_name="srv-a",
            provider="FlexNet",
            prot="27000",
            vendor="ANSYS",
            feature_name="ANSYS-MECH",
            process_name="lmgrd",
            expires_on=date(2026, 12, 31),
        )
    )
    repository.upsert(
        LicenseRecord(
            record_id="r-002",
            server_name="srv-b",
            provider="FlexNet",
            prot="27000",
            vendor="ANSYS",
            feature_name="ANSYS-CFD",
            process_name="lmgrd",
            expires_on=date(2026, 12, 1),
        )
    )
    repository.upsert(
        LicenseRecord(
            record_id="r-003",
            server_name="srv-c",
            provider="FlexNet",
            prot="27000",
            vendor="SIEMENS",
            feature_name="NX",
            process_name="lmgrd",
            expires_on=date(2026, 11, 1),
        )
    )

    export_file = tmp_path / "export.xlsx"
    export_result = binder.export_records(file_path=export_file, records=repository.list_all())
    assert export_result.success is True
    assert export_file.exists()

    workbook = openpyxl.load_workbook(export_file)
    try:
        assert set(workbook.sheetnames) == {"ANSYS", "SIEMENS"}

        ansys_sheet = workbook["ANSYS"]
        siemens_sheet = workbook["SIEMENS"]

        ansys_headers = [cell.value for cell in ansys_sheet[1]]
        assert "record_id" not in ansys_headers
        assert "vendor" in ansys_headers
        vendor_col = ansys_headers.index("vendor") + 1

        ansys_vendors = {
            ansys_sheet.cell(row=row, column=vendor_col).value
            for row in range(2, ansys_sheet.max_row + 1)
        }
        siemens_vendors = {
            siemens_sheet.cell(row=row, column=vendor_col).value
            for row in range(2, siemens_sheet.max_row + 1)
        }

        assert ansys_vendors == {"ANSYS"}
        assert siemens_vendors == {"SIEMENS"}
    finally:
        workbook.close()


def test_export_includes_feature_details_for_excel_and_json(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    repository = InMemoryLicenseRepository()
    feedback = FeedbackCenter()
    feature_catalog = StubFeatureCatalogService(
        {
            "r-001": [("ANSYS-MECH", "2026-12-31", 5), ("ANSYS-CFD", "2026-12-01", 2)],
            "r-002": [("NX", "2026-10-01", 1)],
        }
    )
    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
        feature_catalog_service=feature_catalog,  # type: ignore[arg-type]
    )

    repository.upsert(
        LicenseRecord(
            record_id="r-001",
            server_name="srv-a",
            provider="FlexNet",
            prot="27000",
            vendor="ANSYS",
            feature_name="ANSYS-MECH",
            process_name="lmgrd",
            expires_on=date(2026, 12, 31),
            license_file_path="/licenses/ansys.lic",
        )
    )
    repository.upsert(
        LicenseRecord(
            record_id="r-002",
            server_name="srv-b",
            provider="FlexNet",
            prot="27000",
            vendor="SIEMENS",
            feature_name="NX",
            process_name="lmgrd",
            expires_on=date(2026, 10, 1),
            license_file_path="/licenses/siemens.lic",
        )
    )

    export_excel = tmp_path / "export_with_features.xlsx"
    result_excel = binder.export_records(file_path=export_excel, records=repository.list_all())
    assert result_excel.success is True

    workbook = openpyxl.load_workbook(export_excel)
    try:
        assert set(workbook.sheetnames) == {"ANSYS", "SIEMENS"}

        ansys_sheet = workbook["ANSYS"]
        top_headers = [cell.value for cell in ansys_sheet[1]]
        assert "record_id" not in top_headers
        assert None not in top_headers
        first_feature_index = top_headers.index("feature_name")
        left_headers = top_headers[:first_feature_index]
        right_headers = top_headers[first_feature_index:]
        assert "vendor" in left_headers
        assert right_headers == [
            "feature_name",
            "feature_expires_on",
            "feature_quantity",
        ]

        left_vendor_col = left_headers.index("vendor") + 1
        assert ansys_sheet.cell(row=2, column=left_vendor_col).value == "ANSYS"
        assert ansys_sheet.cell(row=3, column=left_vendor_col).value == "ANSYS"
        right_feature_name_col = len(left_headers) + right_headers.index("feature_name") + 1
        assert ansys_sheet.cell(row=2, column=right_feature_name_col).value in {
            "ANSYS-MECH",
            "ANSYS-CFD",
        }
        assert ansys_sheet.cell(row=3, column=right_feature_name_col).value in {
            "ANSYS-MECH",
            "ANSYS-CFD",
        }
        assert ansys_sheet.cell(row=1, column=1).font.name == "Arial"
        assert ansys_sheet.cell(row=2, column=1).alignment.horizontal == "left"
        assert (ansys_sheet.column_dimensions["A"].width or 0) > 0
    finally:
        workbook.close()

    export_json = tmp_path / "export_with_features.json"
    result_json = binder.export_records(file_path=export_json, records=repository.list_all())
    assert result_json.success is True
    payload = json.loads(export_json.read_text(encoding="utf-8"))

    by_id = {item["record_id"]: item for item in payload}
    assert len(by_id["r-001"]["features"]) == 2
    assert by_id["r-001"]["features"][0]["feature_name"] in {"ANSYS-MECH", "ANSYS-CFD"}
    assert len(by_id["r-002"]["features"]) == 1

