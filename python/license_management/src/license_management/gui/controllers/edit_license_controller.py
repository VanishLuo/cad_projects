from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from license_management.domain.models.license_record import LicenseRecord


class EditSnapshotRepositoryProtocol(Protocol):
    def upsert_license_text_snapshot(
        self,
        record_id: str,
        *,
        initial_text: str | None = None,
        current_text: str | None = None,
    ) -> None: ...


class RemoteTextReadResultProtocol(Protocol):
    @property
    def success(self) -> bool: ...

    @property
    def content(self) -> str: ...

    @property
    def error(self) -> str: ...


class RemoteTextWriteResultProtocol(Protocol):
    @property
    def success(self) -> bool: ...

    @property
    def error(self) -> str: ...


class RemoteHostIdentityResultProtocol(Protocol):
    @property
    def success(self) -> bool: ...

    @property
    def hostname(self) -> str: ...

    @property
    def mac(self) -> str: ...

    @property
    def error(self) -> str: ...


class RemoteLicenseServiceProtocol(Protocol):
    def load_text(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        remote_path: str,
    ) -> RemoteTextReadResultProtocol: ...

    def save_text(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        remote_path: str,
        content: str,
    ) -> RemoteTextWriteResultProtocol: ...

    def query_server_identity(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
    ) -> RemoteHostIdentityResultProtocol: ...


@dataclass(slots=True, frozen=True)
class EditSession:
    record_id: str
    host: str
    remote_path: str
    original_text: str
    server_hostname: str
    server_mac: str


@dataclass(slots=True, frozen=True)
class EditPrepareResult:
    ok: bool
    session: EditSession | None = None
    error: str = ""
    warning: str = ""


@dataclass(slots=True, frozen=True)
class EditSaveResult:
    ok: bool
    no_changes: bool = False
    error: str = ""


class EditLicenseController:
    """Coordinate remote edit workflow and snapshot persistence."""

    def __init__(
        self,
        *,
        repository: EditSnapshotRepositoryProtocol,
        remote_service: RemoteLicenseServiceProtocol,
    ) -> None:
        self._repository = repository
        self._remote_service = remote_service

    def prepare_edit(
        self,
        *,
        record: LicenseRecord,
        username: str,
        password: str | None,
    ) -> EditPrepareResult:
        host = record.server_name.strip()
        remote_path = record.license_file_path.strip()
        if host == "":
            return EditPrepareResult(ok=False, error="Selected row has empty server host.")
        if remote_path == "":
            return EditPrepareResult(ok=False, error="Selected row has empty license file path.")

        loaded = self._remote_service.load_text(
            host=host,
            username=username,
            password=password,
            remote_path=remote_path,
        )
        if not loaded.success:
            return EditPrepareResult(ok=False, error=loaded.error)

        identity = self._remote_service.query_server_identity(
            host=host,
            username=username,
            password=password,
        )
        warning = ""
        server_hostname = ""
        server_mac = ""
        if identity.success:
            server_hostname = identity.hostname
            server_mac = identity.mac
        else:
            warning = identity.error

        return EditPrepareResult(
            ok=True,
            session=EditSession(
                record_id=record.record_id,
                host=host,
                remote_path=remote_path,
                original_text=loaded.content,
                server_hostname=server_hostname,
                server_mac=server_mac,
            ),
            warning=warning,
        )

    def save_edited_text(
        self,
        *,
        session: EditSession,
        username: str,
        password: str | None,
        updated_text: str,
    ) -> EditSaveResult:
        if updated_text == session.original_text:
            self._repository.upsert_license_text_snapshot(
                session.record_id,
                initial_text=session.original_text,
                current_text=session.original_text,
            )
            return EditSaveResult(ok=True, no_changes=True)

        saved = self._remote_service.save_text(
            host=session.host,
            username=username,
            password=password,
            remote_path=session.remote_path,
            content=updated_text,
        )
        if not saved.success:
            return EditSaveResult(ok=False, error=saved.error)

        self._repository.upsert_license_text_snapshot(
            session.record_id,
            initial_text=session.original_text,
            current_text=updated_text,
        )
        return EditSaveResult(ok=True, no_changes=False)

    def load_remote_text(
        self,
        *,
        record: LicenseRecord,
        username: str,
        password: str | None,
    ) -> tuple[str | None, str]:
        host = record.server_name.strip()
        remote_path = record.license_file_path.strip()
        if host == "" or remote_path == "" or username.strip() == "":
            return None, "missing host, remote path, or username"

        loaded = self._remote_service.load_text(
            host=host,
            username=username,
            password=password,
            remote_path=remote_path,
        )
        if not loaded.success:
            return None, loaded.error
        return loaded.content, ""
