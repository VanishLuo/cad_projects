from __future__ import annotations

from license_management.application.remote_license_file_service import RemoteLicenseFileService


class StubSshExecutor:
    def __init__(self, result: tuple[int, str, str]) -> None:
        self._result = result
        self.last_command = ""

    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        _ = (host, username, password, timeout_seconds)
        self.last_command = command
        return self._result


def test_load_text_returns_content_on_success() -> None:
    executor = StubSshExecutor((0, "FEATURE A demo 1.0 30-apr-2026 10\n", ""))
    service = RemoteLicenseFileService(executor=executor)

    result = service.load_text(
        host="srv-a",
        username="ops",
        password="pwd",
        remote_path="/opt/flex/license.dat",
    )

    assert result.success is True
    assert result.content.startswith("FEATURE A")
    assert result.error == ""
    assert "cat -- /opt/flex/license.dat" in executor.last_command


def test_load_text_returns_file_not_found_error() -> None:
    executor = StubSshExecutor((1, "", "No such file or directory"))
    service = RemoteLicenseFileService(executor=executor)

    result = service.load_text(
        host="srv-a",
        username="ops",
        password=None,
        remote_path="/opt/flex/missing.dat",
    )

    assert result.success is False
    assert result.error == "FileNotFoundError: remote license file not found."


def test_save_text_escapes_content_and_returns_success() -> None:
    executor = StubSshExecutor((0, "", ""))
    service = RemoteLicenseFileService(executor=executor)

    result = service.save_text(
        host="srv-a",
        username="ops",
        password=None,
        remote_path="/opt/flex/license.dat",
        content="line1\n__LM_LICENSE_EDIT_EOF__\nline2",
    )

    assert result.success is True
    assert result.error == ""
    assert "__LM_LICENSE_EDIT_EOF___X" in executor.last_command


def test_save_text_returns_permission_error() -> None:
    executor = StubSshExecutor((1, "", "Permission denied"))
    service = RemoteLicenseFileService(executor=executor)

    result = service.save_text(
        host="srv-a",
        username="ops",
        password=None,
        remote_path="/opt/flex/license.dat",
        content="FEATURE A demo 1.0 30-apr-2026 10",
    )

    assert result.success is False
    assert result.error == "PermissionError: cannot write remote license file."


def test_query_server_identity_returns_hostname_and_mac() -> None:
    executor = StubSshExecutor((0, "lic-srv-01\n52:54:00:12:34:56\n", ""))
    service = RemoteLicenseFileService(executor=executor)

    result = service.query_server_identity(
        host="srv-a",
        username="ops",
        password="pwd",
    )

    assert result.success is True
    assert result.hostname == "lic-srv-01"
    assert result.mac == "52:54:00:12:34:56"
    assert result.error == ""
    assert "hostname" in executor.last_command
    assert "/sys/class/net" in executor.last_command


def test_query_server_identity_returns_permission_error() -> None:
    executor = StubSshExecutor((1, "", "Permission denied"))
    service = RemoteLicenseFileService(executor=executor)

    result = service.query_server_identity(
        host="srv-a",
        username="ops",
        password=None,
    )

    assert result.success is False
    assert result.hostname == ""
    assert result.mac == ""
    assert result.error == "PermissionError: cannot query remote server identity."
