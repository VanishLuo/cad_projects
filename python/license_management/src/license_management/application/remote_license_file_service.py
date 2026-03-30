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


@dataclass(slots=True, frozen=True)
class RemoteHostIdentityResult:
    success: bool
    hostname: str = ""
    mac: str = ""
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

    def query_server_identity(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
    ) -> RemoteHostIdentityResult:
        remote_script = (
            'hostname_text="$(hostname 2>/dev/null || uname -n 2>/dev/null || true)"\n'
            'mac_text="$(cat /sys/class/net/*/address 2>/dev/null '
            '| grep -Eiv "^(00:00:00:00:00:00|ff:ff:ff:ff:ff:ff)$" '
            '| head -n 1)"\n'
            'printf "%s\\n%s\\n" "$hostname_text" "$mac_text"\n'
        )
        command = f"sh -lc {shlex.quote(remote_script)}"
        exit_code, stdout, stderr = self._executor.run(
            host=host,
            username=username,
            password=password,
            command=command,
            timeout_seconds=self._timeout_seconds,
        )
        if exit_code != 0:
            return RemoteHostIdentityResult(
                success=False,
                error=self._classify_identity_error(exit_code, stderr),
            )

        lines = stdout.splitlines()
        hostname = lines[0].strip() if len(lines) >= 1 else ""
        mac = lines[1].strip() if len(lines) >= 2 else ""
        return RemoteHostIdentityResult(success=True, hostname=hostname, mac=mac)

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

    def _classify_identity_error(self, exit_code: int, stderr: str) -> str:
        lower_error = stderr.lower()
        if "permission denied" in lower_error:
            return "PermissionError: cannot query remote server identity."
        if "timed out" in lower_error or exit_code == 124:
            return "TimeoutError: SSH connection timed out."

        detail = stderr.strip() or f"identity query failed with exit code {exit_code}"
        return f"ConnectionError: {detail}"
