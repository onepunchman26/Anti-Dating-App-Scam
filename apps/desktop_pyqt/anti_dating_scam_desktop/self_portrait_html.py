"""Render a self-portrait ``self_portrait.json`` into a polished, offline HTML page.

Aligned with the Chat-Analysis Module contract v2 (see
``anti_dating_scam.ai.analysis_contract``): **no trait bars, percentages, or type
labels** — a bar or a 0-1 float IS a score, and scores are forbidden. The page
renders evidence-bound sections (values, stated-vs-revealed wants, communication,
boundaries, market stance, consistency tensions) with word-only confidence badges.
Single self-contained file: no external requests, no CDN, no fonts over the
network. Bilingual with an EN / 中文 toggle.

The generator is tolerant: every field is optional, and each localized value may be a
plain string or a ``{"en": ..., "zh": ...}`` object.
"""

from __future__ import annotations

from copy import deepcopy
from html import escape
from typing import Any

from anti_dating_scam.reports.localized_reports import (
    required_localization_sources,
    validate_localization,
)


def _loc(value: Any) -> tuple[str, str]:
    """Return (en, zh) for a value that may be a string or an {en, zh} dict."""
    if isinstance(value, dict):
        en = str(value.get("en", "") or "")
        zh = str(value.get("zh", "") or "")
        return en, (zh or en)
    text = "" if value is None else str(value)
    return text, text


def _dual(value: Any, *, tag: str = "span", cls: str = "") -> str:
    """Emit both languages; CSS shows one based on the body language class."""
    en, zh = _loc(value)
    if not en and not zh:
        return ""
    klass = f" {cls}" if cls else ""
    return (
        f'<{tag} class="lang en{klass}">{escape(en)}</{tag}>'
        f'<{tag} class="lang zh{klass}">{escape(zh)}</{tag}>'
    )


def _t(en: str, zh: str) -> str:
    """Shorthand for a bilingual literal label."""
    return _dual({"en": en, "zh": zh})


def _chip_values(data: dict) -> str:
    values = data.get("top_values") or []
    cards: list[str] = []
    for value in values:
        name = value.get("name") if isinstance(value, dict) else value
        note = value.get("note") if isinstance(value, dict) else ""
        cards.append(
            '<div class="value-card">'
            f'<div class="value-name">{_dual(name)}</div>'
            f"{_dual(note, tag='p', cls='value-note') if note else ''}"
            "</div>"
        )
    return "\n".join(cards)


def _list_block(items: list, cls: str) -> str:
    lis = [f"<li>{_dual(item)}</li>" for item in items if _loc(item) != ("", "")]
    if not lis:
        return ""
    return f'<ul class="{cls}">' + "\n".join(lis) + "</ul>"


def _growth_cards(data: dict) -> str:
    edges = data.get("growth_edges") or []
    cards: list[str] = []
    for index, edge in enumerate(edges, start=1):
        title = edge.get("title") if isinstance(edge, dict) else edge
        body = edge.get("body") if isinstance(edge, dict) else ""
        cards.append(
            '<div class="edge">'
            f'<div class="edge-num">{index}</div>'
            "<div>"
            f'<div class="edge-title">{_dual(title)}</div>'
            f"{_dual(body, tag='p', cls='edge-body') if body else ''}"
            "</div>"
            "</div>"
        )
    return "\n".join(cards)


def _tags(items: list) -> str:
    tags = [f'<span class="tag">{_dual(item)}</span>' for item in items if _loc(item) != ("", "")]
    return "\n".join(tags)


# Bilingual labels for the attachment-confidence badge so it, too, switches.
_CONF_LABELS = {
    "low": ("low confidence", "低置信度"),
    "medium": ("medium confidence", "中等置信度"),
    "high": ("high confidence", "高置信度"),
}

_CLAIM_TOPICS = {
    "values": ("Relationship values", "关系价值观"),
    "wants": ("Wants and preferences", "愿望与偏好"),
    "communication": ("Communication", "沟通"),
    "boundaries": ("Boundaries", "边界"),
    "market_stance": ("Dating-market assumptions", "婚恋市场观念"),
    "presentation": ("Self-presentation", "自我呈现"),
    "pattern": ("Described pattern", "叙述中的模式"),
}
_CLAIM_TYPES = {
    "observation": ("Observation", "观察"),
    "inference": ("Inference", "推断"),
    "speculation": ("Hypothesis", "假设"),
}


