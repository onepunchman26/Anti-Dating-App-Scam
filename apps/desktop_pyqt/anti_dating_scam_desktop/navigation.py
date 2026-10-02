from collections.abc import Callable

from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QApplication, QFrame, QScrollArea, QStackedWidget, QWidget


class _ScreenViewport(QScrollArea):
    """Scroll focused descendants into view, including programmatic focus."""

    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setWidget(widget)
        self._focus_timer = QTimer(self)
        self._focus_timer.setSingleShot(True)
        self._focus_timer.timeout.connect(self._reveal_focus)
        # A Qt slot uses this viewport as its receiver, so rebuilding the shell
        # disconnects it automatically when the old viewport is destroyed.
        QApplication.instance().focusChanged.connect(self._focus_changed)

    @Slot(QWidget, QWidget)
    def _focus_changed(self, _previous, current) -> None:
        if self.isVisible() and current is not None and self.widget().isAncestorOf(current):
            # Wait until pending layout changes have established the control's
            # geometry. The child timer is destroyed with its page viewport.
            self._focus_timer.start(0)

    @Slot()
    def _reveal_focus(self) -> None:
        current = QApplication.focusWidget()
        if self.isVisible() and current is not None and self.widget().isAncestorOf(current):
            self.ensureWidgetVisible(current)


class Navigator:
    def __init__(self, stack: QStackedWidget) -> None:
        self.stack = stack
        self._screens: dict[str, QWidget] = {}
        self._viewports: dict[str, QScrollArea] = {}
        self._history: list[str] = []
        self.current_name: str | None = None

    def add(self, name: str, widget: QWidget) -> None:
        self._screens[name] = widget
        # A stacked layout takes the minimum size of every page, including
        # hidden ones. Keep each page alive in its own scroll area so a tall
        # form cannot enlarge the whole window or hide its bottom controls.
        viewport = _ScreenViewport(widget)
        self._viewports[name] = viewport
        self.stack.addWidget(viewport)

    def go(self, name: str, *, remember: bool = True) -> None:
        if remember and self.current_name:
            self._history.append(self.current_name)
        widget = self._screens[name]
        self.current_name = name
        if hasattr(widget, "on_enter"):
            widget.on_enter()
        self.stack.setCurrentWidget(self._viewports[name])

    def back(self) -> None:
        if self._history:
            self.go(self._history.pop(), remember=False)

    def bind(self, name: str) -> Callable[[], None]:
        return lambda: self.go(name)
