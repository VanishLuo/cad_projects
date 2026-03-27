from __future__ import annotations

from collections.abc import Callable

from license_management.application.record_check_service import RecordCheckService
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.qt_compat import QObject, QThread, pyqtSignal


class _CheckWorker(QObject):
    finished = pyqtSignal(int, object, object)

    def __init__(self, checker: RecordCheckService, records: list[LicenseRecord]) -> None:
        super().__init__()
        self._checker = checker
        self._records = records

    def run(self) -> None:
        issues, runtime_statuses = self._checker.check_with_runtime(self._records)
        self.finished.emit(len(self._records), issues, runtime_statuses)


class CheckRunController:
    """Manage asynchronous check execution and thread lifecycle."""

    def __init__(
        self,
        *,
        checker: RecordCheckService,
        on_finished: Callable[[int, object, object], None],
        on_state_changed: Callable[[bool], None] | None = None,
        thread_factory: Callable[[], QThread] | None = None,
    ) -> None:
        self._checker = checker
        self._on_finished = on_finished
        self._on_state_changed = on_state_changed
        self._thread_factory = thread_factory
        self._in_progress = False
        self._thread: QThread | None = None
        self._worker: _CheckWorker | None = None

    @property
    def in_progress(self) -> bool:
        return self._in_progress

    def start(self, records: list[LicenseRecord]) -> bool:
        if self._in_progress:
            return False

        thread = self._thread_factory() if self._thread_factory is not None else QThread()
        worker = _CheckWorker(self._checker, records)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._handle_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker
        self._set_in_progress(True)
        thread.start()
        return True

    def _handle_finished(self, scanned: int, issues_raw: object, runtime_statuses_raw: object) -> None:
        self._set_in_progress(False)
        self._thread = None
        self._worker = None
        self._on_finished(scanned, issues_raw, runtime_statuses_raw)

    def _set_in_progress(self, value: bool) -> None:
        self._in_progress = value
        if self._on_state_changed is not None:
            self._on_state_changed(value)
