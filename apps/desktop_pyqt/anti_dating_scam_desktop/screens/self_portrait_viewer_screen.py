import json

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.services.active_reports import ActiveReportError, LegacyReviewOnlyError
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.report_review_dialog import ReportReviewDialog, correction_notice
from anti_dating_scam_desktop.report_selection_dialog import (
    ReportSelectionDialog,
    active_report_error,
    active_report_label,
    review_only_label,
    show_verified_report,
)
from anti_dating_scam_desktop.self_portrait_html import render_self_portrait_html
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader

_EMPTY_MARKDOWN = bi(
    "## No self-portrait yet\n\n"
    "Use **Understand Yourself** to prepare the request, have your agent write it into "
    "`reports/`, then press **Refresh**.",
    "## 尚无自我画像\n\n"
    "请使用「了解你自己」生成请求，让你的代理把它写入 `reports/`，"
    "然后点击「刷新」。",
)


class SelfPortraitViewerScreen(QWidget):
    """Show the self-portrait the agent wrote.

    Primary view is a polished, offline HTML report generated from
    ``reports/self_portrait.json`` (opens in the browser). The in-app Markdown of
    ``reports/self_portrait.md`` is kept as a lightweight fallback/preview.
    """

    def __init__(self, state, profile_store, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(14)
        layout.addWidget(
            StepHeader(
                bi("My Self-Portrait", "我的自我画像"),
                bi(
                    "A reflective mirror from your own words — not a diagnosis or a score.",
                    "一面来自你自己话语的反思之镜——不是诊断，也不是评分。",
                ),
            )
        )

        self.visual_button = PrimaryButton(bi("Open Visual Report", "打开可视化报告"))
        self.visual_button.clicked.connect(self._open_current_report)
        layout.addWidget(self.visual_button)

        self.selection_button = SecondaryButton(bi("Select active report", "选择当前报告"))
        self.selection_button.clicked.connect(self._select_report)
        layout.addWidget(self.selection_button)
        self.review_button = SecondaryButton(bi(
            "Review original evidence & corrections", "复核原报告证据与更正"
        ))
        self.review_button.clicked.connect(self._review_report)
        layout.addWidget(self.review_button)
        self.legacy_button = SecondaryButton(bi("Review legacy files", "复核旧版文件"))
        self.legacy_button.clicked.connect(self._review_legacy)
        layout.addWidget(self.legacy_button)
        self.correction_banner = QLabel()
        self.correction_banner.setTextFormat(Qt.TextFormat.PlainText)
        self.correction_banner.setWordWrap(True)
        self.correction_banner.hide()
        layout.addWidget(self.correction_banner)

        self.path_label = QLabel()
        self.path_label.setTextFormat(Qt.TextFormat.PlainText)
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        layout.addWidget(self.viewer)

        actions = QHBoxLayout()
        refresh = SecondaryButton(bi("Refresh", "刷新"))
        refresh.clicked.connect(self.on_enter)
        self.detailed_button = SecondaryButton(bi("Open Detailed Report", "打开详细报告"))
        self.detailed_button.clicked.connect(self._open_detailed)
        open_folder = SecondaryButton(bi("Open Reports Folder", "打开报告文件夹"))
        open_folder.clicked.connect(self._open_reports)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        for button in (refresh, self.detailed_button, open_folder, back):
            actions.addWidget(button)
        layout.addLayout(actions)

    def on_enter(self) -> None:
        notice = correction_notice(self.profile_store.base_dir, "self_portrait")
        self.correction_banner.setText(notice)
        self.correction_banner.setVisible(bool(notice))
        try:
            active = self.profile_store.read_active_report("self_portrait")
        except LegacyReviewOnlyError:
            self.viewer.clear()
            self.visual_button.setEnabled(False)
            self.detailed_button.setEnabled(False)
            self.path_label.setText(review_only_label())
            return
        except (ActiveReportError, OSError, ValueError):
            self._show_active_error()
            return
        if active is not None:
            self.path_label.setText(active_report_label(active))
            self.viewer.setOpenExternalLinks(False)
            self.viewer.setOpenLinks(False)
            self.viewer.setPlainText(active.markdown)
            self.visual_button.setText(bi("Open selected report", "打开已选报告"))
            self.visual_button.setEnabled(True)
            self.detailed_button.setText(bi("Open selected detailed report", "打开已选详细报告"))
            self.detailed_button.setEnabled(True)
            return
        self.visual_button.setText(bi("Open Visual Report", "打开可视化报告"))
        self.detailed_button.setText(bi("Open Detailed Report", "打开详细报告"))
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setOpenLinks(True)
        has_json = self.profile_store.self_portrait_json_path.exists()
        self.visual_button.setEnabled(has_json)
        self.detailed_button.setEnabled(self.profile_store.self_portrait_detailed_path.exists())

        markdown = self.profile_store.load_original_self_portrait()
        if markdown is None and not has_json:
            self.path_label.setText(
                f"{bi('Expected at', '预期位置')}: {self.profile_store.reports_dir}"
            )
            self.viewer.setMarkdown(_EMPTY_MARKDOWN)
            return
        if has_json:
            self.path_label.setText(
                bi(
                    'Click "Open Visual Report" for the full visual version.',
                    "点击「打开可视化报告」查看完整可视化版本。",
                )
            )
        else:
            self.path_label.setText(
                f"{bi('Showing', '正在显示')}: {self.profile_store.self_portrait_path}"
            )
        # In-app preview: prefer the Markdown narrative; else a note pointing at HTML.
        self.viewer.setMarkdown(
            markdown
            or bi(
                "## Visual report ready\n\nOpen it with the button above.",
                "## 可视化报告已就绪\n\n请用上方按钮打开。",
            )
        )

    def _show_active_error(self) -> None:
        self.viewer.clear()
        self.visual_button.setEnabled(False)
        self.detailed_button.setEnabled(False)
        self.path_label.setText(active_report_error())

    def _select_report(self) -> None:
        ReportSelectionDialog(self.profile_store.base_dir, "self_portrait", self).exec()
        self.on_enter()

    def _open_current_report(self) -> None:
        self._open_visual()

    def _open_visual(self) -> None:
        try:
            active = self.profile_store.read_active_report("self_portrait")
            data = (
                None if active is not None
                else self.profile_store.load_original_self_portrait_json()
            )
        except (ActiveReportError, OSError, ValueError):
            self._show_active_error()
            return
        if active is not None:
            show_verified_report(
                self, active_report_label(active), active.detailed_markdown or active.markdown,
            )
            return
        if not data:
            QMessageBox.information(
                self,
                bi("No structured report", "没有结构化报告"),
                bi(
                    "The visual report is built from reports/self_portrait.json, which "
                    "isn't there yet. Ask your agent to write it first.",
                    "可视化报告基于 reports/self_portrait.json 生成，但该文件尚不存在。"
                    "请先让你的代理生成它。",
                ),
            )
            return
        try:
            companion = self.profile_store.self_portrait_json_path.with_name(
                "self_portrait_localization.json"
            )
            localized_text = None
            if companion.is_file():
                if companion.stat().st_size > 512_000:
                    raise ValueError(bi("Translation file is too large.", "译文文件过大。"))
                payload = json.loads(companion.read_text(encoding="utf-8"))
                if not isinstance(payload, dict) or payload.get("schema_version") != "0.1":
                    raise ValueError(bi("Unsupported translation format.", "不支持此译文格式。"))
                localized_text = payload["localized_text"]
                if not isinstance(localized_text, list):
                    raise ValueError(bi("Invalid translation map.", "双语对照无效。"))
            html = render_self_portrait_html(data, localized_text)
            path = self.profile_store.write_self_portrait_html(html)
        except Exception:  # raw parser errors can contain untrusted report content
            QMessageBox.warning(
                self,
                bi("Could not render report", "无法生成报告"),
                bi(
                    "The report or its translation file is invalid. Regenerate the report.",
                    "报告或对应的译文文件无效，请重新生成报告。",
                ),
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_detailed(self) -> None:
        try:
            active = self.profile_store.read_active_report("self_portrait")
        except (ActiveReportError, OSError, ValueError):
            self._show_active_error()
            return
        if active is not None:
            show_verified_report(
                self, active_report_label(active), active.detailed_markdown or active.markdown,
            )
            return
        path = self.profile_store.self_portrait_detailed_path
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _review_report(self) -> None:
        ReportReviewDialog(self.profile_store.base_dir, "self_portrait", self).exec()
        self.on_enter()

    def _review_legacy(self) -> None:
        from anti_dating_scam_desktop.legacy_report_dialog import LegacyReportDialog

        LegacyReportDialog(self.profile_store.base_dir, "self_portrait", self).exec()

    def _open_reports(self) -> None:
        reports_dir = self.profile_store.get_reports_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(reports_dir)))
