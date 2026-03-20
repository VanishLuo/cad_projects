from __future__ import annotations

import json
from pathlib import Path

from license_management.shared.backlog_management import (
    BacklogItem,
    prioritize_backlog,
    write_backlog_snapshot,
)


def test_backlog_prioritization_and_snapshot(tmp_path: Path) -> None:
    snapshot = prioritize_backlog(
        [
            BacklogItem("BL-3", "Minor UX tweak", "P2", "normal", "small", "ux"),
            BacklogItem("BL-1", "Startup crash", "P0", "high", "small", "backend"),
            BacklogItem("BL-2", "Install timeout", "P1", "medium", "medium", "release"),
        ]
    )

    assert [item.item_id for item in snapshot.items] == ["BL-1", "BL-2", "BL-3"]

    output = tmp_path / "backlog_snapshot.json"
    write_backlog_snapshot(snapshot, output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload[0]["item_id"] == "BL-1"
