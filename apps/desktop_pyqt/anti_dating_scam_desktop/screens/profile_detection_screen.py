from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFileDialog, QLabel, QMessageBox, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.profile_migration_dialog import ProfileMigrationDialog
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ProfileDetectionScreen(QWidget):
    def __init__(self, state, profile_store, on_home, on_add_data, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        self.on_home = on_home
        self.on_add_data = on_add_data
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(StepHeader(bi("Your local folder", "你的本地文件夹")))
        self.status = StatusBanner()
        layout.addWidget(self.status)
        self.detail = QLabel()
        self.detail.setTextFormat(Qt.TextFormat.PlainText)
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)

        self.continue_button = PrimaryButton(
            bi("Continue", "继续")
        )
        self.continue_button.clicked.connect(self._continue_existing)
        self.update_button = SecondaryButton(
            bi("Add More Data", "添加更多数据")
        )
        self.update_button.clicked.connect(on_add_data)
        self.choose_button = SecondaryButton(
            bi("Choose Another Profile File", "选择其他档案文件")
        )
        self.choose_button.clicked.connect(self._choose_profile)
        self.build_button = PrimaryButton(
            bi("Continue to AI Chat", "继续进入 AI 聊天")
        )
        self.build_button.clicked.connect(on_home)
        self.create_button = PrimaryButton(bi("Choose a folder and continue", "选择文件夹并继续"))
        self.create_button.clicked.connect(self._create_vault)
        self.open_vault_button = SecondaryButton(
            bi("Open Existing Vault Folder", "打开现有档案库文件夹")
        )
        self.open_vault_button.clicked.connect(self._open_existing_vault)
        self.migration_button = SecondaryButton(bi(
            "Review Legacy Profile Files", "复核旧版档案文件",
        ))
        self.migration_button.clicked.connect(self._review_current_legacy)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        for button in [
            self.continue_button,
            self.update_button,
            self.choose_button,
            self.migration_button,
            self.build_button,
            self.create_button,
            self.open_vault_button,
            back,
        ]:
            layout.addWidget(button)
        layout.addStretch()

    def on_enter(self) -> None:
        exists = self.profile_store.detect_existing_profile()
        legacy = self.profile_store.has_legacy_profile()
        self.migration_button.setVisible(legacy)
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
            self.build_button.hide()
            self.create_button.hide()
            self.open_vault_button.show()
        elif legacy:
            self.status.set_text(bi("Legacy Profile Files Found", "已找到旧版档案文件"))
            self.detail.setText(
                f"{bi('Vault folder', '档案库文件夹')}: {self.profile_store.base_dir}\n"
                + bi(
                    "This vault stores its profile files at the folder root. Review the "
                    "original text and confirm a local copy into profile/ before continuing. "
                    "No migration or AI processing happens automatically.",
                    "此档案库将档案文件保存在根目录。继续前，请复核原始文字并确认复制到 profile/。"
                    "应用不会自动迁移，也不会自动调用 AI。",
                )
            )
            self.continue_button.hide()
            self.update_button.hide()
            self.choose_button.hide()
            self.build_button.hide()
            self.create_button.hide()
            self.open_vault_button.show()
        elif self.profile_store.is_vault(self.profile_store.base_dir):
            # A real vault is active (e.g. remembered from last time, or just
            # opened) but it has no profile yet. Don't dead-end the user on a
            # bare "no profile" screen - let them build one inside this vault.
            self.status.set_text(bi("Folder ready", "文件夹已准备好"))
            self.detail.setText(
                f"{bi('Vault folder', '档案库文件夹')}: {self.profile_store.base_dir}\n"
                + bi(
                    "You can start chatting without a profile or imported files. "
                    "Reflections are saved here only when you choose to save them.",
                    "无需已有档案或导入文件即可开始聊天。只有你选择保存时，画像才会写入这里。",
                )
            )
            self.continue_button.hide()
            self.update_button.hide()
            self.choose_button.show()
            self.build_button.show()
            self.create_button.hide()
            self.open_vault_button.show()
        else:
            self.status.set_text(bi("Choose where to save reflections", "选择画像的保存位置"))
            self.detail.setText(
                bi(
                    "Choose a folder, then connect ChatGPT and start chatting. No files "
                    "need to be imported. Saved files are not encrypted; a sync folder "
                    "may copy them to the cloud.",
                    "选择文件夹后即可连接 ChatGPT 并开始聊天，无需导入文件。保存的文件未加密；"
                    "同步文件夹可能将文件复制到云端。",
                )
            )
            self.continue_button.hide()
            self.update_button.hide()
            self.choose_button.hide()
            self.build_button.hide()
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
                "Next, connect ChatGPT and open AI Chat. No import or existing profile "
                "is required. You choose what to send and save.",
                "接下来连接 ChatGPT 并进入 AI 聊天。无需导入资料或已有档案；"
                "发送和保存什么由你决定。",
            ),
        )
        self.on_home()

    def _open_existing_vault(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            bi("Open an existing vault folder", "打开现有的档案库文件夹"),
            str(Path.home()),
        )
        if not folder:
            return
        chosen = Path(folder)
        # Tolerate picking the parent folder the vault was created under, or any
        # folder containing a single vault, instead of the vault itself.
        vault = self.profile_store.resolve_vault(chosen)
        if vault is None:
            reply = QMessageBox.question(
                self,
                bi("Not an AI-SlowMatch vault", "这不是 AI-SlowMatch 档案库"),
                f"{bi('Folder', '文件夹')}: {chosen}\n\n"
                + bi(
                    "This folder is not an AI-SlowMatch vault yet. Set it up as your "
                    "vault here?",
                    "该文件夹还不是 AI-SlowMatch 档案库。是否在此将其设置为您的档案库？",
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            vault = chosen

        candidate = ProfileStore(vault, config_path=self.profile_store.config_path)
        if candidate.has_legacy_profile() and not candidate.detect_existing_profile():
            if not self._review_legacy(vault):
                return
        if not self._activate_vault(vault):
            return
        # An empty folder is sufficient for the conversation-first path.
        self.on_home()

    def _continue_existing(self) -> None:
        try:
            markdown, structured = self._read_profile(self.profile_store)
        except (OSError, ValueError):
            self._load_failed()
            return
        self._set_loaded_profile(markdown, structured)
        self.on_home()

    @staticmethod
    def _read_profile(store):
        markdown = store.load_markdown_profile() if store.markdown_path.exists() else None
        structured = store.load_json_profile() if store.json_path.exists() else None
        return markdown, structured

    def _set_loaded_profile(self, markdown, structured) -> None:
        self.state.vault_path = self.profile_store.base_dir
        self.state.profile_path = self.profile_store.markdown_path
        self.state.profile_json_path = self.profile_store.json_path
        self.state.current_profile_markdown = markdown
        self.state.current_profile_json = structured
        self.state.profile_exists = markdown is not None or structured is not None

    def _load_failed(self) -> None:
        QMessageBox.warning(
            self, bi("Profile could not be opened", "无法打开档案"),
            bi(
                "The profile or vault settings could not be read or saved. Your previous "
                "selection and draft remain unchanged. Check the files and try again. "
                "A completed migration copy, if any, remains in the chosen folder.",
                "无法读取档案或保存档案库设置。之前的选择和草稿保持不变，请检查文件后重试。"
                "若此前已完成迁移，复制的文件仍保留在所选文件夹中。",
            ),
        )

    def _activate_vault(self, vault: Path) -> bool:
        candidate = ProfileStore(vault, config_path=self.profile_store.config_path)
        try:
            markdown, structured = self._read_profile(candidate)
            self.profile_store.use_existing_vault(vault)
        except (OSError, ValueError):
            self._load_failed()
            return False
        self._set_loaded_profile(markdown, structured)
        return True

    def _review_legacy(self, vault: Path) -> bool:
        dialog = ProfileMigrationDialog(vault, self)
        return (
            dialog.exec() == QDialog.DialogCode.Accepted
            and dialog.migration_result is not None
        )

    def _review_current_legacy(self) -> None:
        if not self._review_legacy(self.profile_store.base_dir):
            return
        if self._activate_vault(self.profile_store.base_dir):
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
