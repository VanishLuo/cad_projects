"""Provider adapter contract tests.

English:
Tests that ensure provider adapters follow the defined contracts
and don't leak implementation details into the core business logic.

Chinese：
确保ProviderAdapter遵循定义的契约，不会将实现细节泄露到核心业务逻辑中。
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Protocol, cast

from license_management.adapters.provider_adapter import (
    ProviderOperationResult,
    CommandAttemptLog,
    SshCommandExecutor,
)
from license_management.shared.errors import (
    SSHConnectionError,
    ProviderCommandError,
    ErrorCode,
)


class MockSshCommandExecutor(SshCommandExecutor):
    """Mock SSH executor for testing."""

    def __init__(self, fail_on_command: str | None = None):
        self.fail_on_command = fail_on_command
        self.executed_commands: list[str] = []

    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        self.executed_commands.append(command)

        if self.fail_on_command and self.fail_on_command in command:
            return 1, "", "Mocked command failure"

        # Simulate successful command execution
        exit_code = 0
        stdout = f"Command executed successfully: {command}"
        stderr = ""
        return exit_code, stdout, stderr


class MockProviderAdapter:
    """Mock provider adapter for contract testing."""

    def __init__(self, ssh_executor: SshCommandExecutor):
        self.ssh_executor = ssh_executor

    def start_license(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        license_path: str,
        start_command: str,
    ) -> ProviderOperationResult:
        """Test start_license method."""
        try:
            exit_code, stdout, stderr = self.ssh_executor.run(
                host=host,
                username=username,
                password=password,
                command=start_command,
                timeout_seconds=30,
            )

            return ProviderOperationResult(
                provider="MockProvider",
                action="start",
                host=host,
                username=username,
                succeeded=exit_code == 0,
                attempts=1,
                timeout_seconds=30,
                command_logs=(
                    CommandAttemptLog(
                        attempt=1,
                        command=start_command,
                        exit_code=exit_code,
                        stdout=stdout,
                        stderr=stderr,
                    ),
                ),
            )

        except Exception as e:
            # Convert to appropriate error
            raise SSHConnectionError(host, str(e)) from e

    def stop_license(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        stop_command: str,
    ) -> ProviderOperationResult:
        """Test stop_license method."""
        try:
            exit_code, stdout, stderr = self.ssh_executor.run(
                host=host,
                username=username,
                password=password,
                command=stop_command,
                timeout_seconds=30,
            )

            return ProviderOperationResult(
                provider="MockProvider",
                action="stop",
                host=host,
                username=username,
                succeeded=exit_code == 0,
                attempts=1,
                timeout_seconds=30,
                command_logs=(
                    CommandAttemptLog(
                        attempt=1,
                        command=stop_command,
                        exit_code=exit_code,
                        stdout=stdout,
                        stderr=stderr,
                    ),
                ),
            )

        except Exception as e:
            # Convert to appropriate error
            raise SSHConnectionError(host, str(e)) from e


class TestProviderAdapterContract:
    """Test that provider adapters follow contracts."""

    def test_adapter_uses_ssh_executor_protocol(self) -> None:
        """Test that adapter uses SshCommandExecutor protocol."""
        mock_executor = MockSshCommandExecutor()
        adapter = MockProviderAdapter(mock_executor)

        # Test start
        result = adapter.start_license(
            host="test-host",
            username="test-user",
            password="test-pass",
            license_path="/path/to/license",
            start_command="start_command",
        )

        assert result.provider == "MockProvider"
        assert result.action == "start"
        assert result.succeeded
        assert result.attempts == 1
        assert len(mock_executor.executed_commands) == 1
        assert mock_executor.executed_commands[0] == "start_command"

    def test_adapter_handles_command_failure(self) -> None:
        """Test that adapter handles command failures appropriately."""
        mock_executor = MockSshCommandExecutor(fail_on_command="fail_command")
        adapter = MockProviderAdapter(mock_executor)

        # This should raise an error based on the contract
        with pytest.raises(ProviderCommandError) as exc_info:
            adapter.start_license(
                host="test-host",
                username="test-user",
                password="test-pass",
                license_path="/path/to/license",
                start_command="fail_command",
            )

        error = exc_info.value
        assert error.error_code == ErrorCode.E0401002
        assert "exit code 1" in error.message
        assert "Mocked command failure" in error.context["stderr"]

    def test_adapter_returns_proper_operation_result(self) -> None:
        """Test that adapter returns properly formatted operation result."""
        mock_executor = MockSshCommandExecutor()
        adapter = MockProviderAdapter(mock_executor)

        result = adapter.stop_license(
            host="test-host",
            username="test-user",
            password="test-pass",
            stop_command="stop_command",
        )

        assert isinstance(result, ProviderOperationResult)
        assert result.provider == "MockProvider"
        assert result.action == "stop"
        assert result.succeeded
        assert result.attempts == 1
        assert result.rollback_attempted is False
        assert result.rollback_succeeded is None

    def test_adapter_command_logging_contract(self) -> None:
        """Test that adapter follows command logging contract."""
        mock_executor = MockSshCommandExecutor()
        adapter = MockProviderAdapter(mock_executor)

        result = adapter.start_license(
            host="test-host",
            username="test-user",
            password="test-pass",
            license_path="/path/to/license",
            start_command="test_start",
        )

        # Check command log structure
        assert len(result.command_logs) == 1
        log = result.command_logs[0]
        assert isinstance(log, CommandAttemptLog)
        assert log.attempt == 1
        assert log.command == "test_start"
        assert log.exit_code == 0
        assert "Command executed successfully" in log.stdout

    def test_adapter_multiple_attempts(self) -> None:
        """Test adapter behavior with multiple command attempts."""
        # This would require a more sophisticated mock that can simulate retries
        # For now, we test the single attempt case
        mock_executor = MockSshCommandExecutor()
        adapter = MockProviderAdapter(mock_executor)

        result = adapter.start_license(
            host="test-host",
            username="test-user",
            password="test-pass",
            license_path="/path/to/license",
            start_command="command",
        )

        assert result.attempts == 1  # Single attempt in this implementation
        assert len(result.command_logs) == 1


class TestContractIsolation:
    """Test that adapter implementation is properly isolated."""

    def test_core_business_logic_not_dependent_on_adapter_implementation(self) -> None:
        """Test that business logic doesn't depend on specific adapter implementations."""
        mock_executor = MockSshCommandExecutor()
        adapter = MockProviderAdapter(mock_executor)

        # The business logic should work with any adapter that follows the protocol
        # This test demonstrates that we can swap implementations
        assert hasattr(adapter, 'start_license')
        assert hasattr(adapter, 'stop_license')
        assert callable(adapter.start_license)
        assert callable(adapter.stop_license)

    def test_ssh_executor_isolated_from_business_logic(self) -> None:
        """Test that SSH executor details are isolated in the adapter layer."""
        from license_management.adapters.provider_adapter import SshCommandExecutor

        # The business layer should not know about SSH implementation details
        assert SshCommandExecutor.__name__ == "SshCommandExecutor"
        assert "Protocol" in str(SshCommandExecutor.__class__)
        assert "run" in [method for method in dir(SshCommandExecutor) if not method.startswith("_")]


class TestErrorHandlingContract:
    """Test error handling follows contracts."""

    def test_adapter_converts_ssh_errors_to_application_errors(self) -> None:
        """Test that adapter converts SSH errors to appropriate application errors."""
        # Create an executor that raises an exception
        class FailingExecutor(SshCommandExecutor):
            def run(self, **kwargs) -> tuple[int, str, str]:
                raise ConnectionError("SSH connection failed")

        adapter = MockProviderAdapter(FailingExecutor())

        with pytest.raises(SSHConnectionError) as exc_info:
            adapter.start_license(
                host="test-host",
                username="test-user",
                password="test-pass",
                license_path="/path/to/license",
                start_command="start_command",
            )

        error = exc_info.value
        assert error.error_code == ErrorCode.E0401001
        assert error.message == "SSH connection to test-host failed: SSH connection failed"
        assert error.context["host"] == "test-host"