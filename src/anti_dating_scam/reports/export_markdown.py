from typing import Any

from anti_dating_scam.reports.verifier import SIGNATURE_DISCLAIMER


def risk_report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AI-SlowMatch Risk Report",
        "",
        f"- Risk level: `{report.get('risk_level', 'UNKNOWN')}`",
        f"- Provider: `{report.get('provider_name', 'unknown')}`",
        f"- Model: `{report.get('model_name', 'unknown')}`",
        f"- Created at: `{report.get('created_at', 'unknown')}`",
        "",
        "## Risk Signals",
    ]

    signals = report.get("risk_signals", [])
    if signals:
        for signal in signals:
            lines.append(
                "- "
                f"{signal.get('name', 'unknown')} "
                f"({signal.get('severity', 'unknown')}): "
                f"{signal.get('explanation', '')}"
            )
    else:
        lines.append("- No listed risk signal detected.")

    lines.extend(["", "## Uncertainty Notes"])
    for note in report.get("uncertainty_notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Recommended Next Steps"])
    for step in report.get("recommended_next_steps", []):
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety Disclaimer",
            report.get("safety_disclaimer", ""),
            "",
            "## Signature Disclaimer",
            SIGNATURE_DISCLAIMER,
        ]
    )
    return "\n".join(lines).strip() + "\n"
