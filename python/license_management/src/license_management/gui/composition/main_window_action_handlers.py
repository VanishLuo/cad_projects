from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, cast

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.flows.dialog_flows import DialogResult
from license_management.gui.dialogs import RemoteLicenseEditorDialog, TextDiffDialog
from license_management.gui.qt_compat import (
    QFileDialog,
    QMessageBox,
    dialog_exec,
    dialog_is_accepted,
)


class RepositoryProtocol(Protocol):
    @property
    def current_workspace(self) -> str: ...

    def list_all(self) -> list[LicenseRecord]: ...


class CredentialsProtocol(Protocol):
    username: str
    password: str


class BinderProtocol(Protocol):
    def export_records(self, *, file_path: Path, records: list[LicenseRecord]) -> Any: ...


class ImportControllerProtocol(Protocol):
    @property
    def in_progress(self) -> bool: ...

    def start(self, file_paths: list[Path]) -> bool: ...


class CompareControllerProtocol(Protocol):
    def build_payload(
        self,
        *,
        workspace: str,
        selected_records: list[LicenseRecord],
    ) -> tuple[Any | None, str | None]: ...


class ServiceActionControllerProtocol(Protocol):
    def execute(
        self,
        *,
        action: str,
        selected_record: LicenseRecord | None,
        username: str,
        password: str | None,
    ) -> Any: ...


class EditLicenseControllerProtocol(Protocol):
    def prepare_edit(
        self,
        *,
        record: LicenseRecord,
        username: str,
        password: str | None,
    ) -> Any: ...

    def save_edited_text(
        self,
        *,
        session: Any,
        username: str,
        password: str | None,
        updated_text: str,
    ) -> Any: ...


@dataclass(slots=True)
class MainWindowActionHooks:
    set_actions_enabled: Callable[[bool], None]
    set_feedback: Callable[[str], None]
    append_log: Callable[[str, str], None]
    log_event: Callable[[str, dict[str, object]], None]
    enter_staging_workspace: Callable[[str], None]
    clear_current_runtime_statuses: Callable[[], None]
    refresh_after_mutation: Callable[[str], None]


