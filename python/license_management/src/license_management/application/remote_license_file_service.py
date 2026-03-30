from __future__ import annotations

from dataclasses import dataclass
import shlex

from license_management.adapters.provider_adapter import SshCommandExecutor


@dataclass(slots=True, frozen=True)
class RemoteTextReadResult:
    success: bool
    content: str = ""
    error: str = ""


@dataclass(slots=True, frozen=True)
class RemoteTextWriteResult:
    success: bool
    error: str = ""


class RemoteLicenseFileService:
    def __init__(self, *, executor: SshCommandExecutor, timeout_seconds: int = 10) -> None:
        self._executor = executor
        self._timeout_seconds = timeout_seconds

    def load_text(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        remote_path: str,
    ) -> RemoteTextReadResult:
        quoted_path = shlex.quote(remote_path)
        command = f"sh -lc 'cat -- {quoted_path}'"
        exit_code, stdout, stderr = self._executor.run(
            host=host,
            username=username,
            password=password,
            command=command,
            timeout_seconds=self._timeout_seconds,
        )
        if exit_code == 0:
            return RemoteTextReadResult(success=True, content=stdout)
        return RemoteTextReadResult(
            success=False, error=self._classify_read_error(exit_code, stderr)
        )

    def save_text(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        remote_path: str,
        content: str,
    ) -> RemoteTextWriteResult:
        delimiter = "__LM_LICENSE_EDIT_EOF__"
        while delimiter in content:
            delimiter = f"{delimiter}_X"

        quoted_path = shlex.quote(remote_path)
        remote_script = f"cat > {quoted_path} <<'{delimiter}'\n" f"{content}\n" f"{delimiter}\n"
        command = f"sh -lc {shlex.quote(remote_script)}"
        exit_code, _stdout, stderr = self._executor.run(
            host=host,
            username=username,
            password=password,
            command=command,
            timeout_seconds=self._timeout_seconds,
        )
        if exit_code == 0:
            return RemoteTextWriteResult(success=True)
        return RemoteTextWriteResult(
            success=False, error=self._classify_write_error(exit_code, stderr)
        )

    def _classify_read_error(self, exit_code: int, stderr: str) -> str:
        lower_error = stderr.lower()
        if "no such file" in lower_error or "not found" in lower_error:
            return "FileNotFoundError: remote license file not found."
        if "permission denied" in lower_error:
            return "PermissionError: cannot read remote license file."
        if "timed out" in lower_error or exit_code == 124:
            return "TimeoutError: SSH connection timed out."

        detail = stderr.strip() or f"remote read failed with exit code {exit_code}"
        return f"ConnectionError: {detail}"

    def _classify_write_error(self, exit_code: int, stderr: str) -> str:
        lower_error = stderr.lower()
        if "no such file" in lower_error or "not found" in lower_error:
            return "FileNotFoundError: remote path not found."
        if "permission denied" in lower_error:
            return "PermissionError: cannot write remote license file."
        if "timed out" in lower_error or exit_code == 124:
            return "TimeoutError: SSH connection timed out."

        detail = stderr.strip() or f"remote write failed with exit code {exit_code}"
        return f"ConnectionError: {detail}"
