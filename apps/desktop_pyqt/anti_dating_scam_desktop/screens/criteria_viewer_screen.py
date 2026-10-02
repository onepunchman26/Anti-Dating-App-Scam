from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
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
)
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader

_EMPTY_MARKDOWN = bi(
    "## No criteria report yet\n\n"
    'Use **Discover Your Real Criteria** to prepare the request, complete the '
    "interview with your agent, then press **Refresh**.",
    "## 尚无择偶标准报告\n\n"
    "请使用「发现你的真实择偶标准」生成请求，与你的代理完成访谈，然后点击「刷新」。",
)


class CriteriaViewerScreen(QWidget):
    """Render the stated-vs-revealed criteria report the agent wrote."""

    def __init__(self, state, profile_store, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(14)
        layout.addWidget(
            StepHeader(
                bi("My Mate-Selection Criteria", "我的择偶标准"),
                bi(
                    "Stated vs revealed — built from your interview and your choices, "
                    "not just your words.",
                    "口头标准 vs 实际标准——基于你的访谈与选择，而不只是你的说法。",
                ),
            )
        )
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
        open_folder = SecondaryButton(bi("Open Reports Folder", "打开报告文件夹"))
        open_folder.clicked.connect(self._open_reports)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        for button in (refresh, open_folder, back):
            actions.addWidget(button)
        layout.addLayout(actions)

    def on_enter(self) -> None:
        notice = correction_notice(self.profile_store.base_dir, "mate_criteria")
        self.correction_banner.setText(notice)
        self.correction_banner.setVisible(bool(notice))
        try:
            active = self.profile_store.read_active_report("mate_criteria")
        except LegacyReviewOnlyError:
            self.viewer.clear()
            self.path_label.setText(review_only_label())
            return
        except (ActiveReportError, OSError, ValueError):
            self.viewer.clear()
            self.path_label.setText(active_report_error())
            return
        if active is not None:
            self.path_label.setText(active_report_label(active))
            self.viewer.setOpenExternalLinks(False)
            self.viewer.setOpenLinks(False)
            self.viewer.setPlainText(active.markdown)
            return
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setOpenLinks(True)
        markdown = self.profile_store.load_original_mate_criteria()
        if markdown is None:
            self.path_label.setText(
                f"{bi('Expected at', '预期位置')}: {self.profile_store.mate_criteria_path}"
            )
            self.viewer.setMarkdown(_EMPTY_MARKDOWN)
            return
        self.path_label.setText(
            f"{bi('Showing', '正在显示')}: {self.profile_store.mate_criteria_path}"
        )
        self.viewer.setMarkdown(markdown)

    def _open_reports(self) -> None:
        reports_dir = self.profile_store.get_reports_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(reports_dir)))

    def _select_report(self) -> None:
        ReportSelectionDialog(self.profile_store.base_dir, "mate_criteria", self).exec()
        self.on_enter()

    def _review_report(self) -> None:
        ReportReviewDialog(self.profile_store.base_dir, "mate_criteria", self).exec()
        self.on_enter()

    def _review_legacy(self) -> None:
        from anti_dating_scam_desktop.legacy_report_dialog import LegacyReportDialog

        LegacyReportDialog(self.profile_store.base_dir, "mate_criteria", self).exec()
