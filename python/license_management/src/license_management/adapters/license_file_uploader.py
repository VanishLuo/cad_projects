from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import ntpath
import subprocess


@dataclass(slots=True, frozen=True)
class UploadResult:
    success: bool
    remote_file_path: str
    detail: str


class LicenseFileUploader(Protocol):
    def upload(
        self,
        *,
        local_file_path: str,
        host: str,
        remote_dir: str,
        username: str,
        timeout_seconds: int,
    ) -> UploadResult: ...


class ScpLicenseFileUploader:
    """Upload local license file to remote Linux host via scp."""

    def upload(
        self,
        *,
        local_file_path: str,
        host: str,
        remote_dir: str,
        username: str,
        timeout_seconds: int,
    ) -> UploadResult:
        local_path = Path(local_file_path)
        if not local_path.exists() or not local_path.is_file():
            return UploadResult(
                success=False,
                remote_file_path="",
                detail=f"Local file not found: {local_file_path}",
            )

        file_name = ntpath.basename(local_file_path)
        remote_dir_norm = remote_dir.replace("\\", "/").rstrip("/")
        remote_file_path = f"{remote_dir_norm}/{file_name}"

        destination = f"{username}@{host}:{remote_file_path}"
        try:
            completed = subprocess.run(
                ["scp", str(local_path), destination],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return UploadResult(
                success=False,
                remote_file_path="",
                detail="scp command not found. Please install OpenSSH client.",
            )
        except subprocess.TimeoutExpired:
            return UploadResult(
                success=False,
                remote_file_path="",
                detail=f"Upload timed out after {timeout_seconds}s.",
            )

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            return UploadResult(
                success=False,
                remote_file_path="",
                detail=stderr or f"scp failed with exit code {completed.returncode}",
            )

        return UploadResult(
            success=True,
            remote_file_path=remote_file_path,
            detail=f"Uploaded to {remote_file_path}",
        )
