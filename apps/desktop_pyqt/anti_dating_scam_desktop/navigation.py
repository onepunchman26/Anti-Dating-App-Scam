from collections.abc import Callable

from PySide6.QtWidgets import QStackedWidget, QWidget


class Navigator:
    def __init__(self, stack: QStackedWidget) -> None:
        self.stack = stack
        self._screens: dict[str, QWidget] = {}
        self._history: list[str] = []
        self.current_name: str | None = None

    def add(self, name: str, widget: QWidget) -> None:
        self._screens[name] = widget
        self.stack.addWidget(widget)

    def go(self, name: str, *, remember: bool = True) -> None:
        if remember and self.current_name:
            self._history.append(self.current_name)
        widget = self._screens[name]
        self.current_name = name
        if hasattr(widget, "on_enter"):
            widget.on_enter()
        self.stack.setCurrentWidget(widget)

    def back(self) -> None:
        if self._history:
            self.go(self._history.pop(), remember=False)

    def bind(self, name: str) -> Callable[[], None]:
        return lambda: self.go(name)
