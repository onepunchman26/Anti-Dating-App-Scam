"""Render bilingual human reports only from validated canonical artifacts.

Exact mapping coverage and language characters are structural checks, not proof
of translation fidelity or of the underlying claims. Evidence remains untranslated.
This module performs no provider calls, filesystem operations, or UI work.
"""

from __future__ import annotations

import html
import re
from typing import Any

from anti_dating_scam.reports.local_artifacts import (
    ArtifactValidationError,
    validate_local_artifact,
)

_HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002fa1f]")
_LATIN = re.compile(r"[A-Za-z]")
_MARKDOWN = re.compile(r"([\\`*_{}\[\]()#+\-.!|:/@])")
_ERROR = (
    "Report localization is incomplete, inconsistent, or invalid; no report was rendered. "
    "/ 报告的双语映射不完整、不一致或无效，未生成报告。"
)

_TOPICS = {
    "values": ("Values", "价值观"),
    "wants": ("Wants", "个人期待"),
    "communication": ("Communication", "沟通方式"),
    "boundaries": ("Boundaries", "个人边界"),
    "market_stance": ("Relationship preferences", "关系偏好"),
    "presentation": ("Self-presentation", "自我呈现"),
    "pattern": ("Pattern", "行为模式"),
}
_TYPES = {
    "observation": ("Observation — check against the quotation", "观察——请对照原文核实"),
    "inference": (
        "Inference — an interpretation, not a direct fact",
        "推断——属于解释，并非直接事实",
    ),
    "speculation": (
        "Speculation — a possibility requiring verification",
        "猜测——属于尚待核实的可能性",
    ),
}
_CONFIDENCE = {
    "low": ("Low — limited support in the submitted material", "低——提交材料中的支持有限"),
    "medium": (
        "Medium — some support, with remaining uncertainty",
        "中——有一定支持，仍存在不确定性",
    ),
    "high": (
        "High — stronger support in this material, not proof",
        "高——在这些材料中支持较强，并非证明",
    ),
}
_TENSIONS = {
    "stated_vs_revealed": ("Stated and expressed preferences", "陈述与表现出的偏好"),
    "front_vs_back": ("Presentation across contexts", "不同情境中的呈现"),
    "internal_logic": ("Internal consistency", "内部一致性"),
    "double_standard": ("Possible difference in standards", "可能的标准差异"),
    "temporal_drift": ("Change over time", "随时间发生的变化"),
    "embellishment": ("Possible embellishment to clarify", "需要澄清的可能修饰"),
}


def _checked_canonical(kind: str, canonical: Any) -> dict:
    expected = {
        "self_portrait": {"report": "self_portrait"},
        "mate_criteria": {"criteria": "mate_criteria", "ideal_profiles": "ideal_profiles"},
    }.get(kind)
    if expected is None or not isinstance(canonical, dict) or set(canonical) != set(expected):
        raise ArtifactValidationError(_ERROR)
    return {
        key: validate_local_artifact(canonical[key], contract) for key, contract in expected.items()
    }


def _sources(kind: str, canonical: dict) -> dict[str, str]:
    sources: dict[str, str] = {}

    def strings(values: list[str], prefix: str) -> None:
        for index, value in enumerate(values):
            sources[f"{prefix}/{index}"] = value

    def claims(values: list[dict], prefix: str) -> None:
        for index, claim in enumerate(values):
            sources[f"{prefix}/{index}/claim"] = claim["claim"]

    if kind == "self_portrait":
        report = canonical["report"]
        for field in ("covered", "not_covered"):
            strings(report["data_coverage"][field], f"/report/data_coverage/{field}")
        claims(report["claims"], "/report/claims")
        for index, finding in enumerate(report["consistency_findings"]):
            for field in (
                "stated",
                "contradicting",
                "framing",
                "clarifying_question",
                "alt_benign_explanation",
            ):
                sources[f"/report/consistency_findings/{index}/{field}"] = finding[field]
        for field in ("open_questions", "caveats"):
            strings(report[field], f"/report/{field}")
    else:
        criteria = canonical["criteria"]
        for field in ("stated", "revealed"):
            claims(criteria[field], f"/criteria/{field}")
        for field in ("open_questions", "caveats"):
            strings(criteria[field], f"/criteria/{field}")
        profiles = canonical["ideal_profiles"]
        for index, candidate in enumerate(profiles["candidates"]):
            for field in ("description", "choice_reason", "uncertainty_notes"):
                if candidate[field] is not None:
                    sources[f"/ideal_profiles/candidates/{index}/{field}"] = candidate[field]
        strings(profiles["caveats"], "/ideal_profiles/caveats")
    return sources


def required_localization_sources(kind: str, canonical: dict) -> dict[str, str]:
    """Return the exact JSON pointer/source pairs needing localization.

    Keys, enum identifiers, source IDs, timestamps, and evidence quotations are
    not narrative translations. Optional headline/summary fields are never rendered.
    """
    return _sources(kind, _checked_canonical(kind, canonical))


