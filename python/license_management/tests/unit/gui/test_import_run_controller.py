from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any
from typing import cast

from license_management.gui.controllers.import_run_controller import _ImportWorker
from license_management.gui.controllers.import_run_controller import ImportRunController
from license_management.gui.qt_compat import QApplication


class _BlockingBinder:
    def __init__(self) -> None:
        self.release = threading.Event()
        self.calls: list[list[Path]] = []

    def import_files(self, file_paths: list[Path]) -> tuple[object, object]:
        self.calls.append(file_paths)
        self.release.wait(timeout=2.0)
        return {"ok": True}, {"count": len(file_paths)}


class _ImmediateBinder:
    def import_files(self, file_paths: list[Path]) -> tuple[object, object]:
        return file_paths, {"count": len(file_paths)}


class _FakeThread:
    def __init__(self, *, running: bool, wait_returns: list[bool]) -> None:
        self._running = running
        self._wait_returns = wait_returns
        self.quit_called = 0
        self.terminate_called = 0
        self.wait_calls: list[int] = []

    def isRunning(self) -> bool:  # noqa: N802 - Qt naming style
        return self._running

    def quit(self) -> None:
        self.quit_called += 1
        self._running = False

    def wait(self, timeout_ms: int) -> bool:
        self.wait_calls.append(timeout_ms)
        if self._wait_returns:
            return self._wait_returns.pop(0)
        return True

    def terminate(self) -> None:
        self.terminate_called += 1
        self._running = False


def _ensure_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return cast(QApplication, app)


def _pump_until(predicate: object, *, timeout_s: float = 2.0) -> bool:
    app = _ensure_qapp()
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        app.processEvents()
        if callable(predicate) and predicate():
            return True
        time.sleep(0.01)
    return False


def test_import_worker_emits_finished_payload() -> None:
    worker = _ImportWorker(cast(Any, _ImmediateBinder()), [Path("a.json"), Path("b.json")])
    captured: list[tuple[object, object]] = []
    worker.finished.connect(lambda result, report: captured.append((result, report)))

    worker.run()

    assert len(captured) == 1
    result, report = captured[0]
    assert result == [Path("a.json"), Path("b.json")]
    assert report == {"count": 2}


def test_start_rejects_parallel_run_and_finishes_cleanly() -> None:
    binder = _BlockingBinder()
    state_changes: list[bool] = []
    finished_payloads: list[tuple[object, object]] = []

    controller = ImportRunController(
        binder=cast(Any, binder),
        on_finished=lambda result, report: finished_payloads.append((result, report)),
        on_state_changed=state_changes.append,
    )

    started = controller.start([Path("x.json")])
    second_start = controller.start([Path("y.json")])
    assert started is True
    assert second_start is False
    assert controller.in_progress is True

    binder.release.set()
    assert _pump_until(lambda: len(finished_payloads) == 1)
    assert _pump_until(lambda: controller.in_progress is False)

    assert binder.calls == [[Path("x.json")]]
    assert finished_payloads[0][1] == {"count": 1}
    assert state_changes[0] is True
    assert state_changes[-1] is False


def test_shutdown_handles_non_running_thread() -> None:
    controller = ImportRunController(
        binder=cast(Any, _ImmediateBinder()),
        on_finished=lambda _result, _report: None,
    )
    controller._thread = _FakeThread(running=False, wait_returns=[])  # type: ignore[assignment]

    controller.shutdown()

    assert controller._thread is None


def test_shutdown_forces_terminate_when_wait_times_out() -> None:
    state_changes: list[bool] = []
    controller = ImportRunController(
        binder=cast(Any, _ImmediateBinder()),
        on_finished=lambda _result, _report: None,
        on_state_changed=state_changes.append,
    )
    controller._in_progress = True
    controller._worker = cast(_ImportWorker, object())
    fake_thread = _FakeThread(running=True, wait_returns=[False, True])
    controller._thread = fake_thread  # type: ignore[assignment]

    controller.shutdown(wait_ms=1)

    assert fake_thread.quit_called == 1
    assert fake_thread.terminate_called == 1
    assert fake_thread.wait_calls == [1, 500]
    assert controller._thread is None
    assert controller._worker is None
    assert controller.in_progress is False
    assert state_changes[-1] is False

