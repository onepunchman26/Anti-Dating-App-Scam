from anti_dating_scam.models.conversation import (
    JournalSummaryRequest,
    JournalSummaryResponse,
)
from anti_dating_scam.models.risk import RiskAnalysisRequest, RiskLevel, SignalSeverity
from anti_dating_scam.services.consent_manager import ConsentManager
from anti_dating_scam.services.scam_risk_analyzer import ScamRiskAnalyzer


class JournalSummarizer:
    def __init__(
        self,
        consent_manager: ConsentManager | None = None,
        analyzer: ScamRiskAnalyzer | None = None,
    ) -> None:
        self.consent_manager = consent_manager or ConsentManager()
        self.analyzer = analyzer or ScamRiskAnalyzer(consent_manager=self.consent_manager)

    def summarize(self, request: JournalSummaryRequest) -> JournalSummaryResponse:
        self.consent_manager.ensure_confirmed(request.consent_confirmed)
        if not request.entries:
            return JournalSummaryResponse(
                overall_risk_level=RiskLevel.UNKNOWN,
                pattern_summary=["No journal entries were provided."],
                recurring_risk_signals=[],
                positive_trust_indicators=[],
                uncertainty=["A pattern cannot be inferred without entries."],
                recommended_next_steps=[
                    "Add consented, relevant events before drawing conclusions."
                ],
            )

        combined = "\n".join(entry.event_text for entry in request.entries)
        analysis = self.analyzer.analyze(
            RiskAnalysisRequest(
                conversation_text=combined,
                consent_confirmed=True,
            )
        )
        positives = self._positive_indicators(combined)
        recurring = [
            signal
            for signal in analysis.risk_signals
            if signal.severity in {SignalSeverity.MEDIUM, SignalSeverity.HIGH}
        ]

        return JournalSummaryResponse(
            overall_risk_level=analysis.risk_level,
            pattern_summary=self._pattern_summary(analysis.risk_level, recurring, positives),
            recurring_risk_signals=recurring,
            positive_trust_indicators=positives,
            uncertainty=[
                "Journal summaries depend on what the user chose to log.",
                "Patterns should support reflection, not certainty about another person's intent.",
            ],
            recommended_next_steps=analysis.recommended_next_steps,
        )

    def _positive_indicators(self, text: str) -> list[str]:
        lowered = text.lower()
        indicators: list[str] = []
        if "respected boundary" in lowered or "respected my boundary" in lowered:
            indicators.append("Respected a stated boundary.")
        if "handled disagreement calmly" in lowered or "calmly" in lowered:
            indicators.append("Handled disagreement calmly.")
        if "consistent" in lowered and "inconsistent" not in lowered:
            indicators.append("Showed repeated consistency.")
        return indicators

    def _pattern_summary(
        self, risk_level: RiskLevel, recurring: list, positives: list[str]
    ) -> list[str]:
        if risk_level == RiskLevel.UNKNOWN:
            return ["The entries do not provide enough information for a confident pattern."]
        summary = [f"Overall journal pattern is currently assessed as {risk_level.value} risk."]
        if recurring:
            summary.append("Recurring risk signals deserve slower trust progression.")
        if positives:
            summary.append(
                "Positive indicators are present, but they do not cancel out safety concerns."
            )
        return summary
