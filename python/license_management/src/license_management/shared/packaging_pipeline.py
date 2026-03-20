from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class BuildArtifact:
    name: str
    relative_path: str
    size_bytes: int
    sha256: str


@dataclass(slots=True, frozen=True)
class PackagingManifest:
    product: str
    version: str
    target_platform: str
    artifacts: tuple[BuildArtifact, ...]


def sha256_of_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    *,
    product: str,
    version: str,
    target_platform: str,
    dist_dir: Path,
) -> PackagingManifest:
    artifacts: list[BuildArtifact] = []

    for file_path in sorted(path for path in dist_dir.rglob("*") if path.is_file()):
        artifacts.append(
            BuildArtifact(
                name=file_path.name,
                relative_path=str(file_path.relative_to(dist_dir)).replace("\\", "/"),
                size_bytes=file_path.stat().st_size,
                sha256=sha256_of_file(file_path),
            )
        )

    return PackagingManifest(
        product=product,
        version=version,
        target_platform=target_platform,
        artifacts=tuple(artifacts),
    )


def write_manifest(manifest: PackagingManifest, output_path: Path) -> None:
    payload = {
        "product": manifest.product,
        "version": manifest.version,
        "target_platform": manifest.target_platform,
        "artifacts": [
            {
                "name": item.name,
                "relative_path": item.relative_path,
                "size_bytes": item.size_bytes,
                "sha256": item.sha256,
            }
            for item in manifest.artifacts
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
