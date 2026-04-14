"""Error management module for license management system."""

from .error_codes import (
    ErrorCode,
    LicenseManagementError,
    ValidationError,
    DuplicateLicenseError,
    ImportError,
    SSHConnectionError,
    ProviderCommandError,
    get_error_category,
    is_recoverable_error,
)

__all__ = [
    "ErrorCode",
    "LicenseManagementError",
    "ValidationError",
    "DuplicateLicenseError",
    "ImportError",
    "SSHConnectionError",
    "ProviderCommandError",
    "get_error_category",
    "is_recoverable_error",
]
