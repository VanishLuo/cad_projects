from __future__ import annotations

from typing import Any, Protocol

from license_management.domain.expiration_engine import ExpirationStatus
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.state.models import UiLicenseRow
from license_management.gui.qt_compat import QColor, QTableWidget, QTableWidgetItem, Qt


class TableRecordRepositoryProtocol(Protocol):
    def get(self, record_id: str) -> LicenseRecord | None: ...


class MainWindowTableHelper:
    """Own table row rendering plus selected record resolution."""

    def __init__(
        self,
        *,
        table: QTableWidget,
        table_columns: tuple[str, ...],
        editable_columns: set[str],
        repository: TableRecordRepositoryProtocol,
    ) -> None:
        self._table = table
        self._table_columns = table_columns
        self._editable_columns = editable_columns
        self._repository = repository

    def selected_record(self) -> LicenseRecord | None:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return None

        indexes = selection_model.selectedRows()
        if not indexes:
            return None
        if "record_id" not in self._table_columns:
            return None

        id_col = self._table_columns.index("record_id")
        item = self._table.item(indexes[0].row(), id_col)
        if item is None:
            return None

        return self._repository.get(item.text())

    def selected_records(self) -> list[LicenseRecord]:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return []
        if "record_id" not in self._table_columns:
            return []

        id_col = self._table_columns.index("record_id")
        records: list[LicenseRecord] = []
        seen_ids: set[str] = set()
        for idx in selection_model.selectedRows():
            item = self._table.item(idx.row(), id_col)
            if item is None:
                continue
            record_id = item.text().strip()
            if record_id == "" or record_id in seen_ids:
                continue
            seen_ids.add(record_id)
            record = self._repository.get(record_id)
            if record is not None:
                records.append(record)
        return records

    def render_rows(self, rows: tuple[UiLicenseRow, ...]) -> None:
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [str(getattr(row, column, "")) for column in self._table_columns]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                column_name = self._table_columns[col_index]
                if column_name not in self._editable_columns:
                    item.setFlags(item.flags() & ~_qt_enum_member(Qt, "ItemFlag", "ItemIsEditable"))
                if column_name == "status":
                    if value == ExpirationStatus.ACTIVE.value:
                        item.setForeground(QColor("#1b5e20"))
                    elif value == ExpirationStatus.EXPIRED.value:
                        item.setForeground(QColor("#b00020"))
                    elif value == ExpirationStatus.UNKNOWN.value:
                        item.setForeground(QColor("#666666"))
                self._table.setItem(row_index, col_index, item)


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)
