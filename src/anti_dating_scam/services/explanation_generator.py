from anti_dating_scam.models.risk import RiskLevel, RiskSignal


class ExplanationGenerator:
    def risk_summary(self, risk_level: RiskLevel, signals: list[RiskSignal]) -> str:
        if not signals:
            if risk_level == RiskLevel.LOW:
                return (
                    "No major scam signals were detected in the submitted text. "
                    "This does not prove safety, but it supports continuing slowly."
                )
            return (
                "There is insufficient information to assess risk confidently. "
                "Consider slowing down and gathering more context."
            )

        signal_names = ", ".join(signal.name for signal in signals[:3])
        return (
            f"Risk signal detected: {signal_names}. This does not prove malicious intent, "
            "but it is enough to recommend caution, slower interaction, and safe verification."
        )

    def safe_tone_note(self) -> str:
        return (
            "Use non-accusatory language: risk signal detected, insufficient information, "
            "consider slowing down, do not send money, and verify identity through safe, "
            "consent-based methods."
        )
