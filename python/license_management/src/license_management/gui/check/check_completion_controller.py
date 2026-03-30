from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from license_management.domain.expiration_engine import ExpirationStatus
from license_management.domain.models.license_record import LicenseRecord
from license_management.application.record_check_service import RecordCheckIssue


class CheckRepositoryProtocol(Protocol):
    @property
    def current_workspace(self) -> str: ...

    def list_all(self) -> list[LicenseRecord]: ...

    def upsert(self, record: LicenseRecord) -> None: ...


class CheckFeatureCatalogProtocol(Protocol):
    def sync_from_record(self, record: LicenseRecord) -> object: ...


class WorkspaceSwitcherProtocol(Protocol):
    def switch_workspace(self, workspace: str) -> None: ...


@dataclass(slots=True, frozen=True)
class CheckIssueGrouping:
    license: list[RecordCheckIssue]
    ssh: list[RecordCheckIssue]
    start: list[RecordCheckIssue]
    other: list[RecordCheckIssue]


@dataclass(slots=True, frozen=True)
class CheckAnalysisResult:
    grouped: CheckIssueGrouping
    active_count: int
    expired_count: int
    unknown_count: int
    blocking_issues: list[RecordCheckIssue]
    blocked_record_ids: set[str]


@dataclass(slots=True, frozen=True)
class CheckPublishResult:
    published_rows: int
    committed_statuses: dict[str, str]


class CheckCompletionController:
    """Analyze check outcome and publish passing staging rows to committed."""

    def __init__(
        self,
        *,
        repository: CheckRepositoryProtocol,
        feature_catalog: CheckFeatureCatalogProtocol,
        workspace_switcher: WorkspaceSwitcherProtocol,
    ) -> None:
        self._repository = repository
        self._feature_catalog = feature_catalog
        self._workspace_switcher = workspace_switcher

    def analyze(
        self,
        *,
        issues: list[RecordCheckIssue],
        runtime_statuses: dict[str, str],
    ) -> CheckAnalysisResult:
        grouped = CheckIssueGrouping(license=[], ssh=[], start=[], other=[])
        for issue in issues:
            if issue.status == "license_not_found":
                grouped.license.append(issue)
            elif issue.status == "ssh_failed":
                grouped.ssh.append(issue)
            elif issue.status == "start_command_error":
                grouped.start.append(issue)
            else:
                grouped.other.append(issue)

        active_count = sum(
            1 for value in runtime_statuses.values() if value == ExpirationStatus.ACTIVE.value
        )
        expired_count = sum(
            1 for value in runtime_statuses.values() if value == ExpirationStatus.EXPIRED.value
        )
        unknown_count = sum(
            1 for value in runtime_statuses.values() if value == ExpirationStatus.UNKNOWN.value
        )

        blocking_statuses = {"license_not_found", "ssh_failed", "start_command_error"}
        blocking_issues = [item for item in issues if item.status in blocking_statuses]
        blocked_record_ids = {item.record_id for item in blocking_issues}

        return CheckAnalysisResult(
            grouped=grouped,
            active_count=active_count,
            expired_count=expired_count,
            unknown_count=unknown_count,
            blocking_issues=blocking_issues,
            blocked_record_ids=blocked_record_ids,
        )

    def publish_passing_rows_to_committed(
        self,
        *,
        runtime_statuses: dict[str, str],
        blocked_record_ids: set[str],
        committed_statuses: dict[str, str],
    ) -> CheckPublishResult:
        if self._repository.current_workspace != "staging":
            return CheckPublishResult(published_rows=0, committed_statuses=dict(committed_statuses))

        staging_records = self._repository.list_all()
        passing_records = [
            record for record in staging_records if record.record_id not in blocked_record_ids
        ]
        if not passing_records:
            return CheckPublishResult(published_rows=0, committed_statuses=dict(committed_statuses))

        updated_committed_statuses = dict(committed_statuses)
        self._workspace_switcher.switch_workspace("committed")
        try:
            published = 0
            for record in passing_records:
                self._repository.upsert(record)
                self._feature_catalog.sync_from_record(record)
                committed_status = runtime_statuses.get(record.record_id, "").strip()
                if committed_status:
                    updated_committed_statuses[record.record_id] = committed_status
                published += 1
        finally:
            self._workspace_switcher.switch_workspace("staging")

        return CheckPublishResult(
            published_rows=published,
            committed_statuses=updated_committed_statuses,
        )
