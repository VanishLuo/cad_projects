from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from license_management.application.record_check_service import RecordCheckIssue
from license_management.gui.check.check_completion_controller import CheckAnalysisResult
from license_management.gui.check.check_result_presenter import CheckPresentation


class CheckDialogProtocol(Protocol):
    def close(self) -> None: ...

    def setModal(self, modal: bool) -> None: ...

    def show(self) -> None: ...

    def raise_(self) -> None: ...

    def activateWindow(self) -> None: ...


class CheckPresenterProtocol(Protocol):
    def present(
        self,
        *,
        mapped_issues: list[RecordCheckIssue],
        analysis: CheckAnalysisResult,
        published_rows: int,
    ) -> CheckPresentation: ...


@dataclass(slots=True)
class CheckCompletionHooks:
    append_log: Callable[[str, str], None]
    log_event: Callable[[str, dict[str, object]], None]


class CheckCompletionCoordinator:
    """Coordinate check completion presentation, dialog lifecycle, and event reporting."""

    def __init__(
        self,
        *,
        presenter: CheckPresenterProtocol,
        create_dialog: Callable[[int, dict[str, list[RecordCheckIssue]], Any], CheckDialogProtocol],
        hooks: CheckCompletionHooks,
    ) -> None:
        self._presenter = presenter
        self._create_dialog = create_dialog
        self._hooks = hooks

    def coordinate(
        self,
        *,
        scanned: int,
        mapped_issues: list[RecordCheckIssue],
        analysis: CheckAnalysisResult,
        published_rows: int,
        current_dialog: CheckDialogProtocol | None,
        parent: Any,
    ) -> CheckDialogProtocol | None:
        presentation = self._presenter.present(
            mapped_issues=mapped_issues,
            analysis=analysis,
            published_rows=published_rows,
        )

        next_dialog = current_dialog
        if presentation.show_dialog:
            if current_dialog is not None:
                current_dialog.close()
            next_dialog = self._open_dialog(
                scanned=scanned, presentation=presentation, parent=parent
            )

        self._hooks.append_log(presentation.summary_message, presentation.summary_level)
        self._hooks.log_event(
            "check_completed",
            {
                "scanned": scanned,
                "issues": presentation.event_issue_count,
                "active": analysis.active_count,
                "expired": analysis.expired_count,
                "unknown": analysis.unknown_count,
                "deleted": 0,
            },
        )
        for entry in presentation.issue_logs:
            self._hooks.append_log(entry.message, entry.level)

        return next_dialog

    def _open_dialog(
        self,
        *,
        scanned: int,
        presentation: CheckPresentation,
        parent: Any,
    ) -> CheckDialogProtocol:
        dialog = self._create_dialog(
            scanned,
            {
                "license": presentation.grouped.license,
                "ssh": presentation.grouped.ssh,
                "start": presentation.grouped.start,
                "other": presentation.grouped.other,
            },
            parent,
        )
        dialog.setModal(False)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog
