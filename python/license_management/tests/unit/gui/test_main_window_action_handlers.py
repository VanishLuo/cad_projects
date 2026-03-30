from __future__ import annotations
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportArgumentType=false

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pytest import MonkeyPatch

from license_management.adapters.provider_adapter import CommandAttemptLog
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.composition.main_window_action_handlers import (
    MainWindowActionHandlers,
    MainWindowActionHooks,
)


@dataclass
class _Feedback:
    detail: str


@dataclass
class _Message:
    success: bool
    feedback: _Feedback


@dataclass
class _ImportReport:
    total: int
    succeeded: int
    failed: int
    deduplicated: int
    warnings: list[str]
    errors: list[str]


@dataclass
class _ComparePayload:
    left_title: str
    right_title: str
    left_text: str
    right_text: str


class _Repo:
    def __init__(self) -> None:
        self.current_workspace = "committed"
        self.rows = [
            LicenseRecord(
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
            )
        ]

    def list_all(self) -> list[LicenseRecord]:
        return list(self.rows)


class _Binder:
    def __init__(self) -> None:
        self.last_export_path: Path | None = None

    def export_records(self, *, file_path: Path, records: list[LicenseRecord]) -> _Message:
        _ = records
        self.last_export_path = file_path
        return _Message(success=True, feedback=_Feedback(detail="ok"))


class _ImportController:
    def __init__(self) -> None:
        self.in_progress = False
        self.started_paths: list[Path] = []

    def start(self, file_paths: list[Path]) -> bool:
        self.started_paths = list(file_paths)
        return True


class _CompareController:
    def build_payload(
        self,
        *,
        workspace: str,
        selected_records: list[LicenseRecord],
    ) -> tuple[_ComparePayload | None, str | None]:
        _ = (workspace, selected_records)
        return _ComparePayload("L", "R", "left", "right"), None


class _ServiceActionResult:
    def __init__(self) -> None:
        self.allowed = True
        self.blocked_message = ""
        self.blocked_event_reason = ""
        self.record_id = "r1"
        self.detail = "done"
        self.success = True
        self.host = "srv-a"
        self.operation_logs = (
            CommandAttemptLog(attempt=1, command="cmd", exit_code=0, stdout="ok", stderr=""),
        )


class _ServiceActionController:
    def __init__(self) -> None:
        self.result = _ServiceActionResult()

    def execute(
        self,
        *,
        action: str,
        selected_record: LicenseRecord | None,
        username: str,
        password: str | None,
    ) -> _ServiceActionResult:
        _ = (action, selected_record, username, password)
        return self.result


class _EditSession:
    def __init__(self) -> None:
        self.host = "srv-a"
        self.remote_path = "/opt/license.dat"
        self.original_text = "old"
        self.server_hostname = "host-a"
        self.server_mac = "11:22:33:44:55:66"


class _PrepareResult:
    def __init__(self) -> None:
        self.ok = True
        self.session = _EditSession()
        self.warning = ""
        self.error = ""


class _SaveResult:
    def __init__(self) -> None:
        self.ok = True
        self.no_changes = False
        self.error = ""


class _EditController:
    def prepare_edit(
        self, *, record: LicenseRecord, username: str, password: str | None
    ) -> _PrepareResult:
        _ = (record, username, password)
        return _PrepareResult()

    def save_edited_text(
        self,
        *,
        session: _EditSession,
        username: str,
        password: str | None,
        updated_text: str,
    ) -> _SaveResult:
        _ = (session, username, password, updated_text)
        return _SaveResult()


class _Credentials:
    username = "ops"
    password = "pwd"


def _record() -> LicenseRecord:
    return LicenseRecord(
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
    )


def _make_hooks(
    logs: list[str], events: list[tuple[str, dict[str, object]]], feedback: list[str]
) -> MainWindowActionHooks:
    return MainWindowActionHooks(
        set_actions_enabled=lambda _enabled: None,
        set_feedback=lambda text: feedback.append(text),
        append_log=lambda message, _level: logs.append(message),
        log_event=lambda event, fields: events.append((event, fields)),
        enter_staging_workspace=lambda _reason: None,
        clear_current_runtime_statuses=lambda: None,
        refresh_after_mutation=lambda _detail: None,
    )