def _confidence_badge(conf: Any) -> str:
    if not conf:
        return ""
    labels = _CONF_LABELS.get(str(conf).lower())
    if labels is None:
        return ""
    en, zh = labels
    return f'<span class="conf">{_t(en, zh)}</span>'


def _coverage_section(data: dict) -> str:
    """Display the v0.2 coverage contract without interpreting missing facts."""
    coverage = data.get("data_coverage")
    if not isinstance(coverage, dict):
        return ""
    groups = []
    for key, en, zh in (
        ("sources_read", "Sources considered", "参考来源"),
        ("covered", "Topics covered", "已涉及的主题"),
        ("not_covered", "Missing information", "尚缺的信息"),
    ):
        items = coverage.get(key)
        if isinstance(items, list) and items:
            groups.append(
                '<div class="conn-card">'
                f'<div class="conn-title">{_t(en, zh)}</div>'
                + _list_block(items, "needs")
                + "</div>"
            )
    if not groups:
        groups.append(
            _dual(
                {
                    "en": "No coverage information was provided. Conclusions remain uncertain.",
                    "zh": "尚未提供材料覆盖范围，结论仍有不确定性。",
                },
                tag="p",
            )
        )
    return (
        '<section class="card">'
        f"<h2>{_t('Evidence coverage', '证据覆盖范围')}</h2>"
        f'<div class="glossary">{"".join(groups)}</div></section>'
    )


def _claims_section(data: dict) -> str:
    """Render v0.2 claims, exact quotes, sources, type and word-only confidence."""
    if "claims" not in data or not isinstance(data["claims"], list):
        return ""
    cards = []
    for claim in data["claims"]:
        if not isinstance(claim, dict) or not claim.get("claim"):
            continue
        topic = _CLAIM_TOPICS.get(str(claim.get("topic")), ("Reflection", "反思"))
        kind = _CLAIM_TYPES.get(str(claim.get("type")), ("Unspecified", "尚未分类"))
        evidence = []
        for item in claim.get("evidence") or []:
            if isinstance(item, dict) and item.get("quote"):
                evidence.append(
                    '<blockquote class="quote">'
                    + _dual(item["quote"])
                    + '<span class="quote-src">'
                    + _t("Source: ", "来源：")
                    + escape(str(item.get("source", "")))
                    + "</span></blockquote>"
                )
        if not evidence:
            evidence.append(
                _dual(
                    {
                        "en": "No supporting evidence supplied; treat this claim as unverified.",
                        "zh": "未提供支持证据，请将此说法视为尚未核实。",
                    },
                    tag="p",
                    cls="conn-note",
                )
            )
        cards.append(
            '<article class="conn-card tension">'
            f'<div class="conn-title">{_t(*topic)}'
            f'<span class="conf">{_t(*kind)}</span>'
            + _confidence_badge(claim.get("confidence"))
            + "</div>"
            + _dual(claim["claim"], tag="p", cls="conn-note")
            + "".join(evidence)
            + "</article>"
        )
    if not cards:
        cards.append(
            _dual(
                {
                    "en": "Insufficient evidence for supported claims. More information is needed.",
                    "zh": "目前证据不足，尚无法支持具体判断，需要更多信息。",
                },
                tag="p",
                cls="conn-note",
            )
        )
    return (
        '<section class="card">'
        f"<h2>{_t('Evidence-linked reflections', '有证据依据的反思')}</h2>"
        + "".join(cards)
        + "</section>"
    )


def _questions_section(data: dict) -> str:
    items = data.get("open_questions")
    if not isinstance(items, list) or not items:
        return ""
    return (
        '<section class="card">'
        f"<h2>{_t('Questions to clarify', '待澄清的问题')}</h2>"
        + _list_block(items, "needs")
        + "</section>"
    )


