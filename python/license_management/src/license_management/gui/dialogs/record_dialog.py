from __future__ import annotations

from pathlib import Path
from typing import Any

from license_management.gui.qt_compat import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
)
from license_management.infrastructure.config.table_header_config import load_table_header_config


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)


class RecordDialog(QDialog):
    """SQLite-header driven dialog for adding one record."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("RecordDialog")
        self.setWindowTitle("Add Record")
        self.setMinimumSize(560, 260)
        self.resize(760, 420)

        cfg = load_table_header_config()
        self._required_fields = set(cfg.sqlite_required_fields)
        self._fields: dict[str, QLineEdit] = {}

        form = QFormLayout()
        form.setLabelAlignment(
            _qt_enum_member(Qt, "AlignmentFlag", "AlignRight")
            | _qt_enum_member(Qt, "AlignmentFlag", "AlignVCenter")
        )

        for field in cfg.sqlite_columns.keys():
            editor = QLineEdit("")
            self._fields[field] = editor
            label_text = cfg.gui_headers.get(field, field)
            required_mark = " *" if field in self._required_fields else ""

            if field == "license_file_path":
                browse_row = QHBoxLayout()
                browse_row.setContentsMargins(0, 0, 0, 0)
                browse_row.addWidget(editor)
                btn_browse = QPushButton("Browse...")
                btn_browse.clicked.connect(self._browse_local_license_file)
                browse_row.addWidget(btn_browse)

                browse_wrap = QWidget()
                browse_wrap.setLayout(browse_row)
                form.addRow(f"{label_text}{required_mark}", browse_wrap)
            else:
                form.addRow(f"{label_text}{required_mark}", editor)

        ok_button = _qt_enum_member(QDialogButtonBox, "StandardButton", "Ok")
        cancel_button = _qt_enum_member(QDialogButtonBox, "StandardButton", "Cancel")
        buttons = QDialogButtonBox(ok_button | cancel_button)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self._ok_button = buttons.button(ok_button)
        if self._ok_button is not None:
            self._ok_button.setObjectName("DialogOkButton")
        self._required_inputs = tuple(self._fields[field] for field in self._required_fields)

        for field in self._required_inputs:
            field.textChanged.connect(self._update_submit_state)

        self._update_submit_state()

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _update_submit_state(self) -> None:
        all_required_present = all(field.text().strip() != "" for field in self._required_inputs)
        if self._ok_button is not None:
            self._ok_button.setEnabled(all_required_present)
            if all_required_present:
                self._ok_button.setToolTip("")
            else:
                self._ok_button.setToolTip("Please fill all required fields.")

    def _browse_local_license_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select local license file",
            str(Path.cwd()),
            "License Files (*.lic *.dat *.txt);;All Files (*.*)",
        )
        if selected:
            field = self._fields.get("license_file_path")
            if field is not None:
                field.setText(selected)

    def payload(self) -> dict[str, str]:
        return {field: editor.text().strip() for field, editor in self._fields.items()}
