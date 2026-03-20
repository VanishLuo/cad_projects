from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class TelemetryEvent:
    event_id: str
    source: str
    category: str
    message: str
    impact_score: int
    affected_users: int
    created_at: datetime


@dataclass(slots=True, frozen=True)
class TriageItem:
    event_id: str
    severity: str
    value: str
    owner_queue: str


@dataclass(slots=True, frozen=True)
class TriageSummary:
    items: tuple[TriageItem, ...]
    p0_count: int
    p1_count: int
    p2_count: int


def classify_severity(event: TelemetryEvent) -> str:
    if event.impact_score >= 90 or event.affected_users >= 20:
        return "P0"
    if event.impact_score >= 70 or event.affected_users >= 8:
        return "P1"
    return "P2"


def classify_value(event: TelemetryEvent) -> str:
    message = event.message.lower()
    if "crash" in message or "data loss" in message:
        return "high"
    if "slow" in message or "timeout" in message:
        return "medium"
    return "normal"


def assign_owner_queue(event: TelemetryEvent) -> str:
    if event.category in {"packaging", "install"}:
        return "release"
    if event.category in {"runtime", "service", "adapter"}:
        return "backend"
    return "triage"


def triage_events(events: list[TelemetryEvent]) -> TriageSummary:
    items: list[TriageItem] = []

    for event in sorted(events, key=lambda item: item.created_at):
        severity = classify_severity(event)
        value = classify_value(event)
        owner_queue = assign_owner_queue(event)
        items.append(
            TriageItem(
                event_id=event.event_id,
                severity=severity,
                value=value,
                owner_queue=owner_queue,
            )
        )

    p0 = sum(1 for item in items if item.severity == "P0")
    p1 = sum(1 for item in items if item.severity == "P1")
    p2 = sum(1 for item in items if item.severity == "P2")
    return TriageSummary(items=tuple(items), p0_count=p0, p1_count=p1, p2_count=p2)
