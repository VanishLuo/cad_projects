from __future__ import annotations

from license_management.gui.presenters.log_presenter import (
    EventFilterPresenter,
    LogLinePresenter,
    UiLogService,
)


def test_log_line_presenter_formats_html() -> None:
    html_line = LogLinePresenter().format_html(message="hello", level="info")
    assert "hello" in html_line
    assert "span" in html_line


def test_event_filter_presenter_filters_non_error_events() -> None:
    presenter = EventFilterPresenter()
    assert presenter.to_log_line(event="search_applied", fields={}) is None


def test_event_filter_presenter_formats_blocked_event() -> None:
    presenter = EventFilterPresenter()
    line = presenter.to_log_line(
        event="service_action_blocked",
        fields={"reason": "no_row", "record_id": "r1"},
    )
    assert line is not None
    assert "event=service_action_blocked" in line.message


def test_ui_log_service_appends_filtered_event() -> None:
    lines: list[str] = []
    service = UiLogService(append_html=lines.append)

    service.log_event("service_action_blocked", reason="no_row", record_id="r1")

    assert len(lines) == 1