def _connection(data: dict) -> str:
    # v2: no attachment-style verdict card — attachment language may only appear
    # inside prose as a loose, caveated lens, never as a labeled result.
    conn = data.get("connection") or {}
    cards: list[str] = []
    if conn.get("communication"):
        title = _t("Communication & conflict", "沟通与冲突")
        cards.append(
            '<div class="conn-card">'
            f'<div class="conn-title">{title}</div>'
            f"{_dual(conn.get('communication'), tag='p', cls='conn-note')}"
            "</div>"
        )
    if conn.get("front_back_stage"):
        title = _t("Front-stage vs. back-stage (Goffman)", "前台与后台（戈夫曼）")
        cards.append(
            '<div class="conn-card">'
            f'<div class="conn-title">{title}</div>'
            f"{_dual(conn.get('front_back_stage'), tag='p', cls='conn-note')}"
            "</div>"
        )
    return "\n".join(cards)


def _wants_section(data: dict) -> str:
    wants = data.get("wants") or {}
    stated, revealed = wants.get("stated"), wants.get("revealed")
    if not stated and not revealed:
        return ""
    cards: list[str] = []
    if stated:
        cards.append(
            '<div class="conn-card">'
            f'<div class="conn-title">{_t("Stated ideal", "口头的理想型")}</div>'
            f"{_dual(stated, tag='p', cls='conn-note')}"
            "</div>"
        )
    if revealed:
        cards.append(
            '<div class="conn-card">'
            f'<div class="conn-title">{_t("Revealed pattern", "实际显露的模式")}</div>'
            f"{_dual(revealed, tag='p', cls='conn-note')}"
            "</div>"
        )
    sub = _t(
        "Side by side — from your words vs. your described choices.",
        "并排对照——你说的话 vs. 你描述过的选择。",
    )
    return (
        '<section class="card">'
        f"<h2>{_t('What you seem to actually want', '你似乎真正想要的')}</h2>"
        f'<p class="section-sub">{sub}</p>'
        f'<div class="grid2">{"".join(cards)}</div>'
        "</section>"
    )


def _boundaries_section(data: dict) -> str:
    block = _list_block(data.get("boundaries") or [], "needs")
    if not block:
        return ""
    return (
        '<section class="card">'
        f"<h2>{_t('Boundaries & deal-breakers', '边界与不可妥协项')}</h2>"
        f"{block}"
        "</section>"
    )


def _market_section(data: dict) -> str:
    market = data.get("market_stance") or {}
    stance, origin = market.get("stance"), market.get("origin")
    if not stance and not origin:
        return ""
    parts = ""
    if stance:
        parts += _dual(stance, tag="p", cls="conn-note")
    if origin:
        parts += (
            f'<div class="conn-title" style="margin-top:10px">'
            f"{_t('Where it comes from', '它从哪里来')}</div>"
            + _dual(origin, tag="p", cls="conn-note")
        )
    return (
        '<section class="card">'
        f"<h2>{_t('Your stance toward the dating market', '你对婚恋市场的态度')}</h2>"
        f"{parts}"
        "</section>"
    )


def _tensions_section(data: dict) -> str:
    findings = data.get("consistency_findings") or []
    cards: list[str] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        framing = finding.get("framing")
        if _loc(framing) == ("", ""):
            continue
        quotes = "".join(
            f'<blockquote class="quote">{escape(str(q.get("quote", "")))}'
            f'<span class="quote-src">{escape(str(q.get("source", "")))}</span></blockquote>'
            for q in (finding.get("quotes") or [])
            if isinstance(q, dict) and q.get("quote")
        )
        question = finding.get("clarifying_question")
        question_html = (
            f'<div class="conn-title" style="margin-top:8px">'
            f"{_t('A question to resolve it', '一个可以澄清它的问题')}</div>"
            + _dual(question, tag="p", cls="conn-note")
            if question
            else ""
        )
        benign = finding.get("alt_benign_explanation")
        benign_html = _dual(benign, tag="p", cls="conn-note") if benign else ""
        accounts = ""
        for key, en, zh in (
            ("stated", "Stated account", "陈述内容"),
            ("contradicting", "Contrasting account", "存在差异的陈述"),
        ):
            if finding.get(key):
                accounts += (
                    f'<div class="conn-title">{_t(en, zh)}</div>'
                    + _dual(finding[key], tag="p", cls="conn-note")
                )
        cards.append(
            '<div class="conn-card tension">'
            f'<div class="conn-title">{_dual(framing)}'
            f"{_confidence_badge(finding.get('confidence'))}</div>"
            f"{accounts}{quotes}{question_html}{benign_html}"
            "</div>"
        )
    if not cards:
        return ""
    sub = _t(
        "Tensions in your own account — to resolve, not accusations.",
        "你自己叙述中的张力——是待澄清的问题，不是指控。",
    )
    return (
        '<section class="card">'
        f"<h2>{_t('Self-report consistency audit', '自述一致性审计')}</h2>"
        f'<p class="section-sub">{sub}</p>'
        f"{''.join(cards)}"
        "</section>"
    )


