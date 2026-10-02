import re

from anti_dating_scam_desktop.self_portrait_html import render_self_portrait_html

# Synthetic sample in the v2-aligned schema (0.3): no scores, no trait bars,
# no attachment verdicts — evidence + word-only confidence instead.
SAMPLE = {
    "generated_at": "2026-01-01",
    "schema_version": "0.3",
    "headline": {"en": "The Curious Connector", "zh": "好奇的连接者"},
    "summary": {"en": "A short summary.", "zh": "简短摘要。"},
    "top_values": [{"name": {"en": "Benevolence", "zh": "仁善"}}],
    "wants": {
        "stated": {"en": "Says income does not matter.", "zh": "口头说收入不重要。"},
        "revealed": {"en": "Rejections often cite earnings.", "zh": "拒绝理由常提收入。"},
    },
    "connection": {
        "communication": {"en": "Talks first, cools later.", "zh": "先沟通，后冷静。"},
        "front_back_stage": {"en": "Curated in public.", "zh": "公开场合较为修饰。"},
    },
    "boundaries": [{"en": "No money talk online.", "zh": "线上不谈钱。"}],
    "market_stance": {
        "stance": {"en": "Wary of apps.", "zh": "对交友软件警惕。"},
        "origin": {"en": "Mostly paid-matchmaking stories.", "zh": "主要来自付费相亲经历。"},
    },
    "consistency_findings": [
        {
            "kind": "stated_vs_revealed",
            "framing": {"en": "There's a tension between X and Y.", "zh": "X 与 Y 之间存在张力。"},
            "quotes": [{"quote": "synthetic quote", "source": "imports/chat.md"}],
            "confidence": "medium",
            "clarifying_question": {"en": "Which matters more?", "zh": "哪个更重要？"},
        }
    ],
    "growth_edges": [{"title": {"en": "Say the hard thing", "zh": "说出难说的话"}}],
    "frameworks_used": [{"en": "Goffman", "zh": "戈夫曼"}],
    "guide": [{"en": "Read it as a mirror.", "zh": "把它当作镜子来读。"}],
    "frameworks_glossary": [
        {
            "name": {"en": "Goffman", "zh": "戈夫曼"},
            "what": {"en": "Front-stage vs back-stage self.", "zh": "前台与后台的自我。"},
        }
    ],
    "how_to_use": [{"en": "Try one experiment.", "zh": "做一个实验。"}],
    "caveats": [{"en": "Synthetic sample.", "zh": "合成示例。"}],
}


def test_render_produces_self_contained_offline_document() -> None:
    html = render_self_portrait_html(SAMPLE)

    assert "<!doctype html>" in html.lower()
    for needle in ["The Curious Connector", "Growth edges", "Benevolence"]:
        assert needle in html
    # Privacy: no external network requests of any kind.
    assert not re.findall(r"https?://", html)
    assert "src=" not in html and "@import" not in html


def test_no_scores_bars_or_type_verdicts(  # the v2 hard exclusion, enforced in output
) -> None:
    html = render_self_portrait_html(SAMPLE)

    # No trait bars or percentage readouts anywhere in the DOM markup.
    assert "trait-pct" not in html and 'class="bar"' not in html
    assert not re.search(r">\s*\d+%\s*<", html)
    # No Big Five trait rows or attachment verdict cards.
    for banned in [
        "Openness",
        "Conscientiousness",
        "Extraversion",
        "Neuroticism",
        "Emotional steadiness",
        "Attachment leaning",
    ]:
        assert banned not in html, banned


def test_v2_sections_render(  # wants, boundaries, market stance, tensions
) -> None:
    html = render_self_portrait_html(SAMPLE)

    for needle in [
        "What you seem to actually want",
        "你似乎真正想要的",
        "Stated ideal",
        "Revealed pattern",
        "Boundaries &amp; deal-breakers",
        "边界与不可妥协项",
        "Your stance toward the dating market",
        "你对婚恋市场的态度",
        "Self-report consistency audit",
        "自述一致性审计",
        "There&#x27;s a tension between X and Y.",
        "A question to resolve it",
        "synthetic quote",
        "imports/chat.md",
    ]:
        assert needle in html, needle


def test_localized_fields_accept_plain_strings() -> None:
    html = render_self_portrait_html({"headline": "Plain String Headline"})

    assert "Plain String Headline" in html


def test_missing_fields_do_not_crash() -> None:
    html = render_self_portrait_html({})

    assert "<!doctype html>" in html.lower()


def test_text_is_html_escaped() -> None:
    html = render_self_portrait_html({"headline": {"en": "<script>x</script>", "zh": "x"}})

    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_explanatory_sections_render_bilingually() -> None:
    html = render_self_portrait_html(SAMPLE)

    for needle in [
        "How to read this",
        "如何阅读这份报告",
        "The lenses, explained",
        "这些视角的含义",
        "How to use this",
        "如何使用这份报告",
        "Front-stage vs back-stage self.",
        "前台与后台的自我。",
    ]:
        assert needle in html, needle
    assert "gloss-name" in html and "gloss-what" in html


def test_glossary_replaces_bare_tag_list_when_present() -> None:
    html = render_self_portrait_html(SAMPLE)
    assert "Lenses used" not in html
    assert "The lenses, explained" in html


def test_confidence_badge_carries_both_languages() -> None:
    # Word-only confidence (the only "measurement" v2 allows) must render in both
    # languages so it switches with the toggle.
    html = render_self_portrait_html(SAMPLE)
    assert "medium confidence" in html and "置信度" in html


