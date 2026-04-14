"""Deprecation notice for moved configurations.

English:
Configuration modules have been moved to shared/config/ to eliminate scattering
and improve clean architecture boundaries.

Chinese:
配置模块已移至shared/config/以消除分散并改进整洁架构边界。
"""

from __future__ import annotations

import warnings
from pathlib import Path

from license_management.shared.config.interfaces import SshCredentialsProtocol
from license_management.shared.config.license_parser_config import LicenseParserConfig
from license_management.shared.config.table_header_config import TableHeaderConfig

from license_management.shared.config import (
    load_table_header_config,
    load_ssh_credentials,
    load_license_parser_config,
)


def warn_about_move() -> None:
    """Issue deprecation warning when old config paths are used."""
    warnings.warn(
        "Configuration modules have been moved to shared/config/. "
        "Update your imports to use license_management.shared.config",
        DeprecationWarning,
        stacklevel=2,
    )


# Re-export with deprecation warnings
def load_table_header_config_with_warning() -> TableHeaderConfig:
    warn_about_move()
    return load_table_header_config()


def load_ssh_credentials_with_warning(project_root: Path) -> SshCredentialsProtocol:
    warn_about_move()
    return load_ssh_credentials(project_root)


def load_license_parser_config_with_warning() -> LicenseParserConfig:
    warn_about_move()
    return load_license_parser_config()
