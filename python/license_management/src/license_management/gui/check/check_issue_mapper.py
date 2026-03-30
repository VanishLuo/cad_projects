from __future__ import annotations

from license_management.application.record_check_service import RecordCheckIssue


class CheckIssueMapper:
    """Map raw check issue reasons into stable user-facing taxonomy strings."""

    def map_issue(self, issue: RecordCheckIssue) -> RecordCheckIssue:
        reason = issue.reason.strip()
        lower_reason = reason.lower()

        mapped_reason = reason
        if issue.status == "license_not_found":
            mapped_reason = "FileNotFoundError: license file not found"
        elif issue.status == "ssh_failed":
            if "timed out" in lower_reason or "timeout" in lower_reason:
                mapped_reason = "TimeoutError: SSH connection timed out"
            elif "permission denied" in lower_reason or "authentication failed" in lower_reason:
                mapped_reason = "PermissionError: SSH authentication failed"
            elif "host is empty" in lower_reason:
                mapped_reason = "ValueError: SSH host is empty"
            else:
                mapped_reason = "ConnectionError: SSH connection failed"
        elif issue.status == "start_command_error":
            if "exit code 127" in lower_reason or "not found" in lower_reason:
                mapped_reason = "FileNotFoundError: start executable not found"
            elif "permission denied" in lower_reason:
                mapped_reason = "PermissionError: start executable permission denied"
            else:
                mapped_reason = "RuntimeError: start command probe failed"

        if mapped_reason != reason:
            mapped_reason = f"{mapped_reason} | raw={reason}"

        return RecordCheckIssue(
            record_id=issue.record_id,
            status=issue.status,
            reason=mapped_reason,
            license_file_path=issue.license_file_path,
        )
