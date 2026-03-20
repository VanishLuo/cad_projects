from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class BacklogItem:
    item_id: str
    title: str
    severity: str
    business_value: str
    effort: str
    owner: str


@dataclass(slots=True, frozen=True)
class BacklogSnapshot:
    items: tuple[BacklogItem, ...]


def _rank(item: BacklogItem) -> tuple[int, int, int, str]:
    severity_rank = {"P0": 0, "P1": 1, "P2": 2}.get(item.severity, 3)
    value_rank = {"high": 0, "medium": 1, "normal": 2}.get(item.business_value, 3)
    effort_rank = {"small": 0, "medium": 1, "large": 2}.get(item.effort, 3)
    return severity_rank, value_rank, effort_rank, item.item_id


def prioritize_backlog(items: list[BacklogItem]) -> BacklogSnapshot:
    ordered = sorted(items, key=_rank)
    return BacklogSnapshot(items=tuple(ordered))


def write_backlog_snapshot(snapshot: BacklogSnapshot, output_path: Path) -> None:
    payload = [
        {
            "item_id": item.item_id,
            "title": item.title,
            "severity": item.severity,
            "business_value": item.business_value,
            "effort": item.effort,
            "owner": item.owner,
        }
        for item in snapshot.items
    ]
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
