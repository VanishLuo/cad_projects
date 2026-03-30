from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SshCredentials:
    username: str
    password: str


def load_ssh_credentials(project_root: Path) -> SshCredentials:
    """Load SSH credentials from external sources.

    Priority:
    1) username from JSON file (default: <project_root>/config/ssh_credentials.json)
    2) password from environment variable LM_SSH_PASSWORD, fallback to JSON file
    """

    file_path = os.getenv("LM_SSH_CREDENTIALS_FILE", "").strip()
    if file_path:
        config_file = Path(file_path)
    else:
        config_file = project_root / "config" / "ssh_credentials.json"

    file_username = ""
    file_password = ""
    if config_file.exists() and config_file.is_file():
        try:
            raw = json.loads(config_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                file_username = str(raw.get("username", "")).strip()
                file_password = str(raw.get("password", "")).strip()
        except ValueError:
            # Ignore malformed file and fall back to environment/defaults.
            pass

    username = file_username or "operator"
    password = os.getenv("LM_SSH_PASSWORD", "").strip() or file_password
    return SshCredentials(username=username, password=password)
