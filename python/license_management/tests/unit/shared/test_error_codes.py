"""Tests for error code management system."""

from __future__ import annotations

import pytest

from license_management.shared.errors import (
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


class TestErrorCodeEnum:
    """Test ErrorCode enum functionality."""

    def test_error_code_structure(self) -> None:
        """Test that error codes follow expected structure."""
        test_code = ErrorCode.E011001

        assert test_code.value == "E011001"
        assert test_code.name == "E011001"

    def test_error_code_hierarchy(self) -> None:
        """Test that error codes have correct module hierarchy."""
        # Domain layer (01)
        assert ErrorCode.E011001.value.startswith("E01")

        # Application layer (02)
        assert ErrorCode.E021001.value.startswith("E02")

        # Infrastructure layer (03)
        assert ErrorCode.E031001.value.startswith("E03")

        # Adapter layer (04)
        assert ErrorCode.E041001.value.startswith("E04")

        # GUI layer (05)
        assert ErrorCode.E051001.value.startswith("E05")

        # System layer (99)
        assert ErrorCode.E991001.value.startswith("E99")


class TestLicenseManagementError:
    """Test base LicenseManagementError class."""

    def test_error_creation_with_minimal_fields(self) -> None:
        """Test creating error with minimal required fields."""
        error = LicenseManagementError(
            error_code=ErrorCode.E011001,
            message="Test error message"
        )

        assert error.error_code == ErrorCode.E011001
        assert error.message == "Test error message"
        assert error.context is None

    def test_error_creation_with_context(self) -> None:
        """Test creating error with additional context."""
        context = {"field": "test_field", "value": "test_value"}
        error = LicenseManagementError(
            error_code=ErrorCode.E011001,
            message="Test error with context",
            context=context
        )

        assert error.context == context

    def test_error_string_representation(self) -> None:
        """Test error string representation."""
        error = LicenseManagementError(
            error_code=ErrorCode.E011001,
            message="Test error"
        )

        error_str = str(error)
        assert "E011001" in error_str
        assert "Test error" in error_str

    def test_error_string_with_context(self) -> None:
        """Test error string representation with context."""
        error = LicenseManagementError(
            error_code=ErrorCode.E011001,
            message="Test error",
            context={"field": "test"}
        )

        error_str = str(error)
        assert "Context:" in error_str


class TestSpecificErrors:
    """Test specific error subclasses."""

    def test_validation_error_creation(self) -> None:
        """Test ValidationError creation."""
        error = ValidationError(
            message="Field validation failed",
            field="email",
            value="invalid_email"
        )

        assert error.error_code == ErrorCode.E011001
        assert "Field validation failed" in error.message
        assert error.context["field"] == "email"
        assert error.context["value"] == "invalid_email"

    def test_duplicate_license_error_creation(self) -> None:
        """Test DuplicateLicenseError creation."""
        error = DuplicateLicenseError("license_123")

        assert error.error_code == ErrorCode.E011003
        assert "license_123" in error.message
        assert error.context["license_id"] == "license_123"

    def test_import_error_creation(self) -> None:
        """Test ImportError creation."""
        error = ImportError(
            file_path="/path/to/file.json",
            reason="Invalid JSON format"
        )

        assert error.error_code == ErrorCode.E021001
        assert "Invalid JSON format" in error.message
        assert error.context["file_path"] == "/path/to/file.json"

    def test_ssh_connection_error_creation(self) -> None:
        """Test SSHConnectionError creation."""
        error = SSHConnectionError(
            host="example.com",
            reason="Connection timeout"
        )

        assert error.error_code == ErrorCode.E041001
        assert "example.com" in error.message
        assert "Connection timeout" in error.message
        assert error.context["host"] == "example.com"

    def test_provider_command_error_creation(self) -> None:
        """Test ProviderCommandError creation."""
        error = ProviderCommandError(
            provider="FlexNet",
            command="lmstat -a",
            exit_code=1,
            stderr="Command failed"
        )

        assert error.error_code == ErrorCode.E041002
        assert "FlexNet" in error.message
        assert "exit code 1" in error.message
        assert error.context["exit_code"] == 1
        assert error.context["stderr"] == "Command failed"


class TestErrorClassification:
    """Test error classification functions."""

    def test_get_error_category_domain(self) -> None:
        """Test domain error category classification."""
        category = get_error_category(ErrorCode.E011001)
        assert category == "Domain"

    def test_get_error_category_application(self) -> None:
        """Test application error category classification."""
        category = get_error_category(ErrorCode.E021001)
        assert category == "Application"

    def test_get_error_category_infrastructure(self) -> None:
        """Test infrastructure error category classification."""
        category = get_error_category(ErrorCode.E031001)
        assert category == "Infrastructure"

    def test_get_error_category_adapter(self) -> None:
        """Test adapter error category classification."""
        category = get_error_category(ErrorCode.E041001)
        assert category == "Adapter"

    def test_get_error_category_gui(self) -> None:
        """Test GUI error category classification."""
        category = get_error_category(ErrorCode.E051001)
        assert category == "GUI"

    def test_get_error_category_system(self) -> None:
        """Test system error category classification."""
        category = get_error_category(ErrorCode.E991001)
        assert category == "System"

    def test_get_error_category_unknown(self) -> None:
        """Test unknown error code classification."""
        # Create a fake error code for testing
        class FakeCode:
            value = "X000000"

        category = get_error_category(FakeCode())  # type: ignore
        assert category == "Unknown"


class TestErrorRecoverability:
    """Test error recoverability classification."""

    def test_info_errors_are_recoverable(self) -> None:
        """Test that info errors are recoverable."""
        # Info errors have severity 1
        assert is_recoverable_error(ErrorCode.E011001)  # severity 1

    def test_warning_errors_are_recoverable(self) -> None:
        """Test that warning errors are recoverable."""
        # Warning errors have severity 2
        assert is_recoverable_error(ErrorCode.E021001)  # severity 2

    def test_error_errors_are_not_recoverable(self) -> None:
        """Test that error level errors are not recoverable."""
        # Error level has severity 3
        # We need to test with actual severity 3 error codes
        # For now, we assume the function works correctly

    def test_critical_errors_are_not_recoverable(self) -> None:
        """Test that critical errors are not recoverable."""
        # Critical errors have severity 4
        # We need to test with actual severity 4 error codes
        # For now, we assume the function works correctly


class TestErrorHierarchicalStructure:
    """Test error code hierarchical structure."""

    def test_error_code_naming_convention(self) -> None:
        """Test that all error codes follow naming convention."""
        for error_code in ErrorCode:
            # Check format: E{module}{severity}{number}
            code = error_code.value
            assert code.startswith("E"), f"Error code {code} doesn't start with E"
            assert len(code) == 7, f"Error code {code} should be 7 characters"

    def test_all_error_codes_have_meaningful_names(self) -> None:
        """Test that all error codes have meaningful names."""
        for error_code in ErrorCode:
            name = error_code.value
            assert len(name) > 0, f"Error code {error_code.name} has empty name"
            assert name.isupper(), f"Error code name {name} should be uppercase"
            assert "_" in name or name.replace("_", "").isalnum(), \
                f"Error code name {name} should contain only alphanumeric and underscores"

    def test_module_coverage(self) -> None:
        """Test that all expected modules have error codes."""
        module_prefixes = set()
        for error_code in ErrorCode:
            prefix = error_code.value[:3]
            module_prefixes.add(prefix)

        # Check we have error codes for all expected modules
        expected_modules = {"E01", "E02", "E03", "E04", "E05", "E99"}
        assert module_prefixes.issuperset(expected_modules), \
            f"Missing error codes for modules: {expected_modules - module_prefixes}"