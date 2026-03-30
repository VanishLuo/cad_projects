from __future__ import annotations

from dataclasses import dataclass

from license_management.application.record_check_service import RecordCheckIssue
from license_management.gui.check.check_completion_controller import (
    CheckAnalysisResult,
    CheckIssueGrouping,
)
from license_management.gui.check.check_completion_coordinator import (
    CheckCompletionCoordinator,
    CheckCompletionHooks,
)
from license_management.gui.check.check_result_presenter import CheckLogEntry, CheckPresentation


@dataclass(slots=True)
class _Dialog:
    closed: bool = False
    modal_value: bool | None = None
    shown: bool = False
    raised: bool = False
    activated: bool = False

    def close(self) -> None:
        self.closed = True

    def setModal(self, modal: bool) -> None:
        self.modal_value = modal

    def show(self) -> None:
        self.shown = True

    def raise_(self) -> None:
        self.raised = True

    def activateWindow(self) -> None:
        self.activated = True


class _Presenter:
    def __init__(self, presentation: CheckPresentation) -> None:
        self._presentation = presentation

    def present(
        self,
        *,
        mapped_issues: list[RecordCheckIssue],
        analysis: CheckAnalysisResult,
        published_rows: int,
    ) -> CheckPresentation:
        _ = (mapped_issues, analysis, published_rows)
        return self._presentation


def _analysis() -> CheckAnalysisResult:
    issue = RecordCheckIssue(record_id="r1", status="ssh_failed", reason="x", license_file_path="")
    return CheckAnalysisResult(
        grouped=CheckIssueGrouping(license=[], ssh=[issue], start=[], other=[]),
        active_count=1,
        expired_count=2,
        unknown_count=3,
        blocking_issues=[issue],
        blocked_record_ids={"r1"},
    )


def test_coordinate_opens_dialog_and_reports_logs_and_event() -> None:
    created: list[_Dialog] = []
    logs: list[tuple[str, str]] = []
    events: list[tuple[str, dict[str, object]]] = []

    presentation = CheckPresentation(
        show_dialog=True,
        grouped=_analysis().grouped,
        summary_message="summary",
        summary_level="error",
        issue_logs=(CheckLogEntry(message="issue-line", level="error"),),
        event_issue_count=5,
    )

    def _create_dialog(
        _scanned: int,
        _grouped: dict[str, list[RecordCheckIssue]],
        _parent: object,
    ) -> _Dialog:
        dialog = _Dialog()
        created.append(dialog)
        return dialog

    coordinator = CheckCompletionCoordinator(
        presenter=_Presenter(presentation),
        create_dialog=_create_dialog,
        hooks=CheckCompletionHooks(
            append_log=lambda message, level: logs.append((message, level)),
            log_event=lambda event, fields: events.append((event, fields)),
        ),
    )

    old_dialog = _Dialog()
    result = coordinator.coordinate(
        scanned=10,
        mapped_issues=[],
        analysis=_analysis(),
        published_rows=0,
        current_dialog=old_dialog,
        parent=object(),
    )

    assert old_dialog.closed is True
    assert result is not None
    assert created and created[0].shown is True
    assert created[0].raised is True
    assert created[0].activated is True
    assert created[0].modal_value is False
    assert logs == [("summary", "error"), ("issue-line", "error")]
    assert events[0][0] == "check_completed"
    assert events[0][1]["scanned"] == 10
    assert events[0][1]["issues"] == 5


def test_coordinate_without_dialog_keeps_current_dialog() -> None:
    logs: list[tuple[str, str]] = []
    events: list[tuple[str, dict[str, object]]] = []

    presentation = CheckPresentation(
        show_dialog=False,
        grouped=_analysis().grouped,
        summary_message="ok",
        summary_level="success",
        issue_logs=(),
        event_issue_count=0,
    )
    coordinator = CheckCompletionCoordinator(
        presenter=_Presenter(presentation),
        create_dialog=lambda _scanned, _grouped, _parent: _Dialog(),
        hooks=CheckCompletionHooks(
            append_log=lambda message, level: logs.append((message, level)),
            log_event=lambda event, fields: events.append((event, fields)),
        ),
    )

    current = _Dialog()
    result = coordinator.coordinate(
        scanned=2,
        mapped_issues=[],
        analysis=_analysis(),
        published_rows=0,
        current_dialog=current,
        parent=object(),
    )

    assert result is current
    assert current.closed is False
    assert logs == [("ok", "success")]
    assert events[0][1]["issues"] == 0
