"""Enhanced logging handler for error tracking.

English:
Custom logging handler that formats error codes and provides
structured logging for operational troubleshooting.

Chinese:
自定义日志处理器，格式化错误码并提供结构化日志用于运维排障。
"""

from __future__ import annotations

import logging
import json
from typing import Any, Dict
from datetime import datetime

from .error_codes import ErrorCode, LicenseManagementError


class ErrorTrackingHandler(logging.Handler):
    """Handler for structured error logging with error codes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_counts: Dict[str, int] = {}

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record with enhanced error tracking."""
        if not self.handleError(record):
            # Format the message
            message = self.format(record)

            # Track error codes
            if hasattr(record, 'error_code') and record.error_code:
                error_code = str(record.error_code)
                self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1

            # Output to console
            print(message)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for reporting."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_error_codes": len(self.error_counts),
            "error_counts": self.error_counts,
            "timestamp": datetime.now().isoformat()
        }


def setup_error_logging(level: str = "INFO") -> tuple[logging.Logger, ErrorTrackingHandler]:
    """Setup enhanced logging with error code support.

    Returns:
        Tuple of (logger, handler) for further configuration.
    """
    # Create logger
    logger = logging.getLogger("license_management")
    logger.setLevel(getattr(logging, level.upper()))

    # Create custom handler
    handler = ErrorTrackingHandler()

    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(error_code)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger, handler


# Helper function to log exceptions with error codes
def log_exception_with_code(
    logger: logging.Logger,
    error: LicenseManagementError,
    extra_context: Dict[str, Any] | None = None
) -> None:
    """Log an exception with its error code.

    Args:
        logger: Logger instance
        error: LicenseManagementError to log
        extra_context: Additional context to include in the log
    """
    log_data = {
        "error_code": error.error_code.value,
        "message": error.message,
        "context": error.context,
        "category": error.error_code.name,
        "severity": error.error_code.value[5],  # Extract severity digit
        "recoverable": error.error_code.value[5] in ['1', '2']
    }

    if extra_context:
        log_data.update(extra_context)

    # Map error codes to log levels
    log_levels = {
        '1': logging.INFO,      # Info
        '2': logging.WARNING,   # Warning
        '3': logging.ERROR,     # Error
        '4': logging.CRITICAL,  # Critical
    }

    severity = error.error_code.value[5]
    log_level = log_levels.get(severity, logging.ERROR)

    logger.log(
        log_level,
        f"Error occurred: {error.message}",
        extra={
            "error_code": error.error_code.value,
            "error_data": log_data
        }
    )


def create_error_context(
    operation: str,
    details: Dict[str, Any] | None = None,
    user_action: str | None = None
) -> Dict[str, Any]:
    """Create standardized error context.

    Args:
        operation: Operation that failed
        details: Additional details about the failure
        user_action: User action that triggered the error

    Returns:
        Dictionary with standardized error context
    """
    context = {
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "user_action": user_action
    }

    if details:
        context.update(details)

    return context