def _guide_section(data: dict) -> str:
    block = _list_block(data.get("guide") or [], "guide-list")
    if not block:
        return ""
    return (
        '<section class="card guide">'
        f"<h2>{_t('How to read this', '如何阅读这份报告')}</h2>"
        f"{block}"
        "</section>"
    )


def _how_to_use_section(data: dict) -> str:
    block = _list_block(data.get("how_to_use") or [], "howto")
    if not block:
        return ""
    sub = _t("Concrete ways to act on the reflections above.", "把上面的反思落到具体行动的方式。")
    return (
        '<section class="card">'
        f"<h2>{_t('How to use this', '如何使用这份报告')}</h2>"
        f'<p class="section-sub">{sub}</p>'
        f"{block}"
        "</section>"
    )


def _glossary_section(data: dict) -> str:
    items = data.get("frameworks_glossary") or []
    rows: list[str] = []
    for item in items:
        name = item.get("name") if isinstance(item, dict) else item
        what = item.get("what") if isinstance(item, dict) else ""
        if _loc(name) == ("", ""):
            continue
        what_html = _dual(what, tag="p", cls="gloss-what") if what else ""
        rows.append(
            f'<div class="gloss-item"><div class="gloss-name">{_dual(name)}</div>{what_html}</div>'
        )
    if not rows:
        return ""
    sub = _t(
        "Plain-language definitions of each framework used above.",
        "上面用到的每个理论框架的通俗解释。",
    )
    return (
        '<section class="card">'
        f"<h2>{_t('The lenses, explained', '这些视角的含义')}</h2>"
        f'<p class="section-sub">{sub}</p>'
        f'<div class="glossary">{"".join(rows)}</div>'
        "</section>"
    )


