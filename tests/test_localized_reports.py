from copy import deepcopy

import pytest

from anti_dating_scam.reports.local_artifacts import ArtifactValidationError
from anti_dating_scam.reports.localized_reports import (
    render_localized_reports,
    required_localization_sources,
    validate_localization,
)


def _claim():
    return {
        "topic": "values",
        "claim": "I prefer clear communication.",
        "type": "observation",
        "confidence": "low",
        "evidence": [{"quote": "I prefer clear communication.", "source": "synthetic-note-1"}],
    }


def _portrait():
    return {
        "report": {
            "schema_version": "0.2",
            "report_type": "self_portrait",
            "generated_at": "2026-09-28T00:00:00Z",
            "headline": {"en": "UNUSED_HEADLINE", "zh": "不用的标题"},
            "summary": {"en": "UNUSED_SUMMARY", "zh": "不用的摘要"},
            "data_coverage": {
                "sources_read": ["synthetic-note-1"],
                "covered": ["Communication preferences."],
                "not_covered": ["Long-term behavior."],
            },
            "claims": [_claim()],
            "consistency_findings": [
                {
                    "kind": "temporal_drift",
                    "stated": "An earlier preference.",
                    "contradicting": "A later preference.",
                    "confidence": "low",
                    "framing": "These contexts may differ.",
                    "clarifying_question": "Did context change?",
                    "alt_benign_explanation": "The circumstances may have changed.",
                    "quotes": [
                        {"quote": "I prefer clear communication.", "source": "synthetic-note-1"},
                        {"quote": "I want time to reflect.", "source": "synthetic-note-2"},
                    ],
                }
            ],
            "open_questions": ["What does clarity mean to you?"],
            "caveats": ["One synthetic note does not establish a stable trait."],
        }
    }


def _criteria():
    return {
        "criteria": {
            "schema_version": "0.1",
            "report_type": "mate_criteria",
            "stated": [_claim()],
            "revealed": [],
            "open_questions": ["Which trade-offs would you accept?"],
            "caveats": ["No expressed choice is recorded."],
        },
        "ideal_profiles": {
            "schema_version": "0.1",
            "candidates": [
                {
                    "synthetic_id": "fictional-A",
                    "age": 30,
                    "fictional": True,
                    "description": "An explicitly fictional adult values open communication.",
                    "choice_reason": None,
                    "evidence": [],
                    "uncertainty_notes": "This scenario does not describe a real person.",
                }
            ],
            "caveats": ["Fictional scenarios are prompts, not recommendations."],
        },
    }


def _entries(kind, canonical):
    return [
        {"path": path, "source": source, "en": source, "zh": f"合成中文译文第{index}项"}
        for index, (path, source) in enumerate(
            required_localization_sources(kind, canonical).items()
        )
    ]


def test_required_paths_cover_all_portrait_narratives_and_exclude_quotes_metadata():
    sources = required_localization_sources("self_portrait", _portrait())
    assert set(sources) == {
        "/report/data_coverage/covered/0",
        "/report/data_coverage/not_covered/0",
        "/report/claims/0/claim",
        "/report/open_questions/0",
        "/report/caveats/0",
        *{
            f"/report/consistency_findings/0/{field}"
            for field in (
                "stated",
                "contradicting",
                "framing",
                "clarifying_question",
                "alt_benign_explanation",
            )
        },
    }
    assert not any(
        word in path
        for path in sources
        for word in (
            "headline",
            "summary",
            "generated_at",
            "source",
            "quote",
            "confidence",
            "topic",
        )
    )


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "duplicate",
        "changed_source",
        "changed_path",
        "extra_field",
        "altered_english",
        "english_only_zh",
        "one_han",
        "same_languages",
        "not_list",
    ],
)
def test_localization_rejects_incomplete_forged_or_monolingual_maps_without_echo(damage):
    canonical = _portrait()
    entries = _entries("self_portrait", canonical)
    if damage == "missing":
        entries.pop()
    elif damage == "extra":
        entries.append({"path": "/invented", "source": "private-marker", "en": "X", "zh": "中文"})
    elif damage == "duplicate":
        entries[-1] = dict(entries[0])
    elif damage == "changed_source":
        entries[0]["source"] = "private-marker"
    elif damage == "changed_path":
        entries[0]["path"] = "/report/claims/0/evidence/0/quote"
    elif damage == "extra_field":
        entries[0]["extra"] = "private-marker"
    elif damage == "altered_english":
        entries[0]["en"] = "A new claim not in the source."
    elif damage == "english_only_zh":
        entries[0]["zh"] = "Not a Chinese translation."
    elif damage == "one_han":
        entries[0]["zh"] = "中 English filler"
    elif damage == "same_languages":
        entries[0]["zh"] = entries[0]["en"]
    elif damage == "not_list":
        entries = {"invented": "private-marker"}
    with pytest.raises(ArtifactValidationError) as caught:
        render_localized_reports("self_portrait", canonical, entries)
    assert "private-marker" not in str(caught.value)


