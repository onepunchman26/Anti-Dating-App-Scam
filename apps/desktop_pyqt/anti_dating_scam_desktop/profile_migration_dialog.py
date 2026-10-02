"""Explicit literal review of a local, lossless historical profile layout copy."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
)

from anti_dating_scam.services.profile_migration import (
    ProfileMigrationError,
    ProfileMigrationService,
)
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton


def _label(text: str) -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    return widget


def _reader() -> QPlainTextEdit:
    widget = QPlainTextEdit()
    widget.setReadOnly(True)
    return widget


class ProfileMigrationDialog(QDialog):
    """The core checks exact source bytes and destination again on confirmation."""

    def __init__(self, vault_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.vault_dir = Path(vault_dir)
        self.service = None
        self.preview = None
        self.migration_result = None
        self.setWindowTitle(bi("Review legacy profile layout", "复核旧版档案目录"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Review the two fixed profile files at the vault root. Confirming copies the "
            "available files byte for byte into profile/ and keeps the originals. This "
            "changes the folder layout only; it does not rewrite content, infer missing "
            "details or call AI. Existing destination content is never overwritten.",
            "请复核档案库根目录中的两个固定档案文件。确认后，应用会将现有文件逐字节复制到 "
            "profile/，同时保留原文件。此操作仅调整目录布局，不改写内容、不推断缺失信息、"
            "不调用 AI，也不会覆盖目标目录中的现有内容。",
        )))
        layout.addWidget(_label(str(self.vault_dir)))
        self.tabs = QTabWidget()
        self.review_text = _reader()
        self.tabs.addTab(self.review_text, bi("Copy plan and checks", "复制计划与检查"))
        self.file_readers = {}
        for name in ("profile.mpm.md", "profile.json"):
            reader = _reader()
            self.file_readers[name] = reader
            self.tabs.addTab(reader, name)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(_label(bi(
            "Copies remain unencrypted local files. Review every available file before "
            "confirming. Invalid or unsupported JSON must be corrected separately; its "
            "literal content remains available for review here.",
            "副本仍是未加密的本地文件。确认前请复核所有现有文件。无效或不受支持的 JSON "
            "需要另行修正；您仍可在这里查看其原始文字内容。",
        )))
        self.confirm = QCheckBox(bi(
            "I reviewed the files and confirm this exact local copy.",
            "我已复核这些文件，确认执行此次本地原样复制。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        layout.addWidget(self.confirm)
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.refresh_button = SecondaryButton(bi("Refresh review", "刷新复核"))
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        actions.addStretch()
        self.migrate_button = PrimaryButton(bi("Copy into profile/", "复制到 profile/"))
        self.migrate_button.setAutoDefault(False)
        self.migrate_button.clicked.connect(self._migrate)
        actions.addWidget(self.migrate_button)
        self.cancel_button = SecondaryButton(bi("Cancel", "取消"))
        self.cancel_button.clicked.connect(self.reject)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)
        self.refresh()

    def _update_buttons(self) -> None:
        if not hasattr(self, "migrate_button"):
            return
        eligible = self.preview is not None and self.preview.eligible
        self.confirm.setEnabled(eligible)
        self.migrate_button.setEnabled(eligible and self.confirm.isChecked())

    def refresh(self) -> None:
        self.preview = None
        self.confirm.setChecked(False)
        self.review_text.clear()
        for reader in self.file_readers.values():
            reader.clear()
        try:
            self.service = ProfileMigrationService(self.vault_dir)
            self.preview = self.service.inspect()
            lines = [bi(
                "Copy available files without changing their bytes:",
                "原样复制现有文件，不更改任何字节：",
            )]
            for entry in self.preview.files:
                lines.append(f"{entry.filename} → profile/{entry.filename}")
                lines.append(bi(
                    f"Present: {entry.present}; bytes: {entry.size_bytes}",
                    f"存在：{'是' if entry.present else '否'}；字节数：{entry.size_bytes}",
                ))
                if entry.sha256:
                    lines.append("SHA-256: " + entry.sha256)
                lines.append("")
                self.file_readers[entry.filename].setPlainText(
                    entry.text if entry.text is not None else bi(
                        "File absent or unavailable as UTF-8 text.",
                        "文件不存在或无法作为 UTF-8 文字查看。",
                    )
                )
            lines.extend(bi(issue.message_en, issue.message_zh) for issue in self.preview.issues)
            self.review_text.setPlainText("\n".join(lines))
            self.status.setText(bi(
                "Ready for review. No files have been copied.",
                "已准备好复核，尚未复制任何文件。",
            ) if self.preview.eligible else bi(
                "Copying is blocked. Read the checks and original text; your current vault "
                "and these originals have not changed.",
                "暂时无法复制。请查看检查结果和原始文字；当前档案库与这些原文件均未更改。",
            ))
        except (ProfileMigrationError, OSError, ValueError):
            self.preview = None
            self.status.setText(bi(
                "These files could not be safely inspected. Nothing was copied. Check the "
                "folder and refresh; your current vault remains selected.",
                "无法安全检查这些文件，未复制任何内容。请检查文件夹后刷新；仍保留当前档案库选择。",
            ))
        self._update_buttons()

    def _migrate(self) -> None:
        if not self.migrate_button.isEnabled():
            return
        try:
            self.migration_result = self.service.migrate(
                self.preview, confirmed=self.confirm.isChecked(),
            )
        except (ProfileMigrationError, OSError, ValueError):
            self.preview = None
            self.confirm.setChecked(False)
            self.status.setText(bi(
                "The files or destination changed, or the copy could not be completed. "
                "The displayed review is stale. Refresh and review again before confirming; "
                "your current vault remains selected.",
                "文件或目标目录已变化，或复制未能完成。当前复核内容已失效，请刷新并重新复核后"
                "再确认；仍保留当前档案库选择。",
            ))
            self._update_buttons()
            return
        self.accept()