_CSS = """
:root{
  --bg:#f6f7fb; --card:#ffffff; --ink:#1c2030; --muted:#5b6172;
  --line:#e7e9f2; --brand:#6a5cff; --brand2:#b455ff; --accent:#ff6aa2;
  --shadow:0 10px 30px rgba(30,30,60,.08);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",
  "PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.lang{display:none}
body.lang-en .en{display:inline}
body.lang-zh .zh{display:inline}
body.lang-en p.en,body.lang-en li.en,body.lang-en div.en{display:block}
body.lang-zh p.zh,body.lang-zh li.zh,body.lang-zh div.zh{display:block}
.wrap{max-width:820px;margin:0 auto;padding:0 20px 72px}
.hero{background:linear-gradient(135deg,var(--brand) 0%,var(--brand2) 55%,var(--accent) 120%);
  color:#fff;padding:64px 20px 72px;text-align:center;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;inset:0;
  background:radial-gradient(1200px 300px at 50% -30%,rgba(255,255,255,.25),transparent)}
.hero-inner{max-width:820px;margin:0 auto;position:relative;z-index:1}
.eyebrow{letter-spacing:.22em;text-transform:uppercase;font-size:12px;opacity:.85;margin:0 0 14px}
.headline{font-size:clamp(28px,5vw,44px);font-weight:800;margin:0 0 16px;line-height:1.15}
.summary{font-size:clamp(15px,2.4vw,18px);max-width:620px;margin:0 auto;opacity:.96}
.disclaimer{margin-top:22px;display:inline-block;background:rgba(255,255,255,.16);
  border:1px solid rgba(255,255,255,.3);padding:7px 14px;border-radius:999px;font-size:12.5px}
.toggle{position:absolute;top:18px;right:18px;z-index:2;background:rgba(255,255,255,.18);
  color:#fff;border:1px solid rgba(255,255,255,.4);border-radius:999px;padding:7px 14px;
  font-size:13px;cursor:pointer;backdrop-filter:blur(4px)}
.toggle:hover{background:rgba(255,255,255,.3)}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;
  padding:26px 26px 24px;margin-top:22px;box-shadow:var(--shadow)}
h2{font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);
  margin:0 0 6px}
.section-sub{color:var(--muted);font-size:13.5px;margin:0 0 18px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.tension{margin:12px 0}
.quote{margin:8px 0;padding:6px 12px;border-left:3px solid var(--brand2);
  color:var(--muted);font-size:13.5px;font-style:italic}
.quote-src{display:block;font-style:normal;font-size:11.5px;color:#9aa0b4;margin-top:2px}
.conn-card,.value-card{background:#fbfbff;border:1px solid var(--line);
  border-radius:14px;padding:16px 18px}
.conn-title{font-weight:700;font-size:14.5px;margin-bottom:6px;display:flex;
  align-items:center;gap:8px;flex-wrap:wrap}
.conf{font-size:11px;color:var(--muted);background:#eef0f8;
  border-radius:999px;padding:2px 8px;font-weight:600}
.conn-label{color:var(--brand);font-weight:700;margin-bottom:4px}
.conn-note,.value-note{color:var(--muted);font-size:14px;margin:0}
.value-name{font-weight:700}
.needs li,.friction li{margin:6px 0}
.friction li{color:var(--muted)}
.edge{display:flex;gap:16px;padding:16px 0;border-top:1px solid var(--line)}
.edge:first-of-type{border-top:none}
.edge-num{flex:0 0 34px;height:34px;border-radius:50%;display:grid;place-items:center;
  font-weight:800;color:#fff;background:linear-gradient(135deg,var(--brand),var(--accent))}
.edge-title{font-weight:700;margin-bottom:2px}
.edge-body{color:var(--muted);font-size:14.5px;margin:0}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}
.tag{background:#eef0fb;color:#4a4f6a;border-radius:999px;padding:5px 12px;
  font-size:12.5px;font-weight:600}
.guide{background:#f3f1ff;border:1px solid #e2ddfb}
.guide-list,.howto{margin:6px 0 0;padding-left:20px}
.guide-list li,.howto li{margin:8px 0;color:#4a4f6a}
.glossary{display:grid;gap:14px;margin-top:6px}
.gloss-item{border-left:3px solid var(--brand);padding:1px 0 1px 14px}
.gloss-name{font-weight:700}
.gloss-what{color:var(--muted);font-size:14px;margin:3px 0 0}
.caveats{background:#fff8f0;border:1px solid #f4e3cf}
.caveats li{color:#7a6a55;font-size:13.5px}
.foot{color:var(--muted);font-size:12.5px;text-align:center;margin-top:26px}
@media (max-width:640px){.grid2{grid-template-columns:1fr}}
@media print{.toggle{display:none}.hero{color:#000}.card{box-shadow:none}}
"""

_JS = """
(function(){
  var b=document.body;
  function set(l){b.classList.remove('lang-en','lang-zh');b.classList.add('lang-'+l);
    var t=document.getElementById('t');if(t)t.textContent=(l==='en'?'中文':'EN');}
  var t=document.getElementById('t');
  if(t)t.addEventListener('click',function(){set(b.classList.contains('lang-en')?'zh':'en');});
})();
"""


