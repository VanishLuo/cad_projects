from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class WindowsCompatProbe:
    platform_system: str
    platform_release: str
    python_version: str
    path_separator: str
    cwd: str
    cwd_is_absolute: bool
    supports_long_paths: bool


def collect_windows_compat_probe() -> WindowsCompatProbe:
    cwd_path = Path.cwd()
    return WindowsCompatProbe(
        platform_system=platform.system(),
        platform_release=platform.release(),
        python_version=platform.python_version(),
        path_separator=os.path.sep,
        cwd=str(cwd_path),
        cwd_is_absolute=cwd_path.is_absolute(),
        supports_long_paths=sys.platform.startswith("win"),
    )
