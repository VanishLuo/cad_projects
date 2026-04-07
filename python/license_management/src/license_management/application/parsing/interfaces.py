"""Parser interfaces for decoupled parsing access.

English:
Provides protocol-based interfaces for parser configuration access, allowing
application layer to access parser configuration without depending on
infrastructure implementation details.

Chinese:
提供基于协议的解析器配置访问接口，允许应用层访问解析器配置而不依赖
基础设施实现细节。
"""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence


class ParserProfileEntryProtocol(Protocol):
    @property
    def feature_keyword(self) -> str: ...

    @property
    def feature_keywords(self) -> tuple[str, ...]: ...

    @property
    def feature_name_token_index(self) -> int: ...

    @property
    def quantity_regexes(self) -> tuple[str, ...]: ...

    @property
    def expiry_regexes(self) -> tuple[str, ...]: ...


class ParserRouteEntryProtocol(Protocol):
    @property
    def provider_pattern(self) -> str: ...

    @property
    def vendor_pattern(self) -> str: ...

    @property
    def profile(self) -> str: ...


class ParserProfileProtocol(Protocol):
    """Protocol for parser profile configuration.

    English:
    Application layer depends on this protocol for parser configuration,
    not the concrete infrastructure implementation.

    Chinese:
    应用层依赖此协议进行解析器配置，而非具体的基础设施实现。
    """

    @property
    def default_profile(self) -> str: ...

    @property
    def profiles(self) -> Mapping[str, ParserProfileEntryProtocol]: ...


class ParserRouteProtocol(Protocol):
    """Protocol for parser route configuration."""

    @property
    def routes(self) -> Sequence[ParserRouteEntryProtocol]: ...


class ParserConfigFactory(Protocol):
    """Factory for creating parser configuration instances."""

    def create_parser_profile_config(self) -> ParserProfileProtocol: ...

    def create_parser_route_config(self) -> ParserRouteProtocol: ...
