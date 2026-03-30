from __future__ import annotations

from datetime import date
from pathlib import Path

from license_management.application.record_check_service import RecordCheckService
from license_management.domain.models.license_record import LicenseRecord


class StubSshExecutor:
    def __init__(
        self,
        results: dict[str, tuple[int, str, str]],
        command_contains_results: dict[str, tuple[int, str, str]] | None = None,
    ) -> None:
        self._results = results
        self._command_contains_results = command_contains_results or {}
        self.calls: list[str] = []

    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        _ = (username, password, command, timeout_seconds)
        self.calls.append(host)
        for marker, result in self._command_contains_results.items():
            if marker in command:
                return result
        return self._results.get(host, (0, "ok", ""))


def _record(*, record_id: str, license_file_path: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name="srv-a",
        provider="FlexNet",
        prot="27000",
        feature_name="",
        process_name="",
        expires_on=date(2027, 1, 1),
        vendor="",
        start_executable_path="",
        license_file_path=license_file_path,
    )


def test_check_returns_issue_for_missing_license_file(tmp_path: Path) -> None:
    service = RecordCheckService()
    missing = tmp_path / "missing.lic"

    issues = service.check([_record(record_id="r1", license_file_path=str(missing))])

    assert len(issues) == 1
    assert issues[0].record_id == "r1"
    assert issues[0].status == "license_not_found"
    assert issues[0].reason.startswith("license_file_path:")


def test_check_ignores_existing_file_and_empty_path(tmp_path: Path) -> None:
    service = RecordCheckService()
    existing = tmp_path / "ok.lic"
    existing.write_text("FEATURE A demo 1.0 2027-01-01 1\n", encoding="utf-8")

    issues = service.check(
        [
            _record(record_id="r1", license_file_path=str(existing)),
            _record(record_id="r2", license_file_path=""),
        ]
    )

    assert issues == []


def test_check_returns_issue_when_ssh_failed() -> None:
    executor = StubSshExecutor({"srv-a": (255, "", "connection refused")})
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    issues = service.check(
        [
            _record(
                record_id="r1",
                license_file_path="",
            )
        ]
    )

    assert len(issues) == 1
    assert issues[0].record_id == "r1"
    assert issues[0].status == "ssh_failed"
    assert "srv-a" in issues[0].reason
    assert executor.calls == ["srv-a"]


def test_check_deduplicates_ssh_probe_by_host() -> None:
    executor = StubSshExecutor({"srv-a": (255, "", "timeout")})
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    records = [
        _record(record_id="r1", license_file_path=""),
        _record(record_id="r2", license_file_path=""),
    ]
    issues = service.check(records)

    assert len(issues) == 2
    assert all(item.status == "ssh_failed" for item in issues)
    assert executor.calls == ["srv-a"]


def test_check_returns_issue_when_start_command_probe_failed() -> None:
    executor = StubSshExecutor(
        {"srv-a": (0, "ok", "")},
        command_contains_results={
            "test -e": (0, "", ""),
            "command -v lmgrd": (1, "", "lmgrd not found"),
            "pgrep -f": (0, "", ""),
        },
    )
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    issues = service.check([_record(record_id="r1", license_file_path="")])

    assert len(issues) == 1
    assert issues[0].record_id == "r1"
    assert issues[0].status == "start_command_error"
    assert "probe failed" in issues[0].reason


def test_check_returns_issue_when_remote_license_file_missing_over_ssh() -> None:
    executor = StubSshExecutor(
        {"srv-a": (0, "ok", "")},
        command_contains_results={
            "test -e": (1, "", "No such file or directory"),
            "pgrep -f": (0, "", ""),
        },
    )
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    issues = service.check([_record(record_id="r1", license_file_path="/opt/fake/license.dat")])

    assert len(issues) == 1
    assert issues[0].record_id == "r1"
    assert issues[0].status == "license_not_found"
    assert "remote path not found" in issues[0].reason


def test_check_deduplicates_remote_license_path_probe() -> None:
    executor = StubSshExecutor(
        {"srv-a": (0, "ok", "")},
        command_contains_results={
            "test -e": (1, "", "No such file or directory"),
            "command -v lmgrd": (0, "", ""),
            "pgrep -f": (0, "", ""),
        },
    )
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    records = [
        _record(record_id="r1", license_file_path="/opt/fake/license.dat"),
        _record(record_id="r2", license_file_path="/opt/fake/license.dat"),
    ]
    issues = service.check(records)

    assert len(issues) == 2
    assert all(item.status == "license_not_found" for item in issues)
    assert executor.calls == ["srv-a", "srv-a", "srv-a", "srv-a"]


def test_check_with_runtime_returns_active_when_process_is_running() -> None:
    executor = StubSshExecutor(
        {"srv-a": (0, "ok", "")},
        command_contains_results={
            "test -e": (0, "", ""),
            "command -v lmgrd": (0, "", ""),
            "pgrep -f": (0, "123\n", ""),
        },
    )
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    issues, runtime_statuses = service.check_with_runtime(
        [_record(record_id="r1", license_file_path="/opt/fake/license.dat")]
    )

    assert issues == []
    assert runtime_statuses == {"r1": "active"}


def test_check_with_runtime_returns_expired_when_process_is_not_running() -> None:
    executor = StubSshExecutor(
        {"srv-a": (0, "ok", "")},
        command_contains_results={
            "test -e": (0, "", ""),
            "command -v lmgrd": (0, "", ""),
            "pgrep -f": (1, "", ""),
        },
    )
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    issues, runtime_statuses = service.check_with_runtime(
        [_record(record_id="r1", license_file_path="/opt/fake/license.dat")]
    )

    assert issues == []
    assert runtime_statuses == {"r1": "expired"}


def test_check_with_runtime_returns_unknown_when_ssh_failed() -> None:
    executor = StubSshExecutor({"srv-a": (255, "", "connection refused")})
    service = RecordCheckService(
        ssh_executor=executor,
        ssh_username="ops",
        ssh_password="pwd",
    )

    issues, runtime_statuses = service.check_with_runtime(
        [_record(record_id="r1", license_file_path="/opt/fake/license.dat")]
    )

    assert len(issues) == 1
    assert issues[0].status == "ssh_failed"
    assert runtime_statuses == {"r1": "unknown"}
