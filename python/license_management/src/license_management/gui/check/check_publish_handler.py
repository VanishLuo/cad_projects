from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from license_management.gui.check.check_completion_controller import CheckPublishResult


class CheckPublisherProtocol(Protocol):
    def publish_passing_rows_to_committed(
        self,
        *,
        runtime_statuses: dict[str, str],
        blocked_record_ids: set[str],
        committed_statuses: dict[str, str],
    ) -> CheckPublishResult: ...


@dataclass(slots=True)
class CheckPublishHooks:
    append_log: Callable[[str, str], None]


@dataclass(slots=True, frozen=True)
class CheckPublishOutcome:
    published_rows: int
    committed_statuses: dict[str, str]


class CheckPublishHandler:
    """Handle staging publish-to-committed logic and auto-commit logging."""

    def __init__(
        self,
        *,
        publisher: CheckPublisherProtocol,
        hooks: CheckPublishHooks,
    ) -> None:
        self._publisher = publisher
        self._hooks = hooks

    def publish_if_needed(
        self,
        *,
        current_workspace: str,
        runtime_statuses: dict[str, str],
        blocked_record_ids: set[str],
        committed_statuses: dict[str, str],
    ) -> CheckPublishOutcome:
        if current_workspace != "staging":
            return CheckPublishOutcome(
                published_rows=0, committed_statuses=dict(committed_statuses)
            )

        publish_result = self._publisher.publish_passing_rows_to_committed(
            runtime_statuses=runtime_statuses,
            blocked_record_ids=blocked_record_ids,
            committed_statuses=committed_statuses,
        )
        published_rows = publish_result.published_rows
        next_committed_statuses = dict(publish_result.committed_statuses)
        if published_rows > 0:
            self._hooks.append_log(
                f"Check auto-commit: passed_rows={published_rows} written to committed workspace.",
                "success",
            )
        return CheckPublishOutcome(
            published_rows=published_rows,
            committed_statuses=next_committed_statuses,
        )
