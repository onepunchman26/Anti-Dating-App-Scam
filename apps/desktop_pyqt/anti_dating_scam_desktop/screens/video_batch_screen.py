"""Collection UI; parsing, AI and memory rules live in the existing Python core."""

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.batch_context.analysis import BatchGrant, disclosure_text
from anti_dating_scam.batch_context.importers import (
    import_files,
    import_notes,
    parse_text,
    preview_rows,
)
from anti_dating_scam.batch_context.models import Preview
from anti_dating_scam.batch_context.retrieval import PublicMetadata
from anti_dating_scam.batch_context.service import BatchService
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi, current_language
from anti_dating_scam_desktop.navigation import _ScreenViewport
from anti_dating_scam_desktop.widgets.relationship_memory_dialog import RelationshipMemoryDialog
from anti_dating_scam_desktop.workers import run_async

LABELS = {
    "pending": ("Waiting", "待处理"),
    "full": ("Full supplied text", "完整处理所供文本"),
    "partial": ("Partial / metadata", "部分／仅元数据"),
    "skipped": ("Skipped", "已跳过"),
    "failed": ("Unsuccessful", "未成功"),
    "imported": ("Imported", "导入"),
    "duplicates": ("Duplicates merged", "合并重复"),
    "invalid": ("Invalid / unsupported", "无效／不支持"),
    "reused": ("Reused", "复用"),
    "draft": ("Draft", "草稿"),
    "confirmed": ("Adopted", "已采纳"),
    "rejected": ("Rejected", "已拒绝"),
    "removed": ("Removed", "已移除"),
    "transcript": ("Supplied transcript", "所供字幕"),
    "description": ("Creator description", "创作者描述"),
    "existing_summary": ("Existing summary (authorship unknown)", "已有摘要（作者未核实）"),
    "user_annotation": ("Explicit user annotation", "明确用户备注"),
    "title": ("Title", "标题"),
    "metadata": ("Title only", "仅标题"),
    "link": ("Link only", "仅链接"),
    "possible": ("Possible interest", "可能兴趣"),
    "recurring": ("Recurring saves", "反复收藏"),
    "recent": ("Recent exploration", "近期探索"),
    "aspirational": ("Aspiration", "希望尝试"),
    "task_related": ("Task-related", "任务相关"),
    "ready": ("Ready", "待开始"),
    "running": ("Processing", "处理中"),
    "paused": ("Paused", "已暂停"),
    "complete": ("Review ready", "可审阅"),
    "no_content": ("No supplied content", "没有提供正文"),
    "metadata_unavailable": ("Public title unavailable", "公开标题不可用"),
    "analysis_failed": ("Analysis failed; retry manually", "分析失败，可手动重试"),
    "batch_changed": ("Batch changed; reopen it.", "批次已变化，请重新打开。"),
    "batch_usage": ("Plan limit reached; progress saved.", "套餐额度用完，进度已保存。"),
    "batch_auth": ("Reconnect ChatGPT; progress saved.", "请重新连接 ChatGPT，进度已保存。"),
    "batch_model": ("Choose an available model.", "请选择可用模型。"),
    "batch_cancelled": ("Stopped; completed work is kept.", "已停止，保留已完成工作。"),
    "memory_changed_or_disabled": (
        "Enable memory in Memory settings, then review again.",
        "请在记忆设置中启用复用，再重新审阅。",
    ),
    "memory_full_20": (
        "Memory has a 20-note limit; merge or remove notes first.",
        "记忆最多 20 条，请先合并或移除条目。",
    ),
    "select_findings": ("Select one or more findings.", "请选择一个或多个结论。"),
    "edit_length_1_250": ("Enter 1–250 characters.", "请输入 1～250 字。"),
    "merge_same_kind": (
        "Select two or more groups of the same type.",
        "请选择同类的至少两个分组。",
    ),
    "revise_one_group": ("Select one group to revise.", "请选择一个要修改的分组。"),
    "already_reviewable": (
        "This batch is already processed. Review the results.",
        "此批次已处理，请审阅结果。",
    ),
}


def label(value):
    return bi(*LABELS[value]) if value in LABELS else value


