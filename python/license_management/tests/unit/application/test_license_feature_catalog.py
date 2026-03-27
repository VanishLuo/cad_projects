from __future__ import annotations

from datetime import date
from pathlib import Path

from license_management.application.license_feature_catalog import LicenseFeatureCatalogService
from license_management.application.license_file_parser import ParsedLicenseFeature
from license_management.domain.models.license_record import LicenseRecord
from license_management.infrastructure.repositories.sqlite_license_feature_repository import (
    SqliteLicenseFeatureRepository,
)


class _StubParser:
    def __init__(self, *, file_features: list[ParsedLicenseFeature], text_features: list[ParsedLicenseFeature]) -> None:
        self._file_features = file_features
        self._text_features = text_features

    def parse(self, file_path: Path) -> list[ParsedLicenseFeature]:
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        return list(self._file_features)

    def parse_text(self, content: str) -> list[ParsedLicenseFeature]:
        _ = content
        return list(self._text_features)


class _StubResolver:
    def __init__(self, parser: _StubParser) -> None:
        self._parser = parser

    def resolve(self, *, provider: str, vendor: str) -> _StubParser:
        _ = (provider, vendor)
        return self._parser


class _StubSshExecutor:
    def __init__(self, *, exit_code: int, stdout: str = "", stderr: str = "") -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.commands: list[str] = []

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
        self.commands.append(command)
        return self.exit_code, self.stdout, self.stderr


def _record(path: str) -> LicenseRecord:
    return LicenseRecord(
        record_id="r1",
        server_name="srv-a",
        provider="FlexNet",
        vendor="cadence",
        prot="27000",
        feature_name="",
        process_name="lmgrd",
        expires_on=date(2026, 1, 1),
        license_file_path=path,
    )


def test_sync_from_record_falls_back_to_ssh_when_local_path_missing(tmp_path: Path) -> None:
    repo = SqliteLicenseFeatureRepository(tmp_path / "feature.sqlite3")
    parser = _StubParser(
        file_features=[],
        text_features=[ParsedLicenseFeature(feature_name="FEAT-SSH", expires_on=date(2027, 1, 1), quantity=3)],
    )
    ssh = _StubSshExecutor(exit_code=0, stdout="FEATURE FEAT-SSH vendor 1.0 1-jan-2027 3")
    service = LicenseFeatureCatalogService(
        repository=repo,
        resolver=_StubResolver(parser),
        ssh_executor=ssh,
        ssh_username="operator",
        ssh_password="secret",
    )

    record = _record("/remote/path/license.dat")
    result = service.sync_from_record(record)

    assert result.license_missing is False
    assert result.feature_groups == 1
    assert result.total_quantity == 3
    assert repo.list_for_record(record) == [("FEAT-SSH", "2027-01-01", 3)]
    assert len(ssh.commands) == 1


def test_sync_from_record_reports_missing_when_ssh_fetch_fails(tmp_path: Path) -> None:
    repo = SqliteLicenseFeatureRepository(tmp_path / "feature.sqlite3")
    parser = _StubParser(file_features=[], text_features=[])
    ssh = _StubSshExecutor(exit_code=1, stderr="not found")
    service = LicenseFeatureCatalogService(
        repository=repo,
        resolver=_StubResolver(parser),
        ssh_executor=ssh,
        ssh_username="operator",
    )

    record = _record("/remote/path/missing.dat")
    result = service.sync_from_record(record)

    assert result.license_missing is True
    assert result.feature_groups == 0
    assert result.total_quantity == 0
    assert repo.list_for_record(record) == []
