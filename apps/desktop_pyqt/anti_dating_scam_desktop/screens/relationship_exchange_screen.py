"""Manual encrypted attachments and consented two-summary discussion."""

import json
import threading
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.services.reflection_chat import list_saved_reflections
from anti_dating_scam.services.relationship_comparison import (
    RelationshipComparisonService,
    render_relationship_comparison,
)
from anti_dating_scam.services.relationship_exchange import (
    RelationshipExchangeService,
    import_relationship_file,
    preview_relationship_profile,
    profile_digest,
)
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi, current_language
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader
from anti_dating_scam_desktop.widgets.wrapped_checkbox import WrappedCheckBox
from anti_dating_scam_desktop.workers import run_async


@dataclass
class RelationshipExchangeState:
    vault_key: str | None = None
    own_packet: object = None
    other_packet: object = None
    prepared_export: object = None
    report: object = None
    comparison: object = None
    token: int = 0
    cancel_event: object = None
    own_consented: bool = False
    other_consented: bool = False

    def stop(self):
        self.token += 1
        if self.cancel_event is not None:
            self.cancel_event.set()
        if self.comparison is not None:
            self.comparison.stop()

    def clear_for_vault(self, key):
        if self.vault_key == key:
            return
        self.stop()
        self.vault_key = key
        self.own_packet = self.other_packet = self.prepared_export = self.report = None
        self.comparison = None
        self.own_consented = self.other_consented = False


