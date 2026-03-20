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


@dataclass(slots=True, frozen=True)
class DeploymentProfileResult:
    profile_name: str
    install_dir: str
    install_dir_is_absolute: bool
    install_dir_exists: bool
    is_supported: bool


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


def validate_deployment_profile(profile_name: str, install_dir: str) -> DeploymentProfileResult:
    normalized = Path(install_dir)
    supported_profiles = {"desktop-installer", "portable-zip", "enterprise-rollout"}
    return DeploymentProfileResult(
        profile_name=profile_name,
        install_dir=str(normalized),
        install_dir_is_absolute=normalized.is_absolute(),
        install_dir_exists=normalized.exists(),
        is_supported=profile_name in supported_profiles,
    )
