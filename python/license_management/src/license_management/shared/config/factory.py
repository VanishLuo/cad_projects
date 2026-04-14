"""Default configuration factory implementations.

English:
Provides default implementations of configuration factories that use
infrastructure configuration modules internally.

Chinese:
提供使用基础设施配置模块的配置工厂默认实现。
"""

from __future__ import annotations

from license_management.shared.config.interfaces import TableConfigFactory, TableConfigProtocol


class DefaultTableConfigFactory(TableConfigFactory):
    """Default table configuration factory.

    English:
    Delegates to infrastructure configuration module. This allows GUI
    layer to depend on protocol only.

    Chinese:
    委托给基础设施配置模块。这允许GUI层仅依赖协议。
    """

    def create_table_config(self) -> TableConfigProtocol:
        # Import here to decouple from infrastructure at protocol level
        from license_management.infrastructure.config.table_header_config import (
            load_table_header_config,
        )

        return load_table_header_config()
