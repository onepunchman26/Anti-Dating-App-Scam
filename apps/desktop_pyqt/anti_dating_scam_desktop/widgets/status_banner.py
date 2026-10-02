from math import ceil

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAbstractTextDocumentLayout, QPainter, QTextDocument, QTextOption
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class _WrappingStatusLabel(QLabel):
    """Keep literal status text while wrapping even an unbroken path segment.

    QLabel's ordinary WordWrap can still overflow on long tokens. Qt's document
    layout supplies a word-boundary-or-anywhere fallback for both measurement and
    drawing; it never inserts characters or treats the text as HTML.
    """

    def _document(self, width: int) -> QTextDocument:
        document = QTextDocument()
        document.setDocumentMargin(0)
        document.setDefaultFont(self.font())
        option = document.defaultTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        document.setDefaultTextOption(option)
        document.setPlainText(self.text())
        document.setTextWidth(max(1, width))
        return document

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        margins = self.contentsMargins()
        document = self._document(width - margins.left() - margins.right())
        return ceil(document.size().height()) + margins.top() + margins.bottom()

    def minimumSizeHint(self) -> QSize:
        return QSize(0, self.fontMetrics().height())

    def sizeHint(self) -> QSize:
        width = min(640, super().sizeHint().width())
        return QSize(width, self.heightForWidth(width))

    def paintEvent(self, event) -> None:
        document = self._document(self.contentsRect().width())
        painter = QPainter(self)
        painter.translate(self.contentsRect().topLeft())
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette = self.palette()
        document.documentLayout().draw(painter, context)


class StatusBanner(QFrame):
    def __init__(self, text: str = "") -> None:
        super().__init__()
        self.setObjectName("StatusBanner")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        self.label = _WrappingStatusLabel(text)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

    def set_text(self, text: str) -> None:
        self.label.setText(text)
