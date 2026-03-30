from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from license_management.gui.flows.dialog_flows import DialogFlowBinder
from license_management.gui.qt_compat import QObject, QThread, pyqtSignal


class _ImportWorker(QObject):
    finished = pyqtSignal(object, object)

    def __init__(self, binder: DialogFlowBinder, file_paths: list[Path]) -> None:
        super().__init__()
        self._binder = binder
        self._file_paths = file_paths

    def run(self) -> None:
        result, report = self._binder.import_files(self._file_paths)
        self.finished.emit(result, report)


class ImportRunController:
    """Manage asynchronous import execution and thread lifecycle."""

    def __init__(
        self,
        *,
        binder: DialogFlowBinder,
        on_finished: Callable[[object, object], None],
        on_state_changed: Callable[[bool], None] | None = None,
        thread_factory: Callable[[], QThread] | None = None,
    ) -> None:
        self._binder = binder
        self._on_finished = on_finished
        self._on_state_changed = on_state_changed
        self._thread_factory = thread_factory
        self._in_progress = False
        self._thread: QThread | None = None
        self._worker: _ImportWorker | None = None

    @property
    def in_progress(self) -> bool:
        return self._in_progress

    def start(self, file_paths: list[Path]) -> bool:
        if self._in_progress:
            return False

        thread = self._thread_factory() if self._thread_factory is not None else QThread()
        worker = _ImportWorker(self._binder, file_paths)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._handle_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._handle_thread_finished)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker
        self._set_in_progress(True)
        thread.start()
        return True

    def _handle_finished(self, result_raw: object, report_raw: object) -> None:
        self._set_in_progress(False)
        self._worker = None
        self._on_finished(result_raw, report_raw)

    def _handle_thread_finished(self) -> None:
        self._thread = None

    def shutdown(self, *, wait_ms: int = 3000) -> None:
        thread = self._thread
        if thread is None:
            return
        if not thread.isRunning():
            self._thread = None
            return

        thread.quit()
        finished = thread.wait(wait_ms)
        if not finished:
            thread.terminate()
            thread.wait(500)
        self._thread = None
        self._worker = None
        self._set_in_progress(False)

    def _set_in_progress(self, value: bool) -> None:
        self._in_progress = value
        if self._on_state_changed is not None:
            self._on_state_changed(value)
