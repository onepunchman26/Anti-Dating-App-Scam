from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatusBanner(QFrame):
    def __init__(self, text: str = "") -> None:
        super().__init__()
        self.setObjectName("StatusBanner")
        layout = QVBoxLayout(self)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

    def set_text(self, text: str) -> None:
        self.label.setText(text)
