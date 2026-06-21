import re
from dataclasses import dataclass

from anti_dating_scam.ai.mock_provider import MockAIProvider
from anti_dating_scam.ai.output_schemas import RISK_OUTPUT_SCHEMA_NAME
from anti_dating_scam.ai.prompts import RISK_ANALYSIS_SYSTEM_PROMPT
from anti_dating_scam.ai.provider import LLMClient
from anti_dating_scam.core.safety_policy import SafetyPolicy
from anti_dating_scam.models.risk import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    RiskLevel,
    RiskSignal,
    SignalSeverity,
)
from anti_dating_scam.services.consent_manager import ConsentManager
from anti_dating_scam.services.explanation_generator import ExplanationGenerator


@dataclass(frozen=True)
class RiskRule:
    name: str
    severity: SignalSeverity
    patterns: tuple[re.Pattern[str], ...]
    evidence: str
    explanation: str


def _patterns(*values: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(value, re.IGNORECASE) for value in values)


RISK_RULES: tuple[RiskRule, ...] = (
    RiskRule(
        name="money_or_payment_request",
        severity=SignalSeverity.HIGH,
        patterns=_patterns(
            r"\bsend (me )?(money|cash)\b",
            r"\bgift cards?\b",
            r"\bwire transfer\b",
            r"\bbank (details|account|login)\b",
            r"\bcrypto\b",
            r"\bbitcoin\b",
            r"\bpay .*fee\b",
        ),
        evidence="The conversation includes a request or prompt involving money or payment.",
        explanation=(
            "Requests for money, gift cards, crypto, wire transfers, or bank details are "
            "high-risk signals in online-only romantic contact."
        ),
    ),
    RiskRule(
        name="rapid_emotional_escalation",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\bi love you\b",
            r"\bsoulmate\b",
            r"\bmy future (wife|husband|spouse)\b",
            r"\bdestiny brought us\b",
            r"\bafter only\b",
            r"\bcan't live without you\b",
        ),
        evidence=(
            "The conversation shows intense emotional commitment before enough shared "
            "context exists."
        ),
        explanation="Fast emotional escalation can be a scam pattern, though it is not proof.",
    ),
    RiskRule(
        name="refusal_to_verify_or_meet",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\b(can'?t|cannot|won'?t|refuse) (video|video call|call|meet)\b",
            r"\bno video call\b",
            r"\bmy camera (is )?broken\b",
            r"\bdo not ask me to verify\b",
        ),
        evidence="The conversation includes avoidance of basic identity verification or meeting.",
        explanation=(
            "Repeated refusal to use safe, consent-based verification can increase uncertainty."
        ),
    ),
    RiskRule(
        name="inconsistent_biography",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\binconsistent (story|stories|biography|details)\b",
            r"\bstory changed\b",
            r"\bdifferent (name|age|job|location)\b",
            r"\bcontradict(s|ed)?\b",
        ),
        evidence="The submitted text or notes mention inconsistent personal details.",
        explanation=(
            "Inconsistent biography can be a risk signal, but it may also reflect missing context."
        ),
    ),
    RiskRule(
        name="pressure_to_move_off_platform",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\bmove to whatsapp\b",
            r"\btelegram\b",
            r"\bsignal app\b",
            r"\bleave this app\b",
            r"\boff[- ]platform\b",
            r"\btext me immediately\b",
        ),
        evidence="The conversation pressures a move away from the original platform.",
        explanation=(
            "Immediate off-platform pressure can reduce reporting options and increase "
            "information asymmetry."
        ),
    ),
    RiskRule(
        name="investment_or_pig_butchering_pattern",
        severity=SignalSeverity.HIGH,
        patterns=_patterns(
            r"\binvest(ment|ing)?\b",
            r"\btrading platform\b",
            r"\bforex\b",
            r"\bguaranteed profit\b",
            r"\bdouble your money\b",
            r"\bliquidity mining\b",
        ),
        evidence="The conversation links romance or intimacy to investment or trading.",
        explanation="Romance-linked investment opportunities are a high-risk scam pattern.",
    ),
    RiskRule(
        name="emergency_story",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\bemergency\b",
            r"\bhospital\b",
            r"\bmedical bill\b",
            r"\bstranded\b",
            r"\bcustoms fee\b",
            r"\bvisa fee\b",
            r"\bfamily crisis\b",
        ),
        evidence="The conversation includes an urgent hardship or emergency story.",
        explanation=(
            "Emergency stories can be legitimate, but they are often used to accelerate "
            "money requests."
        ),
    ),
    RiskRule(
        name="isolation_pressure",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\bdon'?t tell (your )?(friends|family)\b",
            r"\bkeep this between us\b",
            r"\byour friends don'?t understand\b",
            r"\bonly trust me\b",
        ),
        evidence="The conversation discourages outside perspective or support.",
        explanation="Isolation pressure can weaken a user's ability to assess risk calmly.",
    ),
    RiskRule(
        name="guilt_or_fear_pressure",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\bif you loved me\b",
            r"\bprove your love\b",
            r"\burgent\b",
            r"\bright now\b",
            r"\bdeadline\b",
            r"\byou are hurting me\b",
        ),
        evidence="The conversation uses guilt, fear, or urgency to pressure action.",
        explanation="Pressure tactics can reduce autonomy and make careful verification harder.",
    ),
    RiskRule(
        name="private_images_or_sensitive_information_request",
        severity=SignalSeverity.HIGH,
        patterns=_patterns(
            r"\bnudes?\b",
            r"\bprivate photos?\b",
            r"\bpassport\b",
            r"\bsocial security\b",
            r"\bssn\b",
            r"\bdriver'?s license\b",
            r"\bhome address\b",
            r"\bbank login\b",
        ),
        evidence=(
            "The conversation requests private images, identity documents, or sensitive "
            "information."
        ),
        explanation=(
            "Requests for private images or sensitive information create safety, privacy, "
            "and coercion risk."
        ),
    ),
    RiskRule(
        name="repeated_boundary_violation",
        severity=SignalSeverity.MEDIUM,
        patterns=_patterns(
            r"\bignored my boundary\b",
            r"\bkept asking\b",
            r"\bwould not take no\b",
            r"\bpressured me\b",
            r"\brepeated boundary\b",
        ),
        evidence="The submitted text or notes describe repeated pressure after a boundary was set.",
        explanation=(
            "Repeated boundary violations are a trust-ladder warning even when no scam is proven."
        ),
    ),
)


