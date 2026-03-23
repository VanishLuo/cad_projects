from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class LicenseRecord:
    """Represents one license process record managed by the application."""

    record_id: str
    server_name: str
    provider: str
    feature_name: str
    process_name: str
    expires_on: date
    prot: str = ""
    vendor: str = ""
    start_executable_path: str = ""
    license_file_path: str = ""
    start_option_override: str = ""

    def is_expired(self, today: date) -> bool:
        return self.expires_on < today
