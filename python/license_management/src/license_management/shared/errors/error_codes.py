"""Error code management and exception taxonomy.

English:
Centralized error codes and exception definitions for the license management system.
Following the error code taxonomy defined in M02_T2.4.

Chinese:
许可证管理系统的统一错误码和异常定义。
遵循M02_T2.4中定义的错误码分层体系。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any


class ErrorCode(enum.Enum):
    """Centralized error codes with hierarchical structure.

    English:
    Error codes follow the pattern E{module}{severity}{number}
    Module: 01=domain, 02=application, 03=infrastructure, 04=adapters, 05=gui
    Severity: 1=info, 2=warning, 3=error, 4=critical

    Chinese:
    错误码遵循 E{模块}{严重程度}{编号} 的模式
    模块：01=领域层，02=应用层，03=基础设施层，04=适配器层，05=GUI层
    严重程度：1=信息，2=警告，3=错误，4=严重
    """

    # Domain layer errors (01) - Severity 1=info, 2=warning, 3=error, 4=critical
    E011001 = "E011001"  # License record validation failed
    E011002 = "E011002"  # Invalid expiration date
    E011003 = "E011003"  # Duplicate license detected
    E011004 = "E011004"  # License not found

    # Application layer errors (02)
    E021001 = "E021001"  # Import validation error
    E021002 = "E021002"  # Parser config error
    E021003 = "E021003"  # Comparison engine error
    E021004 = "E021004"  # Expire calculation error

    # Infrastructure layer errors (03)
    E031001 = "E031001"  # Database connection error
    E031002 = "E031002"  # Migration failed
    E031003 = "E031003"  # Backup restore error
    E031004 = "E031004"  # Config load error

    # Adapter layer errors (04)
    E041001 = "E041001"  # SSH connection failed
    E041002 = "E041002"  # Provider command error
    E041003 = "E041003"  # Remote file access error
    E041004 = "E041004"  # Adapter protocol error

    # GUI layer errors (05)
    E051001 = "E051001"  # UI validation error
    E051002 = "E051002"  # Dialog flow error
    E051003 = "E051003"  # User input error
    E051004 = "E051004"  # State sync error

    # System errors (99)
    E991001 = "E991001"  # System initialization error
    E991002 = "E991002"  # Dependency injection error
    E991003 = "E991003"  # Unexpected error


@dataclass(slots=True)
class LicenseManagementError(Exception):
    """Base exception for the license management system.

    English:
    All custom exceptions inherit from this base class.
    Includes error code, message, and optional context data.

    Chinese:
    所有自定义异常的基类。
    包含错误码、消息和可选的上下文数据。
    """

    error_code: ErrorCode
    message: str
    context: dict[str, Any] | None = None

    def __str__(self) -> str:
        context_str = f" | Context: {self.context}" if self.context else ""
        return f"[{self.error_code.value}] {self.message}{context_str}"


# Specific exception classes for better error handling
class ValidationError(LicenseManagementError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        super().__init__(
            error_code=ErrorCode.E011001,
            message=message,
            context={"field": field, "value": value} if field or value else None,
        )


class DuplicateLicenseError(LicenseManagementError):
    """Raised when duplicate license is detected."""

    def __init__(self, license_id: str):
        super().__init__(
            error_code=ErrorCode.E011003,
            message=f"Duplicate license detected: {license_id}",
            context={"license_id": license_id},
        )


class ImportError(LicenseManagementError):
    """Raised when import operation fails."""

    def __init__(self, file_path: str | None = None, reason: str | None = None):
        super().__init__(
            error_code=ErrorCode.E021001,
            message=f"Import operation failed{f': {reason}' if reason else ''}",
            context={"file_path": file_path} if file_path else None,
        )


class SSHConnectionError(LicenseManagementError):
    """Raised when SSH connection fails."""

    def __init__(self, host: str, reason: str | None = None):
        super().__init__(
            error_code=ErrorCode.E041001,
            message=f"SSH connection to {host} failed{f': {reason}' if reason else ''}",
            context={"host": host},
        )


class ProviderCommandError(LicenseManagementError):
    """Raised when provider command execution fails."""

    def __init__(self, provider: str, command: str, exit_code: int, stderr: str):
        super().__init__(
            error_code=ErrorCode.E041002,
            message=f"Provider {provider} command failed with exit code {exit_code}",
            context={
                "provider": provider,
                "command": command,
                "exit_code": exit_code,
                "stderr": stderr,
            },
        )


def get_error_category(error_code: ErrorCode) -> str:
    """Get the category of an error code.

    English:
    Returns the module category based on the error code prefix.

    Chinese:
    根据错误码前缀返回模块类别。
    """
    prefix = error_code.value[:3]
    categories = {
        "E01": "Domain",
        "E02": "Application",
        "E03": "Infrastructure",
        "E04": "Adapter",
        "E05": "GUI",
        "E99": "System",
    }
    return categories.get(prefix, "Unknown")


def is_recoverable_error(error_code: ErrorCode) -> bool:
    """Check if an error is recoverable.

    English:
    Errors with severity 1-2 are recoverable, 3-4 are not.

    Chinese:
    严重程度为1-2的错误可恢复，3-4不可恢复。
    """
    severity_code = int(error_code.value[3])
    return severity_code <= 2
