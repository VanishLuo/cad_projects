from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class FileExistenceCheckResult:
    exists: bool
    detail: str = ""


class RemoteLicenseFileExistenceChecker(Protocol):
    """Reserved interface for checking file existence on remote server via SSH."""

    def check(
        self,
        *,
        host: str,
        username: str,
        remote_file_path: str,
        timeout_seconds: int,
    ) -> FileExistenceCheckResult: ...
