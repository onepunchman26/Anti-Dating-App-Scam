"""User-owned annotations: every addition/correction is a deliberate action."""

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from anti_dating_scam.services.relationship_memory import RelationshipMemory
from anti_dating_scam_desktop.i18n import bi


class RelationshipMemoryDialog(QDialog):
    def __init__(self, vault, parent=None, session_id=None):
        super().__init__(parent)
        self.memory = RelationshipMemory(vault)
        self.session_id = session_id
        self.setWindowTitle(bi("My approved notes", "我批准的记忆"))
        self.resize(710, 580)
        layout = QVBoxLayout(self)
        note = QLabel(
            bi(
                "Only notes you approve here can be reused. Up to 20 notes, 250 characters each. "
                "These are unverified annotations, stored locally without encryption. "
                "Enabled notes "
                "appear in the next chat's sending review; "
                "they never become portrait evidence. "
                "Deleting removes this app's copy, not files you previously exported or sent.",
                "只复用你在这里批准的记忆，最多 20 条、每条 250 字。记忆是未经核实的备注，"
                "以未加密文件保存在本地。启用的条目会在下一次聊天发送前供你审阅，不能作为画像证据。"
                "删除会移除本应用的副本，不会删除你之前导出或发送的文件。",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.items = QListWidget()
        self.items.currentRowChanged.connect(self._select)
        layout.addWidget(self.items, 1)
        self.kind = QComboBox()
        for en, zh, key in (
            ("Preference", "偏好", "preference"),
            ("Self-report", "自述", "self_report"),
            ("Tentative interpretation", "暂定解释", "interpretation"),
        ):
            self.kind.addItem(bi(en, zh), key)
        layout.addWidget(self.kind)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            bi("Write a note you want to approve.", "写下你要批准的记忆。")
        )
        self.editor.setMaximumHeight(85)
        layout.addWidget(self.editor)
        for controls in (
            (
                ("Approve new note", "批准新增", "add"),
                ("Approve correction", "批准纠正", "correct"),
                ("Delete selected", "删除所选", "delete"),
            ),
            (
                ("Enable reuse", "启用复用", "enable"),
                ("Pause / revoke reuse", "暂停／撤销复用", "revoke"),
                ("Delete all", "删除全部", "clear"),
            ),
        ):
            row = QHBoxLayout()
            for en, zh, action in controls:
                button = QPushButton(bi(en, zh))
                button.setObjectName("memory_" + action)
                button.clicked.connect(lambda _checked=False, action=action: self._change(action))
                row.addWidget(button)
            layout.addLayout(row)
        export = QPushButton(bi("Export my notes (unencrypted)", "导出我的记忆（未加密）"))
        export.clicked.connect(self._export)
        layout.addWidget(export)
        close = QPushButton(bi("Close", "关闭"))
        close.clicked.connect(self.accept)
        layout.addWidget(close)
        self._reload()

    def _reload(self):
        self.state = self.memory.read()
        self.items.clear()
        for item in self.state.entries:
            source = (
                bi("Manual approval", "手动批准")
                if item.source == "manual"
                else bi("Chat note", "聊天备注")
            )
            self.items.addItem(f"{item.text}\n{source} · {item.approved_at:%Y-%m-%d %H:%M} UTC")
        self.status.setText(
            bi("Reuse enabled", "已启用复用")
            if self.state.enabled
            else bi("Reuse paused", "已暂停复用")
        )

    def _select(self, row):
        if 0 <= row < len(self.state.entries):
            item = self.state.entries[row]
            self.editor.setPlainText(item.text)
            self.kind.setCurrentIndex(self.kind.findData(item.kind))

    def _change(self, action):
        row = self.items.currentRow()
        entry_id = self.state.entries[row].id if 0 <= row < len(self.state.entries) else None
        if (
            action in {"clear", "delete"}
            and QMessageBox.question(
                self,
                bi("Delete notes?", "删除记忆？"),
                bi("This cannot be undone here.", "在这里无法撤销删除。"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self.memory.change(
                self.state.revision,
                confirmed=True,
                action=action,
                text=self.editor.toPlainText(),
                kind=self.kind.currentData(),
                source="session:" + self.session_id if self.session_id else "manual",
                entry_id=entry_id if action in {"correct", "delete"} else None,
            )
            self._reload()
            self.editor.clear()
        except (ValueError, OSError):
            self.status.setText(
                bi(
                    "Could not save. Check selection, length or changed notes; reopen to refresh.",
                    "无法保存，请检查选择、字数及记忆是否已变化；可重新打开刷新。",
                )
            )

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            bi("Export unencrypted notes", "导出未加密记忆"),
            "my-approved-notes.json",
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            self.memory.export(Path(path), confirmed=True)
            self.status.setText(
                bi("Exported. Keep this private file safe.", "已导出，请妥善保管这份私人文件。")
            )
        except (ValueError, OSError):
            self.status.setText(
                bi("Could not export. Choose a new file name.", "无法导出，请选择新的文件名。")
            )
