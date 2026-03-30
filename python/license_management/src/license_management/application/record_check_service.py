from __future__ import annotations

from dataclasses import dataclass
import shlex

from license_management.adapters.provider_command_profiles import resolve_start_option_tokens
from license_management.adapters.provider_adapter import SshCommandExecutor
from license_management.domain.expiration_engine import ExpirationStatus
from license_management.domain.models.license_record import LicenseRecord
from license_management.shared.path_normalization import normalize_local_path_text


@dataclass(slots=True, frozen=True)
class RecordCheckIssue:
    record_id: str
    status: str
    reason: str
    license_file_path: str


class RecordCheckService:
    """Checks record-level issues without writing to any database."""

    def __init__(
        self,
        *,
        ssh_executor: SshCommandExecutor | None = None,
        ssh_username: str = "",
        ssh_password: str | None = None,
        ssh_timeout_seconds: int = 6,
    ) -> None:
        self._ssh_executor = ssh_executor
        self._ssh_username = ssh_username.strip()
        self._ssh_password = ssh_password
        self._ssh_timeout_seconds = ssh_timeout_seconds

    def check(self, records: list[LicenseRecord]) -> list[RecordCheckIssue]:
        issues, _runtime_statuses = self.check_with_runtime(records)
        return issues

    def check_with_runtime(
        self,
        records: list[LicenseRecord],
    ) -> tuple[list[RecordCheckIssue], dict[str, str]]:
        issues: list[RecordCheckIssue] = []
        runtime_statuses: dict[str, str] = {}
        ssh_cache: dict[str, str | None] = {}
        license_path_cache: dict[tuple[str, str], str | None] = {}
        start_probe_cache: dict[tuple[str, str], str | None] = {}
        process_probe_cache: dict[tuple[str, str], str | None] = {}
        for record in records:
            ssh_issue = self._check_ssh(record.server_name, cache=ssh_cache)
            if ssh_issue is not None:
                runtime_statuses[record.record_id] = ExpirationStatus.UNKNOWN.value
                issues.append(
                    RecordCheckIssue(
                        record_id=record.record_id,
                        status="ssh_failed",
                        reason=ssh_issue,
                        license_file_path=record.license_file_path,
                    )
                )
                continue

            license_issue = self._check_license_file(record, cache=license_path_cache)
            if license_issue is not None:
                issues.append(
                    RecordCheckIssue(
                        record_id=record.record_id,
                        status="license_not_found",
                        reason=license_issue,
                        license_file_path=record.license_file_path,
                    )
                )

            start_issue = self._check_start_command(record, cache=start_probe_cache)
            if start_issue is not None:
                issues.append(
                    RecordCheckIssue(
                        record_id=record.record_id,
                        status="start_command_error",
                        reason=start_issue,
                        license_file_path=record.license_file_path,
                    )
                )

            process_issue = self._check_process_running(record, cache=process_probe_cache)
            if process_issue is not None:
                runtime_statuses[record.record_id] = ExpirationStatus.EXPIRED.value
            else:
                runtime_statuses[record.record_id] = ExpirationStatus.ACTIVE.value

        return issues, runtime_statuses

    def _check_ssh(self, host: str, *, cache: dict[str, str | None]) -> str | None:
        if self._ssh_executor is None:
            return None

        normalized_host = host.strip()
        if normalized_host == "":
            return "ssh host is empty"

        if normalized_host in cache:
            return cache[normalized_host]

        exit_code, _stdout, stderr = self._ssh_executor.run(
            host=normalized_host,
            username=self._ssh_username,
            password=self._ssh_password,
            command="echo ssh_check_ok",
            timeout_seconds=self._ssh_timeout_seconds,
        )
        if exit_code == 0:
            cache[normalized_host] = None
            return None

        detail = stderr.strip() or f"ssh check failed with exit code {exit_code}"
        reason = f"ssh to host '{normalized_host}' failed: {detail}"
        cache[normalized_host] = reason
        return reason

    def _check_license_file(
        self,
        record: LicenseRecord,
        *,
        cache: dict[tuple[str, str], str | None],
    ) -> str | None:
        normalized_path = normalize_local_path_text(record.license_file_path)
        if normalized_path == "":
            return None

        if self._ssh_executor is None:
            try:
                from pathlib import Path

                if Path(normalized_path).exists():
                    return None
            except OSError:
                pass
            return "license_file_path: license file not found"

        host = record.server_name.strip()
        cache_key = (host, normalized_path)
        if cache_key in cache:
            return cache[cache_key]

        probe_command = self._build_path_probe_command(normalized_path)
        exit_code, _stdout, stderr = self._ssh_executor.run(
            host=host,
            username=self._ssh_username,
            password=self._ssh_password,
            command=probe_command,
            timeout_seconds=self._ssh_timeout_seconds,
        )
        if exit_code == 0:
            cache[cache_key] = None
            return None

        detail = stderr.strip() or f"path probe failed with exit code {exit_code}"
        reason = f"license_file_path: remote path not found on host '{host}': {detail}"
        cache[cache_key] = reason
        return reason

    def _check_start_command(
        self,
        record: LicenseRecord,
        *,
        cache: dict[tuple[str, str], str | None],
    ) -> str | None:
        executable = record.start_executable_path.strip() or "lmgrd"
        if "\n" in executable or "\r" in executable:
            return "start executable contains invalid newline characters"

        host = record.server_name.strip()
        cache_key = (host, executable)
        if cache_key in cache:
            return cache[cache_key]

        if self._ssh_executor is None:
            tokens = self._resolve_start_tokens(record)
            if not tokens:
                reason = "start options cannot be resolved"
                cache[cache_key] = reason
                return reason
            cache[cache_key] = None
            return None

        probe_command = self._build_probe_command(executable)
        exit_code, _stdout, stderr = self._ssh_executor.run(
            host=host,
            username=self._ssh_username,
            password=self._ssh_password,
            command=probe_command,
            timeout_seconds=self._ssh_timeout_seconds,
        )
        if exit_code == 0:
            cache[cache_key] = None
            return None

        detail = stderr.strip() or f"probe failed with exit code {exit_code}"
        reason = f"start executable probe failed on host '{host}': {detail}"
        cache[cache_key] = reason
        return reason

    def _check_process_running(
        self,
        record: LicenseRecord,
        *,
        cache: dict[tuple[str, str], str | None],
    ) -> str | None:
        process_hint = (
            record.process_name.strip() or record.start_executable_path.strip() or "lmgrd"
        )
        if "\n" in process_hint or "\r" in process_hint:
            return "process name contains invalid newline characters"

        if self._ssh_executor is None:
            return None

        host = record.server_name.strip()
        cache_key = (host, process_hint)
        if cache_key in cache:
            return cache[cache_key]

        probe_command = self._build_process_probe_command(process_hint)
        exit_code, _stdout, stderr = self._ssh_executor.run(
            host=host,
            username=self._ssh_username,
            password=self._ssh_password,
            command=probe_command,
            timeout_seconds=self._ssh_timeout_seconds,
        )
        if exit_code == 0:
            cache[cache_key] = None
            return None

        detail = stderr.strip() or f"process probe failed with exit code {exit_code}"
        reason = f"process '{process_hint}' not running on host '{host}': {detail}"
        cache[cache_key] = reason
        return reason

    def _resolve_start_tokens(self, record: LicenseRecord) -> tuple[str, ...]:
        if record.start_option_override.strip() != "":
            return tuple(token for token in record.start_option_override.split() if token)
        return resolve_start_option_tokens(
            record.provider,
            license_file_path=(record.license_file_path or "license.dat"),
        )

    def _build_probe_command(self, executable: str) -> str:
        if "/" in executable or "\\" in executable or executable.startswith("."):
            return f"sh -lc 'test -x {shlex.quote(executable)}'"
        return f"sh -lc 'command -v {shlex.quote(executable)} >/dev/null 2>&1'"

    def _build_path_probe_command(self, path_text: str) -> str:
        return f"sh -lc 'test -e {shlex.quote(path_text)}'"

    def _build_process_probe_command(self, process_hint: str) -> str:
        escaped = shlex.quote(process_hint)
        return (
            'sh -lc "if command -v pgrep >/dev/null 2>&1; '
            f"then pgrep -f -- {escaped} >/dev/null 2>&1; "
            f'else ps -ef | grep -F -- {escaped} | grep -v grep >/dev/null 2>&1; fi"'
        )
