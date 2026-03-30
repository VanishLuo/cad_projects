from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from license_management.adapters.provider_adapter import CommandAttemptLog
from license_management.domain.models.license_record import LicenseRecord


@dataclass(slots=True, frozen=True)
class ServiceActionExecution:
    allowed: bool
    action: str
    record_id: str = ""
    host: str = ""
    detail: str = ""
    blocked_event_reason: str = ""
    blocked_message: str = ""
    success: bool = False
    operation_logs: tuple[CommandAttemptLog, ...] = ()


class FeedbackMessageProtocol(Protocol):
    @property
    def detail(self) -> str: ...


class ServiceActionDialogResultProtocol(Protocol):
    @property
    def success(self) -> bool: ...

    @property
    def feedback(self) -> FeedbackMessageProtocol: ...

    @property
    def operation_logs(self) -> tuple[CommandAttemptLog, ...]: ...


class ServiceActionBinderProtocol(Protocol):
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
    ) -> ServiceActionDialogResultProtocol: ...


class ServiceActionController:
    """Coordinate start/stop input validation and binder invocation."""

    def __init__(self, *, binder: ServiceActionBinderProtocol) -> None:
        self._binder = binder

    def execute(
        self,
        *,
        action: str,
        selected_record: LicenseRecord | None,
        username: str,
        password: str | None,
    ) -> ServiceActionExecution:
        if selected_record is None:
            return ServiceActionExecution(
                allowed=False,
                action=action,
                blocked_event_reason="no_row_selected",
                blocked_message="Please select one table row first.",
            )

        host = selected_record.server_name.strip()
        if host == "":
            return ServiceActionExecution(
                allowed=False,
                action=action,
                record_id=selected_record.record_id,
                blocked_event_reason="empty_server_name",
                blocked_message="Selected row has empty server host.",
            )

        result = self._binder.start_stop(
            action=action,
            host=host,
            username=username,
            password=password,
            provider=selected_record.provider,
            start_executable_path=selected_record.start_executable_path,
            license_file_path=selected_record.license_file_path,
            start_option_override=selected_record.start_option_override,
        )
        return ServiceActionExecution(
            allowed=True,
            action=action,
            record_id=selected_record.record_id,
            host=host,
            detail=result.feedback.detail,
            success=result.success,
            operation_logs=result.operation_logs,
        )
