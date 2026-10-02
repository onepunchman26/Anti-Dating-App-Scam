"""Tiny QThread helper: run a blocking function off the UI thread."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QThread, QTimer, Signal, Slot


class FunctionWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any], parent=None) -> None:
        super().__init__(parent)
        self._fn = fn
        # Stay busy until queued result/error callbacks have reached the UI and
        # the native thread has actually exited, not just until run() returns.
        self.settled = False

    def run(self) -> None:  # executed on the worker thread
        try:
            result = self._fn()
        except Exception as exc:  # surfaced to the UI as a readable message
            self.failed.emit(str(exc))
            return
        self.finished_ok.emit(result)

    @Slot()
    def settle(self) -> None:
        """GUI-thread cleanup, after earlier result/error signals are delivered."""
        if not self.wait(0):
            QTimer.singleShot(10, self.settle)
            return
        self.settled = True
        owner = self.parent()
        if owner is not None and getattr(owner, "_active_worker", None) is self:
            owner._active_worker = None
        self.deleteLater()


def has_pending_workers(owner: Any) -> bool:
    """Include every child worker, even if multiple calls reused _active_worker."""
    return any(not worker.settled for worker in owner.findChildren(FunctionWorker))


def run_async(
    owner: Any,
    fn: Callable[[], Any],
    on_ok: Callable[[Any], None],
    on_error: Callable[[str], None],
) -> FunctionWorker:
    """Start ``fn`` on a worker thread; keep a reference on ``owner`` so the
    thread isn't garbage-collected mid-run."""
    worker = FunctionWorker(fn, parent=owner)
    worker.finished_ok.connect(on_ok)
    worker.failed.connect(on_error)
    worker.finished.connect(worker.settle)
    owner._active_worker = worker
    worker.start()
    return worker
