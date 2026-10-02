from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton


class AppCard(QFrame):
    def __init__(
        self,
        title: str,
        description: str,
        button_text: str,
        on_click: Callable[[], None],
        *,
        status: str = "",
    ) -> None:
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(title_label)
        if status:
            status_label = QLabel(status)
            status_label.setWordWrap(True)
            status_label.setStyleSheet("color: #8b90a3; font-size: 12.5px;")
            layout.addWidget(status_label)
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #5b6172;")
        layout.addWidget(description_label)
        layout.addSpacing(4)
        layout.addStretch()
        button = PrimaryButton(button_text)
        button.clicked.connect(on_click)
        layout.addWidget(button)
