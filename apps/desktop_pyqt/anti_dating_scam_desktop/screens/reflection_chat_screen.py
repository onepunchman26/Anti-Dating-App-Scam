"""A user-controlled conversation and separately reviewed private reflection."""

import copy
import threading
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.reports.localized_reports import render_localized_reports
from anti_dating_scam.services.reflection_chat import (
    ReflectionChatService,
    list_saved_reflections,
    read_saved_reflection,
)
from anti_dating_scam.services.relationship_memory import RelationshipMemory
from anti_dating_scam.services.reviewed_ai import isinstance_local
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi, current_language
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.relationship_memory_dialog import RelationshipMemoryDialog
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader
from anti_dating_scam_desktop.widgets.voice_input_dialog import VoiceInputDialog
from anti_dating_scam_desktop.workers import run_async


@dataclass
class ReflectionChatState:
    services: dict[Path, ReflectionChatService] = field(default_factory=dict)
    drafts: dict[Path, str] = field(default_factory=dict)
    saved: dict[Path, Path] = field(default_factory=dict)
    current_vault: Path | None = None


def review_reflection_request(parent, backend, prepared, service):
    """Readable exact disclosure; advanced request details need no editing."""
    if isinstance_local(backend):
        return None
    dialog = QDialog(parent)
    dialog.setWindowTitle(bi("Send to ChatGPT?", "发送给 ChatGPT？"))
    dialog.resize(760, 580)
    layout = QVBoxLayout(dialog)
    note = QLabel(
        bi(
            "This request sends the answers below and up to two earlier AI questions to "
            "ChatGPT, together with enabled notes shown below. "
            "Other local files and chats are excluded.",
            "本次会将下方回答及至多两条先前 AI 问题发送给 ChatGPT。"
            "以及下方显示的已启用记忆；不包含其他本地文件或聊天，请阅读后再发送。",
        )
    )
    note.setWordWrap(True)
    layout.addWidget(note)
    viewer = QPlainTextEdit()
    viewer.setReadOnly(True)
    parts = [
        f"{item.source}:\n{item.content}" for item in service.transcript if item.role == "user"
    ]
    questions = [item for item in service.transcript if item.role == "assistant"][-2:]
    parts.extend(
        f"{bi('Earlier AI question (context)', '先前 AI 问题（背景）')}:\n"
        f"{item.content_en}\n{item.content_zh}"
        for item in questions
    )
    if service._memory.enabled:
        parts.extend(
            bi("Approved note (unverified context): ", "已批准记忆（未经核实的背景）：") + item.text
            for item in service._memory.entries
        )
    viewer.setPlainText(
        "\n\n".join(parts)
        or bi(
            "No answers yet. Ask the first reflection question.",
            "尚无回答，仅请求第一个反思问题。",
        )
    )
    layout.addWidget(viewer, 1)
    details_button = SecondaryButton(bi("Show request details", "查看请求详情"))
    layout.addWidget(details_button)
    details = QPlainTextEdit()
    details.setReadOnly(True)
    details.setPlainText(
        backend.recipient
        + "\n\n"
        + prepared.request.system
        + "\n\n"
        + "\n\n".join(item.content for item in prepared.request.messages)
    )
    details.setVisible(False)
    layout.addWidget(details)
    details_button.clicked.connect(lambda: details.setVisible(not details.isVisible()))
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
    )
    buttons.button(QDialogButtonBox.StandardButton.Ok).setText(bi("Send", "发送"))
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(bi("Cancel", "取消"))
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    reviewed = build_reviewed_request(
        prepared.request.messages,
        system=prepared.request.system,
        recipient=backend.recipient,
    )
    return reviewed.model_copy(
        update={
            "response_schema": prepared.request.response_schema,
            "allow_schema_fallback": False,
        }
    )


