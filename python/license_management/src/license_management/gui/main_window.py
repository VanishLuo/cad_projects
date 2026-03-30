from __future__ import annotations

from dataclasses import replace
import html
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol, cast

from license_management.adapters.provider_adapter import SshCommandExecutor
from license_management.application.license_feature_catalog import LicenseFeatureCatalogService
from license_management.application.remote_license_file_service import RemoteLicenseFileService
from license_management.application.record_check_service import RecordCheckIssue
from license_management.application.record_check_service import RecordCheckService
from license_management.domain.expiration_engine import ExpirationStatus
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.check_run_controller import CheckRunController
from license_management.gui.dialog_flows import DialogFlowBinder
from license_management.gui.dialogs import (
    CheckResultDialog,
    LicenseFileDetailDialog,
    RecordDialog,
    RemoteLicenseEditorDialog,
)
from license_management.gui.feature_search import FeatureSearchController
from license_management.gui.models import UiLicenseRow
from license_management.gui.qt_compat import (
    QColor,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    Qt,
    QVBoxLayout,
    QWidget,
    dialog_exec,
    dialog_is_accepted,
)
from license_management.gui.validation_feedback import to_license_record, validate_license_form
from license_management.gui.view_model import MainListViewModel
from license_management.gui.workspace_action_policy import build_workspace_action_policy
from license_management.infrastructure.config.table_header_config import load_table_header_config
from license_management.infrastructure.repositories.sqlite_license_repository import (
    SqliteLicenseRepository,
)


class UiContextProtocol(Protocol):
    repository: SqliteLicenseRepository
    feature_catalog: LicenseFeatureCatalogService
    checker: RecordCheckService
    ssh_executor: SshCommandExecutor
    remote_license_service: RemoteLicenseFileService
    ssh_credentials: Any
    view_model: MainListViewModel
    search: FeatureSearchController
    binder: DialogFlowBinder


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    """Resolve Qt enum members across PyQt5/PyQt6 enum styles."""

    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)


