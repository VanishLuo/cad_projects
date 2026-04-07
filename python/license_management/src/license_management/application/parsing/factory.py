"""Default parser configuration factory implementations.

English:
Provides default implementations of parser factories that use
infrastructure configuration modules internally.

Chinese:
提供使用基础设施配置模块的解析器工厂默认实现。
"""

from __future__ import annotations

from license_management.application.parsing.interfaces import (
    ParserConfigFactory,
    ParserProfileProtocol,
    ParserRouteProtocol,
)


class DefaultParserConfigFactory(ParserConfigFactory):
    """Default parser configuration factory.

    English:
    Delegates to infrastructure configuration module.

    Chinese:
    委托给基础设施配置模块。
    """

    def create_parser_profile_config(self) -> ParserProfileProtocol:
        # Import here to decouple from infrastructure at protocol level
        from license_management.infrastructure.config.license_parser_config import (
            load_license_parser_config,
        )

        return load_license_parser_config()

    def create_parser_route_config(self) -> ParserRouteProtocol:
        # Import here to decouple from infrastructure at protocol level
        from license_management.infrastructure.config.license_parser_config import (
            load_license_parser_config,
        )

        return load_license_parser_config()
