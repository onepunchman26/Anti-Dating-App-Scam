"""Desktop workflow for adult introductions and consented peer matching."""

from __future__ import annotations

import copy
import json
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.matchmaking.peer_client import PeerClient, invitation_link, parse_invitation
from anti_dating_scam.matchmaking.peer_models import AdultDeclaration, PeerReport
from anti_dating_scam.services.dating_introduction import IntroductionFormat, IntroductionService
from anti_dating_scam.services.peer_ai import (
    comparison_request,
    generate_comparison,
    render_peer_report,
)
from anti_dating_scam.services.reviewed_ai import isinstance_local
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi, current_language
from anti_dating_scam_desktop.peer_labels import error_text, label
from anti_dating_scam_desktop.peer_runtime import (
    LocalPeerNode,
    PeerSessionStore,
    register_invitation_handler,
)
from anti_dating_scam_desktop.widgets.peer_profile_dialog import MatchingProfileDialog
from anti_dating_scam_desktop.workers import run_async


@dataclass
class PeerWorkbenchState:
    node: object = None
    origin: str = "http://127.0.0.1:8766"
    introductions: dict = field(default_factory=dict)
    edited: dict = field(default_factory=dict)
    pending_link: str = ""

    def stop(self):
        if self.node:
            self.node.stop()


def review_text(parent, title, text, *, cloud=False):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.resize(750, 600)
    layout = QVBoxLayout(dialog)
    preview = QPlainTextEdit()
    preview.setReadOnly(True)
    preview.setPlainText(text)
    layout.addWidget(preview)
    allow = QCheckBox(
        bi(
            "Allow these displayed fields to be sent to ChatGPT for comparison",
            "允许把展示的字段发送给 ChatGPT 进行比较",
        )
    )
    if cloud:
        layout.addWidget(allow)
    actions = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    actions.button(QDialogButtonBox.StandardButton.Ok).setText(bi("Approve", "批准"))
    actions.accepted.connect(dialog.accept)
    actions.rejected.connect(dialog.reject)
    layout.addWidget(actions)
    return dialog.exec() == QDialog.DialogCode.Accepted, allow.isChecked()


def review_ai(parent, backend, request):
    approved, _ = review_text(
        parent,
        bi("Review AI request", "审阅 AI 请求"),
        bi(
            (
                "Only the selected facts below are sent. No pr"
                "ivate database is accessed by the model.\n"
            ),
            "仅发送下方选定事实，模型不能访问私人数据库。\n",
        )
        + backend.recipient
        + "\n\n"
        + request.system
        + "\n\n"
        + "\n".join(m.content for m in request.messages),
    )
    if not approved:
        return None
    if isinstance_local(backend):
        return request
    return build_reviewed_request(
        request.messages, system=request.system, recipient=backend.recipient
    ).model_copy(
        update={"response_schema": request.response_schema, "allow_schema_fallback": False}
    )


