from __future__ import annotations

"""FlexNet provider adapter implementation.

English:
This adapter is the execution layer that translates normalized startup
parameters into concrete FlexNet commands, then sends them through the
SshCommandExecutor contract.

Chinese:
该适配器属于执行层：把上游标准化后的字段（可执行路径、license 路径、
provider 选项策略）组装成 FlexNet 命令，并通过 SshCommandExecutor 下发执行。
"""

from license_management.adapters.provider_command_profiles import resolve_start_option_tokens
from license_management.adapters.provider_adapter import (
    CommandAttemptLog,
    ProviderOperationResult,
    SshCommandExecutor,
)


class FlexNetAdapter:
    """Run FlexNet start/stop over SSH.

    English:
    Core responsibilities:
    1) Assemble provider-specific command line.
    2) Execute with retry and collect attempt logs.
    3) Trigger rollback on start failure.

    Chinese:
    核心职责：
    1) 组装供应商相关命令。
    2) 按重试策略执行并记录每次尝试。
    3) 启动失败时执行回滚。
    """

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

    def start(
        self,
        *,
        host: str,
        username: str,
        provider: str = "",
        executable_path: str | None = None,
        license_file_path: str | None = None,
        start_option_override: str | None = None,
    ) -> ProviderOperationResult:
        """Start license service with composed command.

        English:
        Command composition priority:
        1) executable_path / license_file_path from record payload.
        2) fallback to adapter defaults.
        3) option tokens from override, otherwise provider JSON strategy.

        Chinese:
        命令组装优先级：
        1) 优先使用记录里传入的 executable_path / license_file_path。
        2) 若缺失则回退到适配器默认值。
        3) option 优先使用 start_option_override，否则走 provider JSON 策略。
        """

        executable = executable_path or self._lmgrd_path
        license_file = license_file_path or self._license_file_path
        if start_option_override:
            # Override is space-split into raw tokens for one-record custom behavior.
            # 单条记录可通过覆盖项提供自定义 token。
            option_tokens = tuple(token for token in start_option_override.split() if token)
        else:
            option_tokens = resolve_start_option_tokens(
                provider,
                license_file_path=license_file,
            )

        # Final shape: <exe> <options...> <license_file_path>
        # 最终格式：<可执行文件> <选项...> <license 文件路径>
        effective_start_command = " ".join([executable, *option_tokens, license_file])
        start_logs, start_succeeded = self._run_with_retry(
            host=host,
            username=username,
            command=effective_start_command,
        )

        rollback_logs: tuple[CommandAttemptLog, ...] = ()
        rollback_attempted = False
        rollback_succeeded: bool | None = None

        if not start_succeeded:
            # If start fails after all retries, force stop as rollback attempt.
            # 若启动在全部重试后仍失败，执行强制停止作为回滚。
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
        """Stop license service directly using lmutil lmdown -force.

        Chinese:
        停止流程不需要命令拼装策略，直接执行固定停止命令。
        """

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
        """Execute one command with retry and full attempt logs.

        Chinese:
        按配置重试次数执行同一命令，并返回完整尝试日志与最终成败。
        """

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
        """Execute one remote command once and build a typed attempt log.

        Chinese:
        单次下发远程命令，并构造结构化日志用于审计与问题排查。
        """

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
