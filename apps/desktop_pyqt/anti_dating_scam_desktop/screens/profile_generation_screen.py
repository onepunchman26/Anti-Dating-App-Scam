from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.profile.mpmd_profile import MPMDProfile
from anti_dating_scam.profile.profile_json import build_profile_json_from_sources
from anti_dating_scam.profile.profile_markdown import profile_to_mpmd_markdown
from anti_dating_scam.reports.schema_validator import validate_document
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ProfileGenerationScreen(QWidget):
    def __init__(self, state, profile_store, on_home, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(StepHeader(bi("Generate Local Profile", "生成本地档案")))
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.saved_status = StatusBanner(
            bi(
                "Generate to auto-save profile.mpm.md + profile.json into your vault.",
                "点击「生成」即可把 profile.mpm.md 与 profile.json 自动保存到您的档案库。",
            )
        )
        layout.addWidget(self.saved_status)

        self.output = QTextEdit()
        self.output.setPlaceholderText(
            bi("Generated MPMD Profile will appear here.", "生成的 MPMD 档案将显示在此处。")
        )
        layout.addWidget(self.output)

        generate = PrimaryButton(bi("Generate Profile", "生成档案"))
        generate.clicked.connect(self._generate)

        vault_row = QHBoxLayout()
        open_vault = SecondaryButton(bi("Open Vault Folder", "打开档案库文件夹"))
        open_vault.clicked.connect(self._open_vault)
        copy_path = SecondaryButton(bi("Copy Vault Path", "复制档案库路径"))
        copy_path.clicked.connect(self._copy_path)
        vault_row.addWidget(open_vault)
        vault_row.addWidget(copy_path)

        home = PrimaryButton(bi("Continue to Home", "继续前往主页"))
        home.clicked.connect(on_home)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)

        layout.addWidget(generate)
        layout.addLayout(vault_row)
        layout.addWidget(home)
        layout.addWidget(back)

    def on_enter(self) -> None:
        mode = self.state.analysis_mode or bi("not selected", "未选择")
        mode_note = (
            bi(
                "Agent Mode: profile files are auto-saved into your vault, alongside an "
                "AGENTS.md / CLAUDE.md guide. Open the vault in Claude Code or Cowork to "
                "let your agent help - using only files you put there.",
                "代理模式：档案文件会自动保存到您的档案库，并附带 AGENTS.md / CLAUDE.md 说明文件。"
                "在 Claude Code 或 Cowork 中打开档案库，即可让代理仅基于您放入的文件来协助。",
            )
            if mode == "agent"
            else bi(
                "API Mode is a placeholder in this MVP; no real API call will be made.",
                "API 模式在本 MVP 中只是占位功能，不会发起真实的 API 调用。",
            )
        )
        names = [source.name for source in self.state.import_sources]
        sources_text = (
            ", ".join(names) if names else bi("manual text only or none yet", "目前仅有手动文本或暂无来源")
        )
        self.summary.setText(
            f"{bi('Vault folder', '档案库文件夹')}: {self.profile_store.base_dir}\n"
            f"{bi('Imported source count', '已导入的数据来源数量')}: {len(names)}\n"
            f"{bi('Sources', '来源')}: {sources_text}\n"
            f"{bi('Analysis mode', '分析模式')}: {mode}\n"
            f"{bi('Privacy warning: review and redact sensitive content before sharing.', '隐私提醒：分享前请检查并删除敏感内容。')}\n"
            f"{mode_note}"
        )

    def _generate(self) -> None:
        profile_json = build_profile_json_from_sources(
            manual_notes=self.state.manual_notes,
            memory_summary=self.state.memory_summary,
            chatgpt_export_summary=self.state.chatgpt_export_summary,
        )
        validate_document(profile_json, "personal_profile.schema.json")
        markdown = profile_to_mpmd_markdown(MPMDProfile.from_profile_json(profile_json))
        self.state.current_profile_json = profile_json
        self.state.current_profile_markdown = markdown
        self.output.setPlainText(markdown)

        # Auto-save into the vault in the AI-readable structure (no manual button).
        md_path = self.profile_store.save_markdown_profile(markdown)
        json_path = self.profile_store.save_json_profile(profile_json)
        self.profile_store.write_agent_instructions()
        self.state.profile_path = md_path
        self.state.profile_json_path = json_path
        self.state.vault_path = self.profile_store.base_dir
        self.state.profile_exists = True
        self.saved_status.set_text(
            f"{bi('Auto-saved to vault', '已自动保存到档案库')}: "
            f"{md_path.parent}  ({md_path.name} + {json_path.name})"
        )

    def _open_vault(self) -> None:
        self.profile_store.create_default_directories()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.profile_store.base_dir)))

    def _copy_path(self) -> None:
        QApplication.clipboard().setText(str(self.profile_store.base_dir))
        self.saved_status.set_text(
            bi("Vault path copied to clipboard.", "已将档案库路径复制到剪贴板。")
        )
