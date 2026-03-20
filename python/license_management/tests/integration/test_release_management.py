from __future__ import annotations

import json
from pathlib import Path

from license_management.shared.release_management import (
    PublishRecord,
    build_release_note,
    write_publish_record,
    write_release_note,
)


def test_release_note_and_publish_record_written(tmp_path: Path) -> None:
    note = build_release_note(
        version="0.1.0",
        features=["GUI workflow integration", "Feature-level search"],
        fixes=["Import dedup report accuracy"],
        known_issues=["SQLite resource warning under test runner"],
        release_date="2026-03-20",
    )

    note_path = tmp_path / "RELEASE_NOTES.md"
    write_release_note(note, note_path)
    note_text = note_path.read_text(encoding="utf-8")
    assert "Release 0.1.0" in note_text
    assert "## Features" in note_text

    record = PublishRecord(
        version="0.1.0",
        channel="stable",
        artifact_manifest="manifest.json",
        published_at="2026-03-20T12:00:00Z",
    )
    record_path = tmp_path / "publish_record.json"
    write_publish_record(record, record_path)
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    assert payload["channel"] == "stable"
