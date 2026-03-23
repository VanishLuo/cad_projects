from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from license_management.gui.qt_compat import (
    QApplication,
    QComboBox,
    QColor,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
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
    QVBoxLayout,
    QWidget,
    app_exec,
    dialog_exec,
    dialog_is_accepted,
)

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.adapters.license_file_uploader import (
    LicenseFileUploader,
    ScpLicenseFileUploader,
)
from license_management.adapters.provider_adapter import SshCommandExecutor
from license_management.application.compare_service import CrossTargetCompareService
from license_management.application.import_pipeline import ImportPipelineService
from license_management.domain.expiration_engine import ExpirationStatus
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.dialog_flows import DialogFlowBinder
from license_management.gui.feature_search import FeatureSearchController
from license_management.gui.models import FeedbackCenter, UiLicenseRow
from license_management.gui.validation_feedback import to_license_record, validate_license_form
from license_management.gui.view_model import MainListViewModel
from license_management.infrastructure.config.table_header_config import load_table_header_config
from license_management.infrastructure.repositories.sqlite_license_repository import (
    SqliteLicenseRepository,
)


class _NoopSshExecutor(SshCommandExecutor):
    """Safe default executor for GUI demo mode without real SSH dependency."""

    def run(
        self,
        *,
        host: str,
        username: str,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        _ = timeout_seconds
        return (
            1,
            "",
            f"SSH executor is not configured (host={host}, user={username}, command={command})",
        )


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    """Resolve Qt enum members across PyQt5/PyQt6 enum styles."""

    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)


@dataclass(slots=True)
class _UiContext:
    repository: SqliteLicenseRepository
    feedback: FeedbackCenter
    view_model: MainListViewModel
    search: FeatureSearchController
    binder: DialogFlowBinder
    uploader: LicenseFileUploader


