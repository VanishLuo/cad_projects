"""Parser configuration interfaces and factories.

English:
Provides protocol-based parser configuration access for decoupled architecture.

Chinese:
提供基于协议的解析器配置访问，用于解耦架构。
"""

from license_management.application.parsing.interfaces import (
    ParserConfigFactory,
    ParserProfileProtocol,
    ParserRouteProtocol,
)
from license_management.application.parsing.factory import DefaultParserConfigFactory

__all__ = [
    "ParserConfigFactory",
    "ParserProfileProtocol",
    "ParserRouteProtocol",
    "DefaultParserConfigFactory",
]
