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
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        if status:
            status_label = QLabel(status)
            status_label.setWordWrap(True)
            layout.addWidget(status_label)
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        layout.addStretch()
        button = PrimaryButton(button_text)
        button.clicked.connect(on_click)
        layout.addWidget(button)
