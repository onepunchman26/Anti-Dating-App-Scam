from PySide6.QtWidgets import QPushButton


class SecondaryButton(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("SecondaryButton")
