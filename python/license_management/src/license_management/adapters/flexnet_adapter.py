from __future__ import annotations

from license_management.adapters.provider_adapter import (
    CommandAttemptLog,
    ProviderOperationResult,
    SshCommandExecutor,
)


class FlexNetAdapter:
    """Runs FlexNet start/stop operations on remote host through SSH."""

    provider_name = "FlexNet"

    def __init__(
        self,
        executor: SshCommandExecutor,
        *,
        lmgrd_path: str = "lmgrd",
        lmutil_path: str = "lmutil",
        license_file_path: str = "license.dat",
        timeout_seconds: int = 30,
        retry_times: int = 1,
    ) -> None:
        self._executor = executor
        self._lmgrd_path = lmgrd_path
        self._lmutil_path = lmutil_path
        self._license_file_path = license_file_path
        self._timeout_seconds = timeout_seconds
        self._retry_times = retry_times

    def start(self, *, host: str, username: str) -> ProviderOperationResult:
        start_command = f"{self._lmgrd_path} -c {self._license_file_path}"
        start_logs, start_succeeded = self._run_with_retry(
            host=host,
            username=username,
            command=start_command,
        )

        rollback_logs: tuple[CommandAttemptLog, ...] = ()
        rollback_attempted = False
        rollback_succeeded: bool | None = None

        if not start_succeeded:
            rollback_attempted = True
            rollback_command = f"{self._lmutil_path} lmdown -force"
            rollback_logs, rollback_succeeded = self._run_once(
                host=host,
                username=username,
                command=rollback_command,
                attempt=1,
            )

        return ProviderOperationResult(
            provider=self.provider_name,
            action="start",
            host=host,
            username=username,
            succeeded=start_succeeded,
            attempts=len(start_logs),
            timeout_seconds=self._timeout_seconds,
            command_logs=start_logs + rollback_logs,
            rollback_attempted=rollback_attempted,
            rollback_succeeded=rollback_succeeded,
        )

    def stop(self, *, host: str, username: str) -> ProviderOperationResult:
        stop_command = f"{self._lmutil_path} lmdown -force"
        stop_logs, stop_succeeded = self._run_with_retry(
            host=host,
            username=username,
            command=stop_command,
        )

        return ProviderOperationResult(
            provider=self.provider_name,
            action="stop",
            host=host,
            username=username,
            succeeded=stop_succeeded,
            attempts=len(stop_logs),
            timeout_seconds=self._timeout_seconds,
            command_logs=stop_logs,
        )

    def _run_with_retry(
        self,
        *,
        host: str,
        username: str,
        command: str,
    ) -> tuple[tuple[CommandAttemptLog, ...], bool]:
        logs: list[CommandAttemptLog] = []

        for attempt in range(1, self._retry_times + 2):
            attempt_logs, succeeded = self._run_once(
                host=host,
                username=username,
                command=command,
                attempt=attempt,
            )
            logs.extend(attempt_logs)
            if succeeded:
                return tuple(logs), True

        return tuple(logs), False

    def _run_once(
        self,
        *,
        host: str,
        username: str,
        command: str,
        attempt: int,
    ) -> tuple[tuple[CommandAttemptLog, ...], bool]:
        exit_code, stdout, stderr = self._executor.run(
            host=host,
            username=username,
            command=command,
            timeout_seconds=self._timeout_seconds,
        )
        log = CommandAttemptLog(
            attempt=attempt,
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )
        return (log,), exit_code == 0
