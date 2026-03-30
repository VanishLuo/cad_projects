"""Provider execution contract and result models.

English:
This module defines the stable execution boundary between provider-specific
adapters (for example FlexNet) and the concrete SSH command runner.

Chinese:
本模块定义了供应商适配器（例如 FlexNet）与底层 SSH 执行器之间的稳定契约边界。
上层适配器只关心“要执行什么命令”，底层执行器负责“如何执行命令并返回结果”。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SshCommandExecutor(Protocol):
    """Execute one SSH command and return process tuple.

    English:
    Return format is (exit_code, stdout, stderr).

    Chinese:
    返回值固定为 (退出码, 标准输出, 标准错误)。
    - exit_code == 0 表示命令执行成功
    - stdout/stderr 用于审计与故障定位
    """

    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]: ...


@dataclass(slots=True, frozen=True)
class CommandAttemptLog:
    """One attempt-level execution log / 单次尝试日志。

    English:
    Each retry creates one log entry so callers can reconstruct complete
    execution history.

    Chinese:
    每一次重试都会形成一条日志，便于完整回放执行轨迹。
    """

    attempt: int
    command: str
    exit_code: int
    stdout: str
    stderr: str


@dataclass(slots=True, frozen=True)
class ProviderOperationResult:
    """Provider operation result / 供应商操作结果。

    English:
    Captures outcome for a start/stop workflow, including retries and optional
    rollback execution.

    Chinese:
    表示一次 start/stop 业务流程的最终结果，包含重试次数、命令日志、
    以及是否触发回滚和回滚结果。
    """

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
