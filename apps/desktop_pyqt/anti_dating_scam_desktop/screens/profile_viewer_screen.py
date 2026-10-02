import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ProfileViewerScreen(QWidget):
    def __init__(self, state, profile_store, on_home, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(StepHeader(bi("View / Edit Local Profile", "查看 / 编辑本地档案")))
        self.path_label = QLabel()
        self.path_label.setTextFormat(Qt.TextFormat.PlainText)
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)
        note = QLabel(bi(
            "Edit Markdown here. The JSON companion has a separate read-only view; "
            "saving Markdown does not update JSON automatically.",
            "在此编辑 Markdown。JSON 配套文件在独立只读视图中显示；"
            "保存 Markdown 不会自动更新 JSON。",
        ))
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tabs = QTabWidget()
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(bi(
            "No Markdown profile yet. Write your own notes here to create one.",
            "尚无 Markdown 档案。可以在此写下自己的笔记并保存。",
        ))
        self.json_view = QPlainTextEdit()
        self.json_view.setReadOnly(True)
        self.tabs.addTab(self.editor, bi("Markdown draft", "Markdown 草稿"))
        self.tabs.addTab(self.json_view, bi("JSON companion (read only)", "JSON 配套文件（只读）"))
        layout.addWidget(self.tabs)
        nav = QHBoxLayout()
        self.save_button = SecondaryButton(bi("Save Markdown Profile", "保存 Markdown 档案"))
        self.save_button.clicked.connect(self._save_markdown)
        show_json = SecondaryButton(bi("Show JSON Companion", "显示 JSON 文件"))
        show_json.clicked.connect(self._show_json)
        home = SecondaryButton(bi("Home", "主页"))
        home.clicked.connect(on_home)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        for button in [self.save_button, show_json, home, back]:
            nav.addWidget(button)
        layout.addLayout(nav)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.editor.textChanged.connect(self._update_save)
        self._update_save()

    def _update_save(self) -> None:
        self.save_button.setEnabled(
            self.tabs.currentIndex() == 0 and bool(self.editor.toPlainText().strip())
        )

    def _tab_changed(self, index: int) -> None:
        if index == 1:
            self._load_json_view()
        self._update_save()

    def on_enter(self) -> None:
        text = self.state.current_profile_markdown
        if not text and self.profile_store.markdown_path.exists():
            text = self.profile_store.load_markdown_profile()
            self.state.current_profile_markdown = text
        self.editor.setPlainText(text or "")
        self.tabs.setCurrentIndex(0)
        self.json_view.clear()
        self.path_label.setText(
            f"{bi('Markdown save destination', 'Markdown 保存位置')}: "
            f"{self.profile_store.markdown_path}"
        )

    def _save_markdown(self) -> None:
        if self.tabs.currentIndex() != 0 or not self.editor.toPlainText().strip():
            return
        try:
            path = self.profile_store.save_markdown_profile(self.editor.toPlainText())
        except (OSError, ValueError):
            QMessageBox.warning(self, bi("Not saved", "尚未保存"), bi(
                "The Markdown draft could not be saved. Your draft is still in this window.",
                "无法保存 Markdown 草稿；草稿仍保留在此窗口中。",
            ))
            return
        self.state.profile_path = path
        self.state.current_profile_markdown = self.editor.toPlainText()
        self.state.profile_exists = True
        QMessageBox.information(
            self,
            bi("Saved", "已保存"),
            f"{bi('Saved profile.mpm.md to', '已将 profile.mpm.md 保存到')}:\n{path}",
        )

    def _show_json(self) -> None:
        self._load_json_view()
        self.tabs.setCurrentIndex(1)

    def _load_json_view(self) -> None:
        try:
            profile = self.state.current_profile_json
            if profile is None and self.profile_store.json_path.exists():
                profile = self.profile_store.load_json_profile()
            text = json.dumps(profile, indent=2, ensure_ascii=False) if profile is not None else bi(
                "No JSON companion is available. The Markdown draft is unchanged.",
                "没有 JSON 配套文件；Markdown 草稿保持不变。",
            )
        except (OSError, ValueError, TypeError):
            text = bi(
                "The JSON companion cannot be read. The Markdown draft is unchanged.",
                "无法读取 JSON 配套文件；Markdown 草稿保持不变。",
            )
        self.json_view.setPlainText(text)
