import hashlib
from datetime import UTC, datetime
from typing import Any

from anti_dating_scam import __version__
from anti_dating_scam.reports.export_markdown import risk_report_to_markdown
from anti_dating_scam.reports.schema_validator import validate_document

POLICY_VERSION = "0.1-local-first"
RISK_PROMPT_MARKER = "AI-SlowMatch rule-based local MVP risk analysis"


class ReportGenerator:
    def generate_risk_report(
        self,
        *,
        conversation_text: str,
        risk_analysis: dict[str, Any],
        provider_name: str = "mock",
        model_name: str = "local-rule-based-mvp",
    ) -> dict[str, Any]:
        report = {
            "report_type": "risk_report",
            "schema_version": "0.1",
            "app_version": __version__,
            "policy_version": POLICY_VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "input_hash": self._sha256(conversation_text),
            "prompt_hash": self._sha256(RISK_PROMPT_MARKER),
            "provider_name": provider_name,
            "model_name": model_name,
            "risk_level": risk_analysis.get("risk_level", "UNKNOWN"),
            "risk_signals": risk_analysis.get("risk_signals", []),
            "uncertainty_notes": risk_analysis.get("uncertainty_notes", []),
            "recommended_next_steps": risk_analysis.get("recommended_next_steps", []),
            "safety_disclaimer": risk_analysis.get(
                "safety_disclaimer",
                (
                    "This is a risk-support tool, not a legal, criminal, psychological, "
                    "or medical judgment."
                ),
            ),
        }
        validate_document(report, "risk_report.schema.json")
        return report

    def to_markdown(self, report: dict[str, Any]) -> str:
        return risk_report_to_markdown(report)

    def _sha256(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
