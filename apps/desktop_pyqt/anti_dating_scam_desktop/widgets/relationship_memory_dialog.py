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
    QTextBrowser,
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
                "Enable reuse to request AI memory candidates; each still needs your approval. "
                "Only relevant enabled notes appear in the next chat's sending review; "
                "they never become portrait evidence. "
                "Deleting removes this app's copy, not files you previously exported or sent.",
                "只复用你在这里批准的记忆，最多 20 条、每条 250 字。记忆是未经核实的备注，"
                "以未加密文件保存在本地。启用的条目会在下一次聊天发送前供你审阅，不能作为画像证据。"
                "启用复用后 AI 才提出记忆候选，每条仍需你批准，只有相关条目会用于发送。"
                "删除会移除本应用的副本及依赖它的模型条目，不会删除你之前导出或发送的文件。",
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
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(False)
        self.details.setOpenLinks(False)
        self.details.setMaximumHeight(150)
        layout.addWidget(self.details)
        self.kind = QComboBox()
        for en, zh, key in (
            ("Preference", "偏好", "preference"),
            ("Self-report", "自述", "self_report"),
            ("Tentative interpretation", "暂定解释", "interpretation"),
            ("Event", "事件", "event"),
            ("Goal", "目标", "goal"),
            ("Boundary", "边界", "boundary"),
            ("Tentative pattern", "暂定模式", "pattern"),
            ("Open question", "开放问题", "open_question"),
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
                ("Question interpretation", "质疑解释", "question"),
                ("Reject interpretation", "拒绝解释", "reject"),
            ),
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
            self.details.setPlainText(describe_memory(item))

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
                entry_id=entry_id
                if action in {"correct", "delete", "reject", "question"}
                else None,
            )
            self._reload()
            self.editor.clear()
            self.details.clear()
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


def describe_memory(item):
    """Show evidence and uncertainty as data, never render untrusted HTML."""
    inferred = getattr(item, "origin", None) == "ai_inference" or item.kind in {
        "interpretation",
        "pattern",
        "open_question",
    }
    lines = [
        item.text,
        bi("AI hypothesis, not an established fact", "AI 假设，尚非已确立事实")
        if inferred
        else bi("User report, not independently verified", "用户自述，未经独立核实"),
    ]
    if hasattr(item, "origin"):
        labels = {
            "confirmed": bi("Approved", "已批准"),
            "questioned": bi("Questioned", "已质疑"),
            "rejected": bi("Rejected; excluded from recall", "已拒绝，不参与召回"),
            "corrected": bi("Corrected", "已纠正"),
        }
        lines.append(labels[item.review_status])
        lines.append(bi("Approved at: ", "批准时间：") + item.approved_at.isoformat())
        if item.reviewed_at:
            lines.append(bi("Reviewed at: ", "复核时间：") + item.reviewed_at.isoformat())
        lines.append(bi("Confidence: tentative / unverified", "置信：暂定／未经独立核实"))
    elif item.target_id:
        lines.append(bi("Replaces note: ", "替代记忆：") + item.target_id)
        lines.append(bi("Dependent interpretations will be removed.", "依赖旧条目的解释会被移除。"))
    for field, en, zh in (
        ("context", "Context", "情境"),
        ("basis", "Basis", "依据"),
        ("uncertainty", "Unknown / tentative", "未知／暂定"),
    ):
        if getattr(item, field):
            lines.append(bi(en, zh) + ": " + getattr(item, field))
    for alternative in item.alternatives:
        lines.append(bi("Alternative: ", "其他解释：") + alternative)
    for evidence in item.evidence:
        lines.append(bi("User quote ", "用户原话 ") + evidence.source + ": " + evidence.quote)
    if item.depends_on:
        lines.append(bi("Depends on notes: ", "依赖记忆：") + ", ".join(item.depends_on))
    if item.sensitive:
        lines.append(
            bi(
                "Sensitive content — approval includes these quotes.",
                "包含敏感内容——批准也将保存这些引文。",
            )
        )
    return "\n\n".join(lines)


class MemoryCandidateDialog(QDialog):
    def __init__(self, vault, evaluated, parent=None):
        super().__init__(parent)
        self.memory = RelationshipMemory(vault)
        self.evaluated = evaluated
        self.setWindowTitle(bi("Review personal-model updates", "审核个人模型更新"))
        self.resize(760, 650)
        layout = QVBoxLayout(self)
        note = QLabel(
            bi(
                "Nothing below is saved yet. Approve only the specific text and evidence you want "
                "stored locally (unencrypted) and reused in reviewed cloud requests. Rejecting a "
                "candidate keeps only a content-free decision receipt. Closing saves nothing new.",
                "下方内容尚未保存。仅批准你同意在本机未加密保存、并在审阅后的云端请求中复用的文字和证据。"
                "拒绝候选只保留不含正文的决定记录；关闭不会新增保存。",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.status = QLabel(evaluated.evaluation.reason)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.items = QListWidget()
        for candidate in evaluated.evaluation.candidates:
            self.items.addItem(candidate.text)
        self.items.setMaximumHeight(140)
        layout.addWidget(self.items)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.details, 1)
        self.items.currentRowChanged.connect(self._select)
        row = QHBoxLayout()
        self.approve_button = QPushButton(bi("Approve this update", "批准此项更新"))
        self.approve_button.clicked.connect(lambda: self._decide(False))
        row.addWidget(self.approve_button)
        self.reject_button = QPushButton(bi("Reject this candidate", "拒绝此候选"))
        self.reject_button.clicked.connect(lambda: self._decide(True))
        row.addWidget(self.reject_button)
        close = QPushButton(bi("Close", "关闭"))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)
        self.decided = set()
        self.items.setCurrentRow(0)
        self._select(self.items.currentRow())

    def _select(self, row):
        valid = 0 <= row < len(self.evaluated.evaluation.candidates)
        self.details.setPlainText(
            describe_memory(self.evaluated.evaluation.candidates[row]) if valid else ""
        )
        self.approve_button.setEnabled(valid and row not in self.decided)
        self.reject_button.setEnabled(valid and row not in self.decided)

    def _decide(self, reject):
        row = self.items.currentRow()
        if row in self.decided:
            return
        try:
            state = self.memory.approve(self.evaluated, row, confirmed=True, reject=reject)
            self.decided.add(row)
            # Only our own successful atomic update advances this dialog's revision.
            self.evaluated = self.evaluated.model_copy(update={"revision": state.revision})
            self.status.setText(bi("Decision saved.", "决定已保存。"))
            self._select(row)
        except (ValueError, OSError):
            self.status.setText(
                bi(
                    "Nothing changed. Notes changed, are full, or are disabled. "
                    "Close and review again.",
                    "未作修改。记忆已变化、已满或已停用，请关闭后重新审阅。",
                )
            )
