"""Native checkbox behavior with a complete, wrapping plain-text disclosure."""

from PySide6.QtCore import QEvent, QPoint, QSize, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QWidget,
)


class WrappedCheckBox(QCheckBox):
    """Keep native state, signals, focus and accessibility; wrap only the label.

    QCheckBox's native single-line text drives an unbounded minimum width. Its
    native indicator is retained, while a mouse-transparent QLabel supplies the
    visible text. Clicking anywhere on the disclosure still activates the native
    checkbox, as does Space when it has keyboard focus.
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.label = QLabel(self)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setWordWrap(True)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._text_layout = QHBoxLayout(self)
        self._text_layout.setSpacing(0)
        self._text_layout.addWidget(self.label)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setText(text)
        self._update_indicator_margin()

    def text(self) -> str:
        return self.label.text()

    def setText(self, text: str) -> None:
        self.label.setText(text)
        self.setAccessibleName(text)
        self.updateGeometry()

    def _update_indicator_margin(self) -> None:
        option = QStyleOptionButton()
        self.initStyleOption(option)
        style = self.style()
        indicator = style.subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, self)
        spacing = style.pixelMetric(QStyle.PixelMetric.PM_CheckBoxLabelSpacing, option, self)
        margin = indicator.width() + max(0, spacing)
        if self.layoutDirection() == Qt.LayoutDirection.RightToLeft:
            self._text_layout.setContentsMargins(0, 0, margin, 0)
        else:
            self._text_layout.setContentsMargins(margin, 0, 0, 0)

    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        if hasattr(self, "_text_layout") and event.type() in {
            QEvent.Type.StyleChange,
            QEvent.Type.FontChange,
            QEvent.Type.LayoutDirectionChange,
        }:
            self._update_indicator_margin()
        return result

    def hitButton(self, position: QPoint) -> bool:
        return self.rect().contains(position)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return max(super().sizeHint().height(), self._text_layout.heightForWidth(width))

    def sizeHint(self) -> QSize:
        hint = self._text_layout.sizeHint()
        return QSize(hint.width(), max(hint.height(), super().sizeHint().height()))

    def minimumSizeHint(self) -> QSize:
        hint = self._text_layout.minimumSize()
        return QSize(hint.width(), max(hint.height(), super().minimumSizeHint().height()))
