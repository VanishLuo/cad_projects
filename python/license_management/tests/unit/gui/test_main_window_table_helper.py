# mypy: ignore-errors
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportArgumentType=false
from __future__ import annotations

from datetime import date

from pytest import MonkeyPatch

import license_management.gui.composition.main_window_table_helper as mod
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.state.models import UiLicenseRow


class _Repo:
    def __init__(self) -> None:
        self._records = {
            "r1": LicenseRecord(
                record_id="r1",
                server_name="srv-a",
                provider="FlexNet",
                prot="27000",
                vendor="ansys",
                feature_name="f1",
                process_name="lmgrd",
                expires_on=date(2026, 6, 1),
                start_executable_path="/opt/lmgrd",
                license_file_path="/opt/license.dat",
            ),
            "r2": LicenseRecord(
                record_id="r2",
                server_name="srv-b",
                provider="FlexNet",
                prot="27001",
                vendor="synopsys",
                feature_name="f2",
                process_name="lmgrd",
                expires_on=date(2026, 6, 2),
                start_executable_path="/opt/lmgrd",
                license_file_path="/opt/license.dat",
            ),
        }

    def get(self, record_id: str) -> LicenseRecord | None:
        return self._records.get(record_id)


class _Item:
    def __init__(self, text: str) -> None:
        self._text = text
        self._flags = 1

    def text(self) -> str:
        return self._text

    def setFlags(self, value: int) -> None:
        self._flags = value

    def flags(self) -> int:
        return self._flags

    def setForeground(self, _value: object) -> None:
        return


class _Index:
    def __init__(self, row: int) -> None:
        self._row = row

    def row(self) -> int:
        return self._row


class _SelectionModel:
    def __init__(self, table: "_Table") -> None:
        self._table = table

    def selectedRows(self) -> list[_Index]:
        return [_Index(item) for item in self._table.selected_rows]


class _Table:
    def __init__(self, _rows: int, _cols: int) -> None:
        self.items: dict[tuple[int, int], _Item] = {}
        self.row_count = 0
        self.selected_rows: list[int] = []

    def setHorizontalHeaderLabels(self, _labels: list[str]) -> None:
        return

    def setRowCount(self, count: int) -> None:
        self.row_count = count

    def setItem(self, row: int, col: int, item: _Item) -> None:
        self.items[(row, col)] = item

    def item(self, row: int, col: int) -> _Item | None:
        return self.items.get((row, col))

    def selectionModel(self) -> _SelectionModel:
        return _SelectionModel(self)

    def selectRow(self, row: int) -> None:
        self.selected_rows.append(row)


def _fake_qcolor(_code: str) -> object:
    return object()


def _fake_qt_enum_member(*_args: object, **_kwargs: object) -> int:
    return 1


def test_render_rows_and_selection_resolution(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "QTableWidgetItem", _Item)
    monkeypatch.setattr(mod, "QColor", _fake_qcolor)
    monkeypatch.setattr(mod, "_qt_enum_member", _fake_qt_enum_member)

    table_columns = (
        "record_id",
        "server_name",
        "provider",
        "prot",
        "vendor",
        "feature_name",
        "process_name",
        "expires_on",
        "status",
        "highlight_level",
    )
    table = _Table(0, len(table_columns))
    table.setHorizontalHeaderLabels(list(table_columns))

    helper = mod.MainWindowTableHelper(
        table=table,
        table_columns=table_columns,
        editable_columns={"vendor"},
        repository=_Repo(),
    )

    helper.render_rows(
        (
            UiLicenseRow(
                record_id="r1",
                server_name="srv-a",
                provider="FlexNet",
                prot="27000",
                vendor="ansys",
                feature_name="f1",
                process_name="lmgrd",
                expires_on=date(2026, 6, 1),
                status="active",
                highlight_level="none",
            ),
            UiLicenseRow(
                record_id="r2",
                server_name="srv-b",
                provider="FlexNet",
                prot="27001",
                vendor="synopsys",
                feature_name="f2",
                process_name="lmgrd",
                expires_on=date(2026, 6, 2),
                status="expired",
                highlight_level="none",
            ),
        )
    )

    table.selectRow(0)
    selected = helper.selected_record()
    assert selected is not None
    assert selected.record_id == "r1"

    table.selectRow(1)
    selected_many = helper.selected_records()
    assert len(selected_many) >= 1
    assert selected_many[0].record_id in {"r1", "r2"}
