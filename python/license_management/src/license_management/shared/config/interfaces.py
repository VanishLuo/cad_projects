"""Configuration interfaces for decoupled layer access.

English:
Provides protocol-based interfaces for configuration access, allowing
upper layers (GUI, Application) to access configuration without depending
on infrastructure implementation details.

Chinese:
提供基于协议的配置访问接口，允许上层（GUI、应用）访问配置而不依赖
基础设施实现细节。
"""

from __future__ import annotations

from typing import Protocol


class TableConfigProtocol(Protocol):
    """Protocol for table header configuration.

    English:
    GUI and application layers depend on this protocol for table
    configuration, not the concrete infrastructure implementation.

    Chinese:
    GUI和应用层依赖此协议进行表格配置，而非具体的基础设施实现。
    """

    @property
    def sqlite_table_name(self) -> str:
        """Get sqlite table name."""
        ...

    @property
    def sqlite_columns(self) -> dict[str, str]:
        """Get mapping of domain field to sqlite column name."""
        ...

    @property
    def sqlite_required_fields(self) -> tuple[str, ...]:
        """Get required fields for record creation."""
        ...

    @property
    def gui_column_order(self) -> tuple[str, ...]:
        """Get the order of GUI table columns."""
        ...

    @property
    def gui_headers(self) -> dict[str, str]:
        """Get the mapping of internal field names to GUI display headers."""
        ...

    @property
    def field_whitelist(self) -> tuple[str, ...]:
        """Get whitelist of import-allowed fields."""
        ...


class SshCredentialsProtocol(Protocol):
    """Protocol for SSH credentials."""

    username: str
    password: str


class TableConfigFactory(Protocol):
    """Factory for creating table configuration instances."""

    def create_table_config(self) -> TableConfigProtocol:
        """Create a table configuration instance."""
        ...
