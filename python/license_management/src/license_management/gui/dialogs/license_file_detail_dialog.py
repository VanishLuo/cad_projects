from __future__ import annotations

from typing import Any

from license_management.gui.qt_compat import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)


class LicenseFileDetailDialog(QDialog):
    """Detail dialog for one license file path, grouped by feature and expiry."""

    def __init__(
        self,
        *,
        license_file_path: str,
        rows: list[tuple[str, str, int]],
        record_count: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("LicenseFileDetailDialog")
        self.setWindowTitle("License File Feature Summary")
        self.resize(760, 520)

        summary_text = (
            f"License File: {license_file_path}\n"
            f"Feature+Expiry groups: {len(rows)} | Records: {record_count}"
        )
        summary = QLabel(summary_text)
        summary.setWordWrap(True)

        table = QTableWidget(len(rows), 3)
        table.setHorizontalHeaderLabels(["Feature", "Expires On", "Count"])
        header = table.horizontalHeader()
        if header is not None:
            header_stretch = _qt_enum_member(QHeaderView, "ResizeMode", "Stretch")
            header_resize = _qt_enum_member(QHeaderView, "ResizeMode", "ResizeToContents")
            header.setSectionResizeMode(0, header_stretch)
            header.setSectionResizeMode(1, header_resize)
            header.setSectionResizeMode(2, header_resize)

        table.setEditTriggers(_qt_enum_member(QTableWidget, "EditTrigger", "NoEditTriggers"))
        table.setSelectionBehavior(_qt_enum_member(QTableWidget, "SelectionBehavior", "SelectRows"))

        for row_index, (feature_name, expires_on, count) in enumerate(rows):
            table.setItem(row_index, 0, QTableWidgetItem(feature_name))
            table.setItem(row_index, 1, QTableWidgetItem(expires_on))
            table.setItem(row_index, 2, QTableWidgetItem(str(count)))

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(summary)
        layout.addWidget(table)
        layout.addWidget(close_button)
        self.setLayout(layout)
