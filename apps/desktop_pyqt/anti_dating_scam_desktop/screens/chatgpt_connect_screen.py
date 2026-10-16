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


def default_connection(preferences):
    """Remember the route, never credentials or billing consent in preferences."""
    from anti_dating_scam.ai.codex_connection import CodexConnectionService, find_codex
    from anti_dating_scam.ai.privacy import BackendError

    route = preferences.load_route()
    if route == "codex":
        return CodexConnectionService()
    if route is None:
        try:
            find_codex()
        except BackendError:
            pass
        else:
            return CodexConnectionService()
    return ChatGPTConnectionService()


class ChatGPTConnectScreen(QWidget):
    def __init__(self, state, profile_store, on_done, on_back, *, connection=None):
        super().__init__()
        self.preferences = ModelPreferences()
        active_connection = getattr(ai_backend.get_active(), "connection", None)
        self.connection = connection or active_connection or default_connection(self.preferences)
        self._direct_connection = (
            self.connection if not getattr(self.connection, "compatibility", False) else None
        )
        self._compat_connection = (
            self.connection if getattr(self.connection, "compatibility", False) else None
        )
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
        layout.setContentsMargins(36, 24, 36, 24)
        layout.setSpacing(10)
        layout.addWidget(
            StepHeader(
                bi("Connect ChatGPT", "连接 ChatGPT"),
                bi(
                    "Sign in, choose a model, then enter your conversation.",
                    "登录、选择模型，然后进入聊天。",
                ),
            )
        )
        self.connection_note = note = QLabel(
            bi(
                "ChatGPT runs online. Only the conversation you approve in this app is sent. "
                "This connection cannot read your existing ChatGPT chats.",
                "ChatGPT 在线运行。仅发送你在本应用中同意发送的对话；"
                "此连接无法读取你已有的 ChatGPT 聊天记录。",
            )
        )
        note.setWordWrap(True)
        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(note)
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
        self.compat_button = SecondaryButton(
            bi("Try local Codex connection", "尝试本机 Codex 兼容连接")
        )
        self.compat_button.setObjectName("chatgptCompatibilityConnection")
        self.compat_button.clicked.connect(self._switch_connection)
        details_layout.addWidget(self.compat_button)
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
        self.reload_button = SecondaryButton(bi("Reload models", "重新加载模型"))
        self.reload_button.setObjectName("chatgptReloadModels")
        self.reload_button.clicked.connect(self._load_models)
        details_layout.addWidget(self.reload_button)
        self.model_hint = QLabel(
            bi(
                "Available models come from your account. The default favors a lighter chat model.",
                "可用模型来自你的账号，默认优先轻量聊天模型。",
            )
        )
        self.model_hint.setWordWrap(True)
        details_layout.addWidget(self.model_hint)
        usage = SecondaryButton(bi("Open ChatGPT usage settings", "打开 ChatGPT 用量设置"))
        usage.clicked.connect(lambda: webbrowser.open(USAGE_URL))
        details_layout.addWidget(usage)
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
        details_layout.addWidget(limit_note)
        self.next_step = QLabel()
        self.next_step.setWordWrap(True)
        self.next_step.setObjectName("chatgptNextStep")
        layout.addWidget(self.next_step)
        self.use_button = PrimaryButton(bi("Enter AI Chat", "进入 AI 聊天"))
        self.use_button.clicked.connect(self._use)
        self.use_button.setEnabled(False)
        layout.addWidget(self.use_button)
        self.disconnect_button = SecondaryButton(bi("Disconnect this account", "断开此账号"))
        self.disconnect_button.clicked.connect(self._disconnect)
        details_layout.addWidget(self.disconnect_button)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(lambda: (self._cancel.set(), self._phase_timer.stop(), on_back()))
        layout.addWidget(back)
        self.details_button = SecondaryButton(bi("Connection options & help", "连接选项与帮助"))
        self.details_button.setCheckable(True)
        self.details_button.toggled.connect(details.setVisible)
        layout.addWidget(self.details_button)
        layout.addWidget(details)
        details.hide()
        layout.addStretch()
        self._route_labels()

    def on_enter(self):
        # Merely constructing the window never reads other apps' account data.
        self._cancel.set()
        self._cancel = threading.Event()
        self._epoch += 1
        self._busy = False
        self._phase_timer.stop()
        active = ai_backend.get_active()
        if getattr(active, "connection", None) is self.connection:
            # Preserve the already-activated route and consent within this process,
            # including language rebuilds; never carry it to another account/route.
            self.plan_consent.setChecked(True)
        try:
            status = self.connection.status()
            self._sharing = status.connected and status.sharing
            self._models = ()
            self.model_picker.clear()
            self.model_picker.setPlaceholderText(
                bi("Sign in to load your models", "登录后显示可用模型")
            )
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
        self.connect_button.setVisible(not self._sharing)
        self.compat_button.setEnabled(not self._busy)
        self.disconnect_button.setEnabled(not self._busy)
        self.reload_button.setEnabled(self._sharing and not self._busy)
        self.use_button.setEnabled(
            self._sharing
            and self.plan_consent.isChecked()
            and self.model_picker.currentData() in {choice.slug for choice in self._models}
            and not self._busy
        )
        self.model_picker.setEnabled(bool(self._models) and not self._busy)
        self.progress.setVisible(self._busy)
        if self._busy:
            self.next_step.setText(bi("Please wait…", "请稍候……"))
        elif not self._sharing:
            self.next_step.setText(bi(
                "First, connect your account above.", "请先点击上方按钮连接账号。",
            ))
        elif not self._models:
            self.next_step.setText(bi(
                "Models could not load. Open Connection options & help "
                "to retry or change connection.",
                "模型未加载，请打开“连接选项与帮助”重试或切换连接。",
            ))
        elif self.model_picker.currentData() not in {choice.slug for choice in self._models}:
            self.next_step.setText(bi("Choose a model above.", "请在上方选择模型。"))
        elif not self.plan_consent.isChecked():
            self.next_step.setText(bi(
                "Next: tick the allowance confirmation above, then Enter AI Chat.",
                "下一步：勾选上方套餐确认，再点击“进入 AI 聊天”。",
            ))
        else:
            self.next_step.setText(bi(
                "Setup complete. Enter AI Chat, then press Start.",
                "设置完成。点击“进入 AI 聊天”，然后点击“开始”。",
            ))

    def _switch_connection(self):
        if self._busy:
            return
        from anti_dating_scam.ai.codex_connection import CodexConnectionService

        compatibility = not getattr(self.connection, "compatibility", False)
        if compatibility:
            if self._compat_connection is None:
                self._compat_connection = CodexConnectionService()
            self.connection = self._compat_connection
        else:
            if self._direct_connection is None:
                self._direct_connection = ChatGPTConnectionService()
            self.connection = self._direct_connection
        # Billing confirmation and an active provider never silently cross routes.
        ai_backend.set_active(None)
        self.plan_consent.setChecked(False)
        self._route_labels()
        self.on_enter()

    def _route_labels(self):
        compatibility = getattr(self.connection, "compatibility", False)
        self.compat_button.setText(
            bi("Use standard ChatGPT connection", "使用标准 ChatGPT 连接")
            if compatibility
            else bi("Try local Codex connection", "尝试本机 Codex 兼容连接")
        )
        self.connect_button.setText(
            bi("Connect through local Codex", "通过本机 Codex 连接")
            if compatibility
            else bi("Continue with ChatGPT", "继续使用 ChatGPT")
        )
        self.connection_note.setText(
            bi(
                "Uses your Codex plan allowance through the installed official Codex runtime. "
                "Sign in separately; existing Codex chats and files are not read. "
                "Model names are candidates; actual access is verified when chatting.",
                "通过已安装的官方 Codex 程序使用 Codex 套餐额度。需要单独登录，"
                "不会读取已有 Codex 聊天或文件。列表是候选模型，实际访问以聊天结果验证。",
            )
            if compatibility
            else bi(
                "ChatGPT runs online. Only the conversation you approve in this app is sent. "
                "This connection cannot read your existing ChatGPT chats.",
                "ChatGPT 在线运行。仅发送你在本应用中同意发送的对话；"
                "此连接无法读取你已有的 ChatGPT 聊天记录。",
            )
        )
        self.plan_consent.setText(
            bi(
                "I have disabled Codex extra credits and automatic top-ups. "
                "Use only my included Codex plan allowance.",
                "我已关闭 Codex 额外积分和自动充值，仅使用已有 Codex 套餐额度。",
            )
            if compatibility
            else bi(
                "I have disabled extra-credit use for this app in ChatGPT settings. "
                "Use only my existing plan allowance.",
                "我已在 ChatGPT 设置中关闭本应用的额外积分使用，仅使用现有套餐额度。",
            )
        )

    def _show_phase(self):
        diagnostic = getattr(self.connection, "diagnostic", None)
        if not self._busy or not callable(diagnostic):
            return
        phase = diagnostic().phase
        labels = {
            "runtime_missing": (
                "The compatible local Codex program was not found. "
                "Install or repair Codex, then reconnect.",
                "未找到兼容的本机 Codex 程序，请安装或修复 Codex 后重新连接。",
            ),
            "runtime_version": (
                "The installed Codex version has changed. AI-SlowMatch needs a compatibility "
                "update before this connection can run.",
                "已安装的 Codex 版本发生变化，需要更新 AI-SlowMatch 的兼容支持后再连接。",
            ),
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
        detail = diagnostic() if callable(diagnostic) else None
        code = getattr(detail, "code", "")
        http_status = getattr(detail, "http_status", None)
        labels = {
            "runtime_missing": (
                "Install or repair the official Codex app, "
                "or choose the standard connection in options.",
                "请安装或修复官方 Codex 应用，或在连接选项中切换标准连接。",
            ),
            "runtime_version": (
                "Codex has updated. This AI-SlowMatch version needs a compatibility update.",
                "Codex 已更新，当前 AI-SlowMatch 需要更新兼容支持。",
            ),
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
            "catalog_invalid": (
                "ChatGPT returned an unreadable model list. "
                "Reload models; no chat request was sent.",
                "ChatGPT 返回的模型列表格式无法识别。请重新加载模型；尚未发送聊天请求。",
            ),
        }
        if code in labels:
            message = bi(*labels[code])
        elif getattr(detail, "failed_phase", "") in {"checking_model_access", "loading_models"}:
            if isinstance(http_status, int) and 500 <= http_status <= 599:
                message = bi(
                    "ChatGPT could not load your models. Your saved authorization is preserved. "
                    "Click Reload models to retry; chatting is not ready yet.",
                    "ChatGPT 暂时无法加载可用模型，已保留你的授权。请点击“重新加载模型”重试；"
                    "目前尚不能开始聊天。",
                )
            elif http_status in {401, 403}:
                message = bi(
                    "ChatGPT did not allow model access. "
                    "Reconnect and review this app's plan access.",
                    "ChatGPT 未允许读取模型。请重新连接，并检查本应用的套餐授权。",
                )
            elif http_status == 429:
                message = bi(
                    "ChatGPT limited this request. Check usage settings and reload models later.",
                    "ChatGPT 限制了本次请求。请检查用量设置，稍后重新加载模型。",
                )
            elif not self._sharing:
                message = bi("Sign in again to load models.", "请重新登录以加载模型。")
            else:
                message = bi(fallback_en, fallback_zh)
        else:
            message = bi(fallback_en, fallback_zh)
        if isinstance(http_status, int) and 100 <= http_status <= 599:
            message += f" (HTTP {http_status})"
        self.banner.set_text(message)
        self.details_button.setChecked(True)

    def _load_models(self):
        if self._busy or not self._sharing:
            return
        self._busy = True
        self._models = ()
        self._recommended = None
        self.model_picker.clear()
        self.model_picker.setPlaceholderText(bi("Loading models…", "正在加载模型……"))
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
            if self._models:
                self.model_picker.setPlaceholderText(bi("Choose a model", "请选择模型"))
                self.model_picker.setCurrentIndex(0)
            active = ai_backend.get_active()
            if getattr(active, "connection", None) is self.connection:
                selected = self.model_picker.findData(getattr(active, "model", None))
                if selected >= 0:
                    self.model_picker.setCurrentIndex(selected)
            remembered = self.preferences.load(
                getattr(
                    self.connection,
                    "preference_key",
                    self.connection.status().client_id,
                )
            )
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
            if not self._models:
                self.model_picker.setPlaceholderText(bi("No available models", "暂无可用模型"))
                self.details_button.setChecked(True)
            self.banner.set_text(
                bi(
                    "Models ready. Choose one, confirm extra credits are off, then enter AI Chat.",
                    "模型已准备好。选好模型，确认额外积分已关闭后，即可进入 AI 聊天。",
                )
                if self._models
                else bi(
                    "Account connected, but ChatGPT returned no available model. "
                    "Check plan access in usage settings, then reload models.",
                    "账号已连接，但 ChatGPT 没有返回可用模型。请在用量设置中检查套餐授权，"
                    "然后重新加载模型。",
                )
            )
            if getattr(self.connection, "compatibility", False) and self._models:
                self.banner.set_text(
                    bi(
                        "Signed in through local Codex. Choose a candidate model and confirm "
                        "Codex extra credits are off before chatting.",
                        "已通过本机 Codex 登录。请选择候选模型，"
                        "并确认 Codex 额外积分已关闭后开始聊天。",
                    )
                )
            self._controls()

        def error(_message):
            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            self._models = ()
            self.model_picker.clear()
            self.model_picker.setPlaceholderText(
                bi("Models unavailable — reload to retry", "模型未就绪，请重新加载")
            )
            try:
                status = self.connection.status()
                self._sharing = status.connected and status.sharing
            except Exception:
                self._sharing = False
            if not self._sharing:
                self.success.hide()
            self._failure(
                "The model list could not load. Click Reload models to try again.",
                "模型列表未加载成功，请点击“重新加载模型”重试。",
            )
            self._controls()

        run_async(self, self.connection.list_models, done, error)

    def _connect(self):
        if self._busy:
            return
        if self._sharing:
            self._load_models()
            return
        self._cancel = threading.Event()
        self._epoch += 1
        epoch, cancel = self._epoch, self._cancel
        self._busy = True
        self._models = ()
        self.model_picker.clear()
        self.model_picker.setPlaceholderText(bi("Waiting for sign-in…", "正在等待登录……"))
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
            self.banner.set_text(bi("Choose an available model first.", "请先选择一个可用模型。"))
            self._controls()
            return

        def prepare():
            backend = self.connection.create_backend(slug, included_plan_confirmed=True)
            if self.connection.status().client_id:
                self.preferences.save(
                    getattr(
                        self.connection,
                        "preference_key",
                        self.connection.status().client_id,
                    ),
                    slug,
                )
            return backend

        def done(backend):
            if epoch != self._epoch or cancel.is_set():
                return
            self._busy = False
            if self._cancel.is_set():
                self._controls()
                return
            ai_backend.set_active(backend)
            try:
                self.preferences.save_route(
                    "codex" if getattr(self.connection, "compatibility", False) else "chatgpt"
                )
            except OSError:
                pass  # A preferences write must not discard a usable connection.
            if self.state is not None:
                self.state.provider_name = getattr(backend, "name", "ChatGPT plan")
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
        if getattr(active, "connection", None) is self.connection:
            ai_backend.set_active(None)

        def done(revoked):
            if epoch != self._epoch:
                return
            self._busy = False
            self._sharing = False
            self._models = ()
            self.success.hide()
            self.model_picker.clear()
            self.model_picker.setPlaceholderText(
                bi("Sign in to load your models", "登录后显示可用模型")
            )
            self.plan_consent.setChecked(False)
            active = ai_backend.get_active()
            if getattr(active, "connection", None) is self.connection:
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
