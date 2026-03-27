from __future__ import annotations

import subprocess
from typing import Any

from license_management.adapters.provider_adapter import SshCommandExecutor


class OpenSshCommandExecutor(SshCommandExecutor):
    """Execute remote commands through system OpenSSH client."""

    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        if password:
            return _run_with_paramiko(
                host=host,
                username=username,
                password=password,
                command=command,
                timeout_seconds=timeout_seconds,
            )

        target = f"{username}@{host}" if username.strip() else host
        try:
            completed = subprocess.run(
                ["ssh", target, command],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return completed.returncode, completed.stdout, completed.stderr
        except FileNotFoundError:
            return 127, "", "ssh executable not found in PATH"
        except subprocess.TimeoutExpired as exc:
            stdout = _to_text(exc.stdout)
            stderr = _to_text(exc.stderr)
            suffix = f"command timed out after {timeout_seconds}s"
            if stderr:
                stderr = f"{stderr}\n{suffix}"
            else:
                stderr = suffix
            return 124, stdout, stderr


def _to_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _run_with_paramiko(
    *,
    host: str,
    username: str,
    password: str,
    command: str,
    timeout_seconds: int,
) -> tuple[int, str, str]:
    try:
        import paramiko  # type: ignore[import-untyped]
    except ImportError:
        return 127, "", "paramiko is required for password-based SSH"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            username=username,
            password=password,
            timeout=timeout_seconds,
            banner_timeout=timeout_seconds,
            auth_timeout=timeout_seconds,
        )
        _stdin, stdout_obj, stderr_obj = client.exec_command(command, timeout=timeout_seconds)
        stdout: Any = stdout_obj.read()
        stderr: Any = stderr_obj.read()
        exit_code = int(stdout_obj.channel.recv_exit_status())
        return exit_code, _to_text(stdout), _to_text(stderr)
    except Exception as exc:  # pragma: no cover - depends on network/runtime
        return 1, "", str(exc)
    finally:
        client.close()