def validate_localization(kind: str, canonical: dict, entries: Any) -> dict[str, dict[str, str]]:
    """Require exact coverage and source-language preservation without echoing data."""
    required = required_localization_sources(kind, canonical)
    if not isinstance(entries, list) or len(entries) != len(required):
        raise ArtifactValidationError(_ERROR)
    result: dict[str, dict[str, str]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "source", "en", "zh"}:
            raise ArtifactValidationError(_ERROR)
        if any(not isinstance(value, str) or not value.strip() for value in entry.values()):
            raise ArtifactValidationError(_ERROR)
        if any(len(value) > 8_000 for value in entry.values()):
            raise ArtifactValidationError(_ERROR)
        path, source, en, zh = (entry[key] for key in ("path", "source", "en", "zh"))
        if path in result or path not in required or source != required[path]:
            raise ArtifactValidationError(_ERROR)
        if not _LATIN.search(en) or len(_HAN.findall(zh)) < 2 or en == zh:
            raise ArtifactValidationError(_ERROR)
        source_has_han = bool(_HAN.search(source))
        if (source_has_han and zh != source) or (
            not source_has_han and _LATIN.search(source) and en != source
        ):
            raise ArtifactValidationError(_ERROR)
        result[path] = {"en": en, "zh": zh}
    if set(result) != set(required):
        raise ArtifactValidationError(_ERROR)
    return result


def _escape(value: str) -> str:
    # Escape both raw HTML and Markdown so a narrative/quote cannot create links,
    # headings, images, or executable HTML in a report viewer.
    escaped = _MARKDOWN.sub(r"\\\1", html.escape(value, quote=False))
    # Only renderer-owned block structure is permitted. Fixed inline breaks
    # preserve quotation content without letting embedded newlines open blocks.
    return escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br />")


