from __future__ import annotations

from license_management.application.record_check_service import RecordCheckIssue
from license_management.gui.check.check_completion_controller import (
    CheckAnalysisResult,
    CheckIssueGrouping,
)
from license_management.gui.check.check_result_presenter import CheckResultPresenter


def _issue(record_id: str, status: str, reason: str) -> RecordCheckIssue:
    return RecordCheckIssue(
        record_id=record_id,
        status=status,
        reason=reason,
        license_file_path="/tmp/license.dat",
    )


def test_present_without_blocking_issues_skips_dialog_and_builds_info_logs() -> None:
    presenter = CheckResultPresenter()
    mapped = [_issue("r1", "custom", "warn")]
    analysis = CheckAnalysisResult(
        grouped=CheckIssueGrouping(license=[], ssh=[], start=[], other=mapped),
        active_count=1,
        expired_count=0,
        unknown_count=0,
        blocking_issues=[],
        blocked_record_ids=set(),
    )

    result = presenter.present(mapped_issues=mapped, analysis=analysis, published_rows=2)

    assert result.show_dialog is False
    assert result.summary_level == "success"
    assert "blocking_issues=0" in result.summary_message
    assert result.event_issue_count == 0
    assert len(result.issue_logs) == 1
    assert result.issue_logs[0].level == "info"
    assert "check_non_blocking_issue" in result.issue_logs[0].message


def test_present_with_blocking_issues_shows_dialog_and_error_logs() -> None:
    presenter = CheckResultPresenter()
    blocking = [_issue("r1", "license_not_found", "missing")]
    mapped = blocking + [_issue("r2", "custom", "warn")]
    analysis = CheckAnalysisResult(
        grouped=CheckIssueGrouping(license=blocking, ssh=[], start=[], other=[mapped[1]]),
        active_count=0,
        expired_count=1,
        unknown_count=1,
        blocking_issues=blocking,
        blocked_record_ids={"r1"},
    )

    result = presenter.present(mapped_issues=mapped, analysis=analysis, published_rows=0)

    assert result.show_dialog is True
    assert result.summary_level == "error"
    assert "issues=2" in result.summary_message
    assert result.event_issue_count == 2
    assert len(result.issue_logs) == 2
    assert all(item.level == "error" for item in result.issue_logs)
    assert "check_issue" in result.issue_logs[0].message


def test_present_adds_omitted_line_when_issue_logs_exceed_limit() -> None:
    presenter = CheckResultPresenter()
    mapped = [_issue(f"r{index}", "custom", "warn") for index in range(20)]
    analysis = CheckAnalysisResult(
        grouped=CheckIssueGrouping(license=[], ssh=[], start=[], other=mapped),
        active_count=0,
        expired_count=0,
        unknown_count=20,
        blocking_issues=[],
        blocked_record_ids=set(),
    )

    result = presenter.present(mapped_issues=mapped, analysis=analysis, published_rows=0)

    assert len(result.issue_logs) == 13
    assert "omitted 8 more issue(s)" in result.issue_logs[-1].message