def test_run_export_and_compare(monkeypatch: MonkeyPatch) -> None:
    logs: list[str] = []
    events: list[tuple[str, dict[str, object]]] = []
    feedback: list[str] = []

    import license_management.gui.composition.main_window_action_handlers as mod

    class _FakeTextDiffDialog:
        def __init__(self, **kwargs: object) -> None:
            _ = kwargs

    def _fake_save_file_name(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return ("x", "")

    def _fake_dialog_exec(_dialog: object) -> int:
        return 0

    monkeypatch.setattr(mod.QFileDialog, "getSaveFileName", _fake_save_file_name)
    monkeypatch.setattr(mod, "dialog_exec", _fake_dialog_exec)
    monkeypatch.setattr(mod, "TextDiffDialog", _FakeTextDiffDialog)

    handler = MainWindowActionHandlers(
        parent=object(),
        repository=_Repo(),
        binder=_Binder(),
        credentials=_Credentials(),
        import_controller=_ImportController(),
        compare_controller=_CompareController(),
        service_action_controller=_ServiceActionController(),
        edit_license_controller=_EditController(),
        selected_record=_record,
        selected_records=lambda: [_record()],
        hooks=_make_hooks(logs, events, feedback),
    )

    handler.run_export()
    handler.run_compare_records_text()

    assert any(name == "export_requested" for name, _ in events)
    assert feedback[-1] == "Text compare completed."


def test_run_import_and_finish(monkeypatch: MonkeyPatch) -> None:
    logs: list[str] = []
    events: list[tuple[str, dict[str, object]]] = []
    feedback: list[str] = []

    import license_management.gui.composition.main_window_action_handlers as mod

    def _fake_open_file_names(*_args: object, **_kwargs: object) -> tuple[list[str], str]:
        return (["a.json", "b.xlsx"], "")

    monkeypatch.setattr(
        mod.QFileDialog,
        "getOpenFileNames",
        _fake_open_file_names,
    )

    controller = _ImportController()
    handler = MainWindowActionHandlers(
        parent=object(),
        repository=_Repo(),
        binder=_Binder(),
        credentials=_Credentials(),
        import_controller=controller,
        compare_controller=_CompareController(),
        service_action_controller=_ServiceActionController(),
        edit_license_controller=_EditController(),
        selected_record=_record,
        selected_records=lambda: [_record()],
        hooks=_make_hooks(logs, events, feedback),
    )

    handler.run_import()
    handler.run_import_finished(
        _Message(success=True, feedback=_Feedback(detail="import ok")),
        _ImportReport(total=2, succeeded=2, failed=0, deduplicated=0, warnings=["w1"], errors=[]),
    )

    assert len(controller.started_paths) == 2
    assert any(name == "import_completed" for name, _ in events)


def test_run_service_and_edit_paths(monkeypatch: MonkeyPatch) -> None:
    logs: list[str] = []
    events: list[tuple[str, dict[str, object]]] = []
    feedback: list[str] = []

    import license_management.gui.composition.main_window_action_handlers as mod

    class _FakeRemoteLicenseEditorDialog:
        def __init__(self, **kwargs: object) -> None:
            _ = kwargs

        def text_content(self) -> str:
            return "updated"

    def _fake_dialog_exec(_dialog: object) -> int:
        return 1

    def _fake_dialog_is_accepted(_result: object) -> bool:
        return True

    monkeypatch.setattr(mod, "dialog_exec", _fake_dialog_exec)
    monkeypatch.setattr(mod, "dialog_is_accepted", _fake_dialog_is_accepted)
    monkeypatch.setattr(mod, "RemoteLicenseEditorDialog", _FakeRemoteLicenseEditorDialog)

    handler = MainWindowActionHandlers(
        parent=object(),
        repository=_Repo(),
        binder=_Binder(),
        credentials=_Credentials(),
        import_controller=_ImportController(),
        compare_controller=_CompareController(),
        service_action_controller=_ServiceActionController(),
        edit_license_controller=_EditController(),
        selected_record=_record,
        selected_records=lambda: [_record()],
        hooks=_make_hooks(logs, events, feedback),
    )

    handler.run_start_stop("start")
    handler.run_edit_remote_license()

    assert any(name == "service_action" for name, _ in events)
    assert any("saved remote file successfully" in line for line in logs)