def coverage_label(value):
    return (
        bi("Transcript supplied", "已提供字幕")
        if value == "full"
        else (
            bi("Excerpts / notes supplied", "已提供片段／笔记")
            if value == "partial"
            else label(value)
        )
    )


def review_dialog(parent, title, text):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.resize(760, 610)
    layout = QVBoxLayout(dialog)
    content = QPlainTextEdit()
    content.setReadOnly(True)
    content.setPlainText(text)
    layout.addWidget(content)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(QDialogButtonBox.StandardButton.Ok).setText(bi("Confirm", "确认"))
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    return dialog.exec() == QDialog.DialogCode.Accepted


@dataclass
class VideoBatchState:
    vault: str = ""
    preview: Preview | None = None
    batch_id: str = ""
    grants: dict = field(default_factory=dict)


class VideoBatchScreen(QWidget):
    progressed = Signal(object)

    def __init__(self, state, profile_store, holder, on_back):
        super().__init__()
        self.state, self.profile_store, self.holder = state, profile_store, holder
        self.service = None
        self.batch = None
        self.busy = False
        self.cancel = None
        self.buttons = []
        self.progressed.connect(self._progress)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        self._note(layout, "Saved videos → interests & reflections", "收藏视频 → 兴趣与反思")
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.history = QComboBox()
        self.history.setMinimumContentsLength(15)
        self.history.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        row.addWidget(self.history, 1)
        self._button(row, "Open batch", "打开批次", self._open)
        self._button(row, "Memory settings", "记忆设置", self._memory)
        layout.addLayout(row)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._import_tab()
        self._results_tab()
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        row = QHBoxLayout()
        stop = QPushButton(bi("Pause", "暂停"))
        stop.clicked.connect(self._stop)
        row.addWidget(stop)
        back = QPushButton(bi("Back", "返回"))
        back.clicked.connect(lambda: (self._stop(), on_back()))
        row.addWidget(back)
        layout.addLayout(row)

    def _note(self, layout, en, zh):
        note = QLabel(bi(en, zh))
        note.setWordWrap(True)
        layout.addWidget(note)

    def _button(self, layout, en, zh, call):
        button = QPushButton(bi(en, zh))
        button.clicked.connect(lambda: self._guard(call))
        layout.addWidget(button)
        self.buttons.append(button)
        return button

    def _tab(self, en, zh):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.tabs.addTab(_ScreenViewport(widget), bi(en, zh))
        return layout

    def _import_tab(self):
        layout = self._tab("1. Import a collection", "1. 导入集合")
        self._note(
            layout,
            "Select your own saved/liked exports or p"
            "repared note folder. Sources are read on"
            "ly "
            "after selection; local copies are unencr"
            "ypted. No account scraping or private me"
            "ssages. "
            "Supports Takeout playlist CSV, TikTok sa"
            "ved/liked JSON/TXT, URL lists and Markdo"
            "wn.",
            "选择自己的收藏／点赞导出文件或准备好的笔记文件夹。仅在选择后读取，本机副本未加密"
            "；"
            "不抓取账户或私信。支持 Takeout 播放列表 CSV、TikTok 收藏／点"
            "赞 JSON／TXT、链接列表和 Markdown。",
        )
        row = QHBoxLayout()
        self._button(row, "Select export files", "选择导出文件", self._files)
        self._button(row, "Select notes folder", "选择笔记文件夹", self._folder)
        self._button(row, "Import help", "导入帮助", self._help)
        layout.addLayout(row)
        self.pasted = QPlainTextEdit()
        self.pasted.setPlaceholderText(
            bi("Or paste a list of full video URLs", "或粘贴整批视频完整链接")
        )
        self.pasted.setMaximumHeight(95)
        layout.addWidget(self.pasted)
        self._button(layout, "Preview pasted list", "预览粘贴列表", self._paste)
        row = QHBoxLayout()
        self.source = QComboBox()
        self.collection = QComboBox()
        self.start_date, self.end_date = QLineEdit(), QLineEdit()
        self.start_date.setPlaceholderText(
            bi("From YYYY-MM-DD (optional)", "开始日期 YYYY-MM-DD（可选）")
        )
        self.end_date.setPlaceholderText(
            bi("To YYYY-MM-DD (optional)", "结束日期 YYYY-MM-DD（可选）")
        )
        for widget in (self.source, self.collection, self.start_date, self.end_date):
            row.addWidget(widget)
        layout.addLayout(row)
        self.unknown_dates = QCheckBox(bi("Include unknown dates", "包含日期未知项"))
        self.unknown_dates.setChecked(True)
        layout.addWidget(self.unknown_dates)
        self._button(
            layout, "Apply filters / select visible batch", "应用筛选／选择所示整批", self._filter
        )
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            [
                bi("Use", "选择"),
                bi("Source", "来源"),
                bi("Title / link", "标题／链接"),
                bi("Collection", "集合"),
                bi("Saved", "收藏日期"),
                bi("Coverage", "资料完整度"),
            ]
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(170)
        self.table.setColumnWidth(2, 260)
        self.table.cellDoubleClicked.connect(self._inspect_preview)
        layout.addWidget(self.table)
        self._button(layout, "Import selected batch", "导入选定整批", self._create)

    def _results_tab(self):
        layout = self._tab("2. Process & review groups", "2. 处理与分组审阅")
        self._note(
            layout,
            "A save is not agreement or participation"
            ". Full means all supplied text was analy"
            "zed, "
            "not that AI watched the video. Titles re"
            "main partial. Reflections stay drafts un"
            "til "
            "you adopt them. No automatic memory updates.",
            "收藏不等于赞同或参与。完整处理仅指所供文本均参与分析，不代表 AI 看过视频。仅"
            "标题始终算部分。"
            "反思在你采纳前保持草稿，不自动写入记忆。",
        )
        row = QHBoxLayout()
        self._button(row, "Fetch public titles (optional)", "补全公开标题（可选）", self._metadata)
        self._button(row, "Analyze / resume", "分析／继续", self._analyze)
        self._button(row, "Retry unsuccessful items", "重试未成功项", lambda: self._analyze(True))
        layout.addLayout(row)
        self.kind = QComboBox()
        self.kind.addItem(bi("Interest profile", "兴趣画像"), "interest")
        self.kind.addItem(bi("Viewpoint & reflection drafts", "观点与反思草稿"), "reflection")
        self.kind.currentIndexChanged.connect(self._render_groups)
        layout.addWidget(self.kind)
        self.groups = QListWidget()
        self.groups.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.groups.setMinimumHeight(130)
        self.groups.itemSelectionChanged.connect(self._details)
        layout.addWidget(self.groups)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(150)
        layout.addWidget(self.details)
        self.edit = QLineEdit()
        self.edit.setMaxLength(250)
        self.edit.setPlaceholderText(
            bi(
                "Revise or name a merged group (up to 250 characters)",
                "修改结论或填写合并后的表述（最多 250 字）",
            )
        )
        layout.addWidget(self.edit)
        row = QHBoxLayout()
        for en, zh in (
            ("I like the visual style, not the message.", "我喜欢视觉风格，不代表赞同内容。"),
            ("This was saved for work.", "这是为工作收藏的。"),
            ("This no longer represents me.", "这已不能代表现在的我。"),
        ):
            self._button(row, en, zh, lambda en=en, zh=zh: self.edit.setText(bi(en, zh)))
        layout.addLayout(row)
        row = QHBoxLayout()
        for action, en, zh in (
            ("confirm", "Adopt selected", "采纳所选"),
            ("revise", "Save revision", "保存修改"),
            ("merge", "Merge selected", "合并所选"),
            ("reject", "Reject selected", "拒绝所选"),
            ("remove", "Remove selected", "移除所选"),
        ):
            self._button(row, en, zh, lambda action=action: self._review(action))
        layout.addLayout(row)
        self.questions = QLabel()
        self.questions.setWordWrap(True)
        layout.addWidget(self.questions)
        row = QHBoxLayout()
        self._button(row, "Inspect source items", "查看来源条目", self._sources)
        self._button(row, "Export reviewed results", "导出审阅结果", self._export)
        self._button(row, "Undo this import", "撤销此次导入", self._undo)
        layout.addLayout(row)

    def on_enter(self):
        vault = str(self.state.vault_path or self.profile_store.base_dir)
        if vault != self.holder.vault:
            self._stop()
            self.holder.vault, self.holder.preview, self.holder.batch_id = vault, None, ""
            self.holder.grants.clear()
            self.batch = None
            self.source.clear()
            self.collection.clear()
            self.start_date.clear()
            self.end_date.clear()
            self.status.clear()
            self.pasted.clear()
            self.edit.clear()
            self.details.clear()
            self.table.setRowCount(0)
            self.groups.clear()
            self.questions.clear()
        self.service = BatchService(Path(vault))
        self._guard(self._history)
        if self.holder.preview:
            self._preview(self.holder.preview)
        if self.holder.batch_id:
            self._guard(self._open)

    def _guard(self, call):
        try:
            return call()
        except Exception as exc:
            self._error(str(exc))

    def _error(self, message):
        self.status.setText(
            label(message)
            if message in LABELS
            else bi(
                "Unable to complete this step. Check the "
                "selected format, scope or connection; "
                "completed work is kept. No automatic retry.",
                "此步未完成，请检查所选格式、范围或连接；已完成工作保留，没有自动重试。",
            )
        )

    def _history(self):
        self.history.clear()
        for batch in sorted(self.service.list(), key=lambda b: b.created_at, reverse=True):
            self.history.addItem(
                batch.name + " · " + batch.created_at.strftime("%m-%d %H:%M"), batch.id
            )
        if self.holder.batch_id:
            self.history.setCurrentIndex(self.history.findData(self.holder.batch_id))

    def _open(self):
        batch_id = self.history.currentData()
        if batch_id:
            self.holder.batch_id = batch_id
            self._show_batch(self.service.read(batch_id))

    def _files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            bi("Selected saved-video exports", "选择收藏视频导出"),
            "",
            "CSV / JSON / TXT / Markdown (*.csv *.json *.txt *.md)",
        )
        if paths:
            self._work(lambda _: import_files(paths), self._preview)

    def _folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, bi("Prepared notes folder", "准备好的笔记文件夹")
        )
        if folder:
            self._work(lambda _: import_notes(folder), self._preview)

    def _paste(self):
        self._preview(preview_rows(parse_text(self.pasted.toPlainText())))

    def _preview(self, preview):
        self.holder.preview = preview
        self.source.clear()
        self.collection.clear()
        self.source.addItem(bi("All sources", "所有来源"), "")
        self.collection.addItem(bi("All collections", "所有集合"), "")
        for name in sorted({v.source for v in preview.videos}):
            self.source.addItem(name, name)
        for name in sorted({c for v in preview.videos for c in v.collections}):
            self.collection.addItem(name, name)
        self._filter()
        self.status.setText(
            bi("Preview", "预览")
            + f": {len(preview.videos)} · "
            + label("duplicates")
            + f": {preview.duplicates} · "
            + label("invalid")
            + f": {preview.invalid} · "
            + bi("File notices", "文件提示")
            + f": {len(preview.notices)}"
        )

    def _filter(self):
        preview = self.holder.preview
        if not preview:
            return
        start = (
            date.fromisoformat(self.start_date.text()) if self.start_date.text().strip() else None
        )
        end = date.fromisoformat(self.end_date.text()) if self.end_date.text().strip() else None
        if start and end and start > end:
            raise ValueError("invalid_date_range")
        selected = []
        for video in preview.videos:
            if self.source.currentData() and video.source != self.source.currentData():
                continue
            if (
                self.collection.currentData()
                and self.collection.currentData() not in video.collections
            ):
                continue
            saved = date.fromisoformat(video.saved_at[:10]) if video.saved_at else None
            if not saved and not self.unknown_dates.isChecked():
                continue
            if saved and ((start and saved < start) or (end and saved > end)):
                continue
            selected.append(video)
        self.table.setRowCount(len(selected))
        for row, video in enumerate(selected):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Checked)
            check.setData(Qt.ItemDataRole.UserRole, video.id)
            self.table.setItem(row, 0, check)
            for col, text in enumerate(
                (
                    video.source,
                    video.title or video.url,
                    ", ".join(video.collections),
                    video.saved_at or "—",
                    coverage_label(video.coverage),
                ),
                1,
            ):
                self.table.setItem(row, col, QTableWidgetItem(text))

    def _inspect_preview(self, row, _column):
        if self.holder.preview:
            key = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            video = next(v for v in self.holder.preview.videos if v.id == key)
            review_dialog(self, bi("Source preview", "来源预览"), self._video_text(video))

    def _create(self):
        ids = [
            self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            for row in range(self.table.rowCount())
            if self.table.item(row, 0).checkState() == Qt.CheckState.Checked
        ]
        if not ids or not self.holder.preview:
            return
        if not review_dialog(
            self,
            bi("Import collection", "导入集合"),
            bi(
                f"Import {len(ids)} selected videos from your own saved/liked collection? "
                "The shown excerpts are stored locally wi"
                "thout encryption. No network call yet.",
                f"导入你自己的收藏／点赞集合中选定的 {len(ids)} 项？"
                "所示片段未加密保存在本机，暂不联网。",
            ),
        ):
            return
        batch = self.service.create(
            self.holder.preview, ids, name=bi("Saved videos", "收藏视频"), confirmed=True
        )
        self.holder.batch_id = batch.id
        self._history()
        self._show_batch(batch)
        self.tabs.setCurrentIndex(1)

    def _metadata(self):
        if not self.batch:
            return
        if not review_dialog(
            self,
            bi("Public title lookup", "查询公开标题"),
            bi(
                "Send the following YouTube/TikTok URLs to their public oEmbed endpoints? "
                "No account tokens or transcripts. Other sources use supplied files only.\n\n",
                "将以下 YouTube／TikTok 链接发送到各自公开 oEmbed 接口？不"
                "发送账户令牌、不取得字幕；"
                "其他来源仅使用提供的文件。\n\n",
            )
            + "\n".join(
                i.video.url
                for i in self.batch.items
                if not i.video.title and i.video.source in PublicMetadata.ENDPOINTS
            ),
        ):
            return
        service, batch = self.service, self.batch
        self._work(
            lambda cancel: service.fetch_metadata(
                batch.id,
                PublicMetadata(),
                approved_digest=batch.digest,
                confirmed=True,
                cancel=cancel,
                progress=self.progressed.emit,
            ),
            self._show_batch,
        )

    def _analyze(self, retry=False):
        if not self.batch:
            return
        backend = ai_backend.get_active()
        if backend is None:
            self.status.setText(bi("Connect ChatGPT from Home first.", "请先在主页连接 ChatGPT。"))
            return
        backend = copy.copy(backend)
        batch, service = self.batch, self.service
        grant = self.holder.grants.get(batch.id)
        try:
            if not grant:
                raise ValueError("review")
            grant.check(batch, backend)
        except ValueError:
            grant = None
        if retry or not grant:
            text = disclosure_text(batch, backend)
            if retry:
                text = (
                    bi(
                        "Retry replaces current groups and withdraws this batch's memory; "
                        "review the new results again.\n\n",
                        "重试会替换当前分组并撤回此批次记忆，请重新审阅新结果。\n\n",
                    )
                    + text
                )
            if not review_dialog(self, bi("Approve batch AI scope", "批准整批 AI 范围"), text):
                return
            grant = BatchGrant.approve(batch, backend, confirmed=True)
            self.holder.grants[batch.id] = grant

        def run(cancel):
            backend.cancel_event = cancel
            return service.process(
                batch.id,
                backend,
                grant,
                cancel=cancel,
                retry_failed=retry,
                progress=self.progressed.emit,
            )

        self._work(run, self._show_batch)

    def _work(self, call, done):
        if self.busy:
            return
        self.busy = True
        for button in self.buttons:
            button.setEnabled(False)
        cancel = self.cancel = threading.Event()
        vault = self.holder.vault
        self.status.setText(bi("Processing; you can pause at any time.", "处理中，可随时暂停。"))

        def finish(result=None, error=None):
            self.busy = False
            for button in self.buttons:
                button.setEnabled(True)
            if self.holder.vault != vault:
                return
            if error:
                if self.holder.batch_id:
                    self._guard(self._open)
                self._error(error)
            else:
                done(result)

        run_async(
            self,
            lambda: call(cancel),
            lambda result: finish(result=result),
            lambda error: finish(error=error),
        )

    def _stop(self):
        if self.cancel:
            self.cancel.set()

    def hideEvent(self, event):
        self._stop()
        super().hideEvent(event)

    def _progress(self, batch):
        if self.batch and batch.id == self.batch.id:
            self._show_batch(batch)

    def _show_batch(self, batch):
        self.batch = batch
        counts = batch.counts()
        self.progress.setRange(0, len(batch.items))
        self.progress.setValue(len(batch.items) - counts["pending"])
        self.status.setText(
            label(batch.state)
            + " · "
            + " · ".join(f"{label(key)}: {value}" for key, value in counts.items())
        )
        self.questions.setText(
            bi("Optional questions", "可选问题")
            + ": "
            + " / ".join(getattr(q, current_language()) for q in batch.questions)
            + "\n"
            + bi(
                f"Additional themes not synthesized: {batch.omitted_groups}. Narrow the "
                "next batch to explore these. No unseen items strengthen conclusions.",
                f"未纳入综合的其他主题：{batch.omitted_groups}。可在下次缩小选择范围后分析；"
                "未纳入的条目不会增强结论。",
            )
        )
        self._render_groups()

    def _render_groups(self):
        self.groups.clear()
        self.details.clear()
        self.edit.clear()
        if not self.batch:
            return
        for finding in self.batch.findings:
            if finding.kind != self.kind.currentData():
                continue
            value = finding.edited_text or getattr(finding.text, current_language())
            item = QListWidgetItem(f"{label(finding.status)} · {value}")
            item.setData(Qt.ItemDataRole.UserRole, finding.id)
            self.groups.addItem(item)

    def _chosen(self):
        ids = {i.data(Qt.ItemDataRole.UserRole) for i in self.groups.selectedItems()}
        return [f for f in self.batch.findings if f.id in ids] if self.batch else []

    def _details(self):
        texts = []
        for finding in self._chosen():
            language = current_language()
            texts.append(
                "\n".join(
                    [
                        getattr(finding.broad, language)
                        + " → "
                        + getattr(finding.specific, language),
                        finding.edited_text or getattr(finding.text, language),
                        getattr(finding.explanation, language),
                        getattr(finding.uncertainty, language),
                        label(finding.pattern),
                        bi(
                            f"Distinct source videos: {len(finding.video_ids)} "
                            "(not independent proof)",
                            f"不同来源视频：{len(finding.video_ids)}（不代表独立证明）",
                        ),
                        *[
                            label(q.origin) + " · " + q.video_id[:10] + ": " + q.quote
                            for q in finding.evidence
                        ],
                    ]
                )
            )
        self.details.setPlainText("\n\n".join(texts))

    def _review(self, action):
        chosen = self._chosen()
        if not chosen:
            raise ValueError("select_findings")
        if action == "confirm":
            text = bi(
                "Adopt the selected wording into your enabled personal memory? "
                "Reflection drafts become your explicitly adopted self-report.\n\n",
                "将选定表述采纳到已启用的个人记忆？反思草稿将成为你明确采纳的自述。\n\n",
            )
            text += "\n\n".join(
                (f.edited_text or getattr(f.text, current_language()))
                + "\n"
                + getattr(f.uncertainty, current_language())
                + "\n"
                + "\n".join(label(q.origin) + ": " + q.quote for q in f.evidence)
                for f in chosen
            )
            if not review_dialog(self, bi("Adopt groups", "采纳分组"), text):
                return
        self._show_batch(
            self.service.review(
                self.batch.id,
                self.batch.revision,
                [f.id for f in chosen],
                action=action,
                text=self.edit.text(),
                language=current_language(),
                confirmed=True,
            )
        )

    def _video_text(self, video):
        return "\n\n".join(
            [
                video.title,
                video.url,
                coverage_label(video.coverage),
                *[label(m.origin) + " · " + m.provenance + "\n" + m.text for m in video.materials],
            ]
        )

    def _sources(self):
        if not self.batch:
            return
        chosen = self._chosen()
        ids = {v for f in chosen for v in f.video_ids}
        text = "\n\n——\n\n".join(
            label(item.status) + " · " + label(item.error) + "\n" + self._video_text(item.video)
            for item in self.batch.items
            if not ids or item.video.id in ids
        )
        review_dialog(self, bi("Source items (read only)", "来源条目（只读）"), text)

    def _undo(self):
        if self.batch and review_dialog(
            self,
            bi("Undo import", "撤销导入"),
            bi(
                "Delete this local batch and recalculate "
                "its approved notes? Dependent inferences"
                " "
                "lose their support. Original selected fi"
                "les and earlier disclosures cannot be re"
                "called.",
                "删除此本机批次并重新计算其批准记忆？依赖它的推断将失去依据。原始选择文件和先前披"
                "露不受影响。",
            ),
        ):
            self.service.undo(self.batch.id, confirmed=True)
            self.holder.grants.pop(self.batch.id, None)
            self.holder.batch_id = ""
            self.holder.preview = None
            self.batch = None
            self.pasted.clear()
            self.table.setRowCount(0)
            self._render_groups()
            self.questions.clear()
            self._history()
            self.status.setText(
                bi(
                    "Import removed; affected memory recalculated.",
                    "导入已删除，相关记忆已重新计算。",
                )
            )

    def _memory(self):
        if self.service:
            RelationshipMemoryDialog(self.service.vault, self).exec()

    def _export(self):
        if self.batch:
            path, _ = QFileDialog.getSaveFileName(
                self, bi("Unencrypted results", "未加密结果"), "interests.json", "JSON (*.json)"
            )
            if path:
                self.service.export(self.batch.id, path)

    def _help(self):
        review_dialog(
            self,
            bi("Prepare one batch", "一次准备整批"),
            bi(
                "YouTube: use Google Takeout's selected Y"
                "ouTube playlist CSV files. A playlist UR"
                "L "
                "alone does not expand automatically.\nTik"
                "Tok: request Download your data, choose "
                "JSON/TXT and select only Like List/Favor"
                "ite Videos. Export layouts vary; preview"
                " "
                "before import.\nBilibili / other: paste a"
                " prepared list of full video URLs, or CS"
                "V/JSON "
                "with url,title,collection,saved_at,trans"
                "cript,description,summary,annotation. No"
                " "
                "automatic account integration. Short lin"
                "ks must be expanded in your own browser."
                "\n"
                "Notes: choose a prepared folder, not an "
                "entire private vault. Markdown sections "
                "'Transcript', 'Description', 'Summary', "
                "'User annotation' preserve origins. Ordi"
                "nary "
                "prose is an existing summary with unknow"
                "n authorship, never automatically your b"
                "elief.\n"
                "Limits: 1,000 unique videos, 2 MB/file, "
                "16 MB/selection; excerpts up to 2,000 ch"
                "aracters "
                "per material sent to AI. Hidden folders "
                "and linked files are blocked. No ZIP ext"
                "raction.\n"
                "Public title lookup is optional and supp"
                "orts YouTube/TikTok oEmbed only. No auto"
                "matic "
                "transcript access, cookies, private mess"
                "ages, browser history or paid platform A"
                "PIs.",
                "YouTube：使用 Google Takeout 中选定的 YouTube 播"
                "放列表 CSV；单独播放列表链接不会自动展开。\n"
                "TikTok：申请下载数据，选择 JSON／TXT，仅导入 Like List／"
                "Favorite Videos。导出结构可能变化，先预览。\n"
                "Bilibili／其他：粘贴准备好的完整视频链接，或提供 CSV／JSON 字段 "
                "url,title,collection,saved_at,transcript"
                ",description,summary,annotation。不自动连接账户；"
                "短链接须先在自己的浏览器中展开。\n笔记：选择准备好的文件夹，不要选择整个私人库。"
                "Markdown 使用"
                "“字幕”“描述”“摘要”“我的备注”标题区分来源；普通正文视作作者未核实的已有摘"
                "要，不自动当作你的观点。\n"
                "限制：1,000 个不同视频，每文件 2 MB、每次选择 16 MB；每份材料最"
                "多发送 2,000 字给 AI。"
                "隐藏文件夹和链接文件不会导入，不解压 ZIP。\n公开标题查询可选，仅支持 You"
                "Tube／TikTok oEmbed；"
                "不自动取得字幕、不使用 cookies、不读取私信或浏览器历史、不调用付费平台 API。",
            ),
        )
