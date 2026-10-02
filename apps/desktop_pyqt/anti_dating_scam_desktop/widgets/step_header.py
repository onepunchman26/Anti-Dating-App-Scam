from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StepHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 18)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("ScreenTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("ScreenSubtitle")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
