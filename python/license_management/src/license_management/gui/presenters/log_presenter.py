from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(slots=True, frozen=True)
class LogLine:
    message: str
    level: str


class LogLinePresenter:
    """Render log lines into styled HTML chunks for QTextEdit."""

    def format_html(self, *, message: str, level: str, now: datetime | None = None) -> str:
        stamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        color = "#333333"
        if level == "error":
            color = "#b00020"
        elif level == "success":
            color = "#1b5e20"

        text = html.escape(f"[{stamp}] {message}").replace("\n", "<br/>")
        return f'<span style="color:{color}; white-space:pre-wrap;">{text}</span>'


class EventFilterPresenter:
    """Filter technical events and map them to concise error log lines."""

    def to_log_line(self, *, event: str, fields: dict[str, object]) -> LogLine | None:
        if not (
            event.endswith("_failed")
            or event.endswith("_blocked")
            or event == "service_action_blocked"
        ):
            return None

        reason = str(fields.get("reason", "")).strip()
        detail = str(fields.get("detail", "")).strip()
        record_id = str(fields.get("record_id", "")).strip()
        pieces = [f"event={event}"]
        if record_id:
            pieces.append(f"record_id={record_id}")
        if reason:
            pieces.append(f"reason={reason}")
        if detail:
            pieces.append(f"detail={detail}")
        return LogLine(message=" | ".join(pieces), level="error")


class UiLogService:
    """Compose event filtering and line formatting for GUI log output."""

    def __init__(
        self,
        *,
        append_html: Callable[[str], None],
        line_presenter: LogLinePresenter | None = None,
        event_presenter: EventFilterPresenter | None = None,
    ) -> None:
        self._append_html = append_html
        self._line_presenter = line_presenter or LogLinePresenter()
        self._event_presenter = event_presenter or EventFilterPresenter()

    def append(self, message: str, *, level: str = "info") -> None:
        self._append_html(self._line_presenter.format_html(message=message, level=level))

    def log_event(self, event: str, **fields: object) -> None:
        log_line = self._event_presenter.to_log_line(event=event, fields=fields)
        if log_line is None:
            return
        self.append(log_line.message, level=log_line.level)