class PeerWorkbenchScreen(QWidget):
    def __init__(self, state, profile_store, holder, on_back):
        super().__init__()
        self.state, self.profile_store, self.holder = state, profile_store, holder
        self.vault = None
        self.intro = None
        self.epoch = 0
        self.cancel = None
        self.busy = False
        self.report_invitation = None
        self.cancel_callback = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        title = QLabel(bi("Introductions & invitations", "介绍与邀请"))
        layout.addWidget(title)
        self.status = QLabel(
            bi(
                "Adult participation is optional. Private models stay private.",
                "成年人可按需参与，私人模型保持私密。",
            )
        )
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.buttons = []
        self._introduction_tab()
        self._node_tab()
        self._discovery_tab()
        self._invitations_tab()
        controls = QHBoxLayout()
        stop = QPushButton(bi("Stop current request", "停止当前请求"))
        stop.clicked.connect(self._stop)
        controls.addWidget(stop)
        back = QPushButton(bi("Back", "返回"))
        back.clicked.connect(lambda: (self._stop(), on_back()))
        controls.addWidget(back)
        layout.addLayout(controls)
        self.poll = QTimer(self)
        self.poll.setInterval(15000)
        self.poll.timeout.connect(self._check_report)

    def _button(self, layout, en, zh, callback):
        button = QPushButton(bi(en, zh))
        button.clicked.connect(callback)
        layout.addWidget(button)
        self.buttons.append(button)
        return button

    def _tab(self, en, zh):
        page = QWidget()
        layout = QVBoxLayout(page)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.tabs.addTab(scroll, bi(en, zh))
        return layout

    def _note(self, layout, en, zh):
        note = QLabel(bi(en, zh))
        note.setWordWrap(True)
        layout.addWidget(note)

    def _introduction_tab(self):
        layout = self._tab("My introduction", "我的介绍")
        self._note(
            layout,
            "Choose confirmed non-sensitive notes; nothing is published automatically.",
            "选择已确认且无敏感内容的记忆，不会自动发布任何内容。",
        )
        row = QHBoxLayout()
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        row.addWidget(QLabel(bi("Age", "年龄")))
        row.addWidget(self.age)
        self.adult = QCheckBox(bi("I confirm I am 18 or older", "我确认已年满 18 岁"))
        row.addWidget(self.adult)
        layout.addLayout(row)
        self._button(layout, "Load eligible notes", "载入可用记忆", self._load_sources)
        self.sources = QListWidget()
        self.sources.setMaximumHeight(130)
        layout.addWidget(self.sources)
        self.reconfirm = QCheckBox(
            bi(
                "I reconfirm that selected older notes remain accurate",
                "我重新确认选中的旧记忆仍准确",
            )
        )
        layout.addWidget(self.reconfirm)
        form = QFormLayout()
        self.format_fields = QLineEdit(bi("About me;What I value", "关于我;我重视什么"))
        form.addRow(
            bi(
                "Generic or your own form headings (separate with ;)",
                "通用或自定义栏目（以 ; 分隔）",
            ),
            self.format_fields,
        )
        self.audience = QLineEdit(bi("Consenting adults", "自愿参与的成年人"))
        form.addRow(bi("Audience", "面向谁"), self.audience)
        self.tone = QComboBox()
        self.tone.addItem(bi("Warm and candid", "温暖坦诚"), "warm and candid")
        self.tone.addItem(bi("Short and direct", "简短直接"), "short and direct")
        form.addRow(bi("Tone", "语气"), self.tone)
        self.length = QSpinBox()
        self.length.setRange(80, 1500)
        self.length.setValue(800)
        form.addRow(bi("Total character limit", "总字数上限"), self.length)
        layout.addLayout(form)
        self._button(
            layout, "Generate / regenerate draft", "生成／重新生成草稿", self._generate_intro
        )
        self._button(
            layout, "Shorten with AI (review again)", "用 AI 缩短（重新审核）", self._shorten_intro
        )
        self.fields = QTableWidget(0, 2)
        self.fields.setHorizontalHeaderLabels([bi("Field", "栏目"), bi("Edit text", "编辑文字")])
        self.fields.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.fields)
        self.evidence = QPlainTextEdit()
        self.evidence.setReadOnly(True)
        self.evidence.setMaximumHeight(100)
        layout.addWidget(self.evidence)
        row = QHBoxLayout()
        layout.addLayout(row)
        self._button(row, "Approve edited introduction", "批准编辑后的介绍", self._approve_intro)
        self._button(row, "Copy approved text", "复制已批准文字", self._copy_intro)
        self._button(row, "Export TXT / JSON", "导出 TXT／JSON", self._export_intro)

    def _node_tab(self):
        layout = self._tab("Connection & profile", "连接与匹配资料")
        self._note(
            layout,
            "The local node works on this computer only. Public HTTPS hosting is not configured. "
            "A device identity proves token possession, not verified identity or age.",
            "本机节点仅供同一电脑使用，尚未配置公开 HTTPS 服务。"
            "本机身份仅证明持有访问令牌，不是已核实身份或年龄。",
        )
        self.origin = QLineEdit(self.holder.origin)
        layout.addWidget(self.origin)
        self.origin.textChanged.connect(self._clear_remote_view)
        self._button(layout, "Start local node", "启动本机节点", self._start_node)
        self.alias = QLineEdit()
        self.alias.setPlaceholderText(bi("Your pseudonym", "你的化名"))
        layout.addWidget(self.alias)
        self._note(
            layout,
            "Use the age and 18+ declaration in My introduction. The access credential is saved "
            "under this local folder and protected for your Windows account.",
            "使用“我的介绍”页的年龄及成年声明。"
            "访问凭据保存在当前本地文件夹中，并由 Windows 账户保护。",
        )
        self._button(layout, "Create my node identity", "建立我的节点身份", self._register)
        self._button(layout, "Connect saved identity", "连接已存身份", self._connect)
        self._button(
            layout, "Review matching profile & settings", "审阅匹配资料与设置", self._edit_profile
        )
        self.member_info = QLabel()
        self.member_info.setWordWrap(True)
        layout.addWidget(self.member_info)
        self.member_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._button(
            layout,
            "Publish approved introduction on this node",
            "在此节点发布已批准介绍",
            self._publish,
        )
        self._button(layout, "Withdraw public introduction", "撤下公开介绍", self._unpublish)
        self._button(
            layout,
            "Enable opening app invitation links",
            "启用邀请链接打开应用",
            self._install_links,
        )

    def _discovery_tab(self):
        layout = self._tab("Discover", "发现")
        self._note(
            layout,
            "Only consenting eligible users in the chosen reciprocal areas appear. "
            "Ordering is private and reflects your stated priorities, not a success probability.",
            "只显示在双方选定地区内、合资格且同意的用户。顺序仅自己可见，反映明确偏好，不是关系成功概率。",
        )
        self._button(
            layout, "Refresh eligible candidates", "刷新合资格候选", lambda: self._discover(False)
        )
        self._button(
            layout,
            "Organize authorized comparisons",
            "整理已授权比较",
            lambda: self._discover(True),
        )
        self.candidates = QListWidget()
        layout.addWidget(self.candidates)
        self.candidates.currentRowChanged.connect(self._show_candidate)
        self.candidate_detail = QPlainTextEdit()
        self.candidate_detail.setReadOnly(True)
        layout.addWidget(self.candidate_detail)
        self._button(
            layout,
            "Create invitation for selected participant",
            "为选定参与者创建邀请",
            self._invite_candidate,
        )
        self._button(layout, "Block selected participant", "屏蔽选定参与者", self._block)
        row = QHBoxLayout()
        layout.addLayout(row)
        self._button(row, "Pause discovery", "暂停发现", lambda: self._control("pause"))
        self._button(
            row, "Withdraw matching permission", "撤销匹配许可", lambda: self._control("withdraw")
        )
        self._button(row, "Delete node account", "删除节点账号", lambda: self._control("delete"))

    def _invitations_tab(self):
        layout = self._tab("Invitations & results", "邀请与结果")
        self._note(
            layout,
            "Single-recipient invitations expire. The sender must confirm the claimant, "
            "then both approve the exact versions. "
            "A forwarded link alone never authorizes comparison.",
            "邀请限一位接收人且会到期。发起人须确认认领者，随后双方批准精确版本。转发链接本身不授权比较。",
        )
        self.hours = QSpinBox()
        self.hours.setRange(1, 168)
        self.hours.setValue(48)
        row = QHBoxLayout()
        row.addWidget(QLabel(bi("Expiry in hours", "有效小时数")))
        row.addWidget(self.hours)
        layout.addLayout(row)
        self._button(
            layout, "Create invitation link", "创建邀请链接", lambda: self._create_invite()
        )
        self.link = QLineEdit()
        self.link.setPlaceholderText(bi("Paste invitation link", "粘贴邀请链接"))
        layout.addWidget(self.link)
        self._button(layout, "Copy this invitation link", "复制这份邀请链接", self._copy_link)
        self._button(layout, "Claim this invitation", "认领这份邀请", lambda: self._act("claim"))
        self._button(layout, "Refresh my invitations", "刷新我的邀请", self._refresh_invites)
        self.invites = QListWidget()
        self.invites.setMaximumHeight(120)
        layout.addWidget(self.invites)
        self.invites.currentRowChanged.connect(self._select_invite)
        row = QHBoxLayout()
        layout.addLayout(row)
        self._button(row, "Review and authorize comparison", "审阅并授权比较", self._authorize)
        self._button(row, "Decline", "婉拒", lambda: self._act("decline"))
        self._button(
            row, "Withdraw invitation / consent", "撤销邀请／同意", lambda: self._act("revoke")
        )
        self._button(
            layout,
            "Compare with selected ChatGPT model",
            "使用所选 ChatGPT 模型比较",
            self._compare,
        )
        self._button(layout, "Read current private result", "读取当前私密结果", self._read_result)
        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        layout.addWidget(self.report)

    def on_enter(self):
        vault = Path(self.profile_store.base_dir)
        if vault != self.vault:
            self._stop()
            self.vault = vault
            self.intro = self.holder.introductions.setdefault(
                str(vault), IntroductionService(vault)
            )
            self.report.clear()
            self.report_invitation = None
            self.candidates.clear()
            self.invites.clear()
            self.sources.clear()
            self.fields.setRowCount(0)
        if self.intro.draft:
            self._show_draft(self.intro.draft)
        if self.holder.pending_link:
            self.link.setText(self.holder.pending_link)
            self.tabs.setCurrentIndex(3)
            self.holder.pending_link = ""
        self.poll.start()

    def hideEvent(self, event):
        if self.vault:
            self.holder.edited[str(self.vault)] = self._edited_fields()
        self.poll.stop()
        self._stop()
        self.report.clear()
        self.report_invitation = None
        self.candidates.clear()
        self.candidate_detail.clear()
        super().hideEvent(event)

    def _stop(self):
        self.epoch += 1
        if self.cancel:
            self.cancel.set()
        if self.busy and self.cancel_callback:
            self.cancel_callback()
        self.cancel_callback = None
        self.busy = False
        for button in self.buttons:
            button.setEnabled(True)

    def _clear_remote_view(self):
        self._stop()
        for name in ("report", "candidates", "invites", "member_info", "candidate_detail"):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.clear()
        self.report_invitation = None

    def _error(self, error):
        self.status.setText(error_text(error))

    def _run(self, call, done, *, cancellable=False, on_cancel=None):
        if self.busy:
            return
        self.busy = True
        self.epoch += 1
        epoch = self.epoch
        vault = self.vault
        self.cancel = threading.Event()
        self.cancel_callback = on_cancel
        for button in self.buttons:
            button.setEnabled(False)
        self.status.setText(
            bi("Working… You can stop this request.", "正在处理……可以停止当前请求。")
        )

        def complete(result):
            if epoch != self.epoch or vault != self.vault:
                return
            self.busy = False
            self.cancel_callback = None
            for button in self.buttons:
                button.setEnabled(True)
            self.status.setText(bi("Completed. Review the result.", "已完成，请审阅结果。"))
            try:
                done(result)
            except Exception as exc:
                self._error(exc)

        def failed(error):
            if epoch != self.epoch or vault != self.vault:
                return
            self.busy = False
            self.cancel_callback = None
            for button in self.buttons:
                button.setEnabled(True)
            self._error(error)

        cancel = self.cancel
        run_async(self, (lambda: call(cancel)) if cancellable else call, complete, failed)

    def _client(self):
        origin = self.origin.text().strip()
        self.holder.origin = origin
        identity = PeerSessionStore(self.vault).load(origin)
        if not identity:
            raise ValueError("unauthorized")
        return PeerClient(origin, identity["token"])

    def _request(self, route, payload, done):
        try:
            client = self._client()
        except Exception as exc:
            self._error(exc)
            return
        self._run(lambda: client.call(route, payload), done)

    def _eligibility(self):
        return AdultDeclaration(age=self.age.value(), adult_confirmed=self.adult.isChecked())

    def _load_sources(self):
        try:
            sources = self.intro.list_sources(self._eligibility())
        except Exception as exc:
            self._error(exc)
            return
        self.sources.clear()
        for source in sources:
            text = source["text"] + (
                bi(" [reconfirm age of note]", "［旧记忆待重确认］") if source["outdated"] else ""
            )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, source)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.sources.addItem(item)
        if not sources:
            self.status.setText(
                bi(
                    (
                        "No eligible confirmed facts. Add a non-sensit"
                        "ive self-report in My approved notes first."
                    ),
                    "暂无可用确认事实。请先在“我批准的记忆”加入无敏感内容的自述。",
                )
            )

    def _generate_intro(self):
        backend = ai_backend.get_active()
        if backend is None:
            self._error("connection_failed")
            return
        try:
            selected = [
                self.sources.item(i).data(Qt.ItemDataRole.UserRole)["id"]
                for i in range(self.sources.count())
                if self.sources.item(i).checkState() == Qt.CheckState.Checked
            ]
            form = IntroductionFormat(
                fields=[x.strip() for x in self.format_fields.text().split(";") if x.strip()],
                audience=self.audience.text(),
                tone=self.tone.currentData(),
                language=current_language(),
                max_chars=self.length.value(),
            )
            request = self.intro.prepare(
                self._eligibility(), selected, selected if self.reconfirm.isChecked() else [], form
            )
            reviewed = review_ai(self, backend, request)
            if reviewed is None:
                return
        except Exception as exc:
            self._error(exc)
            return
        service = self.intro
        backend = copy.copy(backend)

        def work(cancel_event):
            cancel = getattr(backend, "set_cancel_event", None)
            if cancel:
                cancel(cancel_event)
            if cancel_event.is_set():
                raise ValueError("cancelled")
            return service.generate(backend, reviewed)

        def show(draft):
            self.holder.edited.pop(str(self.vault), None)
            self._show_draft(draft)

        self._run(work, show, cancellable=True, on_cancel=service.cancel_generation)

    def _shorten_intro(self):
        self.length.setValue(max(80, self.length.value() // 2))
        self._generate_intro()

    def _show_draft(self, draft):
        self.fields.setRowCount(len(draft.fields))
        edited = self.holder.edited.get(str(self.vault), {})
        for index, item in enumerate(draft.fields):
            title = QTableWidgetItem(item.label)
            title.setFlags(title.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.fields.setItem(index, 0, title)
            self.fields.setItem(index, 1, QTableWidgetItem(edited.get(item.label, item.text)))
        self.evidence.setPlainText(
            bi("Missing: ", "缺失：")
            + "; ".join(draft.missing)
            + "\n\n"
            + "\n".join(f"{e.source}: {e.quote}" for item in draft.fields for e in item.evidence)
        )
        self.fields.resizeRowsToContents()

    def _edited_fields(self):
        return {
            self.fields.item(i, 0).text(): self.fields.item(i, 1).text()
            for i in range(self.fields.rowCount())
            if self.fields.item(i, 1)
        }

    def _approve_intro(self):
        try:
            self._eligibility()
        except Exception as exc:
            self._error(exc)
            return
        edited = self._edited_fields()
        accepted, _ = review_text(
            self,
            bi("Approve introduction", "批准介绍"),
            bi(
                "Save this edited introduction locally, unencrypted. Nothing is published.\n\n",
                "将编辑后的介绍保存在本机，未加密，不会发布。\n\n",
            )
            + "\n\n".join(k + "\n" + v for k, v in edited.items()),
        )
        if not accepted:
            return
        try:
            self.intro.approve(edited, confirmed=True)
            self.holder.edited[str(self.vault)] = edited
            self.status.setText(
                bi(
                    "Approved locally. Copy, export or publish separately.",
                    "已在本机批准，复制、导出或发布须另行选择。",
                )
            )
        except Exception as exc:
            self._error(exc)

    def _approved_text(self):
        self._eligibility()
        doc = self.intro.read_approved()
        if self.fields.rowCount() and doc["fields"] != self._edited_fields():
            raise ValueError("approval_required")
        return "\n\n".join(k + "\n" + v for k, v in doc["fields"].items() if v.strip())

    def _copy_intro(self):
        try:
            QApplication.clipboard().setText(self._approved_text())
            self.status.setText(bi("Approved introduction copied.", "已复制批准的介绍。"))
        except Exception as exc:
            self._error(exc)

    def _export_intro(self):
        try:
            self._approved_text()
        except Exception as exc:
            self._error(exc)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, bi("Export approved fields", "导出批准字段"), "", "Text (*.txt);;JSON (*.json)"
        )
        if not path:
            return
        try:
            self.intro.export(path, as_json=Path(path).suffix.lower() == ".json")
        except Exception as exc:
            self._error(exc)

    def _start_node(self):
        if self.holder.node is None:
            self.holder.node = LocalPeerNode()
        self._run(self.holder.node.start, lambda origin: self.origin.setText(origin))

    def _register(self):
        try:
            eligible = self._eligibility()
            origin = self.origin.text().strip()
            if PeerSessionStore(self.vault).load(origin):
                raise ValueError("identity_exists")
            client = PeerClient(origin)
            payload = {"alias": self.alias.text(), **eligible.model_dump()}
        except Exception as exc:
            self._error(exc)
            return
        approved, _ = review_text(
            self,
            bi("Create node identity", "建立节点身份"),
            bi(
                "Send only this declaration and pseudonym to the configured node. "
                "No matching profile is created yet. Keep the protected device credential "
                "to return to this identity.\n",
                "仅向配置节点发送成年声明和化名，尚不建立匹配资料。保留受保护的本机凭据，才能返回此身份。\n",
            )
            + origin
            + "\n"
            + json.dumps(payload, ensure_ascii=False, indent=2),
        )
        if not approved:
            return
        vault = self.vault

        def work():
            identity = client.call("/peer/register", payload, authenticated=False)
            PeerSessionStore(vault).save(origin, identity)
            return identity

        self._run(
            work,
            lambda result: self.member_info.setText(
                bi("Device identity: ", "本机身份：") + result["member_id"]
            ),
        )

    def _connect(self):
        self._request("/peer/me", None, self._show_member)

    def _show_member(self, member):
        self.member_info.setText(
            member["alias"]
            + "\n"
            + bi("Account: ", "账号：")
            + member["id"]
            + "\n"
            + bi("Matching version: ", "匹配版本：")
            + str(member["version"])
            + "\n"
            + (
                bi(
                    "Recommendations updated. Refresh Discover to review.",
                    "推荐已更新，请刷新“发现”查看。",
                )
                if member["notice"]
                else bi("No unread recommendation notice.", "暂无未读推荐提示。")
            )
        )
        self.alias.setText(member["alias"])
        self.age.setValue(member["age"])

    def _edit_profile(self):
        def edit(member):
            dialog = MatchingProfileDialog(member, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            self._request(
                "/peer/profile",
                {
                    "expected_version": member["version"],
                    "profile": dialog.profile.model_dump(),
                    "approved": True,
                },
                lambda result: (
                    self.report.clear(),
                    self.candidates.clear(),
                    self.member_info.setText(
                        bi("Approved matching version: ", "已批准匹配版本：")
                        + str(result["version"])
                    ),
                ),
            )

        self._request("/peer/me", None, edit)

    def _publish(self):
        try:
            text = self._approved_text()
        except Exception as exc:
            self._error(exc)
            return

        def publish(member):
            approved, _ = review_text(
                self,
                bi("Public introduction link", "公开介绍链接"),
                bi(
                    "Everyone with the public URL can read this text. A public link never grants "
                    "private comparison access. This is distinct from an invitation.\n\n",
                    "持有公开链接的任何人均可阅读此文字。公开链接不授权私密比较，与邀请链接不同。\n\n",
                )
                + self.origin.text()
                + "\n\n"
                + text,
            )
            if not approved:
                return
            # Check selected private sources again after the publication review.
            try:
                self._approved_text()
            except Exception as exc:
                self._error(exc)
                return
            self._request(
                "/peer/public",
                {
                    "expected_version": member["public_version"],
                    "text": text,
                    "publish": True,
                    "approved": True,
                },
                lambda result: self.member_info.setText(
                    bi("Public introduction: ", "公开介绍：")
                    + self.origin.text().rstrip("/")
                    + "/p/"
                    + result["member_id"]
                ),
            )

        self._request("/peer/me", None, publish)

    def _unpublish(self):
        self._request(
            "/peer/me",
            None,
            lambda member: self._request(
                "/peer/public",
                {
                    "expected_version": member["public_version"],
                    "text": "",
                    "publish": False,
                    "approved": True,
                },
                lambda _: self.member_info.setText(
                    bi("Public introduction withdrawn.", "公开介绍已撤下。")
                ),
            ),
        )

    def _install_links(self):
        approved, _ = review_text(
            self,
            bi("App invitation links", "应用邀请链接"),
            bi(
                "Register this installed EXE for slowmatch: invitation links "
                "in your Windows account. "
                "Opening a link fills a review field; it never sends data or grants consent.",
                "为当前 Windows 账户注册此 EXE，处理 slowmatch: 邀请链接。"
                "打开链接仅填入待审阅字段，不发送资料或授予同意。",
            ),
        )
        if not approved:
            return
        try:
            if not getattr(sys, "frozen", False):
                raise ValueError("packaged_app_required")
            register_invitation_handler(sys.executable)
            self.status.setText(bi("App links enabled.", "已启用应用链接。"))
        except Exception as exc:
            self._error(exc)

    def _discover(self, authorized=False):
        def display(result):
            self.candidates.clear()
            self.candidate_detail.clear()
            for candidate in result["candidates"]:
                order = str(candidate["order"]) if candidate["order"] else bi("Unranked", "未排序")
                item = QListWidgetItem(order + " · " + candidate["alias"])
                item.setData(Qt.ItemDataRole.UserRole, candidate)
                self.candidates.addItem(item)
            self.status.setText(
                bi("Eligible participants: ", "合资格参与者：")
                + str(result["eligible_count"])
                + (bi(". Showing at most 20.", "，最多展示 20 位。") if result["limited"] else "")
                + (
                    bi(
                        (
                            " No eligible participants in your chosen scop"
                            "e. You may use an invitation."
                        ),
                        " 选定范围内暂无合资格参与者，可使用邀请。",
                    )
                    if not result["candidates"]
                    else ""
                )
            )

        self._request("/peer/discover", {"authorized_only": authorized}, display)

    @staticmethod
    def _profile_text(profile):
        lines = [
            profile["alias"],
            bi("Account: ", "账号：") + profile["member_id"],
            bi("Approved version: ", "批准版本：") + str(profile["version"]),
        ]
        if profile.get("city"):
            lines.append(bi("Shared city: ", "公开城市：") + profile["city"])
        lines.extend(
            label(key) + ": " + ", ".join(label(v) for v in values)
            for key, values in profile["attributes"].items()
        )
        return "\n".join(lines)

    def _candidate(self):
        item = self.candidates.currentItem()
        if not item:
            raise ValueError("select_participant")
        return item.data(Qt.ItemDataRole.UserRole)

    def _show_candidate(self, *_):
        self.candidate_detail.clear()
        if not self.candidates.currentItem():
            return
        candidate = self._candidate()
        text = self._profile_text(candidate)
        for key, en, zh in [
            ("alignment", "Stated overlap", "自述重合"),
            ("differences", "Differences, effect uncertain", "差异，影响不确定"),
            ("missing", "Insufficient disclosed information", "已披露信息不足"),
        ]:
            text += "\n" + bi(en, zh) + ": " + ", ".join(label(v) for v in candidate[key])
        text += "\n\n" + bi(
            "Priority order follows your chosen dimensions. Similarity does not prove "
            "relationship success. Hidden fields never drive this order.",
            "顺序遵循你选定的维度优先级。相似不证明关系成功，隐藏字段不参与排序。",
        )
        self.candidate_detail.setPlainText(text)

    def _invite_candidate(self):
        try:
            target = self._candidate()["member_id"]
        except Exception as exc:
            self._error(exc)
            return
        self._create_invite(target)

    def _block(self):
        try:
            target = self._candidate()["member_id"]
        except Exception as exc:
            self._error(exc)
            return
        self._control("block", target)

    def _control(self, action, target=None):
        descriptions = {
            "pause": bi(
                "Pause discovery and automatic updates. Existing comparison approvals are "
                "invalidated. Resume by reviewing your profile settings.",
                "暂停发现与自动更新，使已有比较授权失效。在匹配资料设置中重新批准即可恢复。",
            ),
            "withdraw": bi(
                "Withdraw matching permission and invalidate comparison approvals and "
                "results. Your public introduction is managed separately.",
                "撤销匹配许可，使比较授权与结果失效。公开介绍需单独撤下。",
            ),
            "block": bi(
                "Exclude this participant and invalidate your comparison approvals.",
                "排除此参与者，并使你的比较授权失效。",
            ),
            "delete": bi(
                "Delete this node identity, matching profile, public introduction, invitations "
                "and results. Your private local notes stay in your chosen folder.",
                "删除此节点身份、匹配资料、公开介绍、邀请与结果。本机私人记忆保留在选定文件夹中。",
            ),
        }
        accepted, _ = review_text(self, bi("Review change", "审阅变更"), descriptions[action])
        if not accepted:
            return
        vault = self.vault
        origin = self.origin.text().strip()

        def complete(_):
            self.report.clear()
            self.report_invitation = None
            self.candidates.clear()
            self.invites.clear()
            if action == "delete":
                PeerSessionStore(vault).clear(origin)
                self.member_info.clear()

        self._request(
            "/peer/control", {"action": action, "target": target, "confirmed": True}, complete
        )

    def _create_invite(self, target=None):
        payload = {
            "request_id": uuid4().hex,
            "hours": self.hours.value(),
            "intended_member": target,
        }

        def display(result):
            self.link.setText(invitation_link(self.origin.text().strip(), result["invitation"]))
            self.tabs.setCurrentIndex(3)
            self.status.setText(
                bi(
                    "Invitation created. Share the link yourself. Nothing was sent.",
                    "邀请已创建，请自行分享链接，应用未发送消息。",
                )
            )

        self._request("/peer/invite", payload, display)

    def _invitation(self):
        return parse_invitation(self.link.text().strip(), self.origin.text().strip())

    def _copy_link(self):
        try:
            identity = self._invitation()
            QApplication.clipboard().setText(invitation_link(self.origin.text().strip(), identity))
        except Exception as exc:
            self._error(exc)

    def _act(self, action):
        try:
            identity = self._invitation()
        except Exception as exc:
            self._error(exc)
            return
        accepted, _ = review_text(
            self,
            bi("Invitation action", "邀请操作"),
            {
                "claim": bi(
                    "Claim this invitation using your node identity and shared profile. "
                    "This does not approve AI analysis. Both participants review versions next.",
                    "使用节点身份与可分享资料认领邀请。这不批准 AI 分析，随后双方须审阅版本。",
                ),
                "decline": bi(
                    "Decline this invitation and exclude this pairing from future recommendations. "
                    "No personality inference is made.",
                    "婉拒此邀请，并从以后推荐中排除此组合，不产生人格推断。",
                ),
                "revoke": bi(
                    "Revoke this invitation and its comparison consent and results.",
                    "撤销此邀请及其比较同意与结果。",
                ),
            }[action],
        )
        if not accepted:
            return
        self._request(
            "/peer/invitation-action",
            {"invitation": identity, "action": action},
            lambda result: self._action_done(result),
        )

    def _action_done(self, result):
        self.report.clear()
        self.report_invitation = None
        self.status.setText(label(result["status"]))
        self._refresh_invites()

    def _refresh_invites(self):
        def display(result):
            self.invites.clear()
            for invite in result["invitations"]:
                title = (
                    label(invite["status"])
                    + " · "
                    + (invite["counterpart_alias"] or bi("Waiting for a participant", "等待参与者"))
                )
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, invite)
                self.invites.addItem(item)

        self._request("/peer/invitations", None, display)

    def _select_invite(self, *_):
        item = self.invites.currentItem()
        if item:
            self.link.setText(
                invitation_link(
                    self.origin.text().strip(), item.data(Qt.ItemDataRole.UserRole)["invitation"]
                )
            )
            self.report.clear()
            self.report_invitation = None

    def _authorize(self):
        try:
            identity = self._invitation()
        except Exception as exc:
            self._error(exc)
            return

        def approve(preview):
            text = bi(
                "Confirm the intended participant by account identifier through a channel you "
                "already trust. Pseudonyms are not verified identities. "
                "Only the displayed disclosed "
                "attributes can enter AI comparison; hidden hard requirements stay on the node. "
                "The result and your ordering are private to you. Both participants must approve "
                "these exact versions.\n\n",
                "请通过已有可信渠道核对对方的账号标识。化名不是已验证身份。只有展示的已披露属性"
                "可进入 AI 比较，隐藏硬条件留在节点。"
                "结果及你的排序仅自己可见，双方须批准这些精确版本。\n\n",
            )
            text += "\n\n".join(self._profile_text(p) for p in preview["participants"])
            accepted, cloud = review_text(
                self, bi("Approve versions and disclosure", "批准版本与披露"), text, cloud=True
            )
            if not accepted:
                return
            self._request(
                "/peer/invitation-action",
                {
                    "invitation": identity,
                    "action": "approve",
                    "allow_cloud_ai": cloud,
                    "expected_versions": preview["versions"],
                },
                self._action_done,
            )

        self._request("/peer/preview", {"invitation": identity}, approve)

    def _compare(self):
        backend = ai_backend.get_active()
        if backend is None:
            self._error("connection_failed")
            return
        try:
            identity = self._invitation()
            client = self._client()
        except Exception as exc:
            self._error(exc)
            return

        def prepared(data):
            reviewed = review_ai(self, backend, comparison_request(data))
            if reviewed is None:
                return
            isolated = copy.copy(backend)

            def work(cancel):
                setter = getattr(isolated, "set_cancel_event", None)
                if setter:
                    setter(cancel)
                if cancel.is_set():
                    raise ValueError("cancelled")
                # Recheck exact permissions after the user finishes reading the preview.
                latest = client.call("/peer/prepare", {"invitation": identity})
                if latest != data:
                    raise ValueError("stale")
                report = generate_comparison(isolated, data, reviewed)
                if cancel.is_set():
                    raise ValueError("cancelled")
                client.call(
                    "/peer/finish",
                    {
                        "invitation": identity,
                        "ticket": data["ticket"],
                        "report": report.model_dump(),
                    },
                )
                return client.call("/peer/result", {"invitation": identity})

            self._run(work, lambda result: self._show_result(identity, result), cancellable=True)

        self._run(lambda: client.call("/peer/prepare", {"invitation": identity}), prepared)

    def _show_result(self, identity, result):
        report = PeerReport.model_validate(result["report"])
        self.report.setPlainText(render_peer_report(report, current_language()))
        self.report_invitation = identity

    def _read_result(self):
        try:
            identity = self._invitation()
        except Exception as exc:
            self._error(exc)
            return
        self.report.clear()
        self.report_invitation = None
        self._request(
            "/peer/result",
            {"invitation": identity},
            lambda result: self._show_result(identity, result),
        )

    def _check_report(self):
        if self.busy or not self.report_invitation:
            return
        identity = self.report_invitation
        # Remove stale material before any attempted refresh; network failure stays closed.
        self.report.clear()
        self.report_invitation = None
        self._request(
            "/peer/result",
            {"invitation": identity},
            lambda result: self._show_result(identity, result),
        )
