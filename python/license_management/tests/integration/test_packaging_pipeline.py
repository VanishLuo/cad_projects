from __future__ import annotations

import json
from pathlib import Path

from license_management.shared.packaging_pipeline import (
    build_manifest,
    sha256_of_file,
    write_manifest,
)


def test_build_manifest_and_write_manifest(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    exe_file = dist / "license-management.exe"
    exe_file.write_text("binary-content", encoding="utf-8")
    config_file = dist / "config.json"
    config_file.write_text('{"env":"prod"}', encoding="utf-8")

    manifest = build_manifest(
        product="license-management",
        version="0.1.0",
        target_platform="windows-x64",
        dist_dir=dist,
    )

    assert manifest.product == "license-management"
    assert len(manifest.artifacts) == 2
    assert any(item.name == "license-management.exe" for item in manifest.artifacts)

    output = tmp_path / "manifest.json"
    write_manifest(manifest, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["product"] == "license-management"
    assert len(payload["artifacts"]) == 2


def test_sha256_of_file_is_stable(tmp_path: Path) -> None:
    file_path = tmp_path / "artifact.bin"
    file_path.write_bytes(b"abc123")

    first = sha256_of_file(file_path)
    second = sha256_of_file(file_path)

    assert first == second
    assert len(first) == 64
