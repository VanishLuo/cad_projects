from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from license_management.adapters.provider_adapter import CommandAttemptLog
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.controllers.service_action_controller import ServiceActionController


@dataclass(slots=True, frozen=True)
class _Feedback:
    detail: str


@dataclass(slots=True, frozen=True)
class _DialogResult:
    success: bool
    feedback: _Feedback
    operation_logs: tuple[CommandAttemptLog, ...] = ()


class _FakeBinder:
    def __init__(self) -> None:
        self.called_with: dict[str, object] | None = None
        self.result = _DialogResult(success=True, feedback=_Feedback(detail="ok"))

    def start_stop(
        self,
        *,
        action: str,
        host: str,
        username: str,
        password: str | None = None,
        provider: str = "",
        start_executable_path: str | None = None,
        license_file_path: str | None = None,
        start_option_override: str | None = None,
    ) -> _DialogResult:
        self.called_with = {
            "action": action,
            "host": host,
            "username": username,
            "password": password,
            "provider": provider,
            "start_executable_path": start_executable_path,
            "license_file_path": license_file_path,
            "start_option_override": start_option_override,
        }
        return self.result


def _record() -> LicenseRecord:
    return LicenseRecord(
        record_id="r1",
        server_name="host-a",
        provider="FlexNet",
        prot="27000",
        feature_name="feat",
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
        vendor="ansys",
        start_executable_path="/opt/lmgrd",
        license_file_path="/opt/license.dat",
        start_option_override="-z",
    )


def test_execute_blocks_when_no_row_selected() -> None:
    binder = _FakeBinder()
    controller = ServiceActionController(binder=binder)

    result = controller.execute(
        action="start",
        selected_record=None,
        username="ops",
        password=None,
    )

    assert result.allowed is False
    assert result.blocked_event_reason == "no_row_selected"
    assert result.blocked_message == "Please select one table row first."


def test_execute_blocks_when_server_name_empty() -> None:
    binder = _FakeBinder()
    controller = ServiceActionController(binder=binder)
    record = _record()
    record.server_name = ""

    result = controller.execute(
        action="stop",
        selected_record=record,
        username="ops",
        password="pwd",
    )

    assert result.allowed is False
    assert result.record_id == "r1"
    assert result.blocked_event_reason == "empty_server_name"


def test_execute_runs_binder_and_returns_logs() -> None:
    binder = _FakeBinder()
    binder.result = _DialogResult(
        success=False,
        feedback=_Feedback(detail="failed detail"),
        operation_logs=(
            CommandAttemptLog(
                attempt=1,
                command="cmd",
                exit_code=1,
                stdout="",
                stderr="err",
            ),
        ),
    )
    controller = ServiceActionController(binder=binder)

    result = controller.execute(
        action="start",
        selected_record=_record(),
        username="ops",
        password="pwd",
    )

    assert result.allowed is True
    assert result.success is False
    assert result.detail == "failed detail"
    assert result.host == "host-a"
    assert len(result.operation_logs) == 1
    assert binder.called_with is not None
    assert binder.called_with["provider"] == "FlexNet"

