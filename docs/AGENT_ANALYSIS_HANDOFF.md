# Agent Analysis Handoff

In Agent Mode the desktop app does **not** run analysis itself. Its job is to
provide two things only:

1. **Rules** — the safety boundaries and the framing the agent must follow.
2. **Data-saving standard** — exactly which files are input, and which files the
   agent must write the result to.

A desktop agent (Claude Code / Cowork) opens the vault, reviews everything, and
synthesizes the output. This keeps responsibility and data local and visible: the
app is a thin contract layer, the agent is the analyst.

## Primary task: self-understanding (self-portrait)

The imported data is the **user's own** chat history and notes. The first and
primary task is to understand *the user*: `agent_handoff.build_self_portrait_request`
writes `SELF_PORTRAIT_REQUEST.md`, asking the agent to read all of `imports/` +
`profile/` and build a deep, theory-grounded personality portrait, grounded in
named frameworks across disciplines:

- psychology — Big Five / OCEAN, attachment theory, Schwartz values, self-determination;
- sociology — Goffman (front/back stage), symbolic interactionism, Bourdieu;
- philosophy — authenticity / existential themes, virtue and care ethics.

Outputs (the data-saving standard):

- `reports/self_portrait.md` — **simple, visual, for the user**. Rendered in-app
  with text/emoji trait bars (`◉`/`○`).
- `reports/self_portrait.detailed.md` — **detailed, for the agent to follow** in
  later steps (framework-by-framework, evidence quotes, citations).
- `reports/self_portrait.json` — structured companion (Big Five 0–1, attachment
  style, top values, needs, growth edges, evidence map). The desktop app renders a
  polished, **offline** visual report `reports/self_portrait.html` from this JSON
  (`self_portrait_html.py`) — hero, animated trait bars, value/growth cards, EN/中文
  toggle, no external requests. The agent writes the `.md` / `.detailed.md` / `.json`;
  the app owns the HTML rendering.

Rules: a reflective lens, not a diagnosis; no score of the user's worth; trait
estimates are descriptive tendencies; people change; warm and specific; nothing
leaves the vault.

## Second stage: criteria discovery interview

After the self-portrait, `build_criteria_interview_request` writes
`CRITERIA_INTERVIEW_REQUEST.md`: the agent interviews the user interactively in chat
(gap-driven, contradiction-probing, forced trade-offs), then presents 5–7 realistic
ideal-partner vignettes (genuine flaws, no Pareto-superior option) for the user to
rank — choices reveal criteria better than statements. Output: verbatim transcript
in `imports/interview/`, candidates + choices in `reports/ideal_partner_profiles.json`,
and a stated-vs-revealed synthesis in `reports/mate_criteria.md` + `.json`. The
contract mandates a non-sycophantic stance: evidence over agreement, no flattery,
incisive about criteria while kind to the person. Full design:
`docs/13_criteria_discovery_interview.md`.

## Secondary task: conversation risk (scam read)

## The vault as a contract

```text
<vault>/
  profile/                # input: the user's own reflection (MPMD + JSON)
  imports/                # input: notes, exported chats, conversation_to_review.md
  reports/                # output: the agent writes the report here
  ANALYSIS_REQUEST.md     # the contract: rules + data manifest + output spec
  AGENTS.md / CLAUDE.md   # standing vault guidance for any agent
```

- **Input** = every file under `profile/` and `imports/`. The app never asks the
  agent to read anything outside the vault.
- **Output** = `reports/risk_report.md` (human-readable, fixed sections) plus a
  `reports/risk_report.json` companion whose keys mirror the `risk_report` schema
  (`src/anti_dating_scam/schemas/risk_report.schema.json`) so the local tooling can
  still load/verify it.

## Who writes what

- `apps/desktop_pyqt/anti_dating_scam_desktop/agent_handoff.py` builds
  `ANALYSIS_REQUEST.md` and the copyable prompt. It performs **no** analysis.
- `ProfileStore` provides the I/O standard: `save_import_text`,
  `write_analysis_request`, `find_latest_report`.
- The **Ask Your Agent to Analyze** screen wires these together: optionally save a
  pasted conversation into `imports/`, write the request, show the prompt, and open
  the vault. The **View Report** screen reads back whatever the agent wrote.

## Rules embedded in every request

Mirrors the project's Safety Boundaries (`AGENTS.md`):

- decision-support, not a verdict; stay uncertainty-aware;
- no personality scores / good-or-bad-person labels;
- no spying, doxxing, harassment, or revenge advice;
- never encourage sending money, private images, or identity documents;
- do not frame risk as a property of one gender;
- privacy-first: nothing leaves the vault.

## Offline fallback

The earlier deterministic engine (`ScamRiskAnalyzer`, `TrustLadderEngine`,
`ReportGenerator`) still exists and is reachable from **Offline Tools** on the Home
hub, for use without an agent. Agent Mode is the recommended path.
