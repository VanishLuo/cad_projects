from __future__ import annotations

import subprocess
from pytest import MonkeyPatch

from license_management.adapters.ssh_command_executor import OpenSshCommandExecutor


class _Completed:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_success(monkeypatch: MonkeyPatch) -> None:
    def _fake_run(*args: object, **kwargs: object) -> _Completed:
        _ = (args, kwargs)
        return _Completed(0, "ok", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    executor = OpenSshCommandExecutor()

    code, out, err = executor.run(
        host="srv-a",
        username="ops",
        password=None,
        command="echo hello",
        timeout_seconds=10,
    )

    assert code == 0
    assert out == "ok"
    assert err == ""


def test_run_file_not_found(monkeypatch: MonkeyPatch) -> None:
    def _fake_run(*args: object, **kwargs: object) -> _Completed:
        _ = (args, kwargs)
        raise FileNotFoundError("ssh")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    executor = OpenSshCommandExecutor()

    code, out, err = executor.run(
        host="srv-a",
        username="ops",
        password=None,
        command="echo hello",
        timeout_seconds=10,
    )

    assert code == 127
    assert out == ""
    assert "not found" in err


def test_run_timeout(monkeypatch: MonkeyPatch) -> None:
    def _fake_run(*args: object, **kwargs: object) -> _Completed:
        _ = (args, kwargs)
        raise subprocess.TimeoutExpired(cmd="ssh", timeout=5, output="partial", stderr="slow")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    executor = OpenSshCommandExecutor()

    code, out, err = executor.run(
        host="srv-a",
        username="ops",
        password=None,
        command="echo hello",
        timeout_seconds=5,
    )

    assert code == 124
    assert out == "partial"
    assert "timed out" in err