def _render_body(
    kind: str,
    canonical: dict,
    localized: dict,
    language: str,
    *,
    concise: bool = False,
) -> str:
    index = 0 if language == "en" else 1
    lines: list[str] = []

    def label(en: str, zh: str) -> str:
        return en if index == 0 else zh

    def translated(path: str) -> str:
        return _escape(localized[path][language])

    def heading(en: str, zh: str, level: int = 3) -> None:
        lines.extend([f"{'#' * level} {label(en, zh)}", ""])

    def field(en: str, zh: str, value: str) -> None:
        lines.extend([f"**{label(en, zh)}:** {value}", ""])

    def narrative_list(values: list[str], prefix: str, en: str, zh: str) -> None:
        if values:
            heading(en, zh)
            lines.extend(f"- {translated(f'{prefix}/{i}')}" for i in range(len(values)))
            lines.append("")

    def evidence(values: list[dict]) -> None:
        for item in values:
            field("Source (original ID)", "来源（原始标识）", _escape(item["source"]))
            lines.extend([f"**{label('Quote (unchanged)', '引用（保留原文）')}:**", ""])
            lines.append(f"> {_escape(item['quote'])}")
            lines.append("")

    def claim_list(values: list[dict], prefix: str, en: str, zh: str) -> None:
        if not values:
            return
        heading(en, zh)
        for i, claim in enumerate(values):
            heading(f"Claim {i + 1}", f"主张 {i + 1}", 4)
            field("Topic", "主题", _TOPICS[claim["topic"]][index])
            lines.extend([translated(f"{prefix}/{i}/claim"), ""])
            field("Claim type", "主张类型", _TYPES[claim["type"]][index])
            field("Confidence", "置信度", _CONFIDENCE[claim["confidence"]][index])
            if concise:
                field(
                    "Sources (original IDs)",
                    "来源（原始标识）",
                    ", ".join(_escape(item["source"]) for item in claim["evidence"]),
                )
            else:
                evidence(claim["evidence"])

    lines.extend(
        [
            label(
                "These labels describe the submitted material, not certainty about a person. "
                "Check interpretations and translations against the original quotations; "
                "structural and language checks do not establish factual truth "
                "or translation accuracy.",
                "这些标签描述提交材料中的支持程度，并不代表对一个人的确定判断。请对照原始引用核实解释与翻译；"
                "结构和语言字符检查不能证明事实真实，也不能证明翻译准确。",
            ),
            "",
        ]
    )

    if kind == "self_portrait":
        report = canonical["report"]
        if concise:
            lines.extend(
                [
                    label(
                        "Summary of the recorded claims and caveats. "
                        "See the detailed self-portrait "
                        "for original quotations, coverage, questions, and clarification findings.",
                        "本摘要列出已记录的主张与限制。原始引用、材料覆盖范围、问题及待澄清记录"
                        "请参阅详细自我画像。",
                    ),
                    "",
                ]
            )
            claim_list(
                report["claims"],
                "/report/claims",
                "Evidence-linked claims",
                "与证据关联的主张",
            )
            narrative_list(report["caveats"], "/report/caveats", "Caveats", "限制与提醒")
            gaps = len(report["data_coverage"]["not_covered"])
            findings = len(report["consistency_findings"])
            questions = len(report["open_questions"])
            lines.extend(
                [
                    label(
                        f"Detailed report: {gaps} coverage gap(s), "
                        f"{findings} clarification finding(s), and {questions} open question(s). "
                        "Review these before interpreting the summary.",
                        f"详细报告记录了 {gaps} 项覆盖缺口、{findings} 项待澄清记录"
                        f"及 {questions} 个待回答问题。"
                        "解读摘要之前，请先查看这些内容。",
                    ),
                    "",
                ]
            )
            return "\n".join(lines).strip() + "\n"
        heading("Data coverage", "材料覆盖范围")
        if report["data_coverage"]["sources_read"]:
            field("Sources read (original IDs)", "已读取来源（原始标识）", "")
            lines.extend(
                f"- {_escape(source)}" for source in report["data_coverage"]["sources_read"]
            )
            lines.append("")
        for name, en, zh in (
            ("covered", "Covered topics", "已覆盖主题"),
            ("not_covered", "Coverage gaps", "尚未覆盖的内容"),
        ):
            narrative_list(
                report["data_coverage"][name],
                f"/report/data_coverage/{name}",
                en,
                zh,
            )
        claim_list(report["claims"], "/report/claims", "Evidence-linked claims", "与证据关联的主张")
        if report["consistency_findings"]:
            heading("Points to clarify", "待澄清之处")
        for i, finding in enumerate(report["consistency_findings"]):
            heading(f"Finding {i + 1}", f"记录 {i + 1}", 4)
            field("Kind", "类别", _TENSIONS[finding["kind"]][index])
            field("Confidence", "置信度", _CONFIDENCE[finding["confidence"]][index])
            for name, en, zh in (
                ("stated", "Stated material", "陈述的内容"),
                ("contradicting", "Material to compare", "需要对照的内容"),
                ("framing", "Uncertainty-aware framing", "保留不确定性的解释"),
                ("clarifying_question", "Clarifying question", "澄清问题"),
                ("alt_benign_explanation", "Alternative benign explanation", "另一种善意解释"),
            ):
                field(en, zh, translated(f"/report/consistency_findings/{i}/{name}"))
            evidence(finding["quotes"])
        narrative_list(
            report["open_questions"], "/report/open_questions", "Open questions", "待回答的问题"
        )
        narrative_list(report["caveats"], "/report/caveats", "Caveats", "限制与提醒")
    else:
        criteria = canonical["criteria"]
        claim_list(criteria["stated"], "/criteria/stated", "Stated criteria", "明确陈述的标准")
        # An empty revealed list must not generate a revealed-preference narrative.
        claim_list(criteria["revealed"], "/criteria/revealed", "Revealed criteria", "表现出的标准")
        narrative_list(
            criteria["open_questions"], "/criteria/open_questions", "Open questions", "待回答的问题"
        )
        narrative_list(
            criteria["caveats"], "/criteria/caveats", "Criteria caveats", "标准的限制与提醒"
        )
        profiles = canonical["ideal_profiles"]
        if profiles["candidates"]:
            heading("Fictional scenarios", "虚构情境")
        for i, candidate in enumerate(profiles["candidates"]):
            heading(f"Fictional candidate {i + 1}", f"虚构候选人 {i + 1}", 4)
            field("Synthetic ID", "合成标识", _escape(candidate["synthetic_id"]))
            field("Adult age", "成年年龄", str(candidate["age"]))
            for name, en, zh in (
                ("description", "Fictional description", "虚构描述"),
                ("choice_reason", "Recorded choice reason", "记录的选择理由"),
                ("uncertainty_notes", "Uncertainty", "不确定性"),
            ):
                if candidate[name] is not None:
                    field(en, zh, translated(f"/ideal_profiles/candidates/{i}/{name}"))
            evidence(candidate["evidence"])
        narrative_list(
            profiles["caveats"],
            "/ideal_profiles/caveats",
            "Scenario caveats",
            "情境的限制与提醒",
        )
    return "\n".join(lines).strip() + "\n"


def render_localized_reports(
    kind: str, canonical: dict, entries: Any, *, language: str | None = None,
) -> dict[str, str]:
    """Render checked narratives; exports default to complete EN/ZH documents."""
    if language not in {None, "en", "zh"}:
        raise ValueError("Choose English or Simplified Chinese.")
    checked = _checked_canonical(kind, canonical)
    localized = validate_localization(kind, checked, entries)

    def body(*, concise=False):
        if language is not None:
            return _render_body(kind, checked, localized, language, concise=concise)
        return "\n".join(
            f"## {heading}\n\n" + _render_body(kind, checked, localized, language, concise=concise)
            for language, heading in (("en", "English"), ("zh", "中文版"))
        )

    if kind == "self_portrait":
        title = {
            None: "Self-Portrait / 自我画像", "en": "Self-Portrait", "zh": "自我画像",
        }[language]
        detailed_title = {
            None: "Detailed Self-Portrait / 详细自我画像",
            "en": "Detailed Self-Portrait", "zh": "详细自我画像",
        }[language]
        return {
            "markdown": f"# {title}\n\n" + body(concise=True),
            "detailed_markdown": f"# {detailed_title}\n\n" + body(),
        }
    title = {
        None: "Relationship Criteria / 择偶标准", "en": "Relationship Criteria", "zh": "择偶标准",
    }[language]
    return {"markdown": f"# {title}\n\n" + body()}
