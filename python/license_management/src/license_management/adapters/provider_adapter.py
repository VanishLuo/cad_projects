from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SshCommandExecutor(Protocol):
    """Executes one remote command over SSH and returns process result."""

    def run(
        self,
        *,
        host: str,
        username: str,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]: ...


@dataclass(slots=True, frozen=True)
class CommandAttemptLog:
    """Audit trail for one command execution attempt."""

    attempt: int
    command: str
    exit_code: int
    stdout: str
    stderr: str


@dataclass(slots=True, frozen=True)
class ProviderOperationResult:
    """Result of provider-level start/stop operation."""

    provider: str
    action: str
    host: str
    username: str
    succeeded: bool
    attempts: int
    timeout_seconds: int
    command_logs: tuple[CommandAttemptLog, ...]
    rollback_attempted: bool = False
    rollback_succeeded: bool | None = None