def review_relationship_request(parent, backend, prepared):
    """Exact request is viewable; approval cannot change its data or schema."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(bi("Review private comparison", "审阅私下相处讨论"))
    dialog.resize(760, 580)
    layout = QVBoxLayout(dialog)
    note = QLabel(
        bi(
            "Only the two summaries are used. Local AI stays on this device; ChatGPT sends "
            "the reviewed summaries online. Both people must permit this use. No email is sent.",
            "只使用双方摘要。本地 AI 在本机运行；ChatGPT 将审阅过的摘要在线处理。"
            "双方须许可此用途，不会发送邮件。",
        )
    )
    note.setWordWrap(True)
    layout.addWidget(note)
    preview = QPlainTextEdit()
    preview.setReadOnly(True)
    preview.setPlainText(
        parent.own_preview.toPlainText() + "\n\n" + parent.other_preview.toPlainText()
    )
    layout.addWidget(preview, 1)
    details = QPlainTextEdit()
    details.setReadOnly(True)
    details.setPlainText(
        backend.recipient
        + "\n\n"
        + prepared.request.system
        + "\n\n"
        + "\n".join(m.content for m in prepared.request.messages)
        + "\n\n"
        + json.dumps(prepared.request.response_schema, ensure_ascii=False)
    )
    details.hide()
    toggle = SecondaryButton(bi("Request details", "请求详情"))
    toggle.clicked.connect(lambda: details.setVisible(not details.isVisible()))
    layout.addWidget(toggle)
    layout.addWidget(details)
    actions = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    actions.button(QDialogButtonBox.StandardButton.Ok).setText(bi("Analyze", "分析"))
    actions.button(QDialogButtonBox.StandardButton.Cancel).setText(bi("Cancel", "取消"))
    actions.accepted.connect(dialog.accept)
    actions.rejected.connect(dialog.reject)
    layout.addWidget(actions)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    from anti_dating_scam.services.reviewed_ai import isinstance_local

    if isinstance_local(backend):
        return prepared.request
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


class RelationshipExchangeScreen(QWidget):
    def __init__(
        self,
        state,
        profile_store,
        exchange_state,
        on_back,
        *,
        backend_getter=None,
        async_runner=None,
        reviewer=None,
    ):
        super().__init__()
        self.profile_store, self.holder = profile_store, exchange_state
        self.on_back = on_back
        self.backend_getter = backend_getter or ai_backend.get_active
        self.async_runner = async_runner or run_async
        self.reviewer = reviewer or review_relationship_request
        self._busy = False
        self._vault = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(12)
        layout.addWidget(
            StepHeader(
                bi("Share or compare reflections", "分享或比对相处画像"),
                bi(
                    "Exchange a private attachment, then discuss two chosen summaries.",
                    "私下交换加密附件，再讨论双方选择分享的摘要。",
                ),
            )
        )
        self.banner = StatusBanner(
            bi(
                "Choose a saved reflection or import your own file.",
                "选择已保存画像，或导入自己的文件。",
            )
        )
        layout.addWidget(self.banner)
        label = QLabel(bi("Your saved reflection", "你已保存的画像"))
        layout.addWidget(label)
        self.saved_picker = QComboBox()
        self.saved_picker.setObjectName("exchange_saved_reflection")
        self.saved_picker.setAccessibleName(label.text())
        label.setBuddy(self.saved_picker)
        layout.addWidget(self.saved_picker)
        self.prepare_button = SecondaryButton(bi("Preview selected reflection", "预览所选画像"))
        self.prepare_button.setObjectName("exchange_prepare")
        self.prepare_button.clicked.connect(self._prepare)
        layout.addWidget(self.prepare_button)
        self.own_preview = self._viewer("exchange_own_preview", bi("Your summary", "你的摘要"))
        layout.addWidget(self.own_preview)
        self.export_consent = WrappedCheckBox(
            bi(
                "I reviewed this exact summary and choose to share it with my intended recipient.",
                "我已审阅这份准确摘要，选择将它分享给我指定的接收者。",
            )
        )
        self.export_consent.toggled.connect(self._controls)
        layout.addWidget(self.export_consent)
        self.export_button = PrimaryButton(bi("Export encrypted attachment", "导出加密附件"))
        self.export_button.setObjectName("exchange_export")
        self.export_button.clicked.connect(self._export)
        layout.addWidget(self.export_button)
        note = QLabel(
            bi(
                "Attach the exported .slowmatch file using your own email app. Send its "
                "password separately. The app never sends email. "
                "Local chat history is not encrypted.",
                "由你自己把导出的 .slowmatch 文件附到邮件，密码另行发送。应用不会发送邮件。"
                "本地聊天历史仍未加密。",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.own_consent = WrappedCheckBox(
            bi(
                "I permit my summary to be opened and used for this private AI comparison.",
                "我许可打开我的摘要，并用于这次私下 AI 相处讨论。",
            )
        )
        self.other_consent = WrappedCheckBox(
            bi(
                "The other person permits opening their file and this private use, including "
                "the selected AI after request review. Their identity is not verified.",
                "对方许可打开其文件并用于此次私下讨论，包括审阅后使用所选 AI；其身份未经核实。",
            )
        )
        for box in (self.own_consent, self.other_consent):
            box.toggled.connect(self._permissions)
            layout.addWidget(box)
        self.import_own_button = SecondaryButton(bi("Import my encrypted file", "导入我的加密文件"))
        self.import_own_button.setObjectName("exchange_import_own")
        self.import_own_button.clicked.connect(lambda: self._import_file(own=True))
        layout.addWidget(self.import_own_button)
        self.import_other_button = SecondaryButton(
            bi("Import their encrypted file", "导入对方加密文件")
        )
        self.import_other_button.setObjectName("exchange_import_other")
        self.import_other_button.clicked.connect(lambda: self._import_file(own=False))
        layout.addWidget(self.import_other_button)
        self.other_preview = self._viewer("exchange_other_preview", bi("Their summary", "对方摘要"))
        layout.addWidget(self.other_preview)
        self.compare_button = PrimaryButton(
            bi("Ask AI about how we might relate", "请 AI 讨论我们如何相处")
        )
        self.compare_button.setObjectName("exchange_compare")
        self.compare_button.clicked.connect(self._compare)
        layout.addWidget(self.compare_button)
        self.stop_button = SecondaryButton(bi("Stop comparison", "停止讨论"))
        self.stop_button.setObjectName("exchange_stop")
        self.stop_button.clicked.connect(self._stop)
        layout.addWidget(self.stop_button)
        self.offline_button = SecondaryButton(
            bi("Offline question guide (no AI)", "离线问题提纲（不调用 AI）")
        )
        self.offline_button.setObjectName("exchange_offline")
        self.offline_button.clicked.connect(self._offline)
        layout.addWidget(self.offline_button)
        self.result_view = self._viewer("exchange_result", bi("Discussion result", "讨论结果"))
        layout.addWidget(self.result_view)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(lambda: (self._stop(), self.on_back()))
        layout.addWidget(back)
        self._controls()

    def _viewer(self, name, accessible):
        viewer = QPlainTextEdit()
        viewer.setObjectName(name)
        viewer.setAccessibleName(accessible)
        viewer.setReadOnly(True)
        viewer.setMinimumHeight(140)
        return viewer

    def on_enter(self):
        self._vault = Path(self.profile_store.base_dir)
        self.holder.clear_for_vault(str(self._vault))
        self._busy = False
        self.saved_picker.clear()
        self.saved_picker.addItem(bi("Choose a saved reflection", "选择已保存画像"), None)
        try:
            for item in list_saved_reflections(self._vault):
                self.saved_picker.addItem(
                    bi("Reflection", "画像") + " " + item.session_id[:10], item.session_id
                )
        except ValueError:
            self.banner.set_text(
                bi("Saved reflections could not be verified.", "无法核验已保存画像。")
            )
        for box, value in (
            (self.own_consent, self.holder.own_consented),
            (self.other_consent, self.holder.other_consented),
        ):
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)
        self._render()
        self._controls()

    def _controls(self):
        ready = bool(
            self.holder.own_packet
            and self.holder.other_packet
            and self.own_consent.isChecked()
            and self.other_consent.isChecked()
        )
        self.prepare_button.setEnabled(not self._busy)
        self.saved_picker.setEnabled(not self._busy)
        self.export_button.setEnabled(
            bool(self.holder.prepared_export) and self.export_consent.isChecked() and not self._busy
        )
        self.import_own_button.setEnabled(self.own_consent.isChecked() and not self._busy)
        self.import_other_button.setEnabled(self.other_consent.isChecked() and not self._busy)
        self.compare_button.setEnabled(
            ready and self.backend_getter() is not None and not self._busy
        )
        self.offline_button.setEnabled(ready and not self._busy)
        self.stop_button.setEnabled(self._busy)

    def _render(self):
        for packet, viewer in (
            (self.holder.own_packet, self.own_preview),
            (self.holder.other_packet, self.other_preview),
        ):
            viewer.setPlainText(
                preview_relationship_profile(packet, current_language())
                if packet is not None
                else ""
            )
        self.result_view.setPlainText(
            render_relationship_comparison(
                self.holder.report,
                current_language(),
            )
            if self.holder.report is not None
            else ""
        )

    def _permissions(self):
        self.holder.own_consented = self.own_consent.isChecked()
        self.holder.other_consented = self.other_consent.isChecked()
        if not self.holder.own_consented or not self.holder.other_consented:
            self._stop()
            self.holder.report = None
            if not self.holder.other_consented:
                self.holder.other_packet = None
            self._render()
        self._controls()

    def _prepare(self):
        if self._busy or self._vault is None or self.saved_picker.currentData() is None:
            return
        try:
            prepared = RelationshipExchangeService(self._vault).prepare_export(
                self.saved_picker.currentData(),
            )
            self._stop()
            self.holder.prepared_export = prepared
            self.holder.own_packet = prepared.packet
            self.holder.report = None
            self.export_consent.setChecked(False)
            self._render()
            self.banner.set_text(
                bi("Review every line before choosing to export.", "请逐行审阅，再选择是否导出。")
            )
        except ValueError:
            self.banner.set_text(
                bi("This saved reflection could not be verified.", "无法核验这份画像。")
            )
        self._controls()

    def _password(self):
        password, ok = QInputDialog.getText(
            self,
            bi("File password", "文件密码"),
            bi(
                "Password/passphrase (12–256 characters). There is no password recovery.",
                "密码或口令（12–256 字符），不提供密码找回。",
            ),
            QLineEdit.EchoMode.Password,
        )
        return password if ok else None

    def _export(self):
        if self._busy or not self.export_consent.isChecked() or not self.holder.prepared_export:
            return
        password = self._password()
        if password is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            bi("Save encrypted attachment", "保存加密附件"),
            "relationship.slowmatch",
            "SlowMatch (*.slowmatch)",
        )
        if not path:
            return
        try:
            exported = RelationshipExchangeService(self._vault).export_file(
                self.holder.prepared_export,
                Path(path),
                password,
                confirmed=True,
            )
            self.banner.set_text(
                bi(
                    "Encrypted attachment saved. Attach it to your email:",
                    "加密附件已保存，可自行附加到邮件：",
                )
                + "\n"
                + str(exported.path)
            )
        except ValueError:
            self.banner.set_text(
                bi(
                    "Could not export. Check the password and choose a new filename.",
                    "导出未完成，请检查密码并选择新文件名。",
                )
            )

    def _import_file(self, *, own):
        consent = self.own_consent if own else self.other_consent
        if self._busy or not consent.isChecked():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, bi("Open encrypted file", "打开加密文件"), "", "SlowMatch (*.slowmatch)"
        )
        if not path:
            return
        password = self._password()
        if password is None:
            return
        try:
            packet = import_relationship_file(Path(path), password, confirmed=True)
            self._stop()
            if own:
                self.holder.own_packet = packet
                self.holder.prepared_export = None
                self.export_consent.setChecked(False)
            else:
                self.holder.other_packet = packet
            self.holder.report = None
            self._render()
            self.banner.set_text(
                bi(
                    "Opened in memory. Review the summary; nothing was uploaded.",
                    "已在内存中打开，请审阅摘要；未上传任何内容。",
                )
            )
        except ValueError:
            self.banner.set_text(
                bi(
                    "Could not open this file. Check its password and format.",
                    "无法打开此文件，请检查密码与格式。",
                )
            )
        self._controls()

    def _comparison(self):
        if not (
            self.own_consent.isChecked()
            and self.other_consent.isChecked()
            and self.holder.own_packet
            and self.holder.other_packet
        ):
            raise ValueError("Both summaries and permissions are required.")
        return RelationshipComparisonService(self.holder.own_packet, self.holder.other_packet)

    def _compare(self):
        backend = self.backend_getter()
        if self._busy or backend is None:
            return
        try:
            service = self._comparison()
            prepared = service.prepare(own_consent=True, other_consent=True)
            reviewed = self.reviewer(self, backend, prepared)
            if reviewed is None:
                service.stop()
                self.banner.set_text(bi("Canceled. Nothing was sent.", "已取消，未发送任何内容。"))
                return
            if (
                not self.own_consent.isChecked()
                or not self.other_consent.isChecked()
                or self.holder.own_packet is None
                or self.holder.other_packet is None
                or profile_digest(self.holder.own_packet) != prepared.own_digest
                or profile_digest(self.holder.other_packet) != prepared.other_digest
            ):
                service.stop()
                raise ValueError("The reviewed summaries or permissions changed.")
            from anti_dating_scam.services.reviewed_ai import isinstance_local

            local = isinstance_local(backend)
            self.holder.stop()
            self.holder.comparison = service
            self.holder.cancel_event = threading.Event()
            cancel, token = self.holder.cancel_event, self.holder.token
            self.holder.report = None
            self._busy = True
            self._render()
            self.banner.set_text(
                bi(
                    "AI is preparing a discussion… You can stop now.",
                    "AI 正在准备讨论……你可以随时停止。",
                )
            )
            self._controls()

            def work():
                if cancel.is_set():
                    raise ValueError("Stopped before transport.")
                if hasattr(backend, "set_cancel_event"):
                    backend.set_cancel_event(cancel)
                return service.generate(
                    prepared, backend, confirmed=True, reviewed_request=None if local else reviewed
                )

            def done(report):
                if token != self.holder.token or cancel.is_set():
                    return
                self._busy = False
                self.holder.report = report
                self._render()
                self.banner.set_text(
                    bi(
                        "Review possibilities, quotations and unknowns together.",
                        "请一起审阅可能性、引文与未知事项。",
                    )
                )
                self._controls()

            def error(_message):
                if token != self.holder.token or cancel.is_set():
                    return
                self._busy = False
                self.banner.set_text(
                    bi(
                        "No AI result was accepted. Check the connection or try again.",
                        "未接纳 AI 结果，请检查连接或自行重试。",
                    )
                )
                self._controls()

            self.async_runner(self, work, done, error)
        except ValueError:
            self.banner.set_text(
                bi(
                    "Review two distinct summaries and both permissions first.",
                    "请先审阅双方不同的摘要及两份许可。",
                )
            )

    def _offline(self):
        if self._busy:
            return
        try:
            self.holder.report = self._comparison().offline_discussion(
                own_consent=True,
                other_consent=True,
            )
            self._render()
            self.banner.set_text(
                bi("Static local guide; no AI was called.", "静态本地提纲，未调用 AI。")
            )
        except ValueError:
            self.banner.set_text(
                bi("Both summaries and permissions are needed.", "需要双方摘要及许可。")
            )

    def _stop(self):
        self.holder.stop()
        self._busy = False
        self._controls()