class RecordDialog(QDialog):
    """Upload-only dialog for adding one license file record."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("RecordDialog")
        self.setWindowTitle("Add License File")
        self.setMinimumSize(560, 260)
        self.resize(620, 320)

        self._server_name = QLineEdit("")
        self._local_license_file_path = QLineEdit("")
        self._remote_upload_dir = QLineEdit("/opt/licenses")

        form = QFormLayout()
        form.setLabelAlignment(
            _qt_enum_member(Qt, "AlignmentFlag", "AlignRight")
            | _qt_enum_member(Qt, "AlignmentFlag", "AlignVCenter")
        )
        form.addRow("Server IP/Host", self._server_name)

        browse_row = QHBoxLayout()
        browse_row.setContentsMargins(0, 0, 0, 0)
        browse_row.addWidget(self._local_license_file_path)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_local_license_file)
        browse_row.addWidget(btn_browse)

        browse_wrap = QWidget()
        browse_wrap.setLayout(browse_row)
        form.addRow("Local License File", browse_wrap)
        form.addRow("Remote Upload Dir", self._remote_upload_dir)

        ok_button = _qt_enum_member(QDialogButtonBox, "StandardButton", "Ok")
        cancel_button = _qt_enum_member(QDialogButtonBox, "StandardButton", "Cancel")
        buttons = QDialogButtonBox(ok_button | cancel_button)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self._ok_button = buttons.button(ok_button)
        if self._ok_button is not None:
            self._ok_button.setObjectName("DialogOkButton")
        self._required_inputs = (
            self._server_name,
            self._local_license_file_path,
            self._remote_upload_dir,
        )

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
            self._local_license_file_path.setText(selected)

    def payload(self) -> dict[str, str]:
        return {
            "server_name": self._server_name.text().strip(),
            "local_license_file_path": self._local_license_file_path.text().strip(),
            "remote_upload_dir": self._remote_upload_dir.text().strip(),
        }


class MainWindow(QMainWindow):
    def __init__(self, context: _UiContext) -> None:
        super().__init__()
        self._ctx = context
        self.setWindowTitle("License Management")
        self.resize(1440, 900)

        self._keyword = QLineEdit()
        self._vendor = QLineEdit()
        self._server = QLineEdit()
        self._status = QComboBox()
        self._status.addItems(["", *(status.value for status in ExpirationStatus)])

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
        # Allow only single row selection to simplify edit/delete actions. 仅允许单行选择以简化编辑/删除操作。
        self._table.setSelectionMode(
            _qt_enum_member(QTableWidget, "SelectionMode", "SingleSelection")
        )
        # Keep table as read-only display; modifications should go through dialog workflows.
        self._table.setEditTriggers(_qt_enum_member(QTableWidget, "EditTrigger", "NoEditTriggers"))
        self._table.setAlternatingRowColors(True)

        self._hint = QLabel("")
        self._feedback = QLabel("Ready")
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Import and runtime logs will appear here.")

        self._build_layout()
        self._bind_live_search()
        self._refresh_after_mutation("Ready")
        self._append_log("Application started.")

    def _bind_live_search(self) -> None:
        # Live filtering: update results while user types or changes status.
        self._keyword.textChanged.connect(self._on_search_text_changed)
        self._server.textChanged.connect(self._on_search_text_changed)
        self._vendor.textChanged.connect(self._on_search_text_changed)
        self._status.currentIndexChanged.connect(self._on_status_changed)

    def _on_search_text_changed(self, _text: str) -> None:
        self._apply_search()

    def _on_status_changed(self, _index: int) -> None:
        self._apply_search()

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
        btn_search.clicked.connect(self._apply_search)
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
        btn_import = QPushButton("Import Files")
        btn_import.clicked.connect(self._import_json)
        btn_export = QPushButton("Export JSON")
        btn_export.clicked.connect(self._export_json)
        btn_compare = QPushButton("Compare Snapshot")
        btn_compare.clicked.connect(self._compare_snapshot)
        btn_start = QPushButton("Start Service")
        btn_start.clicked.connect(lambda: self._start_stop("start"))
        btn_stop = QPushButton("Stop Service")
        btn_stop.clicked.connect(lambda: self._start_stop("stop"))

        for button in [btn_add, btn_import, btn_export, btn_compare, btn_start, btn_stop]:
            action_row.addWidget(button)
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

        layout = QVBoxLayout()
        layout.addWidget(search_box, 2)
        layout.addLayout(action_row)
        layout.addWidget(records_box, 6)
        layout.addWidget(log_box, 2)
        layout.addWidget(self._feedback)
        root.setLayout(layout)

    def _apply_search(self) -> None:
        keyword = self._keyword.text().strip()
        result = self._ctx.search.search(
            today=date.today(),
            keyword=keyword,
            vendor=self._vendor.text().strip(),
            server_name=self._server.text().strip(),
            status=self._status.currentText().strip(),
        )
        self._render_rows(result.rows)
        self._hint.setText(result.empty_hint)

    def _reset_filters(self) -> None:
        self._keyword.clear()
        self._vendor.clear()
        self._server.clear()
        self._status.setCurrentIndex(0)

        result = self._ctx.search.reset(today=date.today())
        self._render_rows(result.rows)
        self._hint.setText(result.empty_hint)
        self._feedback.setText("Filters reset.")

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

    def _add_record(self) -> None:
        dialog = RecordDialog(self)
        if not dialog_is_accepted(dialog_exec(dialog)):
            return

        payload = dialog.payload()
        upload_result = self._ctx.uploader.upload(
            local_file_path=payload.get("local_license_file_path", ""),
            host=payload.get("server_name", ""),
            remote_dir=payload.get("remote_upload_dir", ""),
            username="operator",
            timeout_seconds=60,
        )
        if not upload_result.success:
            QMessageBox.warning(self, "Upload failed", upload_result.detail)
            self._feedback.setText(f"Upload failed: {upload_result.detail}")
            return

        payload["license_file_path"] = upload_result.remote_file_path
        record_id = self._build_record_id(
            server_name=payload.get("server_name", ""),
            license_file_path=payload["license_file_path"],
        )
        record = LicenseRecord(
            record_id=record_id,
            server_name=payload.get("server_name", ""),
            provider="FlexNet",
            feature_name="",
            process_name="",
            expires_on=date.today(),
            vendor="",
            start_executable_path="",
            license_file_path=payload["license_file_path"],
            start_option_override="",
        )
        self._ctx.repository.upsert(record)
        self._refresh_after_mutation(f"Uploaded and saved: {record.license_file_path}")

    def _build_record_id(self, *, server_name: str, license_file_path: str) -> str:
        server = server_name.strip().lower().replace(" ", "_") or "unknown"
        remote = license_file_path.strip().replace("\\", "/")
        return f"{server}:{remote}"

    def _import_json(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select import files",
            str(Path.cwd()),
            "Import Files (*.json *.xlsx *.xlsm)",
        )
        if not file_paths:
            return

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
        self._refresh_after_mutation(detail)

    def _export_json(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self,
            "Export records",
            str(Path.cwd() / "exported_licenses.json"),
            "JSON Files (*.json)",
        )
        if not output:
            return

        message = self._ctx.binder.export_records(
            file_path=Path(output),
            records=self._ctx.repository.list_all(),
        )
        self._feedback.setText(message.feedback.detail)

    def _compare_snapshot(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select comparison JSON",
            str(Path.cwd()),
            "JSON Files (*.json)",
        )
        if not selected:
            return

        right_records = self._load_records_from_json(Path(selected))
        if right_records is None:
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
        self._feedback.setText(result.feedback.detail)

    def _start_stop(self, action: str) -> None:
        selected = self._selected_record()
        host = (
            selected.server_name if selected is not None else self._server.text().strip()
        ) or "localhost"
        username = "operator"
        provider = selected.provider if selected is not None else ""
        start_executable_path = selected.start_executable_path if selected is not None else None
        license_file_path = selected.license_file_path if selected is not None else None
        start_option_override = selected.start_option_override if selected is not None else None
        result = self._ctx.binder.start_stop(
            action=action,
            host=host,
            username=username,
            provider=provider,
            start_executable_path=start_executable_path,
            license_file_path=license_file_path,
            start_option_override=start_option_override,
        )
        level = "Information" if result.success else "Warning"
        QMessageBox.information(self, level, result.feedback.detail)
        self._feedback.setText(result.feedback.detail)

    def _refresh_after_mutation(self, feedback: str) -> None:
        self._ctx.view_model.load(self._ctx.repository.list_all(), today=date.today())
        self._render_rows(self._ctx.view_model.rows)
        self._hint.setText(self._ctx.view_model.empty_state_hint())
        self._feedback.setText(feedback)

    def _append_log(self, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log.append(f"[{stamp}] {message}")

    def _render_rows(self, rows: tuple[UiLicenseRow, ...]) -> None:
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [str(getattr(row, column, "")) for column in self._table_columns]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if row.highlight_level == "danger":
                    item.setBackground(QColor("#f66"))
                elif row.highlight_level == "warning":
                    item.setBackground(QColor("#f6d365"))
                self._table.setItem(row_index, col_index, item)

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


def build_context() -> _UiContext:
    project_root = Path(__file__).resolve().parents[3]
    db_path = project_root / "data" / "license_management.sqlite3"
    repository = SqliteLicenseRepository(db_path)
    feedback = FeedbackCenter()
    view_model = MainListViewModel(warning_days=30)
    search = FeatureSearchController(view_model)
    import_service = ImportPipelineService(repository)
    compare_service = CrossTargetCompareService()
    flexnet = FlexNetAdapter(executor=_NoopSshExecutor())
    uploader = ScpLicenseFileUploader()
    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
        import_service=import_service,
        flexnet_adapter=flexnet,
        compare_service=compare_service,
    )
    return _UiContext(
        repository=repository,
        feedback=feedback,
        view_model=view_model,
        search=search,
        binder=binder,
        uploader=uploader,
    )


def run_gui() -> int:
    app = QApplication.instance()
    if app is None or not isinstance(app, QApplication):
        app = QApplication([])
    _apply_stylesheet(app)
    window = MainWindow(build_context())
    window.show()
    return app_exec(app)


def _apply_stylesheet(app: QApplication) -> None:
    style_path = Path(__file__).with_name("app.qss")
    try:
        stylesheet = style_path.read_text(encoding="utf-8")
    except OSError:
        return

    app.setStyleSheet(stylesheet)
