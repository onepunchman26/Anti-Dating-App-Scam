"""One explicit ChatGPT plan connection, without API-key or prompt setup."""

import threading
import webbrowser

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox, QLabel, QProgressBar, QVBoxLayout, QWidget

from anti_dating_scam.ai.chatgpt_auth import MANAGE_USAGE_URL, ChatGPTConnectionService
from anti_dating_scam.ai.chatgpt_preferences import ModelPreferences
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.connection_success_badge import ConnectionSuccessBadge
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader
from anti_dating_scam_desktop.widgets.wrapped_checkbox import WrappedCheckBox
from anti_dating_scam_desktop.workers import run_async

USAGE_URL = MANAGE_USAGE_URL


class ChatGPTConnectScreen(QWidget):
    def __init__(self, state, profile_store, on_done, on_back, *, connection=None):
        super().__init__()
        self.connection = connection or ChatGPTConnectionService()
        self.preferences = ModelPreferences()
        self.state = state
        self.on_done = on_done
        self._cancel = threading.Event()
        self._epoch = 0
        self._busy = False
        self._sharing = False
        self._models = ()
        self._recommended = None
        self._phase_timer = QTimer(self)
        self._phase_timer.setInterval(250)
        self._phase_timer.timeout.connect(self._show_phase)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(14)
        layout.addWidget(
            StepHeader(
                bi("Connect ChatGPT", "连接 ChatGPT"),
                bi(
                    "Use an eligible Plus or Pro plan. Sign in and authorize in your browser.",
                    "使用符合条件的 Plus 或 Pro 套餐，在浏览器中登录并授权。",
                ),
            )
        )
        note = QLabel(
            bi(
                "ChatGPT runs online. Only the conversation you approve in this app is sent. "
                "This connection cannot read your existing ChatGPT chats.",
                "ChatGPT 在线运行。仅发送你在本应用中同意发送的对话；"
                "此连接无法读取你已有的 ChatGPT 聊天记录。",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.banner = StatusBanner(bi("Not connected", "尚未连接"))
        layout.addWidget(self.banner)
        self.success = ConnectionSuccessBadge(self)
        layout.addWidget(self.success)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.connect_button = PrimaryButton(bi("Continue with ChatGPT", "继续使用 ChatGPT"))
        self.connect_button.clicked.connect(self._connect)
        layout.addWidget(self.connect_button)
        model_label = QLabel(bi("Chat model", "聊天模型"))
        layout.addWidget(model_label)
        self.model_picker = QComboBox()
        self.model_picker.setObjectName("chatgptModelPicker")
        self.model_picker.setAccessibleName(bi("Chat model", "聊天模型"))
        model_label.setBuddy(self.model_picker)
        self.model_picker.addItem(bi("Sign in to load your models", "登录后显示你的可用模型"), None)
        self.model_picker.setEnabled(False)
        self.model_picker.currentIndexChanged.connect(self._controls)
        layout.addWidget(self.model_picker)
        self.model_hint = QLabel(
            bi(
                "Available models come from your account. The default favors a lighter chat model.",
                "可用模型来自你的账号，默认优先轻量聊天模型。",
            )
        )
        self.model_hint.setWordWrap(True)
        layout.addWidget(self.model_hint)
        usage = SecondaryButton(bi("Open ChatGPT usage settings", "打开 ChatGPT 用量设置"))
        usage.clicked.connect(lambda: webbrowser.open(USAGE_URL))
        layout.addWidget(usage)
        self.plan_consent = WrappedCheckBox(
            bi(
                "I have disabled extra-credit use for this app in ChatGPT settings. "
                "Use only my existing plan allowance.",
                "我已在 ChatGPT 设置中关闭本应用的额外积分使用，仅使用现有套餐额度。",
            )
        )
        self.plan_consent.toggled.connect(self._controls)
        layout.addWidget(self.plan_consent)
        limit_note = QLabel(
            bi(
                "ChatGPT controls plan eligibility, limits and credits. The app cannot verify "
                "the credit switch. If you reach a limit, chatting stops for you to review it.",
                "套餐资格、额度和积分由 ChatGPT 管理，本应用无法核验积分开关。"
                "达到额度限制时会停止聊天，留给你检查。",
            )
        )
        limit_note.setWordWrap(True)
        layout.addWidget(limit_note)
        self.use_button = PrimaryButton(bi("Use ChatGPT for AI Chat", "用 ChatGPT 开始 AI 聊天"))
        self.use_button.clicked.connect(self._use)
        self.use_button.setEnabled(False)
        layout.addWidget(self.use_button)
        self.disconnect_button = SecondaryButton(bi("Disconnect this account", "断开此账号"))
        self.disconnect_button.clicked.connect(self._disconnect)
        layout.addWidget(self.disconnect_button)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(lambda: (self._cancel.set(), self._phase_timer.stop(), on_back()))
        layout.addWidget(back)
        layout.addStretch()

    def on_enter(self):
        # Merely constructing the window never reads other apps' account data.
        self._cancel.set()
        self._cancel = threading.Event()
        self._epoch += 1
        self._busy = False
        self._phase_timer.stop()
        try:
            status = self.connection.status()
            self._sharing = status.connected and status.sharing
            self._models = ()
            self.model_picker.clear()
            if status.connected:
                self.success.confirm()
                if self._sharing:
                    self._load_models()
                else:
                    self.banner.set_text(
                        bi(
                            "Account connected. ChatGPT plan permission is missing; sign in to "
                            "authorize plan use.",
                            "账号已连接，但尚未获得套餐使用权限；请重新登录并授权套餐使用。",
                        )
                    )
            else:
                self.success.hide()
                self.banner.set_text(bi("Not connected", "尚未连接"))
        except Exception:
            self._sharing = False
            self._models = ()
            self.success.hide()
            self.banner.set_text(bi("Sign in again to connect.", "请重新登录以连接。"))
        self._controls()

    def _controls(self):
        self.connect_button.setEnabled(not self._busy)
        self.disconnect_button.setEnabled(not self._busy)
        self.use_button.setEnabled(
            self._sharing
            and self.plan_consent.isChecked()
            and bool(self._models)
            and not self._busy
        )
        self.model_picker.setEnabled(bool(self._models) and not self._busy)
        self.progress.setVisible(self._busy)

    def _show_phase(self):
        diagnostic = getattr(self.connection, "diagnostic", None)
        if not self._busy or not callable(diagnostic):
            return
        phase = diagnostic().phase
        labels = {
            "waiting_callback": (
                "Waiting for your browser authorization…",
                "正在等待你完成浏览器授权……",
            ),
            "token_exchange": ("Checking the returned authorization…", "正在核验返回的授权……"),
            "identity_verification": ("Verifying the account identity…", "正在验证账号身份……"),
            "credential_save": ("Saving the protected connection…", "正在保存受保护的连接……"),
        }
        if phase in labels:
            self.banner.set_text(bi(*labels[phase]))

    def _failure(self, fallback_en, fallback_zh):
        diagnostic = getattr(self.connection, "diagnostic", None)
        code = diagnostic().code if callable(diagnostic) else ""
        labels = {
            "invalid_grant": (
                "This authorization expired. Sign in again; no model request was made.",
                "本次授权已过期，请重新登录；尚未调用模型。",
            ),
            "invalid_client": (
                "The account registration was not accepted. Sign in again to reconnect.",
                "账号注册未被接受，请重新登录以连接。",
            ),
            "network_unavailable": (
                "Could not reach ChatGPT. Check your connection and try again.",
                "无法连接 ChatGPT，请检查网络后重试。",
            ),
            "subscription_sharing_user_not_eligible": (
                "ChatGPT plan use is unavailable for this account or workspace.",
                "此账号或工作区暂不可使用 ChatGPT 套餐授权。",
            ),
            "subscription_sharing_usage_unavailable": (
                "ChatGPT could not check the plan allowance. Try again later.",
                "ChatGPT 暂时无法核查套餐额度，请稍后重试。",
            ),
        }
        self.banner.set_text(bi(*labels.get(code, (fallback_en, fallback_zh))))

    def _load_models(self):
        if self._busy or not self._sharing:
            return
        self._busy = True
        epoch, cancel = self._epoch, self._cancel
        self._controls()
        self.banner.set_text(
            bi("Account connected. Loading your models…", "账号已连接，正在读取可用模型……")
        )

        def done(models):
            from anti_dating_scam.ai.chatgpt_models import recommend_chatgpt_model

            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            self._models = tuple(models)
            self._recommended = recommend_chatgpt_model(self._models)
            self.model_picker.blockSignals(True)
            self.model_picker.clear()
            if self._recommended:
                choice = next(item for item in self._models if item.slug == self._recommended.slug)
                self.model_picker.addItem(
                    bi("Default (recommended)", "默认（推荐）") + " · " + choice.display_name,
                    choice.slug,
                )
                self.model_hint.setText(
                    bi(
                        self._recommended.reason_en,
                        self._recommended.reason_zh,
                    )
                )
            for choice in self._models:
                self.model_picker.addItem(choice.display_name, choice.slug)
            active = ai_backend.get_active()
            if getattr(active, "provider_id", "") == "chatgpt_plan":
                selected = self.model_picker.findData(getattr(active, "model", None))
                if selected >= 0:
                    self.model_picker.setCurrentIndex(selected)
            remembered = self.preferences.load(self.connection.status().client_id)
            if remembered:
                self.model_picker.setCurrentIndex(self.model_picker.findData(remembered))
                if self.model_picker.currentIndex() < 0:
                    self.model_hint.setText(
                        bi(
                            "Your saved model is unavailable. Choose a model explicitly.",
                            "之前的模型目前不可用，请重新选择。",
                        )
                    )
            self.model_picker.blockSignals(False)
            self.banner.set_text(
                bi(
                    "Models ready. Choose one, confirm extra credits are off, then enter AI Chat.",
                    "模型已准备好。选好模型，确认额外积分已关闭后，即可进入 AI 聊天。",
                )
                if self._models
                else bi(
                    "Account connected, but ChatGPT returned no available model.",
                    "账号已连接，但 ChatGPT 没有返回可用模型。",
                )
            )
            self._controls()

        def error(_message):
            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            self._models = ()
            self._failure(
                "Account connected, but the model list could not load. Try again later.",
                "账号已连接，但模型列表未加载成功，请稍后重试。",
            )
            self._controls()

        run_async(self, self.connection.list_models, done, error)

    def _connect(self):
        if self._busy:
            return
        self._cancel = threading.Event()
        self._epoch += 1
        epoch, cancel = self._epoch, self._cancel
        self._busy = True
        self._phase_timer.start()
        self._controls()
        self.banner.set_text(
            bi(
                "Complete sign-in in your browser. Return here after authorizing.",
                "请在浏览器中完成登录和授权，然后返回这里。",
            )
        )

        def done(status):
            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            self._phase_timer.stop()
            if self._cancel.is_set():
                self._controls()
                return
            self._sharing = status.connected and status.sharing
            self.banner.set_text(
                bi(
                    "Signed in. Review usage settings, then enable AI Chat.",
                    "已登录。检查用量设置后，再启用 AI 聊天。",
                )
                if self._sharing
                else bi(
                    "Plan permission was not granted. Authorize it in ChatGPT to continue.",
                    "未获套餐使用授权，请在 ChatGPT 中授权后继续。",
                )
            )
            self._controls()
            if status.connected:
                self.success.confirm()
            if self._sharing:
                self._load_models()

        def error(_message):
            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            self._phase_timer.stop()
            self._failure(
                "Sign-in was canceled or could not complete. You can try again.",
                "登录已取消或未完成，可以重新尝试。",
            )
            self._controls()

        run_async(self, lambda: self.connection.connect(cancel_event=cancel), done, error)

    def _use(self):
        if self._busy or not self._sharing or not self.plan_consent.isChecked() or not self._models:
            return
        self._busy = True
        epoch, cancel = self._epoch, self._cancel
        self._controls()
        self.banner.set_text(bi("Enabling the selected model…", "正在启用所选模型……"))
        slug = self.model_picker.currentData()
        if slug not in {choice.slug for choice in self._models}:
            self._busy = False
            self._controls()
            return

        def prepare():
            backend = self.connection.create_backend(slug, included_plan_confirmed=True)
            if self.connection.status().client_id:
                self.preferences.save(self.connection.status().client_id, slug)
            return backend

        def done(backend):
            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            if self._cancel.is_set():
                self._controls()
                return
            ai_backend.set_active(backend)
            if self.state is not None:
                self.state.provider_name = "ChatGPT plan"
                self.state.model_name = slug
            self.success.confirm(chat_ready=True)
            self._controls()
            self.on_done()

        def error(_message):
            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            self.banner.set_text(
                bi(
                    "This account has no available plan model, or needs sign-in again. "
                    "Check ChatGPT usage settings.",
                    "此账号暂无可用套餐模型，或需要重新登录。请检查 ChatGPT 用量设置。",
                )
            )
            self._controls()

        self._cancel.clear()
        run_async(self, prepare, done, error)

    def _disconnect(self):
        if self._busy:
            return
        self._busy = True
        epoch = self._epoch
        self._controls()

        active = ai_backend.get_active()
        if getattr(active, "provider_id", None) == "chatgpt_plan":
            ai_backend.set_active(None)

        def done(revoked):
            if epoch != self._epoch:
                return
            self._busy = False
            self._sharing = False
            self._models = ()
            self.success.hide()
            self.model_picker.clear()
            self.plan_consent.setChecked(False)
            active = ai_backend.get_active()
            if getattr(active, "provider_id", None) == "chatgpt_plan":
                ai_backend.set_active(None)
            self.banner.set_text(
                bi("Disconnected.", "已断开。")
                if revoked
                else bi(
                    "Disconnected locally. Remove this app's access in ChatGPT settings too.",
                    "已在本机断开，请同时在 ChatGPT 设置中移除此应用的访问权限。",
                )
            )
            self._controls()

        def error(_message):
            if epoch != self._epoch:
                return
            self._busy = False
            self.banner.set_text(
                bi(
                    "Could not disconnect. Check ChatGPT settings.",
                    "未能断开，请检查 ChatGPT 设置。",
                )
            )
            self._controls()

        run_async(self, self.connection.disconnect, done, error)
