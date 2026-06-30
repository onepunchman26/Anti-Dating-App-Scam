from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QGridLayout, QTextEdit, QVBoxLayout, QWidget

from anti_dating_scam.engine.chatgpt_export_parser import ChatGPTExportParser
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.app_card import AppCard
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ImportDataScreen(QWidget):
    def __init__(self, state, on_generation, on_assisted_export, on_back) -> None:
        super().__init__()
        self.state = state
        self.parser = ChatGPTExportParser()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                bi("Import Data to Build Your Local Profile", "导入数据以建立您的本地档案"),
                bi(
                    "Choose one or more local sources. Nothing is uploaded by this screen.",
                    "选择一个或多个本地数据来源。本界面不会上传任何内容。",
                ),
            )
        )
        self.banner = StatusBanner(bi("No sources imported yet.", "尚未导入任何数据来源。"))
        layout.addWidget(self.banner)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            bi("Paste Manual Markdown / Notes here.", "在此粘贴手动 Markdown / 笔记。")
        )
        layout.addWidget(self.notes)
        grid = QGridLayout()
        cards = [
            AppCard(
                bi("Manual Markdown / Notes", "手动 Markdown / 笔记"),
                bi(
                    "Paste above or load a local .md / .txt file.",
                    "在上方粘贴，或加载本地 .md / .txt 文件。",
                ),
                bi("Import", "导入"),
                self._import_notes,
            ),
            AppCard(
                bi("ChatGPT Export ZIP", "ChatGPT 导出 ZIP"),
                bi(
                    "Load an official local export if available.",
                    "如有官方本地导出文件，可在此加载。",
                ),
                bi("Import", "导入"),
                self._import_chatgpt_export,
            ),
            AppCard(
                bi("Saved Web AI Chat HTML / JSON", "已保存的网页 AI 聊天 HTML / JSON"),
                bi(
                    "Load exported or saved files from another AI chat platform.",
                    "加载从其他 AI 聊天平台导出或保存的文件。",
                ),
                bi("Import", "导入"),
                self._import_saved_file,
            ),
            AppCard(
                bi("Assisted Browser Export", "辅助浏览器导出"),
                bi(
                    "Open the user-assisted local browser export screen.",
                    "打开用户辅助的本地浏览器导出界面。",
                ),
                bi("Open", "打开"),
                on_assisted_export,
            ),
            AppCard(
                bi("Existing Profile File", "现有档案文件"),
                bi(
                    "Choose an existing .mpm.md or .json profile.",
                    "选择现有的 .mpm.md 或 .json 档案文件。",
                ),
                bi("Import", "导入"),
                self._import_existing_profile,
            ),
        ]
        for index, card in enumerate(cards):
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        next_button = PrimaryButton(bi("Continue to Generate Profile", "继续生成档案"))
        next_button.clicked.connect(on_generation)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        layout.addWidget(next_button)
        layout.addWidget(back)

    def _import_notes(self) -> None:
        text = self.notes.toPlainText().strip()
        if not text:
            path, _ = QFileDialog.getOpenFileName(
                self,
                bi("Load Markdown or notes", "加载 Markdown 或笔记"),
                "",
                "Notes (*.md *.txt)",
            )
            if not path:
                return
            selected = Path(path)
            text = selected.read_text(encoding="utf-8")
            self.state.import_sources.append(selected)
        self.state.manual_notes = text
        self._update_banner()

    def _import_chatgpt_export(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, bi("Load ChatGPT export", "加载 ChatGPT 导出文件"), "", "ChatGPT export (*.zip *.json)"
        )
        if not path:
            return
        selected = Path(path)
        self.state.import_sources.append(selected)
        self.state.chatgpt_export_summary = self.parser.parse(selected).to_dict()
        self._update_banner()

    def _import_saved_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            bi("Load saved AI chat file", "加载已保存的 AI 聊天文件"),
            "",
            "AI chat files (*.html *.htm *.json *.md *.txt)",
        )
        if not path:
            return
        selected = Path(path)
        self.state.import_sources.append(selected)
        self.state.manual_notes += "\n\n" + selected.read_text(encoding="utf-8", errors="ignore")
        self._update_banner()

    def _import_existing_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            bi("Load existing profile", "加载现有档案"),
            "",
            "Profile files (*.mpm.md *.md *.json)",
        )
        if not path:
            return
        selected = Path(path)
        self.state.import_sources.append(selected)
        if selected.suffix == ".json":
            self.state.profile_json_path = selected
        else:
            self.state.profile_path = selected
        self._update_banner()

    def _update_banner(self) -> None:
        self.banner.set_text(
            f"{bi('Imported sources', '已导入的数据来源')}: {len(self.state.import_sources)}"
        )
