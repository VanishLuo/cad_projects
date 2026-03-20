from __future__ import annotations

from datetime import datetime, timedelta

from license_management.shared.ops_triage import TelemetryEvent, triage_events


def _event(
    *,
    event_id: str,
    category: str,
    message: str,
    impact_score: int,
    affected_users: int,
    created_at: datetime,
) -> TelemetryEvent:
    return TelemetryEvent(
        event_id=event_id,
        source="gui",
        category=category,
        message=message,
        impact_score=impact_score,
        affected_users=affected_users,
        created_at=created_at,
    )


def test_triage_events_classifies_severity_value_and_queue() -> None:
    t0 = datetime(2026, 3, 20, 10, 0, 0)
    summary = triage_events(
        [
            _event(
                event_id="e-1",
                category="runtime",
                message="critical crash on startup",
                impact_score=92,
                affected_users=5,
                created_at=t0,
            ),
            _event(
                event_id="e-2",
                category="install",
                message="installer timeout on slow disk",
                impact_score=75,
                affected_users=3,
                created_at=t0 + timedelta(minutes=1),
            ),
            _event(
                event_id="e-3",
                category="ui",
                message="minor typo in message",
                impact_score=20,
                affected_users=1,
                created_at=t0 + timedelta(minutes=2),
            ),
        ]
    )

    assert summary.p0_count == 1
    assert summary.p1_count == 1
    assert summary.p2_count == 1

    by_id = {item.event_id: item for item in summary.items}
    assert by_id["e-1"].severity == "P0"
    assert by_id["e-1"].value == "high"
    assert by_id["e-1"].owner_queue == "backend"

    assert by_id["e-2"].severity == "P1"
    assert by_id["e-2"].value == "medium"
    assert by_id["e-2"].owner_queue == "release"

    assert by_id["e-3"].severity == "P2"
    assert by_id["e-3"].owner_queue == "triage"
