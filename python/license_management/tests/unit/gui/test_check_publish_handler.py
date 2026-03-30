from __future__ import annotations

from dataclasses import dataclass

from license_management.gui.check.check_completion_controller import CheckPublishResult
from license_management.gui.check.check_publish_handler import (
    CheckPublishHandler,
    CheckPublishHooks,
)


@dataclass(slots=True, frozen=True)
class _PublishResult:
    published_rows: int
    committed_statuses: dict[str, str]


class _Publisher:
    def __init__(self, result: _PublishResult) -> None:
        self.result = result
        self.calls = 0

    def publish_passing_rows_to_committed(
        self,
        *,
        runtime_statuses: dict[str, str],
        blocked_record_ids: set[str],
        committed_statuses: dict[str, str],
    ) -> CheckPublishResult:
        _ = (runtime_statuses, blocked_record_ids, committed_statuses)
        self.calls += 1
        return CheckPublishResult(
            published_rows=self.result.published_rows,
            committed_statuses=self.result.committed_statuses,
        )


def test_publish_if_needed_skips_when_not_staging() -> None:
    publisher = _Publisher(_PublishResult(published_rows=2, committed_statuses={"r1": "active"}))
    logs: list[tuple[str, str]] = []
    handler = CheckPublishHandler(
        publisher=publisher,
        hooks=CheckPublishHooks(append_log=lambda message, level: logs.append((message, level))),
    )

    result = handler.publish_if_needed(
        current_workspace="committed",
        runtime_statuses={"r1": "active"},
        blocked_record_ids=set(),
        committed_statuses={"old": "unknown"},
    )

    assert publisher.calls == 0
    assert result.published_rows == 0
    assert result.committed_statuses == {"old": "unknown"}
    assert logs == []


def test_publish_if_needed_updates_statuses_and_logs_auto_commit() -> None:
    publisher = _Publisher(
        _PublishResult(
            published_rows=3,
            committed_statuses={"r1": "active", "r2": "expired"},
        )
    )
    logs: list[tuple[str, str]] = []
    handler = CheckPublishHandler(
        publisher=publisher,
        hooks=CheckPublishHooks(append_log=lambda message, level: logs.append((message, level))),
    )

    result = handler.publish_if_needed(
        current_workspace="staging",
        runtime_statuses={"r1": "active", "r2": "expired"},
        blocked_record_ids={"r9"},
        committed_statuses={"old": "unknown"},
    )

    assert publisher.calls == 1
    assert result.published_rows == 3
    assert result.committed_statuses == {"r1": "active", "r2": "expired"}
    assert logs == [("Check auto-commit: passed_rows=3 written to committed workspace.", "success")]