class MainWindowActionHandlers:
    """Concrete handlers for import/export/compare/start-stop/edit flows."""

    def __init__(
        self,
        *,
        parent: Any,
        repository: RepositoryProtocol,
        binder: BinderProtocol,
        credentials: CredentialsProtocol,
        import_controller: ImportControllerProtocol,
        compare_controller: CompareControllerProtocol,
        service_action_controller: ServiceActionControllerProtocol,
        edit_license_controller: EditLicenseControllerProtocol,
        selected_record: Callable[[], LicenseRecord | None],
        selected_records: Callable[[], list[LicenseRecord]],
        hooks: MainWindowActionHooks,
    ) -> None:
        self._parent = parent
        self._repository = repository
        self._binder = binder
        self._credentials = credentials
        self._import_controller = import_controller
        self._compare_controller = compare_controller
        self._service_action_controller = service_action_controller
        self._edit_license_controller = edit_license_controller
        self._selected_record = selected_record
        self._selected_records = selected_records
        self._hooks = hooks

    def run_import(self) -> None:
        if self._import_controller.in_progress:
            QMessageBox.information(
                self._parent, "Import running", "Import is still running, please wait."
            )
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self._parent,
            "Select import files",
            str(Path.cwd()),
            "Import Files (*.json *.xlsx *.xlsm)",
        )
        if not file_paths:
            self._hooks.log_event("import_cancelled", {})
            return

        self._hooks.log_event("import_requested", {"files": file_paths})
        self._hooks.enter_staging_workspace("import")
        paths = [Path(path) for path in file_paths]
        self._hooks.set_actions_enabled(False)
        self._hooks.set_feedback(f"Import started: files={len(paths)}")
        self._hooks.append_log(f"Import request: {len(paths)} file(s).", "info")
        started = self._import_controller.start(paths)
        if not started:
            self._hooks.set_actions_enabled(True)
            QMessageBox.information(
                self._parent, "Import running", "Import is still running, please wait."
            )

    def run_import_finished(self, result_raw: object, report_raw: object) -> None:
        result = cast(DialogResult, result_raw)
        self._hooks.set_actions_enabled(True)

        detail = result.feedback.detail
        typed_report = cast(Any, report_raw)
        if typed_report is not None and typed_report.errors:
            detail = f"{detail} | errors={len(typed_report.errors)}"
            self._hooks.append_log(
                f"Import completed with {len(typed_report.errors)} error(s).",
                "info",
            )
            for message in typed_report.errors:
                self._hooks.append_log(f"ERROR: {message}", "info")
        elif typed_report is not None:
            self._hooks.append_log(
                "Import completed: "
                f"total={typed_report.total}, succeeded={typed_report.succeeded}, "
                f"failed={typed_report.failed}, deduplicated={typed_report.deduplicated}",
                "info",
            )
            if typed_report.warnings:
                max_warning_lines = 80
                for warning in typed_report.warnings[:max_warning_lines]:
                    self._hooks.append_log(f"WARNING: {warning}", "info")
                omitted = len(typed_report.warnings) - max_warning_lines
                if omitted > 0:
                    self._hooks.append_log(
                        f"WARNING: omitted {omitted} additional warning line(s) to keep log readable.",
                        "info",
                    )

        self._hooks.log_event(
            "import_completed",
            {
                "success": result.success,
                "detail": detail,
                "total": (typed_report.total if typed_report is not None else 0),
                "succeeded": (typed_report.succeeded if typed_report is not None else 0),
                "failed": (typed_report.failed if typed_report is not None else 0),
                "deduplicated": (typed_report.deduplicated if typed_report is not None else 0),
                "warnings": (len(typed_report.warnings) if typed_report is not None else 0),
                "errors": (len(typed_report.errors) if typed_report is not None else 0),
            },
        )
        self._hooks.clear_current_runtime_statuses()
        self._hooks.refresh_after_mutation(detail)

    def run_export(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self._parent,
            "Export records",
            str(Path.cwd() / "exported_licenses.xlsx"),
            "Export Files (*.json *.xlsx *.xlsm)",
        )
        if not output:
            self._hooks.log_event("export_cancelled", {})
            return

        output_path = Path(output)
        if output_path.suffix.strip() == "":
            output_path = output_path.with_suffix(".xlsx")
            output = str(output_path)

        record_count = len(self._repository.list_all())
        self._hooks.log_event("export_requested", {"output": output, "record_count": record_count})
        message = self._binder.export_records(
            file_path=output_path,
            records=self._repository.list_all(),
        )
        self._hooks.set_feedback(message.feedback.detail)
        self._hooks.log_event(
            "export_completed",
            {
                "success": message.success,
                "output": output,
                "detail": message.feedback.detail,
            },
        )

    def run_compare_records_text(self) -> None:
        workspace = self._repository.current_workspace
        if workspace != "committed":
            QMessageBox.information(
                self._parent,
                "Compare",
                "Compare is only available in committed workspace.",
            )
            return

        selected = self._selected_records()
        if len(selected) == 0:
            QMessageBox.information(self._parent, "Compare", "Please select one or two rows first.")
            return
        if len(selected) > 2:
            QMessageBox.information(self._parent, "Compare", "Please select at most two rows.")
            return

        payload, error_message = self._compare_controller.build_payload(
            workspace=workspace,
            selected_records=selected,
        )
        if error_message is not None:
            QMessageBox.information(self._parent, "Compare", error_message)
            return
        if payload is None:
            return

        dialog = TextDiffDialog(
            title="Record Text Compare",
            summary=f"{payload.left_title} vs {payload.right_title}",
            left_title=payload.left_title,
            right_title=payload.right_title,
            left_text=payload.left_text,
            right_text=payload.right_text,
            parent=self._parent,
        )
        dialog_exec(dialog)
        self._hooks.set_feedback("Text compare completed.")

    def run_start_stop(self, action: str) -> None:
        result = self._service_action_controller.execute(
            action=action,
            selected_record=self._selected_record(),
            username=self._credentials.username,
            password=self._credentials.password or None,
        )
        if not result.allowed:
            blocked_message = result.blocked_message
            self._hooks.append_log(f"service_action_blocked: {blocked_message}", "error")
            self._hooks.set_feedback(blocked_message)
            self._hooks.log_event(
                "service_action_blocked",
                {
                    "action": action,
                    "reason": result.blocked_event_reason,
                    "record_id": result.record_id,
                },
            )
            return

        self._hooks.append_log(
            f"[{action}] {result.detail}",
            ("success" if result.success else "error"),
        )
        self._hooks.set_feedback(result.detail)
        if result.operation_logs:
            self._hooks.append_log(
                f"[{action}] host={result.host} attempts={len(result.operation_logs)}",
                "info",
            )
            for log in result.operation_logs:
                command_level = "success" if log.exit_code == 0 else "error"
                self._hooks.append_log(
                    f"  attempt={log.attempt} exit_code={log.exit_code} command={log.command}",
                    command_level,
                )
                stdout_text = log.stdout.strip()
                stderr_text = log.stderr.strip()
                if stdout_text:
                    self._hooks.append_log(f"  stdout:\n{stdout_text}", "success")
                if stderr_text:
                    self._hooks.append_log(f"  stderr:\n{stderr_text}", "error")
        self._hooks.log_event(
            "service_action",
            {
                "action": action,
                "success": result.success,
                "host": result.host,
                "record_id": result.record_id,
                "detail": result.detail,
            },
        )

    def run_edit_remote_license(self) -> None:
        selected = self._selected_record()
        if selected is None:
            self._hooks.append_log("edit_blocked: Please select one table row first.", "error")
            return

        username = self._credentials.username.strip()
        password = self._credentials.password or None
        prepare = self._edit_license_controller.prepare_edit(
            record=selected,
            username=username,
            password=password,
        )
        if not prepare.ok:
            if prepare.error.startswith("Selected row has empty"):
                self._hooks.append_log(f"edit_blocked: {prepare.error}", "error")
            else:
                self._hooks.append_log(f"[edit] failed: {prepare.error}", "error")
            return

        session = prepare.session
        if session is None:
            self._hooks.append_log("[edit] failed: missing edit session", "error")
            return

        self._hooks.append_log(
            f"[edit] loading remote file: host={session.host} path={session.remote_path}",
            "info",
        )

        if prepare.warning.strip() != "":
            self._hooks.append_log(
                f"[edit] server identity unavailable: {prepare.warning}",
                "info",
            )

        dialog = RemoteLicenseEditorDialog(
            host=session.host,
            remote_path=session.remote_path,
            content=session.original_text,
            server_hostname=session.server_hostname,
            server_mac=session.server_mac,
            parent=self._parent,
        )
        if not dialog_is_accepted(dialog_exec(dialog)):
            self._hooks.append_log("[edit] cancelled by user.", "info")
            return

        save_result = self._edit_license_controller.save_edited_text(
            session=session,
            username=username,
            password=password,
            updated_text=dialog.text_content(),
        )
        if save_result.ok and save_result.no_changes:
            self._hooks.append_log("[edit] no changes detected; skipped upload.", "info")
            return
        if save_result.ok:
            self._hooks.append_log(
                f"[edit] saved remote file successfully: host={session.host} path={session.remote_path}",
                "success",
            )
        else:
            self._hooks.append_log(f"[edit] failed: {save_result.error}", "error")
