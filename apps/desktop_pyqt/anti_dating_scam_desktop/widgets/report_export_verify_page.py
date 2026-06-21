import json
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.engine.report_generator import ReportGenerator
from anti_dating_scam.reports.signer import sign_report
from anti_dating_scam.reports.verifier import SIGNATURE_DISCLAIMER, verify_report


class ReportExportVerifyPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.report_generator = ReportGenerator()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Report Export / Verify</h2>"))
        disclaimer = QLabel(SIGNATURE_DISCLAIMER)
        disclaimer.setWordWrap(True)
        layout.addWidget(disclaimer)

        buttons = QHBoxLayout()
        for label, handler in [
            ("Export Current Report JSON", self._export_json),
            ("Export Current Report Markdown", self._export_markdown),
            ("Sign Current Report Locally", self._sign_current_report),
            ("Load And Verify Report", self._load_and_verify),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def _current_report(self) -> dict | None:
        return self.state.get("signed_report") or self.state.get("risk_report")

    def _export_json(self) -> None:
        report = self._current_report()
        if not report:
            QMessageBox.information(self, "No report", "Run conversation risk analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export report JSON", "", "JSON (*.json)")
        if path:
            Path(path).write_text(
                json.dumps(report, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _export_markdown(self) -> None:
        report = self._current_report()
        if not report:
            QMessageBox.information(self, "No report", "Run conversation risk analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export report Markdown", "", "Markdown (*.md)")
        if path:
            Path(path).write_text(self.report_generator.to_markdown(report), encoding="utf-8")

    def _sign_current_report(self) -> None:
        report = self.state.get("risk_report")
        if not report:
            QMessageBox.information(self, "No report", "Run conversation risk analysis first.")
            return
        signed = sign_report(report)
        self.state["signed_report"] = signed
        self.output.setPlainText(json.dumps(signed, indent=2, ensure_ascii=False))

    def _load_and_verify(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load report JSON", "", "JSON (*.json)")
        if not path:
            return
        try:
            report = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "Could not load report", str(exc))
            return
        result = verify_report(report, known_signers={"local_hash_mvp"})
        self.output.setPlainText(json.dumps(result, indent=2, ensure_ascii=False))