def test_bare_tag_fallback_is_bilingual() -> None:
    tags_only = {"frameworks_used": [{"en": "Goffman", "zh": "戈夫曼"}]}
    html = render_self_portrait_html(tags_only)

    assert 'class="tag"' in html
    assert "Goffman" in html and "戈夫曼" in html
    assert '<span class="lang zh">戈夫曼</span>' in html


def _validated_portrait():
    from anti_dating_scam.reports.local_artifacts import validate_local_artifact

    return validate_local_artifact(
        {
            "schema_version": "0.2",
            "data_coverage": {
                "sources_read": ["synthetic-notes"],
                "covered": ["communication"],
                "not_covered": ["Conflict episodes remain unknown."],
            },
            "claims": [
                {
                    "topic": "communication",
                    "claim": "May prefer a pause before replying.",
                    "type": "inference",
                    "confidence": "low",
                    "evidence": [
                        {
                            "quote": "I take a break before difficult conversations.",
                            "source": "synthetic-notes",
                        }
                    ],
                }
            ],
            "consistency_findings": [],
            "open_questions": ["Does a pause help you listen?"],
            "caveats": ["One synthetic note is insufficient to establish a stable pattern."],
        },
        "self_portrait",
    )


def test_validated_v02_portrait_shows_evidence_coverage_and_unknowns():
    html = render_self_portrait_html(_validated_portrait())
    for expected in (
        "Evidence coverage",
        "证据覆盖范围",
        "Sources considered",
        "参考来源",
        "Topics covered",
        "已涉及的主题",
        "Missing information",
        "尚缺的信息",
        "Evidence-linked reflections",
        "有证据依据的反思",
        "Inference",
        "推断",
        "low confidence",
        "低置信度",
        "May prefer a pause",
        "I take a break",
        "synthetic-notes",
        "Does a pause help you listen?",
        "Conflict episodes remain unknown.",
        "One synthetic note is insufficient",
        "Questions to clarify",
        "待澄清的问题",
    ):
        assert expected in html
    assert "Generated locally" not in html
    assert "Everything stays in your vault" not in html


def test_v02_untrusted_claim_quote_source_and_coverage_are_escaped():
    data = _validated_portrait()
    injection = '<img src="https://synthetic.test" onerror="alert(1)">'
    data["claims"][0]["claim"] = injection
    data["claims"][0]["evidence"][0] = {"quote": injection, "source": injection}
    data["data_coverage"]["not_covered"] = [injection]
    data["open_questions"] = [injection]
    html = render_self_portrait_html(data)
    assert injection not in html
    assert "<img" not in html
    assert "&lt;img" in html and "&quot;" in html


def test_empty_v02_claims_show_uncertainty_and_default_title():
    data = _validated_portrait()
    data["claims"] = []
    data["headline"] = None
    html = render_self_portrait_html(data)
    assert "Insufficient evidence for supported claims" in html
    assert "目前证据不足" in html
    assert "Your Self-Portrait" in html and "你的自我画像" in html


def test_v02_numeric_confidence_is_rejected_before_visual_export():
    import pytest

    from anti_dating_scam.reports.local_artifacts import ArtifactValidationError

    data = _validated_portrait()
    data["claims"][0]["confidence"] = 0.99
    with pytest.raises(ArtifactValidationError):
        render_self_portrait_html(data)


def test_visual_report_uses_verified_localizations_without_mutating_canonical():
    from anti_dating_scam.reports.localized_reports import required_localization_sources

    data = _validated_portrait()
    limited_note = "One synthetic note is insufficient to establish a stable pattern."
    translations = {
        "communication": "沟通",
        "Conflict episodes remain unknown.": "尚不了解发生冲突时的具体经历。",
        "May prefer a pause before replying.": "可能倾向于在回复之前暂停片刻。",
        "Does a pause help you listen?": "暂停片刻有助于你倾听吗？",
        limited_note: "一条虚构测试笔记不足以确定稳定模式。",
    }
    entries = [
        {"path": path, "source": source, "en": source, "zh": translations[source]}
        for path, source in required_localization_sources("self_portrait", {"report": data}).items()
    ]
    html = render_self_portrait_html(data, entries)
    assert "可能倾向于在回复之前暂停片刻。" in html
    assert "一条虚构测试笔记不足以确定稳定模式。" in html
    assert "尚无经过核对的中文译文" not in html
    assert data["claims"][0]["claim"] == "May prefer a pause before replying."
    assert "I take a break before difficult conversations." in html


def test_visual_report_rejects_stale_or_incomplete_localization():
    import pytest

    from anti_dating_scam.reports.local_artifacts import ArtifactValidationError

    with pytest.raises(ArtifactValidationError):
        render_self_portrait_html(_validated_portrait(), [])


def test_viewer_rejects_null_companion_without_opening_legacy_fallback(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from anti_dating_scam_desktop.screens import self_portrait_viewer_screen as viewer

    companion = tmp_path / "self_portrait_localization.json"
    companion.write_text('{"schema_version":"0.1","localized_text":null}', encoding="utf-8")
    opened, warnings = [], []
    store = SimpleNamespace(
        self_portrait_json_path=tmp_path / "self_portrait.json",
        read_active_report=lambda kind: None,
        load_original_self_portrait_json=_validated_portrait,
        write_self_portrait_html=lambda html: opened.append(html),
    )
    monkeypatch.setattr(viewer.QMessageBox, "warning", lambda *args: warnings.append(args))
    monkeypatch.setattr(viewer.QDesktopServices, "openUrl", lambda *args: opened.append(args))
    viewer.SelfPortraitViewerScreen._open_visual(SimpleNamespace(profile_store=store))
    assert len(warnings) == 1
    assert opened == []
