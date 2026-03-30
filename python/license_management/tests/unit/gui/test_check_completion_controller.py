from __future__ import annotations

from datetime import date

from license_management.application.record_check_service import RecordCheckIssue
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.check.check_completion_controller import CheckCompletionController


class _FakeRepository:
    def __init__(self) -> None:
        self.current_workspace = "staging"
        self._staging = [
            _record("r1", "srv-a"),
            _record("r2", "srv-b"),
        ]
        self._committed: list[LicenseRecord] = []

    def list_all(self) -> list[LicenseRecord]:
        if self.current_workspace == "staging":
            return list(self._staging)
        return list(self._committed)

    def upsert(self, record: LicenseRecord) -> None:
        target = self._committed if self.current_workspace == "committed" else self._staging
        for index, existing in enumerate(target):
            if existing.record_id == record.record_id:
                target[index] = record
                return
        target.append(record)


class _FakeFeatureCatalog:
    def __init__(self) -> None:
        self.synced_ids: list[str] = []

    def sync_from_record(self, record: LicenseRecord) -> object:
        self.synced_ids.append(record.record_id)
        return object()


class _FakeWorkspaceSwitcher:
    def __init__(self, repo: _FakeRepository) -> None:
        self._repo = repo
        self.calls: list[str] = []

    def switch_workspace(self, workspace: str) -> None:
        self.calls.append(workspace)
        self._repo.current_workspace = workspace


def _record(record_id: str, server_name: str) -> LicenseRecord:
    return LicenseRecord(
        record_id=record_id,
        server_name=server_name,
        provider="FlexNet",
        prot="27000",
        feature_name="feat",
        process_name="lmgrd",
        expires_on=date(2026, 6, 1),
        vendor="ansys",
        start_executable_path="/opt/lmgrd",
        license_file_path="/opt/license.dat",
    )


def test_analyze_groups_issues_and_counts_statuses() -> None:
    repo = _FakeRepository()
    catalog = _FakeFeatureCatalog()
    switcher = _FakeWorkspaceSwitcher(repo)
    controller = CheckCompletionController(
        repository=repo,
        feature_catalog=catalog,
        workspace_switcher=switcher,
    )
    issues = [
        RecordCheckIssue(
            record_id="r1", status="license_not_found", reason="x", license_file_path=""
        ),
        RecordCheckIssue(record_id="r2", status="ssh_failed", reason="x", license_file_path=""),
        RecordCheckIssue(
            record_id="r3", status="start_command_error", reason="x", license_file_path=""
        ),
        RecordCheckIssue(record_id="r4", status="custom", reason="x", license_file_path=""),
    ]

    analysis = controller.analyze(
        issues=issues,
        runtime_statuses={"r1": "active", "r2": "expired", "r3": "unknown"},
    )

    assert len(analysis.grouped.license) == 1
    assert len(analysis.grouped.ssh) == 1
    assert len(analysis.grouped.start) == 1
    assert len(analysis.grouped.other) == 1
    assert analysis.active_count == 1
    assert analysis.expired_count == 1
    assert analysis.unknown_count == 1
    assert analysis.blocked_record_ids == {"r1", "r2", "r3"}


def test_publish_passing_rows_to_committed_updates_status_and_restores_workspace() -> None:
    repo = _FakeRepository()
    catalog = _FakeFeatureCatalog()
    switcher = _FakeWorkspaceSwitcher(repo)
    controller = CheckCompletionController(
        repository=repo,
        feature_catalog=catalog,
        workspace_switcher=switcher,
    )

    result = controller.publish_passing_rows_to_committed(
        runtime_statuses={"r1": "active", "r2": "expired"},
        blocked_record_ids={"r2"},
        committed_statuses={"old": "unknown"},
    )

    assert result.published_rows == 1
    assert result.committed_statuses == {"old": "unknown", "r1": "active"}
    assert repo.current_workspace == "staging"
    assert switcher.calls == ["committed", "staging"]
    assert catalog.synced_ids == ["r1"]


def test_publish_returns_without_switch_when_not_in_staging() -> None:
    repo = _FakeRepository()
    repo.current_workspace = "committed"
    catalog = _FakeFeatureCatalog()
    switcher = _FakeWorkspaceSwitcher(repo)
    controller = CheckCompletionController(
        repository=repo,
        feature_catalog=catalog,
        workspace_switcher=switcher,
    )

    result = controller.publish_passing_rows_to_committed(
        runtime_statuses={"r1": "active"},
        blocked_record_ids=set(),
        committed_statuses={"old": "unknown"},
    )

    assert result.published_rows == 0
    assert result.committed_statuses == {"old": "unknown"}
    assert switcher.calls == []