class ReflectionChatScreen(QWidget):
    def __init__(self, state, profile_store, holder, on_connect, on_back, on_exchange=None):
        super().__init__()
        self.profile_store = profile_store
        self.holder = holder
        self.on_connect = on_connect
        self.on_back = on_back
        self._busy = False
        self._retry_available = False
        self._cancel_event = None
        self._vault = None
        self.service = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(10)
        layout.addWidget(
            StepHeader(
                bi("AI Chat", "AI 聊天"),
                bi(
                    "Explore needs, boundaries and ways of relating. Skip or change topic freely.",
                    "聊聊需要、边界与相处方式。可以跳过问题，也可以换个话题。",
                ),
            )
        )
        self.banner = StatusBanner()
        layout.addWidget(self.banner)
        self.connect_button = SecondaryButton(bi("Connect ChatGPT", "连接 ChatGPT"))
        self.connect_button.clicked.connect(on_connect)
        layout.addWidget(self.connect_button)
        row = QHBoxLayout()
        self.start_button = PrimaryButton(bi("Start", "开始"))
        self.start_button.clicked.connect(self._start)
        self.end_button = SecondaryButton(bi("End", "结束"))
        self.end_button.clicked.connect(self._end)
        row.addWidget(self.start_button)
        row.addWidget(self.end_button)
        layout.addLayout(row)
        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(False)
        self.chat_view.setOpenLinks(False)
        self.chat_view.setMinimumHeight(160)
        layout.addWidget(self.chat_view, 1)
        self.input_box = QPlainTextEdit()
        self.input_box.setObjectName("reflection_answer")
        self.input_box.setAccessibleName(bi("Your answer", "你的回答"))
        self.input_box.setPlaceholderText(
            bi(
                "Answer in your own words. You can say ‘skip’ or choose another topic.",
                "用自己的话回答，也可以说“跳过”或另选话题。",
            )
        )
        self.input_box.setMaximumHeight(85)
        self.input_box.textChanged.connect(self._remember_draft)
        layout.addWidget(self.input_box)
        send_row = QHBoxLayout()
        self.voice_button = SecondaryButton(bi("Voice input", "语音输入"))
        self.voice_button.setObjectName("reflection_voice_input")
        self.voice_button.clicked.connect(self._voice)
        send_row.addWidget(self.voice_button)
        self.send_button = PrimaryButton(bi("Send", "发送"))
        self.send_button.clicked.connect(self._send)
        send_row.addWidget(self.send_button)
        layout.addLayout(send_row)
        self.retry_button = SecondaryButton(bi("Try this reply again", "重新请求回复"))
        self.retry_button.clicked.connect(self._retry)
        self.retry_button.setVisible(False)
        layout.addWidget(self.retry_button)
        self.portrait_button = SecondaryButton(bi("Create my reflection", "生成我的相处画像"))
        self.portrait_button.clicked.connect(self._portrait)
        layout.addWidget(self.portrait_button)
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(False)
        self.preview.setOpenLinks(False)
        self.preview.setMinimumHeight(190)
        self.preview.setVisible(False)
        layout.addWidget(self.preview)
        self.save_button = SecondaryButton(bi("Save this reflection", "保存这份画像"))
        self.save_button.clicked.connect(self._save)
        self.save_button.setVisible(False)
        layout.addWidget(self.save_button)
        self.memory_button = SecondaryButton(bi("My approved notes", "我批准的记忆"))
        self.memory_button.clicked.connect(self._memory)
        layout.addWidget(self.memory_button)
        self.history_button = SecondaryButton(bi("Saved reflections", "已保存画像"))
        self.history_button.clicked.connect(self._history)
        layout.addWidget(self.history_button)
        if on_exchange is not None:
            exchange = SecondaryButton(bi("Share or compare reflections", "分享或比对相处画像"))
            exchange.clicked.connect(on_exchange)
            layout.addWidget(exchange)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(lambda: (self._end(), self.on_back()))
        layout.addWidget(back)
        self.on_enter()

    def on_enter(self):
        vault = Path(self.profile_store.base_dir)
        if vault != self._vault:
            old = self.holder.current_vault
            if old is not None and old != vault and old in self.holder.services:
                self.holder.services[old].stop()
            self._vault = vault
            self.holder.current_vault = vault
            self.service = self.holder.services.setdefault(
                vault,
                ReflectionChatService(language=current_language()),
            )
            self.input_box.setPlainText(self.holder.drafts.get(vault, ""))
        self._render()
        self._controls()
        if ai_backend.get_active() is None:
            self.banner.set_text(
                bi("Connect ChatGPT, then press Start.", "连接 ChatGPT，然后点击开始。")
            )
        elif not self.service.session_id:
            self.banner.set_text(bi("Press Start whenever you are ready.", "准备好时，点击开始。"))

    def _remember_draft(self):
        if self._vault is not None:
            self.holder.drafts[self._vault] = self.input_box.toPlainText()

    def _controls(self):
        connected = ai_backend.get_active() is not None
        running = bool(self.service and self.service.running)
        ended = bool(self.service and self.service.session_id and not running)
        self.start_button.setEnabled(connected and not running and not self._busy)
        # End always invalidates a pending reply, even during a network request.
        self.end_button.setEnabled(running or self._busy)
        self.send_button.setEnabled(connected and running and not self._busy)
        self.input_box.setEnabled(running and not self._busy)
        self.voice_button.setEnabled(running and not self._busy)
        self.portrait_button.setEnabled(connected and ended and not self._busy)
        self.portrait_button.setEnabled(
            self.portrait_button.isEnabled() and self._vault not in self.holder.saved
        )
        self.retry_button.setVisible(running and self._retry_available)
        self.retry_button.setEnabled(connected and running and not self._busy)
        self.connect_button.setVisible(not connected)
        self.history_button.setEnabled(not self._busy)
        self.memory_button.setEnabled(not self._busy)
        self.save_button.setEnabled(not self._busy and self._vault not in self.holder.saved)

    def _render(self):
        lang = current_language()
        lines = []
        for item in self.service.transcript:
            who = bi("You", "你") if item.role == "user" else bi("AI", "AI")
            text = item.content if item.role == "user" else getattr(item, "content_" + lang)
            lines.append(f"{who}:\n{text}")
        self.chat_view.setPlainText("\n\n".join(lines))
        self.chat_view.verticalScrollBar().setValue(self.chat_view.verticalScrollBar().maximum())
        bundle = self.service.portrait
        self.preview.setVisible(bundle is not None)
        self.save_button.setVisible(bundle is not None)
        if bundle:
            self._show_bundle(bundle)

    def _show_bundle(self, bundle):
        rendered = render_localized_reports(
            "self_portrait",
            {"report": bundle["report"]},
            bundle["localized_text"],
            language=current_language(),
        )
        self.preview.setMarkdown(
            bi(
                "Tentative reflection of what you said; review wording and quotations.",
                "基于你所说内容的暂定反思，请核对措辞和引文。",
            )
            + "\n\n"
            + rendered["detailed_markdown"]
        )
        self.preview.setVisible(True)

    def _sync_memory(self):
        try:
            self.service.set_memory(RelationshipMemory(self._vault).read())
            return True
        except (OSError, ValueError):
            self.banner.set_text(
                bi(
                    "Approved notes could not be read. Nothing was sent.",
                    "无法读取已批准记忆，尚未发送任何内容。",
                )
            )
            return False

    def _memory(self):
        try:
            RelationshipMemoryDialog(self._vault, self, self.service.session_id).exec()
            self._sync_memory()
        except (OSError, ValueError):
            self.banner.set_text(bi("Notes could not be opened safely.", "无法安全打开记忆。"))

    def _start(self):
        if self._busy or ai_backend.get_active() is None or self.service.running:
            return
        if self.service.session_id and self._vault not in self.holder.saved:
            answer = QMessageBox.question(
                self,
                bi("Start again?", "重新开始？"),
                bi(
                    "The current unsaved conversation will be replaced in this window. "
                    "Cancel to create and save its reflection first.",
                    "当前窗口中未保存的对话将被替换。可以取消，先生成并保存它的画像。",
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        if not self._sync_memory():
            return
        self.holder.saved.pop(self._vault, None)
        self._retry_available = False
        self._call(self.service.begin())

    def _send(self):
        text = self.input_box.toPlainText()
        if self._busy or not self.service.running or not text.strip():
            return
        if not self._sync_memory():
            return
        try:
            prepared = self.service.propose_turn(text)
        except ValueError:
            self.banner.set_text(
                bi(
                    "This answer or conversation is too long. Shorten it or end and reflect.",
                    "本次回答或对话过长。请缩短回答，或结束并生成画像。",
                )
            )
            return
        self._call(prepared, clear_draft=True)

    def _voice(self):
        if self._busy or not self.service.running:
            return
        dialog = VoiceInputDialog(self, language=current_language())
        dialog.transcript_ready.connect(self._voice_draft)
        dialog.exec()

    def _voice_draft(self, text):
        # Recognition is an editable draft, never an implicit model request.
        if self._busy or not self.service.running or not text.strip():
            return
        old = self.input_box.toPlainText()
        self.input_box.setPlainText(old + ("\n" if old else "") + text)
        self.input_box.setFocus()
        self.banner.set_text(
            bi(
                "Voice text added. Edit it, then press Send when you choose.",
                "语音文字已加入草稿。请修改，准备好后自行点击发送。",
            )
        )

    def _retry(self):
        if self._busy or not self.service.running:
            return
        try:
            self._call(self.service.question_request())
        except ValueError:
            self.banner.set_text(
                bi("End the conversation or try a new one.", "请结束这段对话，或开始新对话。")
            )

    def _end(self):
        if self._cancel_event is not None:
            self._cancel_event.set()
        self._busy = False
        if self.service:
            self.service.stop()
        self.banner.set_text(
            bi(
                "Ended. You can create a reflection or start again. A pending online request "
                "may still finish; its reply is discarded.",
                "已结束，可以生成画像或重新开始。正在处理的在线请求可能仍会完成，回复将被丢弃。",
            )
        )
        self._controls()

    def _portrait(self):
        if self._busy:
            return
        try:
            self._call(self.service.portrait_request())
        except ValueError:
            self.banner.set_text(
                bi("End the chat before creating a new reflection.", "请先结束聊天，再生成新画像。")
            )

    def _call(self, prepared, *, clear_draft=False):
        backend = ai_backend.get_active()
        if backend is None:
            self.service.cancel_pending()
            self._controls()
            return
        service, vault = self.service, self._vault
        reviewed = review_reflection_request(self, backend, prepared, service)
        if not isinstance_local(backend) and reviewed is None:
            service.cancel_pending()
            if clear_draft:
                self.input_box.clear()
            self.banner.set_text(
                bi(
                    "Nothing was sent. Your answer stays in this chat; you can retry or end.",
                    "尚未发送，你的回答保留在聊天记录中；可以重新请求或结束。",
                )
            )
            self._retry_available = prepared.purpose == "question"
            self._render()
            self._controls()
            return
        if clear_draft:
            self.input_box.clear()
        self._busy = True
        self._retry_available = False
        self._cancel_event = threading.Event()
        cancel = self._cancel_event
        backend = copy.copy(backend)
        set_cancel = getattr(backend, "set_cancel_event", None)
        if callable(set_cancel):
            set_cancel(self._cancel_event)
        self._render()
        self._controls()
        self.banner.set_text(
            bi("Thinking… You can press End now.", "正在思考……你仍可随时点击结束。")
        )

        def call():
            return service.generate(prepared, backend, confirmed=True, reviewed_request=reviewed)

        def done(_result):
            if cancel.is_set() or cancel is not self._cancel_event or vault != self._vault:
                return
            self._busy = False
            if vault == self._vault:
                self._render()
                self.banner.set_text(
                    bi(
                        "Take your time. Answer, skip, change topic, or end.",
                        "慢慢来，可以回答、跳过、换话题或结束。",
                    )
                    if service.running
                    else bi(
                        "Review the reflection and its evidence before saving.",
                        "保存前，请核对画像及其引用。",
                    )
                )
            if service.ai_receipts:
                receipt = service.ai_receipts[-1]
                self.banner.set_text(
                    self.banner.label.text()
                    + "\n"
                    + bi("Requested: ", "请求模型：")
                    + receipt.requested_model
                    + " · "
                    + bi("Reported: ", "返回模型：")
                    + (receipt.reported_model or bi("not reported", "未提供"))
                    + (
                        bi(" (different ID; alias unverified)", "（标识不同，尚未核验别名）")
                        if receipt.model_agreement == "different"
                        else ""
                    )
                )
            self._controls()

        def error(_message):
            if cancel.is_set() or cancel is not self._cancel_event or vault != self._vault:
                return
            self._busy = False
            self._retry_available = prepared.purpose == "question"
            self._render()
            self.banner.set_text(
                bi(
                    "No new AI result was accepted. Your words are kept here. Check the "
                    "connection or ChatGPT usage settings; no retry runs automatically.",
                    "未接纳新的 AI 结果，你的话语仍保留在这里。请检查连接或 ChatGPT 用量设置；"
                    "不会自动重试。",
                )
                if service.running
                else bi("Ended; pending replies were discarded.", "已结束，待处理回复已丢弃。")
            )
            if service.running and _message:
                self.banner.set_text(_message)
            self._controls()

        run_async(self, call, done, error)

    def _save(self):
        if self._busy or not self.service.portrait:
            return
        answer = QMessageBox.question(
            self,
            bi("Save this reflection?", "保存这份画像？"),
            bi(
                "Save this reflection and conversation as separate ordinary files in your "
                "local folder? They are not encrypted. Review quotations and translations first.",
                "将这份画像与对话另存为本地文件？文件未加密，请先核对引文及翻译。",
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            saved = self.service.save(self._vault, confirmed=True)
            self.holder.saved[self._vault] = saved.directory
            self.banner.set_text(
                bi(
                    "Saved. You can read it under Saved reflections.",
                    "已保存，可从已保存画像中查看。",
                )
            )
        except ValueError:
            self.banner.set_text(
                bi(
                    "Could not save; your conversation remains here.",
                    "无法保存，你的对话仍保留在这里。",
                )
            )
        self._controls()

    def _history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(bi("Saved reflections", "已保存画像"))
        dialog.resize(800, 620)
        layout = QVBoxLayout(dialog)
        viewer = QTextBrowser()
        viewer.setOpenExternalLinks(False)
        viewer.setOpenLinks(False)
        try:
            items = list_saved_reflections(self._vault)
            for item in items:
                button = QPushButton(bi("Reflection", "画像") + " " + item.session_id[:10])

                def read(_checked=False, record=item):
                    try:
                        bundle = read_saved_reflection(self._vault, record.session_id)
                        rendered = render_localized_reports(
                            "self_portrait",
                            {"report": bundle["report"]},
                            bundle["localized_text"],
                            language=current_language(),
                        )
                        viewer.setMarkdown(rendered["detailed_markdown"])
                    except ValueError:
                        viewer.setPlainText(
                            bi("Saved files could not be verified.", "无法核验保存文件。")
                        )

                button.clicked.connect(read)
                layout.addWidget(button)
            if not items:
                viewer.setPlainText(
                    bi("No saved reflections in this folder.", "此文件夹尚无已保存画像。")
                )
        except ValueError:
            viewer.setPlainText(bi("Saved files could not be verified.", "无法核验保存文件。"))
        layout.addWidget(viewer, 1)
        close = SecondaryButton(bi("Close", "关闭"))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()
