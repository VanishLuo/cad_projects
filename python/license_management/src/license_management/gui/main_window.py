from __future__ import annotations

from datetime import date
from typing import Any, Protocol, cast

from license_management.adapters.provider_adapter import SshCommandExecutor
from license_management.application.license_feature_catalog import LicenseFeatureCatalogService
from license_management.application.remote_license_file_service import RemoteLicenseFileService
from license_management.application.record_check_service import RecordCheckIssue
from license_management.application.record_check_service import RecordCheckService
from license_management.domain.expiration_engine import ExpirationStatus
from license_management.domain.models.license_record import LicenseRecord
from license_management.domain.ports.license_repository import LicenseRepository
from license_management.gui.controllers.add_record_controller import AddRecordController
from license_management.gui.check.check_completion_controller import CheckCompletionController
from license_management.gui.check.check_completion_coordinator import (
    CheckCompletionCoordinator,
    CheckCompletionHooks,
)
from license_management.gui.check.check_publish_handler import (
    CheckPublishHandler,
    CheckPublishHooks,
)
from license_management.gui.check.check_issue_mapper import CheckIssueMapper
from license_management.gui.check.check_result_presenter import CheckResultPresenter
from license_management.gui.controllers.compare_text_controller import CompareTextController
from license_management.gui.check.check_run_controller import CheckRunController
from license_management.gui.flows.dialog_flows import DialogFlowBinder
from license_management.gui.controllers.edit_license_controller import EditLicenseController
from license_management.gui.controllers.feature_detail_controller import FeatureDetailController
from license_management.gui.presenters.log_presenter import UiLogService
from license_management.gui.composition.main_window_action_handlers import (
    MainWindowActionHandlers,
    MainWindowActionHooks,
)
from license_management.gui.composition.main_window_layout_builder import MainWindowLayoutBuilder
from license_management.gui.composition.main_window_table_helper import MainWindowTableHelper
from license_management.gui.dialogs import (
    CheckResultDialog,
    LicenseFileDetailDialog,
    RecordDialog,
)
from license_management.gui.presenters.search_filter_presenter import SearchFilterPresenter
from license_management.gui.feature_search import FeatureSearchController
from license_management.gui.controllers.import_run_controller import ImportRunController
from license_management.gui.state.models import UiLicenseRow
from license_management.gui.presenters.workspace_badge_presenter import WorkspaceBadgePresenter
from license_management.gui.controllers.service_action_controller import ServiceActionController
from license_management.gui.controllers.table_edit_controller import TableEditController
from license_management.gui.presenters.action_state_presenter import ActionStatePresenter
from license_management.gui.controllers.workspace_controller import WorkspaceController
from license_management.gui.qt_compat import (
    QComboBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    Qt,
    dialog_exec,
    dialog_is_accepted,
)
from license_management.gui.state.view_model import MainListViewModel
from license_management.infrastructure.config.table_header_config import load_table_header_config


class UiLicenseRepositoryProtocol(LicenseRepository, Protocol):
    def get_license_text_snapshot(self, record_id: str) -> tuple[str, str] | None: ...

    def upsert_license_text_snapshot(
        self,
        record_id: str,
        *,
        initial_text: str | None = None,
        current_text: str | None = None,
    ) -> None: ...


