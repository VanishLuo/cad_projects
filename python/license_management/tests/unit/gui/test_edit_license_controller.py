from __future__ import annotations

from datetime import date
from dataclasses import dataclass

from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.controllers.edit_license_controller import EditLicenseController


@dataclass(slots=True, frozen=True)
class _ReadResult:
    success: bool
    content: str = ""
    error: str = ""


@dataclass(slots=True, frozen=True)
class _WriteResult:
    success: bool
    error: str = ""


@dataclass(slots=True, frozen=True)
class _IdentityResult:
    success: bool
    hostname: str = ""
    mac: str = ""
    error: str = ""


class _FakeSnapshotRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, str | None]] = []

    def upsert_license_text_snapshot(
        self,
        record_id: str,
        *,
        initial_text: str | None = None,
        current_text: str | None = None,
    ) -> None:
        self.calls.append((record_id, initial_text, current_text))


class _FakeRemoteService:
    def __init__(self) -> None:
        self.read_result = _ReadResult(success=True, content="original")
        self.identity_result = _IdentityResult(
            success=True,
            hostname="srv-host",
            mac="11:22:33:44:55:66",
        )
        self.write_result = _WriteResult(success=True)
        self.last_write_content = ""

    def load_text(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        remote_path: str,
    ) -> _ReadResult:
        _ = (host, username, password, remote_path)
        return self.read_result

    def save_text(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        remote_path: str,
        content: str,
    ) -> _WriteResult:
        _ = (host, username, password, remote_path)
        self.last_write_content = content
        return self.write_result

    def query_server_identity(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
    ) -> _IdentityResult:
        _ = (host, username, password)
        return self.identity_result


def _record() -> LicenseRecord:
    return LicenseRecord(
        record_id="r1",
        server_name="srv-a",
        provider="FlexNet",
        prot="27000",
        feature_name="feat",
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
        vendor="ansys",
        start_executable_path="/opt/lmgrd",
        license_file_path="/opt/license.dat",
    )


def test_prepare_edit_returns_error_for_empty_host() -> None:
    repo = _FakeSnapshotRepository()
    remote = _FakeRemoteService()
    controller = EditLicenseController(repository=repo, remote_service=remote)
    record = _record()
    record.server_name = ""

    result = controller.prepare_edit(record=record, username="ops", password=None)

    assert result.ok is False
    assert result.error == "Selected row has empty server host."


def test_prepare_edit_returns_warning_when_identity_query_fails() -> None:
    repo = _FakeSnapshotRepository()
    remote = _FakeRemoteService()
    remote.identity_result = _IdentityResult(success=False, error="identity failed")
    controller = EditLicenseController(repository=repo, remote_service=remote)

    result = controller.prepare_edit(record=_record(), username="ops", password=None)

    assert result.ok is True
    assert result.warning == "identity failed"
    assert result.session is not None
    assert result.session.server_hostname == ""


def test_save_edited_text_no_changes_updates_snapshot_only() -> None:
    repo = _FakeSnapshotRepository()
    remote = _FakeRemoteService()
    controller = EditLicenseController(repository=repo, remote_service=remote)
    prepare = controller.prepare_edit(record=_record(), username="ops", password=None)
    assert prepare.session is not None

    result = controller.save_edited_text(
        session=prepare.session,
        username="ops",
        password=None,
        updated_text="original",
    )

    assert result.ok is True
    assert result.no_changes is True
    assert repo.calls == [("r1", "original", "original")]


def test_save_edited_text_persists_remote_and_snapshot() -> None:
    repo = _FakeSnapshotRepository()
    remote = _FakeRemoteService()
    controller = EditLicenseController(repository=repo, remote_service=remote)
    prepare = controller.prepare_edit(record=_record(), username="ops", password=None)
    assert prepare.session is not None

    result = controller.save_edited_text(
        session=prepare.session,
        username="ops",
        password=None,
        updated_text="changed-content",
    )

    assert result.ok is True
    assert result.no_changes is False
    assert remote.last_write_content == "changed-content"
    assert repo.calls == [("r1", "original", "changed-content")]


def test_load_remote_text_returns_error_message_on_failure() -> None:
    repo = _FakeSnapshotRepository()
    remote = _FakeRemoteService()
    remote.read_result = _ReadResult(success=False, error="read failed")
    controller = EditLicenseController(repository=repo, remote_service=remote)

    loaded, error = controller.load_remote_text(record=_record(), username="ops", password=None)

    assert loaded is None
    assert error == "read failed"

