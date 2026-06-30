import json
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.engine.personal_profile_builder import (
    PersonalProfileBuilder,
    profile_to_markdown,
)
from anti_dating_scam.reports.schema_validator import validate_document
from anti_dating_scam_desktop.i18n import bi


class ProfileViewPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.builder = PersonalProfileBuilder()

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(f"<h2>{bi('Generate Local Personal Profile', '生成本地个人档案')}</h2>")
        )
        note = QLabel(
            bi(
                "This generates a local personal relationship profile document from "
                "user-provided notes, memory summary text, and limited local export snippets. "
                "It is not training a personal model.",
                "本功能会根据您提供的笔记、记忆摘要文本以及有限的本地导出片段，"
                "生成一份本地的个人关系档案文档。这并不是在训练个人模型。",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        generate = QPushButton(bi("Generate Profile", "生成档案"))
        generate.clicked.connect(self._generate_profile)
        save_json = QPushButton(bi("Save Profile JSON", "保存档案 JSON"))
        save_json.clicked.connect(self._save_profile_json)
        load_json = QPushButton(bi("Load Profile JSON", "加载档案 JSON"))
        load_json.clicked.connect(self._load_profile_json)
        export_md = QPushButton(bi("Export Profile Markdown", "导出档案 Markdown"))
        export_md.clicked.connect(self._export_profile_markdown)
        for button in [generate, save_json, load_json, export_md]:
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.output = QTextEdit()
        self.output.setPlaceholderText(bi("Profile JSON will appear here.", "档案 JSON 将显示在此处。"))
        layout.addWidget(self.output)

    def _generate_profile(self) -> None:
        profile = self.builder.build(
            manual_notes=self.state.get("manual_notes", ""),
            memory_summary=self.state.get("memory_summary", ""),
            chatgpt_export_summary=self.state.get("chatgpt_export_summary"),
        )
        validate_document(profile, "personal_profile.schema.json")
        self.state["profile"] = profile
        self.output.setPlainText(json.dumps(profile, indent=2, ensure_ascii=False))

    def _current_profile(self) -> dict | None:
        if self.state.get("profile"):
            return self.state["profile"]
        try:
            profile = json.loads(self.output.toPlainText())
            validate_document(profile, "personal_profile.schema.json")
            self.state["profile"] = profile
            return profile
        except Exception:
            return None

    def _save_profile_json(self) -> None:
        profile = self._current_profile()
        if not profile:
            QMessageBox.information(
                self,
                bi("No profile", "没有档案"),
                bi("Generate or load a valid profile first.", "请先生成或加载一个有效的档案。"),
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, bi("Save profile JSON", "保存档案 JSON"), "", "JSON (*.json)"
        )
        if path:
            Path(path).write_text(
                json.dumps(profile, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _load_profile_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, bi("Load profile JSON", "加载档案 JSON"), "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            profile = json.loads(Path(path).read_text(encoding="utf-8"))
            validate_document(profile, "personal_profile.schema.json")
        except Exception as exc:
            QMessageBox.warning(self, bi("Invalid profile", "档案无效"), str(exc))
            return
        self.state["profile"] = profile
        self.output.setPlainText(json.dumps(profile, indent=2, ensure_ascii=False))

    def _export_profile_markdown(self) -> None:
        profile = self._current_profile()
        if not profile:
            QMessageBox.information(
                self,
                bi("No profile", "没有档案"),
                bi("Generate or load a valid profile first.", "请先生成或加载一个有效的档案。"),
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, bi("Export profile Markdown", "导出档案 Markdown"), "", "Markdown (*.md)"
        )
        if path:
            Path(path).write_text(profile_to_markdown(profile), encoding="utf-8")
