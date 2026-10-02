"""Visible confirmation only after the app has verified a signed-in account."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QLabel, QVBoxLayout

from anti_dating_scam_desktop.i18n import bi


class ConnectionSuccessBadge(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("connectionSuccessBadge")
        self.setStyleSheet(
            "QFrame#connectionSuccessBadge {background:#ecfdf5; border:1px solid #6ee7b7;"
            "border-radius:12px;} QLabel {color:#047857; background:transparent;}"
        )
        layout = QVBoxLayout(self)
        self.label = QLabel(bi("✓ ChatGPT account connected", "✓ ChatGPT 账号连接成功"))
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity", self)
        self.animation.setDuration(650)
        self.animation.setStartValue(0.15)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hide()

    def confirm(self, *, chat_ready=False, animate=True):
        self.label.setText(bi("✓ ChatGPT connected · ready to chat", "✓ ChatGPT 已连接 · 可以聊天")
                           if chat_ready else bi(
                               "✓ ChatGPT account connected", "✓ ChatGPT 账号连接成功",
                           ))
        self.show()
        if animate:
            self.animation.stop()
            self.animation.start()
        else:
            self.effect.setOpacity(1.0)
