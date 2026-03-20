from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class UiLicenseRow:
    record_id: str
    server_name: str
    provider: str
    feature_name: str
    process_name: str
    expires_on: date
    status: str
    highlight_level: str
    matched_terms: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class FeedbackMessage:
    level: str
    title: str
    detail: str
    action: str | None = None


class FeedbackCenter:
    def __init__(self) -> None:
        self._messages: list[FeedbackMessage] = []

    @property
    def messages(self) -> tuple[FeedbackMessage, ...]:
        return tuple(self._messages)

    @property
    def latest(self) -> FeedbackMessage | None:
        if not self._messages:
            return None
        return self._messages[-1]

    def add(self, message: FeedbackMessage) -> None:
        self._messages.append(message)

    def clear(self) -> None:
        self._messages.clear()
