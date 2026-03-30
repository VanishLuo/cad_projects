from __future__ import annotations

from license_management.application.record_check_service import RecordCheckIssue
from license_management.gui.check.check_issue_mapper import CheckIssueMapper


def _issue(status: str, reason: str) -> RecordCheckIssue:
    return RecordCheckIssue(
        record_id="r1",
        status=status,
        reason=reason,
        license_file_path="/tmp/license.dat",
    )


def test_map_issue_handles_license_not_found() -> None:
    mapped = CheckIssueMapper().map_issue(_issue("license_not_found", "raw message"))
    assert "FileNotFoundError" in mapped.reason
    assert "raw=raw message" in mapped.reason


def test_map_issue_handles_ssh_timeout() -> None:
    mapped = CheckIssueMapper().map_issue(_issue("ssh_failed", "connection timed out"))
    assert "TimeoutError" in mapped.reason


def test_map_issue_keeps_unknown_status_reason() -> None:
    mapped = CheckIssueMapper().map_issue(_issue("custom", "keep this"))
    assert mapped.reason == "keep this"
