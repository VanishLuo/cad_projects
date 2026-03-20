from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ReleaseNote:
    version: str
    release_date: str
    features: tuple[str, ...]
    fixes: tuple[str, ...]
    known_issues: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class PublishRecord:
    version: str
    channel: str
    artifact_manifest: str
    published_at: str


def build_release_note(
    *,
    version: str,
    features: list[str],
    fixes: list[str],
    known_issues: list[str],
    release_date: str | None = None,
) -> ReleaseNote:
    date_value = release_date or datetime.utcnow().date().isoformat()
    return ReleaseNote(
        version=version,
        release_date=date_value,
        features=tuple(features),
        fixes=tuple(fixes),
        known_issues=tuple(known_issues),
    )


def write_release_note(note: ReleaseNote, output_path: Path) -> None:
    lines = [
        f"# Release {note.version}",
        "",
        f"Release Date: {note.release_date}",
        "",
        "## Features",
    ]
    lines.extend(f"- {item}" for item in note.features)
    lines.append("")
    lines.append("## Fixes")
    lines.extend(f"- {item}" for item in note.fixes)
    lines.append("")
    lines.append("## Known Issues")
    lines.extend(f"- {item}" for item in note.known_issues)
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_publish_record(record: PublishRecord, output_path: Path) -> None:
    output_path.write_text(
        json.dumps(
            {
                "version": record.version,
                "channel": record.channel,
                "artifact_manifest": record.artifact_manifest,
                "published_at": record.published_at,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
