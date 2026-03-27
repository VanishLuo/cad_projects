from __future__ import annotations

from collections import defaultdict

from license_management.adapters.flexnet_adapter import FlexNetAdapter


class StubSshExecutor:
    def __init__(self, responses: dict[str, list[tuple[int, str, str]]]) -> None:
        self._responses = defaultdict(list, responses)
        self.calls: list[tuple[str, str, str, int]] = []

    def run(
        self,
        *,
        host: str,
        username: str,
        password: str | None,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        self.calls.append((host, username, command, timeout_seconds))
        queue = self._responses[command]
        if queue:
            return queue.pop(0)
        return 1, "", "unexpected command"


def test_start_success_without_retry_or_rollback() -> None:
    executor = StubSshExecutor(
        {
            "lmgrd -c license.dat": [(0, "started", "")],
        }
    )
    adapter = FlexNetAdapter(executor, retry_times=2, timeout_seconds=15)

    result = adapter.start(host="srv-a", username="ops")

    assert result.succeeded is True
    assert result.attempts == 1
    assert result.rollback_attempted is False
    assert result.rollback_succeeded is None
    assert len(result.command_logs) == 1
    assert result.command_logs[0].command == "lmgrd -c license.dat"


def test_start_retries_until_success() -> None:
    executor = StubSshExecutor(
        {
            "lmgrd -c license.dat": [
                (1, "", "network timeout"),
                (0, "started", ""),
            ],
        }
    )
    adapter = FlexNetAdapter(executor, retry_times=2)

    result = adapter.start(host="srv-a", username="ops")

    assert result.succeeded is True
    assert result.attempts == 2
    assert [log.attempt for log in result.command_logs] == [1, 2]


def test_start_failure_triggers_rollback_stop() -> None:
    executor = StubSshExecutor(
        {
            "lmgrd -c license.dat": [
                (1, "", "cannot start"),
                (1, "", "still failed"),
            ],
            "lmutil lmdown -force": [(0, "stopped", "")],
        }
    )
    adapter = FlexNetAdapter(executor, retry_times=1)

    result = adapter.start(host="srv-a", username="ops")

    assert result.succeeded is False
    assert result.rollback_attempted is True
    assert result.rollback_succeeded is True
    assert len(result.command_logs) == 3
    assert result.command_logs[-1].command == "lmutil lmdown -force"


def test_stop_fails_after_all_retries() -> None:
    executor = StubSshExecutor(
        {
            "lmutil lmdown -force": [
                (1, "", "permission denied"),
                (1, "", "permission denied"),
                (1, "", "permission denied"),
            ]
        }
    )
    adapter = FlexNetAdapter(executor, retry_times=2)

    result = adapter.stop(host="srv-a", username="ops")

    assert result.succeeded is False
    assert result.attempts == 3
    assert all(log.command == "lmutil lmdown -force" for log in result.command_logs)


def test_start_override_failure_does_not_trigger_rollback() -> None:
    executor = StubSshExecutor(
        {
            "ls -l": [
                (127, "", "command not found"),
                (127, "", "command not found"),
            ],
            "lmutil lmdown -force": [(0, "stopped", "")],
        }
    )
    adapter = FlexNetAdapter(executor, retry_times=1, start_command_override="ls -l")

    result = adapter.start(host="srv-a", username="ops")

    assert result.succeeded is False
    assert result.rollback_attempted is False
    assert all(log.command == "ls -l" for log in result.command_logs)
