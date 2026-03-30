from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex

from license_management.adapters.provider_adapter import SshCommandExecutor
from license_management.application.license_file_parser import LicenseParserResolver
from license_management.domain.models.license_record import LicenseRecord
from license_management.infrastructure.repositories.sqlite_license_feature_repository import (
    SqliteLicenseFeatureRepository,
)
from license_management.shared.path_normalization import normalize_local_path_text


@dataclass(slots=True, frozen=True)
class CatalogSyncResult:
    feature_groups: int
    total_quantity: int
    license_missing: bool


class LicenseFeatureCatalogService:
    """Synchronizes parsed feature data into a dedicated feature catalog database."""

    def __init__(
        self,
        *,
        repository: SqliteLicenseFeatureRepository,
        resolver: LicenseParserResolver | None = None,
        ssh_executor: SshCommandExecutor | None = None,
        ssh_username: str = "",
        ssh_password: str | None = None,
        ssh_timeout_seconds: int = 10,
    ) -> None:
        self._repository = repository
        self._resolver = resolver or LicenseParserResolver()
        self._ssh_executor = ssh_executor
        self._ssh_username = ssh_username.strip()
        self._ssh_password = ssh_password
        self._ssh_timeout_seconds = max(1, int(ssh_timeout_seconds))

    @property
    def current_workspace(self) -> str:
        return self._repository.current_workspace

    def switch_workspace(self, workspace: str) -> None:
        self._repository.switch_workspace(workspace)

    def enter_staging_workspace(self) -> None:
        self._repository.enter_staging_workspace()

    def publish_staging_to_committed(self) -> int:
        return self._repository.publish_staging_to_committed()

    def sync_from_record(self, record: LicenseRecord) -> CatalogSyncResult:
        normalized_path = normalize_local_path_text(record.license_file_path)
        if normalized_path == "":
            self._repository.delete_for_record(record)
            return CatalogSyncResult(feature_groups=0, total_quantity=0, license_missing=False)

        parser = self._resolver.resolve(provider=record.provider, vendor=record.vendor)
        try:
            features = parser.parse(Path(normalized_path))
        except FileNotFoundError:
            remote_content = self._load_remote_license_content(
                record=record, normalized_path=normalized_path
            )
            if remote_content is None:
                self._repository.delete_for_record(record)
                return CatalogSyncResult(feature_groups=0, total_quantity=0, license_missing=True)
            features = parser.parse_text(remote_content)

        self._repository.replace_for_record(record, features)
        return CatalogSyncResult(
            feature_groups=len(features),
            total_quantity=sum(max(1, int(item.quantity)) for item in features),
            license_missing=False,
        )

    def _load_remote_license_content(
        self, *, record: LicenseRecord, normalized_path: str
    ) -> str | None:
        if self._ssh_executor is None:
            return None

        host = record.server_name.strip()
        if host == "":
            return None

        command = f"sh -lc 'cat -- {shlex.quote(normalized_path)}'"
        exit_code, stdout, _stderr = self._ssh_executor.run(
            host=host,
            username=self._ssh_username,
            password=self._ssh_password,
            command=command,
            timeout_seconds=self._ssh_timeout_seconds,
        )
        if exit_code != 0:
            return None
        return stdout

    def list_for_record(self, record: LicenseRecord) -> list[tuple[str, str, int]]:
        return self._repository.list_for_record(record)

    def remove_for_record(self, record: LicenseRecord) -> None:
        self._repository.delete_for_record(record)
