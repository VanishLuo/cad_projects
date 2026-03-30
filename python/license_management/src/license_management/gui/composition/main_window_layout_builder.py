from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from license_management.gui.qt_compat import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    Qt,
    QVBoxLayout,
    QWidget,
)


@dataclass(slots=True)
class MainWindowLayoutResult:
    action_button_map: dict[str, QPushButton]
    action_buttons: list[QPushButton]
    btn_add: QPushButton
    btn_import: QPushButton
    btn_check: QPushButton
    btn_switch_workspace: QPushButton
    btn_delete: QPushButton
    btn_export: QPushButton
    btn_compare: QPushButton
    btn_edit: QPushButton
    btn_start: QPushButton
    btn_stop: QPushButton


class MainWindowLayoutBuilder:
    """Build the MainWindow widget tree and return created action button references."""

    def build(
        self,
        *,
        window: QWidget,
        keyword: QWidget,
        vendor: QWidget,
        server: QWidget,
        status: QWidget,
        table: QWidget,
        hint: QWidget,
        log: QWidget,
        workspace_badge: QWidget,
        on_search: Callable[[], None],
        on_reset: Callable[[], None],
        on_add: Callable[[], None],
        on_import: Callable[[], None],
        on_check: Callable[[], None],
        on_switch_workspace: Callable[[], None],
        on_delete: Callable[[], None],
        on_export: Callable[[], None],
        on_compare: Callable[[], None],
        on_edit: Callable[[], None],
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> MainWindowLayoutResult:
        root = QWidget()
        if hasattr(window, "setCentralWidget"):
            window.setCentralWidget(root)

        search_box = QGroupBox("Search & Filters")
        search_box.setObjectName("TopPanel")
        search_layout = QGridLayout()
        search_layout.addWidget(QLabel("Keyword"), 0, 0)
        search_layout.addWidget(keyword, 0, 1)
        search_layout.addWidget(QLabel("Server"), 0, 2)
        search_layout.addWidget(server, 0, 3)

        search_layout.addWidget(QLabel("Vendor"), 1, 0)
        search_layout.addWidget(vendor, 1, 1)
        search_layout.addWidget(QLabel("Status"), 1, 2)
        search_layout.addWidget(status, 1, 3)

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(on_search)
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(on_reset)

        search_actions = QHBoxLayout()
        search_actions.addWidget(btn_search)
        search_actions.addWidget(btn_reset)
        search_actions.addStretch(1)

        search_wrap = QVBoxLayout()
        search_wrap.addLayout(search_layout)
        search_wrap.addLayout(search_actions)
        search_box.setLayout(search_wrap)

        action_row = QHBoxLayout()
        action_button_map: dict[str, QPushButton] = {}
        action_buttons: list[QPushButton] = []

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(on_add)
        action_button_map["add"] = btn_add

        btn_import = QPushButton("Import Files")
        btn_import.clicked.connect(on_import)
        action_button_map["import"] = btn_import

        btn_check = QPushButton("Check")
        btn_check.clicked.connect(on_check)
        action_button_map["check"] = btn_check

        btn_switch_workspace = QPushButton("Switch Workspace")
        btn_switch_workspace.clicked.connect(on_switch_workspace)
        action_button_map["switch_workspace"] = btn_switch_workspace

        btn_delete = QPushButton("Delete Selected")
        btn_delete.clicked.connect(on_delete)
        action_button_map["delete"] = btn_delete

        btn_export = QPushButton("Export")
        btn_export.clicked.connect(on_export)
        action_button_map["export"] = btn_export

        btn_compare = QPushButton("Compare Text")
        btn_compare.clicked.connect(on_compare)
        action_button_map["compare"] = btn_compare

        btn_edit = QPushButton("Edit License")
        btn_edit.clicked.connect(on_edit)
        action_button_map["edit"] = btn_edit

        btn_start = QPushButton("Start Service")
        btn_start.clicked.connect(on_start)
        action_button_map["start"] = btn_start

        btn_stop = QPushButton("Stop Service")
        btn_stop.clicked.connect(on_stop)
        action_button_map["stop"] = btn_stop

        for button in [
            btn_add,
            btn_import,
            btn_check,
            btn_switch_workspace,
            btn_delete,
            btn_export,
            btn_compare,
            btn_edit,
            btn_start,
            btn_stop,
        ]:
            action_row.addWidget(button)
            action_buttons.append(button)

        action_row.addStretch(1)
        action_row.addWidget(QLabel("Workspace:"))
        action_row.addWidget(workspace_badge)
        action_row.addStretch(1)

        records_box = QGroupBox("License Servers")
        records_layout = QVBoxLayout()
        records_layout.addWidget(table)
        records_layout.addWidget(hint)
        records_box.setLayout(records_layout)

        log_box = QGroupBox("Logs")
        log_layout = QVBoxLayout()
        log_layout.addWidget(log)
        log_box.setLayout(log_layout)

        top_panel = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(search_box)
        top_layout.addLayout(action_row)
        top_panel.setLayout(top_layout)

        splitter = QSplitter(_qt_enum_member(Qt, "Orientation", "Vertical"))
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(top_panel)
        splitter.addWidget(records_box)
        splitter.addWidget(log_box)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)

        layout = QVBoxLayout()
        layout.addWidget(splitter, 1)
        root.setLayout(layout)

        return MainWindowLayoutResult(
            action_button_map=action_button_map,
            action_buttons=action_buttons,
            btn_add=btn_add,
            btn_import=btn_import,
            btn_check=btn_check,
            btn_switch_workspace=btn_switch_workspace,
            btn_delete=btn_delete,
            btn_export=btn_export,
            btn_compare=btn_compare,
            btn_edit=btn_edit,
            btn_start=btn_start,
            btn_stop=btn_stop,
        )


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)