class UiContextProtocol(Protocol):
    repository: UiLicenseRepositoryProtocol
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
        self._btn_switch_workspace: QPushButton | None = None
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
        self._import_in_progress = False
        self._import_controller = ImportRunController(
            binder=self._ctx.binder,
            on_finished=self._on_import_finished,
            on_state_changed=self._on_import_state_changed,
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
        self._compare_text_controller = CompareTextController(
            repository=self._ctx.repository,
            load_remote_text=self._load_remote_text_for_record,
        )
        self._workspace_controller = WorkspaceController(
            repository=self._ctx.repository,
            feature_catalog=self._ctx.feature_catalog,
        )
        self._check_completion_controller = CheckCompletionController(
            repository=self._ctx.repository,
            feature_catalog=self._ctx.feature_catalog,
            workspace_switcher=self._workspace_controller,
        )
        self._check_publish_handler = CheckPublishHandler(
            publisher=self._check_completion_controller,
            hooks=CheckPublishHooks(
                append_log=lambda message, level: self._append_log(message, level=level),
            ),
        )
        self._check_result_presenter = CheckResultPresenter()
        self._check_completion_coordinator = CheckCompletionCoordinator(
            presenter=self._check_result_presenter,
            create_dialog=lambda scanned, grouped, parent: CheckResultDialog(
                scanned=scanned,
                grouped=grouped,
                parent=parent,
            ),
            hooks=CheckCompletionHooks(
                append_log=lambda message, level: self._append_log(message, level=level),
                log_event=lambda event, fields: self._log_event(event, **fields),
            ),
        )
        self._check_issue_mapper = CheckIssueMapper()
        self._add_record_controller = AddRecordController()
        self._table_edit_controller = TableEditController()
        self._search_filter_presenter = SearchFilterPresenter(self._ctx.search)
        self._action_state_presenter = ActionStatePresenter()
        self._workspace_badge_presenter = WorkspaceBadgePresenter()
        self._layout_builder = MainWindowLayoutBuilder()
        self._table_helper = MainWindowTableHelper(
            table=self._table,
            table_columns=self._table_columns,
            editable_columns=self._editable_table_columns,
            repository=self._ctx.repository,
        )
        self._feature_detail_controller = FeatureDetailController(
            repository=self._ctx.repository,
            feature_catalog=self._ctx.feature_catalog,
        )
        self._service_action_controller = ServiceActionController(binder=self._ctx.binder)
        self._edit_license_controller = EditLicenseController(
            repository=self._ctx.repository,
            remote_service=self._ctx.remote_license_service,
        )
        self._log_service = UiLogService(append_html=self._log.append)
        self._action_handlers = MainWindowActionHandlers(
            parent=self,
            repository=self._ctx.repository,
            binder=self._ctx.binder,
            credentials=self._ctx.ssh_credentials,
            import_controller=self._import_controller,
            compare_controller=self._compare_text_controller,
            service_action_controller=self._service_action_controller,
            edit_license_controller=self._edit_license_controller,
            selected_record=self._selected_record,
            selected_records=self._selected_records,
            hooks=MainWindowActionHooks(
                set_actions_enabled=self._set_action_buttons_enabled,
                set_feedback=self._feedback.setText,
                append_log=lambda message, level: self._append_log(message, level=level),
                log_event=lambda event, fields: self._log_event(event, **fields),
                enter_staging_workspace=lambda reason: self._enter_staging_workspace(reason=reason),
                clear_current_runtime_statuses=self._clear_current_runtime_statuses,
                refresh_after_mutation=self._refresh_after_mutation,
            ),
        )

        self._build_layout()
        self._bind_live_search()
        self._sync_runtime_statuses_from_workspace()
        self._refresh_workspace_badge()
        self._refresh_after_mutation("Ready")
        self._append_log("Application started.")
        self._log_event(
            "app_started",
            repository_type=type(self._ctx.repository).__name__,
            table_columns=list(self._table_columns),
        )

    def _on_check_state_changed(self, in_progress: bool) -> None:
        self._check_in_progress = in_progress

    def _on_import_state_changed(self, in_progress: bool) -> None:
        self._import_in_progress = in_progress

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
        layout = self._layout_builder.build(
            window=self,
            keyword=self._keyword,
            vendor=self._vendor,
            server=self._server,
            status=self._status,
            table=self._table,
            hint=self._hint,
            log=self._log,
            workspace_badge=self._workspace_badge,
            on_search=lambda: self._apply_search(trigger="manual"),
            on_reset=self._reset_filters,
            on_add=self._add_record,
            on_import=self._import_json,
            on_check=self._check_records,
            on_switch_workspace=self._toggle_workspace,
            on_delete=self._delete_selected_records,
            on_export=self._export_json,
            on_compare=self._compare_records_text,
            on_edit=self._edit_remote_license,
            on_start=lambda: self._start_stop("start"),
            on_stop=lambda: self._start_stop("stop"),
        )
        self._action_button_map = layout.action_button_map
        self._action_buttons = layout.action_buttons
        self._btn_add = layout.btn_add
        self._btn_import = layout.btn_import
        self._btn_check = layout.btn_check
        self._btn_switch_workspace = layout.btn_switch_workspace
        self._btn_delete = layout.btn_delete
        self._btn_export = layout.btn_export
        self._btn_compare = layout.btn_compare
        self._btn_edit = layout.btn_edit
        self._btn_start = layout.btn_start
        self._btn_stop = layout.btn_stop

    def _apply_search(self, *, trigger: str = "manual") -> None:
        presentation = self._search_filter_presenter.apply_search(
            trigger=trigger,
            today=date.today(),
            keyword=self._keyword.text().strip(),
            vendor=self._vendor.text().strip(),
            server_name=self._server.text().strip(),
            status=self._status.currentText().strip(),
        )
        self._render_rows(presentation.rows)
        self._hint.setText(presentation.empty_hint)
        self._log_event("search_applied", **presentation.log_fields)

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

        presentation = self._search_filter_presenter.reset_filters(
            today=date.today(), before=before
        )
        self._render_rows(presentation.rows)
        self._hint.setText(presentation.empty_hint)
        self._feedback.setText(presentation.feedback)
        self._log_event("filters_reset", **presentation.log_fields)

    def _selected_record(self) -> LicenseRecord | None:
        return self._table_helper.selected_record()

    def _selected_records(self) -> list[LicenseRecord]:
        return self._table_helper.selected_records()

    def _delete_selected_records(self) -> None:
        selected = self._selected_records()
        if not selected:
            QMessageBox.information(self, "Delete", "Please select at least one row.")
            return

        workspace = self._ctx.repository.current_workspace

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

        deleted = 0
        for record in selected:
            if self._ctx.repository.delete(record.record_id):
                self._ctx.feature_catalog.remove_for_record(record)
                deleted += 1

        self._clear_current_runtime_statuses()
        self._refresh_after_mutation(
            f"Deleted {deleted} selected record(s) in {workspace} workspace."
        )
        self._append_log(
            f"delete_selected: workspace={workspace}, requested={len(selected)}, deleted={deleted}"
        )

    def _toggle_workspace(self) -> None:
        toggled = self._workspace_controller.toggle_workspace()
        self._sync_runtime_statuses_from_workspace()
        self._refresh_workspace_badge()
        self._refresh_after_mutation(
            f"Switched to {toggled.target_workspace} workspace: rows={toggled.row_count}"
        )
        self._append_log(
            f"Workspace switched to {toggled.target_workspace}: rows={toggled.row_count}"
        )

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

        prepared = self._add_record_controller.prepare_add_payload(
            payload=payload,
            existing_records=self._ctx.repository.list_all(),
        )
        if not prepared.ok:
            QMessageBox.warning(self, "Invalid input", prepared.error_detail)
            self._feedback.setText(f"Add failed: {prepared.error_detail}")
            self._log_event("add_failed", reason="validation_failed", detail=prepared.error_detail)
            return

        self._enter_staging_workspace(reason="add_record")
        payload = prepared.payload
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
        mapped_issues = [self._check_issue_mapper.map_issue(issue) for issue in issues]
        runtime_statuses = cast(dict[str, str], runtime_statuses_raw)
        self._set_action_buttons_enabled(True)
        analysis = self._check_completion_controller.analyze(
            issues=mapped_issues,
            runtime_statuses=runtime_statuses,
        )

        current_workspace = self._ctx.repository.current_workspace
        self._runtime_statuses_by_workspace[current_workspace] = dict(runtime_statuses)
        self._sync_runtime_statuses_from_workspace()
        self._refresh_after_mutation(f"Check completed: scanned={scanned}, issues={len(issues)}")

        publish_outcome = self._check_publish_handler.publish_if_needed(
            current_workspace=current_workspace,
            runtime_statuses=runtime_statuses,
            blocked_record_ids=analysis.blocked_record_ids,
            committed_statuses=self._runtime_statuses_by_workspace.get("committed", {}),
        )
        published_rows = publish_outcome.published_rows
        self._runtime_statuses_by_workspace["committed"] = publish_outcome.committed_statuses

        self._check_result_dialog = cast(
            CheckResultDialog | None,
            self._check_completion_coordinator.coordinate(
                scanned=scanned,
                mapped_issues=mapped_issues,
                analysis=analysis,
                published_rows=published_rows,
                current_dialog=self._check_result_dialog,
                parent=self,
            ),
        )

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        presentation = self._action_state_presenter.build(
            enabled=enabled,
            workspace=self._ctx.repository.current_workspace,
            action_keys=set(self._action_button_map.keys()),
        )

        self._keyword.setEnabled(presentation.controls_enabled)
        self._vendor.setEnabled(presentation.controls_enabled)
        self._server.setEnabled(presentation.controls_enabled)
        self._status.setEnabled(presentation.controls_enabled)
        self._table.setEnabled(presentation.controls_enabled)

        for key, button in self._action_button_map.items():
            button.setEnabled(presentation.button_enabled.get(key, True))
            button.setToolTip(presentation.button_tooltips.get(key, ""))

        if not presentation.table_editable:
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
        decision = self._table_edit_controller.apply(
            record=record,
            column_name=column_name,
            value=value,
        )
        if decision.action == "unchanged":
            return
        if decision.action == "invalid":
            if decision.log_message != "":
                self._append_log(decision.log_message, level=decision.log_level)
            self._refresh_after_mutation(decision.user_feedback)
            return

        updated = decision.updated_record
        if updated is None:
            return
        self._ctx.repository.upsert(updated)
        self._clear_current_runtime_statuses()
        self._refresh_after_mutation(f"Table updated: record_id={record_id}, field={column_name}")
        self._append_log(
            f"table_edit: record_id={record_id} field={column_name} value={value}",
            level="info",
        )

    def _import_json(self) -> None:
        self._action_handlers.run_import()

    def _on_import_finished(self, result_raw: object, report_raw: object) -> None:
        self._action_handlers.run_import_finished(result_raw, report_raw)

    def _export_json(self) -> None:
        self._action_handlers.run_export()

    def _compare_records_text(self) -> None:
        self._action_handlers.run_compare_records_text()

    def _start_stop(self, action: str) -> None:
        self._action_handlers.run_start_stop(action)

    def _edit_remote_license(self) -> None:
        self._action_handlers.run_edit_remote_license()

    def _load_remote_text_for_record(self, record: LicenseRecord) -> str | None:
        username = self._ctx.ssh_credentials.username.strip()
        password = self._ctx.ssh_credentials.password or None
        loaded, error = self._edit_license_controller.load_remote_text(
            record=record,
            username=username,
            password=password,
        )
        if loaded is None:
            if error != "missing host, remote path, or username":
                self._append_log(f"compare_load_failed: record_id={record.record_id} {error}")
            return None
        return loaded

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

        detail = self._feature_detail_controller.build_for_record_id(record_id)
        if detail.selected_record is None and detail.reason == "record_not_found":
            self._log_event(
                "row_double_click_ignored", reason="record_not_found", record_id=record_id
            )
            return

        license_file_path = detail.license_file_path
        if detail.sync_license_missing:
            self._log_event(
                "row_double_click_license_file_not_found",
                record_id=record_id,
                license_file_path=(license_file_path or "(empty)"),
            )

        if not detail.found:
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
            rows=list(detail.grouped_rows),
            record_count=detail.record_count,
            parent=self,
        )
        dialog_exec(dialog)
        self._log_event(
            "row_double_click_opened_detail",
            record_id=record_id,
            license_file_path=(license_file_path or "(empty)"),
            feature_expiry_groups=len(detail.grouped_rows),
            record_count=detail.record_count,
        )

    def _refresh_after_mutation(self, feedback: str) -> None:
        self._ctx.view_model.load(self._ctx.repository.list_all(), today=date.today())
        self._render_rows(self._ctx.view_model.rows)
        self._hint.setText(self._ctx.view_model.empty_state_hint())
        self._feedback.setText(feedback)
        self._refresh_workspace_badge()
        if not self._check_in_progress and not self._import_in_progress:
            self._set_action_buttons_enabled(True)

    def closeEvent(self, a0: Any) -> None:
        self._check_controller.shutdown()
        self._import_controller.shutdown()
        super().closeEvent(a0)

    def _refresh_workspace_badge(self) -> None:
        workspace = self._ctx.repository.current_workspace
        view_state = self._workspace_badge_presenter.present(workspace)
        self._workspace_badge.setText(view_state.text)
        self._workspace_badge.setStyleSheet(view_state.style_sheet)

    def _enter_staging_workspace(self, *, reason: str) -> None:
        changed = self._workspace_controller.enter_staging_workspace()
        if changed:
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
        self._log_service.append(message, level=level)

    def _log_event(self, event: str, **fields: object) -> None:
        self._log_service.log_event(event, **fields)

    def _render_rows(self, rows: tuple[UiLicenseRow, ...]) -> None:
        self._is_rendering_table = True
        try:
            self._table_helper.render_rows(rows)
        finally:
            self._is_rendering_table = False
