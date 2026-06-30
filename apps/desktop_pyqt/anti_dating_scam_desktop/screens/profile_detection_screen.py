from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ProfileDetectionScreen(QWidget):
    def __init__(self, state, profile_store, on_home, on_import, on_mode, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        self.on_home = on_home
        self.on_import = on_import
        self.on_mode = on_mode
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(StepHeader(bi("Local Profile Detection", "本地档案检测")))
        self.status = StatusBanner()
        layout.addWidget(self.status)
        self.detail = QLabel()
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)

        self.continue_button = PrimaryButton(
            bi("Continue with Existing Profile", "使用现有档案继续")
        )
        self.continue_button.clicked.connect(self._continue_existing)
        self.update_button = SecondaryButton(
            bi("Import More Data / Update Profile", "导入更多数据 / 更新档案")
        )
        self.update_button.clicked.connect(on_mode)
        self.choose_button = SecondaryButton(
            bi("Choose Another Profile File", "选择其他档案文件")
        )
        self.choose_button.clicked.connect(self._choose_profile)
        self.create_button = PrimaryButton(bi("Create My Local Profile", "创建我的本地档案"))
        self.create_button.clicked.connect(self._create_vault)
        self.open_vault_button = SecondaryButton(
            bi("Open Existing Vault Folder", "打开现有档案库文件夹")
        )
        self.open_vault_button.clicked.connect(self._open_existing_vault)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        for button in [
            self.continue_button,
            self.update_button,
            self.choose_button,
            self.create_button,
            self.open_vault_button,
            back,
        ]:
            layout.addWidget(button)
        layout.addStretch()

    def on_enter(self) -> None:
        exists = self.profile_store.detect_existing_profile()
        self.state.profile_exists = exists
        self.state.vault_path = self.profile_store.base_dir
        self.state.profile_path = self.profile_store.markdown_path
        self.state.profile_json_path = self.profile_store.json_path
        if exists:
            self.status.set_text(bi("Existing Local Profile Found", "已找到本地档案"))
            self.detail.setText(
                f"{bi('Vault folder', '档案库文件夹')}: {self.profile_store.base_dir}\n"
                f"{bi('Markdown Profile', 'Markdown 档案')}: {self.profile_store.markdown_path}\n"
                f"{bi('JSON Profile', 'JSON 档案')}: {self.profile_store.json_path}"
            )
            self.continue_button.show()
            self.update_button.show()
            self.choose_button.show()
            self.create_button.hide()
            self.open_vault_button.show()
        else:
            self.status.set_text(bi("No Local Profile Found", "未找到本地档案"))
            self.detail.setText(
                bi(
                    "AI-SlowMatch keeps everything in a local vault folder you choose. "
                    "Create one and your profile files are generated inside it, ready for a "
                    "desktop agent (Claude Code / Cowork) to open.",
                    "AI-SlowMatch 会把所有内容保存在您自行选择的本地档案库（vault）文件夹中。"
                    "创建后，档案文件会自动生成在其中，可直接让桌面代理（Claude Code / Cowork）打开。",
                )
            )
            self.continue_button.hide()
            self.update_button.hide()
            self.choose_button.hide()
            self.create_button.show()
            self.open_vault_button.show()

    def _create_vault(self) -> None:
        parent = QFileDialog.getExistingDirectory(
            self,
            bi("Choose where to create your vault folder", "选择创建档案库（vault）的位置"),
            str(Path.home()),
        )
        if not parent:
            return
        vault = self.profile_store.create_vault(Path(parent))
        self.state.vault_path = vault
        self.state.profile_path = self.profile_store.markdown_path
        self.state.profile_json_path = self.profile_store.json_path
        QMessageBox.information(
            self,
            bi("Vault created", "档案库已创建"),
            f"{bi('Created vault at', '已创建档案库于')}:\n{vault}\n\n"
            + bi(
                "Your profile files will be auto-generated inside it. You can point "
                "Claude Code / Cowork at this folder.",
                "您的档案文件将自动生成在其中。您可以将 Claude Code / Cowork 指向此文件夹。",
            ),
        )
        self.on_mode()

    def _open_existing_vault(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            bi("Open an existing vault folder", "打开现有的档案库文件夹"),
            str(Path.home()),
        )
        if not folder:
            return
        self.profile_store.use_existing_vault(Path(folder))
        self.state.vault_path = Path(folder)
        self.state.profile_path = self.profile_store.markdown_path
        self.state.profile_json_path = self.profile_store.json_path
        if self.profile_store.detect_existing_profile():
            self._continue_existing()
        else:
            self.on_enter()

    def _continue_existing(self) -> None:
        if self.profile_store.markdown_path.exists():
            self.state.current_profile_markdown = self.profile_store.load_markdown_profile()
        if self.profile_store.json_path.exists():
            self.state.current_profile_json = self.profile_store.load_json_profile()
        self.on_home()

    def _choose_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            bi("Choose profile.mpm.md or profile.json", "选择 profile.mpm.md 或 profile.json"),
            str(Path.home()),
            "Profile files (*.mpm.md *.md *.json)",
        )
        if not path:
            return
        selected = Path(path)
        if selected.suffix == ".json":
            self.state.profile_json_path = selected
            self.state.current_profile_json = self.profile_store.load_json_profile(selected)
        else:
            self.state.profile_path = selected
            self.state.current_profile_markdown = self.profile_store.load_markdown_profile(selected)
        self.state.profile_exists = True
        self.on_home()
