from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.disclosure_review import review_request
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader
from anti_dating_scam_desktop.workers import run_async


class SelfPortraitScreen(QWidget):
    """Understand Yourself — hand your own data to the agent for a self-portrait.

    The app does not analyze here. It writes the rules + output standard
    (``SELF_PORTRAIT_REQUEST.md``) so a desktop agent (Claude Code / Cowork) can
    read the user's own chat history + notes and synthesize the personality
    portrait, grounded in established theory.
    """

    def __init__(self, state, profile_store, on_view_portrait, on_add_data, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        self.on_view_portrait = on_view_portrait

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(16)
        layout.addWidget(
            StepHeader(
                bi("Understand Yourself", "了解你自己"),
                bi(
                    "Your agent reads your own chat history + notes and reflects back a "
                    "deep, theory-grounded portrait of you. The app only sets the rules.",
                    "你的代理会阅读你自己的聊天记录与笔记，结合公认理论，回映出一份对你的深入刻画。"
                    "本应用只负责设定规则。",
                ),
            )
        )

        self.banner = StatusBanner()
        layout.addWidget(self.banner)

        # One-click path when an AI is connected (no copy-paste).
        self.generate_button = PrimaryButton(
            bi("Generate Self-Portrait Now", "立即生成自我画像")
        )
        self.generate_button.clicked.connect(self._generate_now)
        layout.addWidget(self.generate_button)

        layout.addWidget(
            QLabel(
                bi(
                    "Optional: add anything about yourself in your own words (saved into "
                    "the vault's imports/).",
                    "可选：用你自己的话补充任何关于你的内容（将保存到档案库的 imports/ 中）。",
                )
            )
        )
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText(
            bi(
                "e.g. what matters to you, how you handle conflict, what you want in a "
                "relationship... or leave empty to use the data you've already added.",
                "例如：你看重什么、你如何处理冲突、你想要怎样的关系……也可留空，直接使用你已添加的数据。",
            )
        )
        self.notes.setMaximumHeight(140)
        layout.addWidget(self.notes)

        prepare = SecondaryButton(
            bi(
                "Manual local-agent mode: Prepare Request + Prompt",
                "本地代理手动模式：生成请求与提示词",
            )
        )
        prepare.clicked.connect(self._prepare)
        layout.addWidget(prepare)

        layout.addWidget(
            QLabel(bi("For an isolated local model only:", "仅供已隔离的本地模型使用："))
        )
        self.prompt_box = QPlainTextEdit()
        self.prompt_box.setReadOnly(True)
        self.prompt_box.setPlaceholderText(
            bi(
                'Click "Prepare Self-Understanding Request" to generate the prompt.',
                "点击「生成自我理解请求」即可生成提示词。",
            )
        )
        layout.addWidget(self.prompt_box)

        actions = QHBoxLayout()
        self.copy_button = SecondaryButton(bi("Copy Prompt", "复制提示词"))
        self.copy_button.clicked.connect(self._copy_prompt)
        self.add_data_button = SecondaryButton(bi("Add Data", "添加数据"))
        self.add_data_button.clicked.connect(on_add_data)
        self.open_vault_button = SecondaryButton(bi("Open Vault Folder", "打开档案库文件夹"))
        self.open_vault_button.clicked.connect(self._open_vault)
        self.view_button = SecondaryButton(bi("View My Self-Portrait", "查看我的自我画像"))
        self.view_button.clicked.connect(on_view_portrait)
        for button in (
            self.copy_button,
            self.add_data_button,
            self.open_vault_button,
            self.view_button,
        ):
            actions.addWidget(button)
        layout.addLayout(actions)

        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        layout.addWidget(back)

    def on_enter(self) -> None:
        files = agent_handoff.list_vault_data_files(self.profile_store.base_dir)
        request_ready = self.profile_store.self_portrait_request_path.exists()
        has_portrait = self.profile_store.has_self_portrait()
        backend = ai_backend.get_active()
        self.generate_button.setEnabled(backend is not None and bool(files))
        if backend is None:
            self.generate_button.setText(
                bi(
                    "Generate Self-Portrait Now (connect AI first)",
                    "立即生成自我画像（请先连接 AI）",
                )
            )
        else:
            self.generate_button.setText(
                f"{bi('Generate Self-Portrait Now', '立即生成自我画像')} · {backend.name}"
            )
        parts = [
            f"{bi('Vault folder', '档案库文件夹')}: {self.profile_store.base_dir}",
            f"{bi('Your data files found', '找到你的数据文件')}: {len(files)}",
            (
                f"{bi('Self-understanding request', '自我理解请求')}: "
                + (
                    bi("ready (SELF_PORTRAIT_REQUEST.md)", "已就绪（SELF_PORTRAIT_REQUEST.md）")
                    if request_ready
                    else bi("not prepared yet", "尚未生成")
                )
            ),
            (
                bi("Self-portrait: ready to view", "自我画像：可供查看")
                if has_portrait
                else bi("Self-portrait: not written yet", "自我画像：尚未生成")
            ),
        ]
        if not files:
            parts.append(
                bi(
                    'No data yet — use "Add Data" to add your own chat history / notes first.',
                    "暂无数据——请先用「添加数据」加入你自己的聊天记录与笔记。",
                )
            )
        self.banner.set_text("\n".join(parts))
        if request_ready and not self.prompt_box.toPlainText():
            self.prompt_box.setPlainText(
                agent_handoff.build_self_portrait_prompt(self.profile_store.base_dir)
            )

    def _prepare(self) -> None:
        text = self.notes.toPlainText().strip()
        if text:
            saved = self.profile_store.save_import_text(text, "about_me_notes.md")
            if saved not in self.state.import_sources:
                self.state.import_sources.append(saved)
        request_path = self.profile_store.write_self_portrait_request(
            agent_handoff.build_self_portrait_request(self.profile_store.base_dir)
        )
        self.profile_store.write_agent_instructions()
        self.prompt_box.setPlainText(
            agent_handoff.build_self_portrait_prompt(self.profile_store.base_dir)
        )
        self.state.vault_path = self.profile_store.base_dir
        self.on_enter()
        self.banner.set_text(
            f"{bi('Self-understanding request written to', '自我理解请求已写入')}: "
            f"{request_path}\n"
            + bi(
                "Use this manual prompt only with an isolated local model. For external AI, "
                "use Connect AI and review the disclosure inside the app. A desktop agent "
                "may still send data to a cloud model.",
                "手动提示词仅供已隔离的本地模型使用。外部 AI 请通过「连接 AI」"
                "在应用内审核披露内容。"
                "桌面代理也可能将数据发送给云端模型。",
            )
        )

    def _generate_now(self) -> None:
        """One-click generation through the connected backend (no copy-paste)."""
        backend = ai_backend.get_active()
        if backend is None:
            return
        text = self.notes.toPlainText().strip()
        if text:
            saved = self.profile_store.save_import_text(text, "about_me_notes.md")
            if saved not in self.state.import_sources:
                self.state.import_sources.append(saved)
        store = self.profile_store
        request = review_request(self, backend, ai_backend.prepare_self_portrait_request(store))
        if request is None:
            return
        self.generate_button.setEnabled(False)
        self.banner.set_text(
            bi(
                "Generating your self-portrait… this can take a few minutes. The app "
                "stays responsive.",
                "正在生成你的自我画像……可能需要几分钟。应用不会卡住。",
            )
        )

        def call():
            return ai_backend.run_self_portrait(backend, store, request=request)

        def ok(path) -> None:
            self.state.profile_exists = True
            self.on_enter()
            self.banner.set_text(
                f"{bi('Self-portrait saved to', '自我画像已保存到')}: {path}\n"
                + bi("Opening it now…", "正在打开……")
            )
            self.on_view_portrait()

        def err(message: str) -> None:
            self.on_enter()
            self.banner.set_text(f"{bi('Generation failed', '生成失败')}: {message}")

        run_async(self, call, ok, err)

    def _copy_prompt(self) -> None:
        prompt = self.prompt_box.toPlainText().strip()
        if not prompt:
            self._prepare()
            prompt = self.prompt_box.toPlainText().strip()
        QApplication.clipboard().setText(prompt)
        self.banner.set_text(bi("Prompt copied to clipboard.", "提示词已复制到剪贴板。"))

    def _open_vault(self) -> None:
        self.profile_store.create_default_directories()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.profile_store.base_dir)))
