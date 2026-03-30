from __future__ import annotations

from dataclasses import dataclass

from license_management.application.record_check_service import RecordCheckIssue
from license_management.gui.check.check_completion_controller import (
    CheckAnalysisResult,
    CheckIssueGrouping,
)


@dataclass(slots=True, frozen=True)
class CheckLogEntry:
    message: str
    level: str


@dataclass(slots=True, frozen=True)
class CheckPresentation:
    show_dialog: bool
    grouped: CheckIssueGrouping
    summary_message: str
    summary_level: str
    issue_logs: tuple[CheckLogEntry, ...]
    event_issue_count: int


class CheckResultPresenter:
    """Build UI/log presentation model from check analysis results."""

    def present(
        self,
        *,
        mapped_issues: list[RecordCheckIssue],
        analysis: CheckAnalysisResult,
        published_rows: int,
    ) -> CheckPresentation:
        max_issue_log = 12

        if not analysis.blocking_issues:
            issue_entries: list[CheckLogEntry] = []
            for issue in mapped_issues[:max_issue_log]:
                issue_entries.append(
                    CheckLogEntry(
                        message=(
                            f"check_non_blocking_issue: record_id={issue.record_id} "
                            f"status={issue.status} reason={issue.reason}"
                        ),
                        level="info",
                    )
                )
            if len(mapped_issues) > max_issue_log:
                issue_entries.append(
                    CheckLogEntry(
                        message=(
                            "check_non_blocking_issue: omitted "
                            f"{len(mapped_issues) - max_issue_log} more issue(s)."
                        ),
                        level="info",
                    )
                )

            return CheckPresentation(
                show_dialog=False,
                grouped=analysis.grouped,
                summary_message=(
                    f"Check completed: active={analysis.active_count}, "
                    f"expired={analysis.expired_count}, unknown={analysis.unknown_count}, "
                    f"blocking_issues=0, total_issues={len(mapped_issues)}, "
                    f"auto_committed={published_rows}."
                ),
                summary_level="success",
                issue_logs=tuple(issue_entries),
                event_issue_count=0,
            )

        issue_entries = []
        for issue in mapped_issues[:max_issue_log]:
            issue_entries.append(
                CheckLogEntry(
                    message=(
                        f"check_issue: record_id={issue.record_id} "
                        f"status={issue.status} reason={issue.reason}"
                    ),
                    level="error",
                )
            )
        if len(mapped_issues) > max_issue_log:
            issue_entries.append(
                CheckLogEntry(
                    message=f"check_issue: omitted {len(mapped_issues) - max_issue_log} more issue(s).",
                    level="error",
                )
            )

        return CheckPresentation(
            show_dialog=True,
            grouped=analysis.grouped,
            summary_message=(
                f"Check completed: active={analysis.active_count}, "
                f"expired={analysis.expired_count}, unknown={analysis.unknown_count}, "
                f"issues={len(mapped_issues)}."
            ),
            summary_level=("error" if len(mapped_issues) > 0 else "success"),
            issue_logs=tuple(issue_entries),
            event_issue_count=len(mapped_issues),
        )