def render_self_portrait_html(data: dict, localized_text: list[dict] | None = None) -> str:
    """Render the full self-portrait HTML document from a ``self_portrait.json`` dict."""
    if data.get("schema_version") == "0.2":
        canonical = {"report": data}
        if localized_text is not None:
            translations = validate_localization("self_portrait", canonical, localized_text)
        else:
            # Existing reports remain readable, but a missing translation is never
            # silently presented as Chinese. New generated reports require a map.
            sources = required_localization_sources("self_portrait", canonical)
            translations = {
                path: {"en": source, "zh": "尚无经过核对的中文译文，原文：" + source}
                for path, source in sources.items()
            }
        data = deepcopy(data)
        for pointer, translation in translations.items():
            parts = pointer.removeprefix("/report/").split("/")
            target = data
            for part in parts[:-1]:
                target = target[int(part)] if isinstance(target, list) else target[part]
            key = int(parts[-1]) if isinstance(target, list) else parts[-1]
            target[key] = translation
        # Canonical lists supply every displayed finding; optional free summaries
        # are not a second channel for unsupported narrative.
        data.pop("headline", None)
        data.pop("summary", None)
        if localized_text is None:
            data["summary"] = {
                "en": "This older report has no validated translation map. "
                "Original-language text is shown; regenerate for a bilingual report.",
                "zh": "此旧报告缺少经过验证的双语对照，目前显示原始语言文本。"
                "请重新生成以获得完整双语报告。",
            }
    headline = data.get("headline") or {"en": "Your Self-Portrait", "zh": "你的自我画像"}
    summary = data.get("summary", "")
    generated_at = escape(str(data.get("generated_at", "")))

    needs = _list_block(data.get("relationship_needs") or [], "needs")
    friction = _list_block(data.get("friction_points") or [], "friction")

    sections: list[str] = []

    guide = _guide_section(data)
    if guide:
        sections.append(guide)

    for section in (_coverage_section(data), _claims_section(data), _questions_section(data)):
        if section:
            sections.append(section)

    connection = _connection(data)
    if connection:
        sections.append(
            '<section class="card">'
            f"<h2>{_t('How you connect', '你如何与人连接')}</h2>"
            f'<div class="grid2">{connection}</div>'
            "</section>"
        )

    values = _chip_values(data)
    if values:
        sub = _t(
            "Schwartz basic human values (a loose lens, not a test)",
            "施瓦茨基本价值观（宽泛的视角，不是测验）",
        )
        sections.append(
            '<section class="card">'
            f"<h2>{_t('What you value', '你看重什么')}</h2>"
            f'<p class="section-sub">{sub}</p>'
            f'<div class="grid2">{values}</div>'
            "</section>"
        )

    wants = _wants_section(data)
    if wants:
        sections.append(wants)

    boundaries = _boundaries_section(data)
    if boundaries:
        sections.append(boundaries)

    market = _market_section(data)
    if market:
        sections.append(market)

    tensions = _tensions_section(data)
    if tensions:
        sections.append(tensions)

    if needs or friction:
        rel = ""
        if needs:
            rel += f"<h2>{_t('What you need', '你需要什么')}</h2>{needs}"
        if friction:
            heading = _t("Likely friction points", "可能的摩擦点")
            rel += f'<h2 style="margin-top:18px">{heading}</h2>{friction}'
        sections.append(f'<section class="card">{rel}</section>')

    edges = _growth_cards(data)
    if edges:
        sub = _t(
            "Gentle, and mostly things you already saw.",
            "温和的方向，大多是你自己已经看到的。",
        )
        sections.append(
            '<section class="card">'
            f"<h2>{_t('Growth edges', '成长的方向')}</h2>"
            f'<p class="section-sub">{sub}</p>'
            f"{edges}"
            "</section>"
        )

    how_to_use = _how_to_use_section(data)
    if how_to_use:
        sections.append(how_to_use)

    # Prefer the explained glossary; fall back to bare tags if that's all there is.
    glossary = _glossary_section(data)
    if glossary:
        sections.append(glossary)
    else:
        frameworks = data.get("frameworks_used") or []
        if frameworks:
            sections.append(
                '<section class="card">'
                f"<h2>{_t('Lenses used', '所用的视角')}</h2>"
                f'<div class="tags">{_tags(frameworks)}</div>'
                "</section>"
            )

    caveats = _list_block(data.get("caveats") or [], "")
    if caveats:
        sections.append(
            f'<section class="card caveats"><h2>{_t("Caveats", "说明")}</h2>{caveats}</section>'
        )

    body_sections = "\n".join(sections)
    eyebrow = _t("AI-SlowMatch · Self-Portrait", "AI-SlowMatch · 自我画像")
    disclaimer = _t(
        "A reflective mirror — not a diagnosis, score, or label.",
        "一面反思之镜——不是诊断、评分或标签。",
    )
    foot_left = _t("Report displayed on this device", "报告在本设备展示")
    foot_right = _t(
        "External AI receives only disclosures you approve.",
        "外部 AI 仅接收你审核并同意披露的内容。",
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Self-Portrait</title>
<style>{_CSS}</style>
</head>
<body class="lang-en">
<header class="hero">
  <button class="toggle" id="t" type="button">中文</button>
  <div class="hero-inner">
    <p class="eyebrow">{eyebrow}</p>
    <h1 class="headline">{_dual(headline)}</h1>
    <p class="summary">{_dual(summary)}</p>
    <div class="disclaimer">{disclaimer}</div>
  </div>
</header>
<main class="wrap">
{body_sections}
<p class="foot">{foot_left} · {generated_at} · {foot_right}</p>
</main>
<script>{_JS}</script>
</body>
</html>
"""
