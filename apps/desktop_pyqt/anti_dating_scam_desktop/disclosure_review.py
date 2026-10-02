"""Review exactly what leaves this device before invoking an external model."""

import json

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from anti_dating_scam.ai.privacy import ChatRequest, build_reviewed_request
from anti_dating_scam.services.reviewed_ai import isinstance_local
from anti_dating_scam_desktop.i18n import bi


def review_request(parent, backend, request: ChatRequest) -> ChatRequest | None:
    if isinstance_local(backend):
        return request
    dialog = QDialog(parent)
    dialog.setWindowTitle(bi("Review external AI disclosure", "审核发送给外部 AI 的内容"))
    dialog.resize(820, 720)
    layout = QVBoxLayout(dialog)
    label = QLabel(
        bi("Destination", "接收方")
        + ": "
        + backend.recipient
        + "\n"
        + bi(
            "Edit this into a minimal summary. Remove names, contact details and private facts. "
            "Only these approved messages and the instructions below will be sent. "
            "Your provider may charge for use.",
            "请编辑为最小摘要，删除姓名、联系方式及私密事实。"
            "仅发送审核后的消息与下方指令；提供方可能收费。",
        )
    )
    label.setWordWrap(True)
    layout.addWidget(label)
    layout.addWidget(QLabel(bi("Application instructions", "应用指令")))
    instructions = QPlainTextEdit(request.system)
    instructions.setReadOnly(True)
    instructions.setMaximumHeight(150)
    layout.addWidget(instructions)
    layout.addWidget(QLabel(bi("Messages to disclose (editable JSON)", "披露消息（可编辑 JSON）")))
    editor = QPlainTextEdit(
        json.dumps(
            [item.model_dump() for item in request.messages],
            ensure_ascii=False,
            indent=2,
        )
    )
    layout.addWidget(editor)
    error = QLabel()
    error.setWordWrap(True)
    layout.addWidget(error)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(QDialogButtonBox.StandardButton.Ok).setText(bi("Approve and send", "同意并发送"))
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(bi("Cancel", "取消"))
    buttons.rejected.connect(dialog.reject)
    approved = None

    def approve():
        nonlocal approved
        try:
            approved = build_reviewed_request(
                json.loads(editor.toPlainText()),
                system=request.system,
                recipient=backend.recipient,
            )
        except (ValueError, TypeError, RuntimeError):
            error.setText(
                bi(
                    "Use valid user/assistant messages totaling at most 24,000 characters.",
                    "请填写有效的 user/assistant 消息，总计最多 24,000 字符。",
                )
            )
            return
        dialog.accept()

    buttons.accepted.connect(approve)
    layout.addWidget(buttons)
    return approved if dialog.exec() == QDialog.DialogCode.Accepted else None