class MainWindow(QMainWindow):
    def __init__(self, context: UiContextProtocol) -> None:
        super().__init__()
        self._ctx = context
        self.setWindowTitle("License Management")
        self.resize(1440, 900)

        self._keyword = QLineEdit()
        self._vendor = QLineEdit()
        self._server = QLineEdit()
        self._status = QComboBox()
        self._status.addItems(
            [
                "",
                ExpirationStatus.UNKNOWN.value,
                ExpirationStatus.ACTIVE.value,
                ExpirationStatus.EXPIRED.value,
            ]
        )

        self._table_cfg = load_table_header_config()
        self._table_columns = tuple(self._table_cfg.gui_column_order)
        self._table = QTableWidget(0, len(self._table_columns))
        self._table.setHorizontalHeaderLabels(
            [self._table_cfg.gui_headers.get(column, column) for column in self._table_columns]
        )
        header = self._table.horizontalHeader()
        if header is None:
            raise RuntimeError("table header is unavailable")
        header.setDefaultAlignment(
            _qt_enum_member(Qt, "AlignmentFlag", "AlignLeft")
            | _qt_enum_member(Qt, "AlignmentFlag", "AlignVCenter")
        )
        header_stretch = _qt_enum_member(QHeaderView, "ResizeMode", "Stretch")
        header_resize = _qt_enum_member(QHeaderView, "ResizeMode", "ResizeToContents")
        for index, column in enumerate(self._table_columns):
            if column in {"provider", "vendor", "status"}:
                header.setSectionResizeMode(index, header_resize)
            else:
                header.setSectionResizeMode(index, header_stretch)
        self._table.setSelectionBehavior(
            _qt_enum_member(QTableWidget, "SelectionBehavior", "SelectRows")
        )
        self._table.setSelectionMode(
            _qt_enum_member(QTableWidget, "SelectionMode", "ExtendedSelection")
        )
        self._table.setEditTriggers(
            _qt_enum_member(QTableWidget, "EditTrigger", "DoubleClicked")
            | _qt_enum_member(QTableWidget, "EditTrigger", "SelectedClicked")
            | _qt_enum_member(QTableWidget, "EditTrigger", "EditKeyPressed")
        )
        self._editable_table_triggers = self._table.editTriggers()
        self._table.setAlternatingRowColors(True)
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self._table.itemChanged.connect(self._on_table_item_changed)

        self._hint = QLabel("")
        self._feedback = QLabel("Ready")
        self._feedback.hide()
        self._workspace_badge = QLabel("")
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Import and runtime logs will appear here.")
        self._btn_add: QPushButton | None = None
        self._btn_import: QPushButton | None = None
        self._btn_check: QPushButton | None = None
        self._btn_reset_data: QPushButton | None = None
        self._btn_delete: QPushButton | None = None
        self._btn_export: QPushButton | None = None
        self._btn_compare: QPushButton | None = None
        self._btn_edit: QPushButton | None = None
        self._btn_start: QPushButton | None = None
        self._btn_stop: QPushButton | None = None
        self._action_button_map: dict[str, QPushButton] = {}
        self._action_buttons: list[QPushButton] = []
        self._check_in_progress = False
        self._check_controller = CheckRunController(
            checker=self._ctx.checker,
            on_finished=self._on_check_finished,
            on_state_changed=self._on_check_state_changed,
        )
        self._check_result_dialog: CheckResultDialog | None = None
        self._runtime_statuses_by_workspace: dict[str, dict[str, str]] = {
            "committed": {},
            "staging": {},
        }
        self._is_rendering_table = False
        self._editable_table_columns = {
            column for column in self._table_columns if column not in {"record_id", "status"}
        }

        self._build_layout()
        self._bind_live_search()
        self._sync_runtime_statuses_from_workspace()
        self._refresh_workspace_badge()
        self._refresh_after_mutation("Ready")
        self._append_log("Application started.")
        self._log_event(
            "app_started",
            db_path=str(self._ctx.repository._db_path),
            table_columns=list(self._table_columns),
        )

    def _on_check_state_changed(self, in_progress: bool) -> None:
        self._check_in_progress = in_progress

    def _bind_live_search(self) -> None:
        self._keyword.textChanged.connect(self._on_search_text_changed)
        self._server.textChanged.connect(self._on_search_text_changed)
        self._vendor.textChanged.connect(self._on_search_text_changed)
        self._status.currentIndexChanged.connect(self._on_status_changed)

    def _on_search_text_changed(self, _text: str) -> None:
        self._apply_search(trigger="live_text")

    def _on_status_changed(self, _index: int) -> None:
        self._apply_search(trigger="live_status")

    def _build_layout(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        search_box = QGroupBox("Search & Filters")
        search_box.setObjectName("TopPanel")
        search_layout = QGridLayout()
        search_layout.addWidget(QLabel("Keyword"), 0, 0)
        search_layout.addWidget(self._keyword, 0, 1)
        search_layout.addWidget(QLabel("Server"), 0, 2)
        search_layout.addWidget(self._server, 0, 3)

        search_layout.addWidget(QLabel("Vendor"), 1, 0)
        search_layout.addWidget(self._vendor, 1, 1)
        search_layout.addWidget(QLabel("Status"), 1, 2)
        search_layout.addWidget(self._status, 1, 3)

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(lambda: self._apply_search(trigger="manual"))
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self._reset_filters)

        search_actions = QHBoxLayout()
        search_actions.addWidget(btn_search)
        search_actions.addWidget(btn_reset)
        search_actions.addStretch(1)

        search_wrap = QVBoxLayout()
        search_wrap.addLayout(search_layout)
        search_wrap.addLayout(search_actions)
        search_box.setLayout(search_wrap)

        action_row = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._add_record)
        self._btn_add = btn_add
        self._action_button_map["add"] = btn_add
        btn_import = QPushButton("Import Files")
        btn_import.clicked.connect(self._import_json)
        self._btn_import = btn_import
        self._action_button_map["import"] = btn_import
        btn_check = QPushButton("Check")
        btn_check.clicked.connect(self._check_records)
        self._btn_check = btn_check
        self._action_button_map["check"] = btn_check
        btn_reset_data = QPushButton("Switch Workspace")
        btn_reset_data.clicked.connect(self._reset_error_data)
        self._btn_reset_data = btn_reset_data
        self._action_button_map["reset_data"] = btn_reset_data
        btn_delete = QPushButton("Delete Selected")
        btn_delete.clicked.connect(self._delete_selected_records)
        self._btn_delete = btn_delete
        self._action_button_map["delete"] = btn_delete
        btn_export = QPushButton("Export")
        btn_export.clicked.connect(self._export_json)
        self._btn_export = btn_export
        self._action_button_map["export"] = btn_export
        btn_compare = QPushButton("Compare Snapshot")
        btn_compare.clicked.connect(self._compare_snapshot)
        self._btn_compare = btn_compare
        self._action_button_map["compare"] = btn_compare
        btn_edit = QPushButton("Edit License")
        btn_edit.clicked.connect(self._edit_remote_license)
        self._btn_edit = btn_edit
        self._action_button_map["edit"] = btn_edit
        btn_start = QPushButton("Start Service")
        btn_start.clicked.connect(lambda: self._start_stop("start"))
        self._btn_start = btn_start
        self._action_button_map["start"] = btn_start
        btn_stop = QPushButton("Stop Service")
        btn_stop.clicked.connect(lambda: self._start_stop("stop"))
        self._btn_stop = btn_stop
        self._action_button_map["stop"] = btn_stop

        for button in [
            btn_add,
            btn_import,
            btn_check,
            btn_reset_data,
            btn_delete,
            btn_export,
            btn_compare,
            btn_edit,
            btn_start,
            btn_stop,
        ]:
            action_row.addWidget(button)
            self._action_buttons.append(button)
        action_row.addStretch(1)
        action_row.addWidget(QLabel("Workspace:"))
        action_row.addWidget(self._workspace_badge)
        action_row.addStretch(1)

        records_box = QGroupBox("License Servers")
        records_layout = QVBoxLayout()
        records_layout.addWidget(self._table)
        records_layout.addWidget(self._hint)
        records_box.setLayout(records_layout)

        log_box = QGroupBox("Logs")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self._log)
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

    def _apply_search(self, *, trigger: str = "manual") -> None:
        keyword = self._keyword.text().strip()
        vendor = self._vendor.text().strip()
        server_name = self._server.text().strip()
        status = self._status.currentText().strip()
        result = self._ctx.search.search(
            today=date.today(),
            keyword=keyword,
            vendor=vendor,
            server_name=server_name,
            status=status,
        )
        self._render_rows(result.rows)
        self._hint.setText(result.empty_hint)
        self._log_event(
            "search_applied",
            trigger=trigger,
            keyword=keyword,
            vendor=vendor,
            server_name=server_name,
            status=status,
            result_count=len(result.rows),
        )

    def _reset_filters(self) -> None:
        before = {
            "keyword": self._keyword.text().strip(),
            "vendor": self._vendor.text().strip(),
            "server": self._server.text().strip(),
            "status": self._status.currentText().strip(),
        }
        self._keyword.clear()
        self._vendor.clear()
        self._server.clear()
        self._status.setCurrentIndex(0)

        result = self._ctx.search.reset(today=date.today())
        self._render_rows(result.rows)
        self._hint.setText(result.empty_hint)
        self._feedback.setText("Filters reset.")
        self._log_event("filters_reset", before=before, result_count=len(result.rows))

    def _selected_record(self) -> LicenseRecord | None:
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

        record_id = item.text()
        return self._ctx.repository.get(record_id)

    def _selected_records(self) -> list[LicenseRecord]:
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
            record = self._ctx.repository.get(record_id)
            if record is not None:
                records.append(record)
        return records

    def _delete_selected_records(self) -> None:
        selected = self._selected_records()
        if not selected:
            QMessageBox.information(self, "Delete", "Please select at least one row.")
            return

        yes_button = _qt_enum_member(QMessageBox, "StandardButton", "Yes")
        no_button = _qt_enum_member(QMessageBox, "StandardButton", "No")
        decision = QMessageBox.question(
            self,
            "Delete Selected",
            f"Delete {len(selected)} selected record(s)?",
            yes_button | no_button,
        )
        if decision != yes_button:
            return

        self._enter_staging_workspace(reason="delete_selected")

        deleted = 0
        for record in selected:
            if self._ctx.repository.delete(record.record_id):
                self._ctx.feature_catalog.remove_for_record(record)
                deleted += 1

        self._clear_current_runtime_statuses()
        self._refresh_after_mutation(f"Deleted {deleted} selected record(s).")
        self._log_event("delete_selected", requested=len(selected), deleted=deleted)

    def _reset_error_data(self) -> None:
        current_workspace = self._ctx.repository.current_workspace
        target_workspace = "committed" if current_workspace == "staging" else "staging"
        self._switch_workspace(target_workspace)
        rows = len(self._ctx.repository.list_all())
        self._refresh_after_mutation(f"Switched to {target_workspace} workspace: rows={rows}")
        self._append_log(f"Workspace switched to {target_workspace}: rows={rows}")

    def _switch_workspace(self, workspace: str) -> None:
        self._ctx.repository.switch_workspace(workspace)
        self._ctx.feature_catalog.switch_workspace(workspace)
        self._sync_runtime_statuses_from_workspace()
        self._refresh_workspace_badge()

    def _workspace_row_count(self, workspace: str) -> int:
        previous = self._ctx.repository.current_workspace
        self._switch_workspace(workspace)
        count = len(self._ctx.repository.list_all())
        self._switch_workspace(previous)
        return count

    def _add_record(self) -> None:
        dialog = RecordDialog(self)
        if not dialog_is_accepted(dialog_exec(dialog)):
            self._log_event("add_cancelled")
            return

        payload = dialog.payload()
        self._log_event(
            "add_requested",
            record_id=payload.get("record_id", ""),
            server_name=payload.get("server_name", ""),
            provider=payload.get("provider", ""),
            license_file_path=payload.get("license_file_path", ""),
        )

        validation = validate_license_form(payload)
        if not validation.is_valid:
            detail = "; ".join(issue.message for issue in validation.issues)
            QMessageBox.warning(self, "Invalid input", detail)
            self._feedback.setText(f"Add failed: {detail}")
            self._log_event("add_failed", reason="validation_failed", detail=detail)
            return

        self._enter_staging_workspace(reason="add_record")
        result = self._ctx.binder.add_or_edit(payload)
        if not result.success:
            QMessageBox.warning(self, "Add failed", result.feedback.detail)
            self._feedback.setText(result.feedback.detail)
            self._log_event("add_failed", reason="service_rejected", detail=result.feedback.detail)
            return

        self._clear_current_runtime_statuses()
        self._refresh_after_mutation(result.feedback.detail)
        self._log_event(
            "add_succeeded",
            record_id=payload.get("record_id", ""),
            server_name=payload.get("server_name", ""),
            provider=payload.get("provider", ""),
            license_file_path=payload.get("license_file_path", ""),
            detail=result.feedback.detail,
        )

    def _check_records(self) -> None:
        if self._check_controller.in_progress:
            QMessageBox.information(self, "Check running", "Check is still running, please wait.")
            return

        records = self._ctx.repository.list_all()
        self._set_action_buttons_enabled(False)
        self._feedback.setText(f"Check started: scanned={len(records)}")
        self._log_event("check_started", scanned=len(records))

        started = self._check_controller.start(records)
        if not started:
            self._set_action_buttons_enabled(True)
            QMessageBox.information(self, "Check running", "Check is still running, please wait.")

    def _on_check_finished(
        self, scanned: int, issues_raw: object, runtime_statuses_raw: object
    ) -> None:
        issues = cast(list[RecordCheckIssue], issues_raw)
        mapped_issues = [self._map_check_issue(issue) for issue in issues]
        runtime_statuses = cast(dict[str, str], runtime_statuses_raw)
        self._set_action_buttons_enabled(True)

        grouped: dict[str, list[RecordCheckIssue]] = {
            "license": [],
            "ssh": [],
            "start": [],
            "other": [],
        }
        for issue in mapped_issues:
            if issue.status == "license_not_found":
                grouped["license"].append(issue)
            elif issue.status == "ssh_failed":
                grouped["ssh"].append(issue)
            elif issue.status == "start_command_error":
                grouped["start"].append(issue)
            else:
                grouped["other"].append(issue)

        current_workspace = self._ctx.repository.current_workspace
        self._runtime_statuses_by_workspace[current_workspace] = dict(runtime_statuses)
        self._sync_runtime_statuses_from_workspace()
        self._refresh_after_mutation(f"Check completed: scanned={scanned}, issues={len(issues)}")

        active_count = sum(
            1 for value in runtime_statuses.values() if value == ExpirationStatus.ACTIVE.value
        )
        expired_count = sum(
            1 for value in runtime_statuses.values() if value == ExpirationStatus.EXPIRED.value
        )
        unknown_count = sum(
            1 for value in runtime_statuses.values() if value == ExpirationStatus.UNKNOWN.value
        )

        blocking_statuses = {"license_not_found", "ssh_failed", "start_command_error"}
        blocking_issues = [item for item in mapped_issues if item.status in blocking_statuses]
        blocked_record_ids = {item.record_id for item in blocking_issues}

        published_rows = 0
        if current_workspace == "staging":
            published_rows = self._publish_passing_rows_to_committed(
                runtime_statuses=runtime_statuses,
                blocked_record_ids=blocked_record_ids,
            )
            if published_rows > 0:
                self._append_log(
                    f"Check auto-commit: passed_rows={published_rows} written to committed workspace.",
                    level="success",
                )

        if not blocking_issues:
            self._log_event("check_completed", scanned=scanned, issues=0)
            self._append_log(
                (
                    f"Check completed: active={active_count}, expired={expired_count}, "
                    f"unknown={unknown_count}, blocking_issues=0, total_issues={len(mapped_issues)}, "
                    f"auto_committed={published_rows}."
                ),
                level="success",
            )

            if mapped_issues:
                max_issue_log = 12
                for issue in mapped_issues[:max_issue_log]:
                    self._append_log(
                        f"check_non_blocking_issue: record_id={issue.record_id} "
                        f"status={issue.status} reason={issue.reason}",
                        level="info",
                    )
                if len(mapped_issues) > max_issue_log:
                    self._append_log(
                        f"check_non_blocking_issue: omitted {len(mapped_issues) - max_issue_log} more issue(s).",
                    )
            return

        if self._check_result_dialog is not None:
            self._check_result_dialog.close()
        dialog = CheckResultDialog(scanned=scanned, grouped=grouped, parent=self)
        dialog.setModal(False)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self._check_result_dialog = dialog

        self._append_log(
            (
                f"Check completed: active={active_count}, expired={expired_count}, "
                f"unknown={unknown_count}, issues={len(mapped_issues)}."
            ),
            level=("error" if len(mapped_issues) > 0 else "success"),
        )
        self._log_event(
            "check_completed",
            scanned=scanned,
            issues=len(mapped_issues),
            active=active_count,
            expired=expired_count,
            unknown=unknown_count,
            deleted=0,
        )
        max_issue_log = 12
        for issue in mapped_issues[:max_issue_log]:
            self._append_log(
                f"check_issue: record_id={issue.record_id} status={issue.status} reason={issue.reason}",
                level="error",
            )
        if len(mapped_issues) > max_issue_log:
            self._append_log(
                f"check_issue: omitted {len(mapped_issues) - max_issue_log} more issue(s).",
            )

    def _map_check_issue(self, issue: RecordCheckIssue) -> RecordCheckIssue:
        reason = issue.reason.strip()
        lower_reason = reason.lower()

        mapped_reason = reason
        if issue.status == "license_not_found":
            mapped_reason = "FileNotFoundError: license file not found"
        elif issue.status == "ssh_failed":
            if "timed out" in lower_reason or "timeout" in lower_reason:
                mapped_reason = "TimeoutError: SSH connection timed out"
            elif "permission denied" in lower_reason or "authentication failed" in lower_reason:
                mapped_reason = "PermissionError: SSH authentication failed"
            elif "host is empty" in lower_reason:
                mapped_reason = "ValueError: SSH host is empty"
            else:
                mapped_reason = "ConnectionError: SSH connection failed"
        elif issue.status == "start_command_error":
            if "exit code 127" in lower_reason or "not found" in lower_reason:
                mapped_reason = "FileNotFoundError: start executable not found"
            elif "permission denied" in lower_reason:
                mapped_reason = "PermissionError: start executable permission denied"
            else:
                mapped_reason = "RuntimeError: start command probe failed"
        if mapped_reason != reason:
            mapped_reason = f"{mapped_reason} | raw={reason}"

        return RecordCheckIssue(
            record_id=issue.record_id,
            status=issue.status,
            reason=mapped_reason,
            license_file_path=issue.license_file_path,
        )

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        if not enabled:
            for button in self._action_buttons:
                button.setEnabled(False)
            self._keyword.setEnabled(False)
            self._vendor.setEnabled(False)
            self._server.setEnabled(False)
            self._status.setEnabled(False)
            self._table.setEnabled(False)
            return

        self._keyword.setEnabled(True)
        self._vendor.setEnabled(True)
        self._server.setEnabled(True)
        self._status.setEnabled(True)
        self._table.setEnabled(True)
        self._apply_workspace_action_policy()

    def _apply_workspace_action_policy(self) -> None:
        workspace = self._ctx.repository.current_workspace
        policy = build_workspace_action_policy(workspace)

        for key, button in self._action_button_map.items():
            button.setEnabled(policy.action_enabled.get(key, True))
            button.setToolTip(policy.action_tooltips.get(key, ""))

        if not policy.table_editable:
            self._table.setEditTriggers(
                _qt_enum_member(QTableWidget, "EditTrigger", "NoEditTriggers")
            )
            return
        self._table.setEditTriggers(self._editable_table_triggers)

    def _on_cell_clicked(self, row: int, column: int) -> None:
        _ = (row, column)

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._is_rendering_table:
            return
        if self._ctx.repository.current_workspace == "committed":
            self._refresh_after_mutation("Committed workspace is read-only.")
            return
        column_name = self._table_columns[item.column()]
        if column_name not in self._editable_table_columns:
            return
        if "record_id" not in self._table_columns:
            return

        record_id_item = self._table.item(item.row(), self._table_columns.index("record_id"))
        if record_id_item is None:
            return
        record_id = record_id_item.text().strip()
        if record_id == "":
            return

        self._enter_staging_workspace(reason="table_edit")
        record = self._ctx.repository.get(record_id)
        if record is None:
            self._refresh_after_mutation("Table edit ignored: record not found.")
            return

        value = item.text().strip()
        current_value = str(getattr(record, column_name, ""))
        if value == current_value:
            return
        if column_name in {"server_name", "provider", "prot"} and value == "":
            self._append_log(
                f"table_edit_blocked: field={column_name} cannot be empty for record_id={record_id}",
                level="error",
            )
            self._refresh_after_mutation("Table edit reverted due to invalid value.")
            return

        updated: LicenseRecord
        if column_name == "expires_on":
            try:
                parsed_date = date.fromisoformat(value)
            except ValueError:
                self._append_log(
                    (
                        "table_edit_blocked: field=expires_on must be ISO date "
                        f"(YYYY-MM-DD) for record_id={record_id}"
                    ),
                    level="error",
                )
                self._refresh_after_mutation("Table edit reverted due to invalid date format.")
                return
            updated = replace(record, expires_on=parsed_date)
        else:
            updated = replace(record, **cast(dict[str, Any], {column_name: value}))
        self._ctx.repository.upsert(updated)
        self._clear_current_runtime_statuses()
        self._refresh_after_mutation(f"Table updated: record_id={record_id}, field={column_name}")
        self._append_log(
            f"table_edit: record_id={record_id} field={column_name} value={value}",
            level="info",
        )

    def _import_json(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select import files",
            str(Path.cwd()),
            "Import Files (*.json *.xlsx *.xlsm)",
        )
        if not file_paths:
            self._log_event("import_cancelled")
            return

        self._log_event("import_requested", files=file_paths)
        self._enter_staging_workspace(reason="import")
        result, report = self._ctx.binder.import_files([Path(path) for path in file_paths])
        detail = result.feedback.detail
        self._append_log(f"Import request: {len(file_paths)} file(s).")
        if report is not None and report.errors:
            detail = f"{detail} | errors={len(report.errors)}"
            self._append_log(f"Import completed with {len(report.errors)} error(s).")
            for message in report.errors:
                self._append_log(f"ERROR: {message}")
        elif report is not None:
            self._append_log(
                "Import completed: "
                f"total={report.total}, succeeded={report.succeeded}, "
                f"failed={report.failed}, deduplicated={report.deduplicated}"
            )
            if report.warnings:
                max_warning_lines = 80
                for warning in report.warnings[:max_warning_lines]:
                    self._append_log(f"WARNING: {warning}")
                omitted = len(report.warnings) - max_warning_lines
                if omitted > 0:
                    self._append_log(
                        f"WARNING: omitted {omitted} additional warning line(s) to keep log readable."
                    )
        self._log_event(
            "import_completed",
            success=result.success,
            detail=detail,
            total=(report.total if report is not None else 0),
            succeeded=(report.succeeded if report is not None else 0),
            failed=(report.failed if report is not None else 0),
            deduplicated=(report.deduplicated if report is not None else 0),
            warnings=(len(report.warnings) if report is not None else 0),
            errors=(len(report.errors) if report is not None else 0),
        )
        self._clear_current_runtime_statuses()
        self._refresh_after_mutation(detail)

    def _export_json(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self,
            "Export records",
            str(Path.cwd() / "exported_licenses.xlsx"),
            "Export Files (*.json *.xlsx *.xlsm)",
        )
        if not output:
            self._log_event("export_cancelled")
            return

        output_path = Path(output)
        if output_path.suffix.strip() == "":
            output_path = output_path.with_suffix(".xlsx")
            output = str(output_path)

        record_count = len(self._ctx.repository.list_all())
        self._log_event("export_requested", output=output, record_count=record_count)
        message = self._ctx.binder.export_records(
            file_path=output_path,
            records=self._ctx.repository.list_all(),
        )
        self._feedback.setText(message.feedback.detail)
        self._log_event(
            "export_completed",
            success=message.success,
            output=output,
            detail=message.feedback.detail,
        )

    def _compare_snapshot(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select comparison JSON",
            str(Path.cwd()),
            "JSON Files (*.json)",
        )
        if not selected:
            self._log_event("compare_cancelled")
            return

        self._log_event("compare_requested", target_file=selected)
        right_records = self._load_records_from_json(Path(selected))
        if right_records is None:
            self._log_event("compare_failed", reason="invalid_snapshot_file", target_file=selected)
            return

        result, report = self._ctx.binder.compare(
            left_target="local-repository",
            left_records=self._ctx.repository.list_all(),
            right_target=Path(selected).name,
            right_records=right_records,
        )
        if report is not None:
            QMessageBox.information(
                self,
                "Compare Report",
                f"Differences: {len(report.issues)}\n{result.feedback.detail}",
            )
            self._log_event(
                "compare_completed",
                success=result.success,
                target_file=selected,
                differences=len(report.issues),
                detail=result.feedback.detail,
            )
        self._feedback.setText(result.feedback.detail)

    def _start_stop(self, action: str) -> None:
        selected = self._selected_record()
        if selected is None:
            self._append_log(
                "service_action_blocked: Please select one table row first.", level="error"
            )
            self._feedback.setText("Please select one table row first.")
            self._log_event("service_action_blocked", action=action, reason="no_row_selected")
            return

        host = selected.server_name.strip()
        if host == "":
            self._append_log(
                "service_action_blocked: Selected row has empty server host.", level="error"
            )
            self._feedback.setText("Selected row has empty server host.")
            self._log_event(
                "service_action_blocked",
                action=action,
                reason="empty_server_name",
                record_id=selected.record_id,
            )
            return

        username = self._ctx.ssh_credentials.username
        password = self._ctx.ssh_credentials.password or None
        provider = selected.provider
        start_executable_path = selected.start_executable_path
        license_file_path = selected.license_file_path
        start_option_override = selected.start_option_override
        result = self._ctx.binder.start_stop(
            action=action,
            host=host,
            username=username,
            password=password,
            provider=provider,
            start_executable_path=start_executable_path,
            license_file_path=license_file_path,
            start_option_override=start_option_override,
        )
        self._append_log(
            f"[{action}] {result.feedback.detail}",
            level=("success" if result.success else "error"),
        )
        self._feedback.setText(result.feedback.detail)
        if result.operation_logs:
            self._append_log(f"[{action}] host={host} attempts={len(result.operation_logs)}")
            for log in result.operation_logs:
                command_level = "success" if log.exit_code == 0 else "error"
                self._append_log(
                    f"  attempt={log.attempt} exit_code={log.exit_code} command={log.command}",
                    level=command_level,
                )
                stdout_text = log.stdout.strip()
                stderr_text = log.stderr.strip()
                if stdout_text:
                    self._append_log(f"  stdout:\n{stdout_text}", level="success")
                if stderr_text:
                    self._append_log(f"  stderr:\n{stderr_text}", level="error")
        self._log_event(
            "service_action",
            action=action,
            success=result.success,
            host=host,
            record_id=selected.record_id,
            detail=result.feedback.detail,
        )

    def _edit_remote_license(self) -> None:
        selected = self._selected_record()
        if selected is None:
            self._append_log("edit_blocked: Please select one table row first.", level="error")
            return

        host = selected.server_name.strip()
        remote_path = selected.license_file_path.strip()
        if host == "":
            self._append_log("edit_blocked: Selected row has empty server host.", level="error")
            return
        if remote_path == "":
            self._append_log(
                "edit_blocked: Selected row has empty license file path.", level="error"
            )
            return

        username = self._ctx.ssh_credentials.username.strip()
        password = self._ctx.ssh_credentials.password or None
        self._append_log(
            f"[edit] loading remote file: host={host} path={remote_path}",
            level="info",
        )
        loaded = self._ctx.remote_license_service.load_text(
            host=host,
            username=username,
            password=password,
            remote_path=remote_path,
        )
        if not loaded.success:
            self._append_log(f"[edit] failed: {loaded.error}", level="error")
            return

        dialog = RemoteLicenseEditorDialog(
            host=host,
            remote_path=remote_path,
            content=loaded.content,
            parent=self,
        )
        if not dialog_is_accepted(dialog_exec(dialog)):
            self._append_log("[edit] cancelled by user.")
            return

        updated = dialog.text_content()
        if updated == loaded.content:
            self._append_log("[edit] no changes detected; skipped upload.")
            return

        saved = self._ctx.remote_license_service.save_text(
            host=host,
            username=username,
            password=password,
            remote_path=remote_path,
            content=updated,
        )
        if saved.success:
            self._append_log(
                f"[edit] saved remote file successfully: host={host} path={remote_path}",
                level="success",
            )
        else:
            self._append_log(f"[edit] failed: {saved.error}", level="error")

    def _on_row_double_clicked(self, row: int, _column: int) -> None:
        if self._ctx.repository.current_workspace == "staging":
            self._log_event("row_double_click_ignored", reason="staging_workspace")
            return

        column_name = self._table_columns[_column]
        if column_name != "record_id":
            return

        if "record_id" not in self._table_columns:
            self._log_event("row_double_click_ignored", reason="record_id_column_missing")
            return

        id_col = self._table_columns.index("record_id")
        item = self._table.item(row, id_col)
        if item is None:
            self._log_event("row_double_click_ignored", reason="row_item_missing", row=row)
            return

        record_id = item.text().strip()
        if record_id == "":
            self._log_event("row_double_click_ignored", reason="empty_record_id", row=row)
            return

        selected_record = self._ctx.repository.get(record_id)
        if selected_record is None:
            self._log_event(
                "row_double_click_ignored", reason="record_not_found", record_id=record_id
            )
            return

        license_file_path = selected_record.license_file_path.strip()
        grouped_rows = self._ctx.feature_catalog.list_for_record(selected_record)
        if not grouped_rows:
            sync = self._ctx.feature_catalog.sync_from_record(selected_record)
            grouped_rows = self._ctx.feature_catalog.list_for_record(selected_record)
            if sync.license_missing:
                self._log_event(
                    "row_double_click_license_file_not_found",
                    record_id=record_id,
                    license_file_path=(license_file_path or "(empty)"),
                )
        if not grouped_rows:
            all_records = self._ctx.repository.list_all()
            same_file_records = [
                record
                for record in all_records
                if record.license_file_path.strip() == license_file_path
            ]
            grouped_rows = self._build_feature_expiry_rows(same_file_records)
            record_count = len(same_file_records)
        else:
            record_count = sum(item[2] for item in grouped_rows)

        if not grouped_rows:
            QMessageBox.information(
                self,
                "No Feature Data",
                "No parsed feature information is available for this record.",
            )
            self._log_event(
                "row_double_click_blocked",
                reason="no_feature_data",
                record_id=record_id,
                license_file_path=(license_file_path or "(empty)"),
            )
            return

        dialog = LicenseFileDetailDialog(
            license_file_path=license_file_path or "(empty)",
            rows=grouped_rows,
            record_count=record_count,
            parent=self,
        )
        dialog_exec(dialog)
        self._log_event(
            "row_double_click_opened_detail",
            record_id=record_id,
            license_file_path=(license_file_path or "(empty)"),
            feature_expiry_groups=len(grouped_rows),
            record_count=record_count,
        )

    def _build_feature_expiry_rows(
        self,
        records: list[LicenseRecord],
    ) -> list[tuple[str, str, int]]:
        grouped: dict[tuple[str, str], int] = {}
        for record in records:
            feature = record.feature_name.strip() or "(empty)"
            expires_on = record.expires_on.isoformat()
            key = (feature, expires_on)
            grouped[key] = grouped.get(key, 0) + 1

        rows = [(feature, expires_on, count) for (feature, expires_on), count in grouped.items()]
        rows.sort(key=lambda item: (item[1], item[0].lower()))
        return rows

    def _refresh_after_mutation(self, feedback: str) -> None:
        self._ctx.view_model.load(self._ctx.repository.list_all(), today=date.today())
        self._render_rows(self._ctx.view_model.rows)
        self._hint.setText(self._ctx.view_model.empty_state_hint())
        self._feedback.setText(feedback)
        self._refresh_workspace_badge()
        if not self._check_in_progress:
            self._set_action_buttons_enabled(True)

    def _publish_passing_rows_to_committed(
        self,
        *,
        runtime_statuses: dict[str, str],
        blocked_record_ids: set[str],
    ) -> int:
        staging_records = self._ctx.repository.list_all()
        passing_records = [
            record for record in staging_records if record.record_id not in blocked_record_ids
        ]
        if not passing_records:
            return 0

        self._switch_workspace("committed")
        committed_statuses = dict(self._runtime_statuses_by_workspace.get("committed", {}))
        published = 0
        for record in passing_records:
            self._ctx.repository.upsert(record)
            self._ctx.feature_catalog.sync_from_record(record)
            committed_status = runtime_statuses.get(record.record_id, "").strip()
            if committed_status:
                committed_statuses[record.record_id] = committed_status
            published += 1

        self._runtime_statuses_by_workspace["committed"] = committed_statuses
        self._switch_workspace("staging")
        return published

    def _refresh_workspace_badge(self) -> None:
        workspace = self._ctx.repository.current_workspace
        if workspace == "staging":
            self._workspace_badge.setText("STAGING (not committed)")
            self._workspace_badge.setStyleSheet(
                "QLabel { background:#f57c00; color:#ffffff; font-weight:700; "
                "padding:4px 10px; border-radius:10px; }"
            )
            return

        self._workspace_badge.setText("COMMITTED (production)")
        self._workspace_badge.setStyleSheet(
            "QLabel { background:#2e7d32; color:#ffffff; font-weight:700; "
            "padding:4px 10px; border-radius:10px; }"
        )

    def _enter_staging_workspace(self, *, reason: str) -> None:
        previous = self._ctx.repository.current_workspace
        self._ctx.repository.enter_staging_workspace()
        self._ctx.feature_catalog.enter_staging_workspace()
        if previous != self._ctx.repository.current_workspace:
            self._append_log(f"Workspace switched to staging for {reason}.")
            self._sync_runtime_statuses_from_workspace()
            self._refresh_workspace_badge()

    def _sync_runtime_statuses_from_workspace(self) -> None:
        current_workspace = self._ctx.repository.current_workspace
        self._ctx.view_model.set_runtime_statuses(
            self._runtime_statuses_by_workspace.get(current_workspace, {})
        )

    def _clear_current_runtime_statuses(self) -> None:
        current_workspace = self._ctx.repository.current_workspace
        self._runtime_statuses_by_workspace[current_workspace] = {}
        self._sync_runtime_statuses_from_workspace()

    def _append_log(self, message: str, *, level: str = "info") -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "#333333"
        if level == "error":
            color = "#b00020"
        elif level == "success":
            color = "#1b5e20"
        text = html.escape(f"[{stamp}] {message}").replace("\n", "<br/>")
        self._log.append(f'<span style="color:{color}; white-space:pre-wrap;">{text}</span>')

    def _log_event(self, event: str, **fields: object) -> None:
        # Keep log panel focused on user-facing outcomes.
        if not (
            event.endswith("_failed")
            or event.endswith("_blocked")
            or event == "service_action_blocked"
        ):
            return

        reason = str(fields.get("reason", "")).strip()
        detail = str(fields.get("detail", "")).strip()
        record_id = str(fields.get("record_id", "")).strip()
        pieces = [f"event={event}"]
        if record_id:
            pieces.append(f"record_id={record_id}")
        if reason:
            pieces.append(f"reason={reason}")
        if detail:
            pieces.append(f"detail={detail}")
        self._append_log(" | ".join(pieces), level="error")

    def _render_rows(self, rows: tuple[UiLicenseRow, ...]) -> None:
        self._is_rendering_table = True
        self._table.setRowCount(len(rows))
        try:
            for row_index, row in enumerate(rows):
                values = [str(getattr(row, column, "")) for column in self._table_columns]
                for col_index, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    column_name = self._table_columns[col_index]
                    if column_name not in self._editable_table_columns:
                        item.setFlags(
                            item.flags() & ~_qt_enum_member(Qt, "ItemFlag", "ItemIsEditable")
                        )
                    if column_name == "status":
                        if value == ExpirationStatus.ACTIVE.value:
                            item.setForeground(QColor("#1b5e20"))
                        elif value == ExpirationStatus.EXPIRED.value:
                            item.setForeground(QColor("#b00020"))
                        elif value == ExpirationStatus.UNKNOWN.value:
                            item.setForeground(QColor("#666666"))
                    self._table.setItem(row_index, col_index, item)
        finally:
            self._is_rendering_table = False

    def _load_records_from_json(self, file_path: Path) -> list[LicenseRecord] | None:
        try:
            raw: object = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Read failed", f"Cannot load file: {exc}")
            return None

        payloads: list[object]
        if isinstance(raw, dict):
            payloads = [raw]
        elif isinstance(raw, list):
            payloads = cast(list[object], raw)
        else:
            QMessageBox.critical(self, "Format error", "JSON must be object or array.")
            return None

        records: list[LicenseRecord] = []
        errors: list[str] = []

        for payload in payloads:
            if not isinstance(payload, dict):
                errors.append("item is not an object")
                continue

            payload_dict = cast(dict[object, object], payload)
            if not all(isinstance(key, str) for key in payload_dict):
                errors.append("item contains non-string keys")
                continue

            typed_payload: dict[str, str] = {
                key: str(value)
                for key, value in payload_dict.items()
                if isinstance(key, str) and value is not None
            }
            validation = validate_license_form(typed_payload)
            if not validation.is_valid:
                errors.append("; ".join(issue.message for issue in validation.issues))
                continue
            records.append(to_license_record(typed_payload))

        if errors:
            QMessageBox.warning(
                self,
                "Validation warning",
                f"{len(errors)} invalid rows skipped while loading comparison snapshot.",
            )
        return records