def test_chinese_source_is_preserved_exactly_and_english_requires_letters():
    canonical = _portrait()
    canonical["report"]["caveats"] = ["合成材料不足以确定长期行为。"]
    entries = _entries("self_portrait", canonical)
    entry = next(item for item in entries if item["path"] == "/report/caveats/0")
    entry.update(en="Synthetic material does not establish long-term behavior.", zh=entry["source"])
    validated = validate_localization("self_portrait", canonical, entries)
    assert validated["/report/caveats/0"]["zh"] == canonical["report"]["caveats"][0]
    entry["zh"] += "新内容"
    with pytest.raises(ArtifactValidationError):
        validate_localization("self_portrait", canonical, entries)
    entry["zh"] = entry["source"]
    entry["en"] = "只有中文"
    with pytest.raises(ArtifactValidationError):
        validate_localization("self_portrait", canonical, entries)


def test_portrait_render_is_bilingual_immutable_and_has_no_free_summary():
    canonical = _portrait()
    entries = _entries("self_portrait", canonical)
    before = deepcopy((canonical, entries))
    reports = render_localized_reports("self_portrait", canonical, entries)
    assert set(reports) == {"markdown", "detailed_markdown"}
    for text in reports.values():
        assert text.index("## English") < text.index("## 中文版")
        assert "UNUSED_HEADLINE" not in text and "UNUSED_SUMMARY" not in text
        assert "Observation" in text and "观察" in text
        assert "limited support" in text and "支持有限" in text
        assert "2026-09-28" not in text
    assert "另一种善意解释" in reports["detailed_markdown"]
    assert "Alternative benign explanation" in reports["detailed_markdown"]
    assert "另一种善意解释" not in reports["markdown"]
    assert "What does clarity mean to you?" not in reports["markdown"]
    assert "1 coverage gap(s), 1 clarification finding(s)" in reports["markdown"]
    assert len(reports["markdown"]) < len(reports["detailed_markdown"])
    assert (canonical, entries) == before


def test_empty_revealed_list_never_produces_revealed_preferences_or_choice_prose():
    canonical = _criteria()
    entries = _entries("mate_criteria", canonical)
    text = render_localized_reports("mate_criteria", canonical, entries)["markdown"]
    assert text.startswith("# Relationship Criteria / 择偶标准")
    assert "Self-Portrait" not in text
    assert "Revealed" not in text and "表现出的标准" not in text
    assert "choice reason" not in text and "选择理由" not in text
    assert "Fictional candidate" in text and "虚构候选人" in text
    assert "fictional\\-A" in text


def test_evidenced_candidate_choice_adds_only_its_canonical_narrative():
    canonical = _criteria()
    candidate = canonical["ideal_profiles"]["candidates"][0]
    candidate["choice_reason"] = "The user explicitly selected the communication scenario."
    candidate["evidence"] = [{"source": "synthetic-answer", "quote": "I choose A."}]
    entries = _entries("mate_criteria", canonical)
    assert "/ideal_profiles/candidates/0/choice_reason" in required_localization_sources(
        "mate_criteria",
        canonical,
    )
    text = render_localized_reports("mate_criteria", canonical, entries)["markdown"]
    assert "Recorded choice reason" in text and "记录的选择理由" in text
    assert "I choose A\\." in text


@pytest.mark.parametrize(
    "kind,canonical",
    [
        ("unknown", {}),
        ("self_portrait", {"report": {}, "markdown": "injected"}),
        ("mate_criteria", {"report": _portrait()["report"]}),
    ],
)
def test_report_type_and_canonical_structure_determine_heading_or_rejection(kind, canonical):
    with pytest.raises(ArtifactValidationError):
        render_localized_reports(kind, canonical, [])


def test_mismatched_explicit_report_type_is_rejected():
    canonical = _portrait()
    canonical["report"]["report_type"] = "mate_criteria"
    with pytest.raises(ArtifactValidationError):
        required_localization_sources("self_portrait", canonical)


def test_untrusted_markdown_remains_literal_in_qt_including_original_quotes_and_ids():
    gui = pytest.importorskip("PySide6.QtGui")
    widgets = pytest.importorskip("PySide6.QtWidgets")
    app = widgets.QApplication.instance() or widgets.QApplication([])
    canonical = _portrait()
    attack = (
        "Literal content\n# INJECTED HEADING\n![picture](https://example.invalid/image)\n"
        "[link](https://example.invalid/) <script>probe</script> `code`\n"
        "https://example.invalid/ contact@example.invalid"
    )
    canonical["report"]["claims"][0]["claim"] = attack
    canonical["report"]["claims"][0]["evidence"] = [{"quote": attack, "source": attack}]
    canonical["report"]["data_coverage"]["sources_read"] = [attack]
    text = render_localized_reports(
        "self_portrait",
        canonical,
        _entries("self_portrait", canonical),
    )["detailed_markdown"]
    assert "\n# INJECTED HEADING" not in text
    assert "<script>" not in text and "![picture]" not in text
    document = gui.QTextDocument()
    document.setMarkdown(text)
    rendered_html = document.toHtml()
    assert "<img " not in rendered_html and "href=" not in rendered_html
    assert "<script>probe</script>" in document.toPlainText()
    assert "![picture](https://example.invalid/image)" in document.toPlainText()
    assert "# INJECTED HEADING" in document.toPlainText()
    assert app is not None
