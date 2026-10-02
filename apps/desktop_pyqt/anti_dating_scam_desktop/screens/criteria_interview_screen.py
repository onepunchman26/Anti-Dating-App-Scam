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

from anti_dating_scam.services.active_reports import ActiveReportError, ActiveReportService
from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class CriteriaInterviewScreen(QWidget):
    """Discover your real mate-selection criteria — stage 2 after the self-portrait.

    The app writes the interview contract (``CRITERIA_INTERVIEW_REQUEST.md``) and a
    prompt; the agent (Claude Code / Cowork) then interviews the user in chat,
    presents realistic ideal-partner profiles to rank, and writes the stated-vs-
    revealed criteria synthesis back into ``reports/``. The non-sycophancy stance
    lives in the contract, not the UI.
    """

    def __init__(
        self, state, profile_store, on_view_criteria, on_live_interview, on_back
    ) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(16)
        layout.addWidget(
            StepHeader(
                bi("Discover Your Real Criteria", "发现你的真实择偶标准"),
                bi(
                    "Your agent interviews you, then shows realistic (not perfect) "
                    "ideal-partner profiles to rank. Your choices — not your words — "
                    "reveal what you actually select for. The agent is instructed to "
                    "stay objective and challenge you, not to agree with you.",
                    "你的代理会先访谈你，再给出多份现实的（而非完美的）理想伴侣画像让你排序。"
                    "真正揭示你择偶标准的是你的选择，而不是你的说法。代理被明确要求保持客观、"
                    "敢于质疑，而不是迎合你。",
                ),
            )
        )

        self.banner = StatusBanner()
        layout.addWidget(self.banner)

        # One-click path: live interview inside the app (no copy-paste).
        self.live_button = PrimaryButton(
            bi("Start Live Interview In App", "在应用内开始实时访谈")
        )
        self.live_button.clicked.connect(on_live_interview)
        layout.addWidget(self.live_button)

        layout.addWidget(
            QLabel(
                bi(
                    "Optional: anything you already believe about your ideal partner "
                    "(saved into imports/ as interview material).",
                    "可选：你目前对理想伴侣的任何想法（将作为访谈材料保存到 imports/）。",
                )
            )
        )
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText(
            bi(
                "e.g. what you think you want, past relationships that worked or "
                "didn't, hard limits... or leave empty.",
                "例如：你自认为想要什么、过去哪些关系合适或不合适、绝对底线……也可留空。",
            )
        )
        self.notes.setMaximumHeight(120)
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
                'Click "Prepare Interview Request" to generate the prompt.',
                "点击「生成访谈请求」即可生成提示词。",
            )
        )
        layout.addWidget(self.prompt_box)

        actions = QHBoxLayout()
        self.copy_button = SecondaryButton(bi("Copy Prompt", "复制提示词"))
        self.copy_button.clicked.connect(self._copy_prompt)
        self.open_vault_button = SecondaryButton(bi("Open Vault Folder", "打开档案库文件夹"))
        self.open_vault_button.clicked.connect(self._open_vault)
        self.view_button = SecondaryButton(bi("View My Criteria", "查看我的择偶标准"))
        self.view_button.clicked.connect(on_view_criteria)
        for button in (self.copy_button, self.open_vault_button, self.view_button):
            actions.addWidget(button)
        layout.addLayout(actions)

        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        layout.addWidget(back)

    def on_enter(self) -> None:
        has_portrait = self.profile_store.has_self_portrait()
        request_ready = self.profile_store.criteria_interview_request_path.exists()
        has_criteria = self.profile_store.has_mate_criteria()
        backend = ai_backend.get_active()
        self.live_button.setEnabled(backend is not None)
        if backend is None:
            self.live_button.setText(
                bi(
                    "Start Live Interview In App (connect AI first)",
                    "在应用内开始实时访谈（请先连接 AI）",
                )
            )
        else:
            self.live_button.setText(
                f"{bi('Start Live Interview In App', '在应用内开始实时访谈')} · {backend.name}"
            )
        parts = [
            f"{bi('Vault folder', '档案库文件夹')}: {self.profile_store.base_dir}",
            (
                bi("Self-portrait: found (recommended input)", "自我画像：已找到（推荐输入）")
                if has_portrait
                else bi(
                    'Self-portrait: not found — run "Understand Yourself" first for a '
                    "much better interview.",
                    "自我画像：未找到——建议先运行「了解你自己」，访谈效果会好得多。",
                )
            ),
            (
                f"{bi('Interview request', '访谈请求')}: "
                + (
                    bi(
                        "ready (CRITERIA_INTERVIEW_REQUEST.md)",
                        "已就绪（CRITERIA_INTERVIEW_REQUEST.md）",
                    )
                    if request_ready
                    else bi("not prepared yet", "尚未生成")
                )
            ),
            (
                bi("Criteria report: ready to view", "择偶标准报告：可供查看")
                if has_criteria
                else bi("Criteria report: not written yet", "择偶标准报告：尚未生成")
            ),
        ]
        self.banner.set_text("\n".join(parts))
        if request_ready and not self.prompt_box.toPlainText():
            try:
                _, prompt = self._checked_handoff()
                self.prompt_box.setPlainText(prompt)
            except (ActiveReportError, OSError, ValueError):
                self._handoff_error()

    def _checked_handoff(self) -> tuple[str, str]:
        service = ActiveReportService(self.profile_store.base_dir)
        before = service.get_selection("self_portrait").selection_version
        request = agent_handoff.build_criteria_interview_request(self.profile_store.base_dir)
        prompt = agent_handoff.build_criteria_interview_prompt(self.profile_store.base_dir)
        if service.get_selection("self_portrait").selection_version != before:
            raise ActiveReportError("Report selection changed.")
        return request, prompt

    def _handoff_error(self) -> None:
        self.prompt_box.clear()
        self.banner.set_text(bi(
            "The selected portrait cannot be verified. Choose a valid report and prepare the "
            "request again. Previous request files, notes and clipboard have not been changed.",
            "无法校验已选画像。请选择有效报告后重新生成请求。之前的请求文件、笔记和剪贴板"
            "均未改变。",
        ))

    def _prepare(self) -> None:
        try:
            request, prompt = self._checked_handoff()
        except (ActiveReportError, OSError, ValueError):
            self._handoff_error()
            return
        text = self.notes.toPlainText().strip()
        if text:
            saved = self.profile_store.save_import_text(text, "my_stated_ideal_partner.md")
            if saved not in self.state.import_sources:
                self.state.import_sources.append(saved)
        request_path = self.profile_store.write_criteria_interview_request(
            request
        )
        self.profile_store.write_agent_instructions()
        self.prompt_box.setPlainText(prompt)
        self.on_enter()
        self.banner.set_text(
            f"{bi('Interview request written to', '访谈请求已写入')}: {request_path}\n"
            + bi(
                "Use this manual prompt only with an isolated local model. For external AI, "
                "use Connect AI and review the disclosure inside the app. A desktop agent "
                "may still send data to a cloud model.",
                "手动提示词仅供已隔离的本地模型使用。外部 AI 请通过「连接 AI」"
                "在应用内审核披露内容。"
                "桌面代理也可能将数据发送给云端模型。",
            )
        )

    def _copy_prompt(self) -> None:
        try:
            request, prompt = self._checked_handoff()
        except (ActiveReportError, OSError, ValueError):
            self._handoff_error()
            return
        self.profile_store.write_criteria_interview_request(request)
        self.prompt_box.setPlainText(prompt)
        QApplication.clipboard().setText(prompt)
        self.banner.set_text(bi("Prompt copied to clipboard.", "提示词已复制到剪贴板。"))

    def _open_vault(self) -> None:
        self.profile_store.create_default_directories()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.profile_store.base_dir)))
