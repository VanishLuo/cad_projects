"""Shared configuration layer.

English:
Consolidated configuration interfaces and implementations moved from infrastructure.
Provides decoupled configuration access for upper layers.

Chinese：
从基础设施层整合的配置接口和实现。为上层提供解耦的配置访问。
"""

from license_management.shared.config.interfaces import (
    TableConfigProtocol,
    TableConfigFactory,
)
from license_management.shared.config.factory import DefaultTableConfigFactory
from license_management.shared.config.table_header_config import (
    TableHeaderConfig,
    load_table_header_config,
)
from license_management.shared.config.ssh_credentials_config import (
    SshCredentials,
    load_ssh_credentials,
)
from license_management.shared.config.license_parser_config import (
    LicenseParserConfig,
    ParserProfileConfig,
    ParserRouteConfig,
    load_license_parser_config,
)

__all__ = [
    # Table configuration
    "TableConfigProtocol",
    "TableConfigFactory",
    "DefaultTableConfigFactory",
    "TableHeaderConfig",
    "load_table_header_config",
    # SSH credentials
    "SshCredentials",
    "load_ssh_credentials",
    # Parser configuration
    "LicenseParserConfig",
    "ParserProfileConfig",
    "ParserRouteConfig",
    "load_license_parser_config",
]