class ScamRiskAnalyzer:
    def __init__(
        self,
        ai_provider: LLMClient | None = None,
        consent_manager: ConsentManager | None = None,
        safety_policy: SafetyPolicy | None = None,
    ) -> None:
        self.ai_provider = ai_provider or MockAIProvider()
        self.consent_manager = consent_manager or ConsentManager()
        self.safety_policy = safety_policy or SafetyPolicy()
        self.explanations = ExplanationGenerator()

    def analyze(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        self.consent_manager.ensure_confirmed(request.consent_confirmed)
        combined_text = self._combined_text(request)
        self.safety_policy.ensure_allowed(combined_text)

        signals = self._detect_signals(combined_text)
        risk_level = self._score(signals, request.conversation_text)
        recommended_next_steps = self._recommend_next_steps(risk_level)
        uncertainty = self._uncertainty_notes(request, signals)

        self.ai_provider.generate_structured(
            prompt=f"{RISK_ANALYSIS_SYSTEM_PROMPT}\n\n{combined_text}",
            schema_name=RISK_OUTPUT_SCHEMA_NAME,
        )

        return RiskAnalysisResponse(
            risk_level=risk_level,
            risk_signals=signals,
            uncertainty=uncertainty,
            recommended_next_steps=recommended_next_steps,
            do_not_conclude=[
                (
                    "Do not conclude that the other person is a criminal or a bad person "
                    "from this output alone."
                ),
                "Do not use this analysis to harass, expose, threaten, or entrap anyone.",
            ],
        )

    def _combined_text(self, request: RiskAnalysisRequest) -> str:
        parts = [request.conversation_text]
        if request.user_notes:
            parts.append(request.user_notes)
        parts.extend(request.event_log)
        return "\n".join(parts)

    def _detect_signals(self, text: str) -> list[RiskSignal]:
        detected: list[RiskSignal] = []
        for rule in RISK_RULES:
            if any(pattern.search(text) for pattern in rule.patterns):
                detected.append(
                    RiskSignal(
                        name=rule.name,
                        severity=rule.severity,
                        evidence=rule.evidence,
                        explanation=rule.explanation,
                    )
                )
        return detected

    def _score(self, signals: list[RiskSignal], conversation_text: str) -> RiskLevel:
        if any(signal.severity == SignalSeverity.HIGH for signal in signals):
            return RiskLevel.HIGH
        medium_count = sum(signal.severity == SignalSeverity.MEDIUM for signal in signals)
        if medium_count >= 3:
            return RiskLevel.HIGH
        if medium_count > 0:
            return RiskLevel.MEDIUM
        if len(conversation_text.strip()) < 60:
            return RiskLevel.UNKNOWN
        return RiskLevel.LOW

    def _recommend_next_steps(self, risk_level: RiskLevel) -> list[str]:
        baseline = [
            (
                "Do not send money, crypto, gift cards, bank details, private images, "
                "or identity documents."
            ),
            "Verify identity through safe, consent-based methods.",
            "Keep trusted friends, family, or platform safety tools available when appropriate.",
        ]
        if risk_level == RiskLevel.HIGH:
            return [
                "Stop financial interaction immediately.",
                "Step back from the relationship until concerns are resolved.",
                (
                    "Use platform reporting or professional support if there are threats, "
                    "extortion, or fraud attempts."
                ),
                *baseline,
            ]
        if risk_level == RiskLevel.MEDIUM:
            return [
                "Consider slowing down the interaction.",
                "Gather more information before escalating trust.",
                *baseline,
            ]
        if risk_level == RiskLevel.UNKNOWN:
            return [
                "Insufficient information is available for a confident risk assessment.",
                "Stay at a low-pressure conversation stage.",
                *baseline,
            ]
        return [
            "Continue slowly and keep boundaries explicit.",
            "Do not treat low detected risk as proof of safety.",
            *baseline,
        ]

    def _uncertainty_notes(
        self, request: RiskAnalysisRequest, signals: list[RiskSignal]
    ) -> list[str]:
        notes = [
            "This analysis is based only on the submitted text.",
            "Risk signals are not proof of intent, identity, or wrongdoing.",
        ]
        if not request.user_notes:
            notes.append("No user notes were provided, so context may be missing.")
        if not request.event_log:
            notes.append("No longer-term event log was provided.")
        if not signals:
            notes.append(
                "No listed risk pattern was detected, but absence of evidence is not "
                "proof of safety."
            )
        return notes
