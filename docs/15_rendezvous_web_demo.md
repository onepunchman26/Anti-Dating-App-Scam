# 15 — Rendezvous Web Demo: deployable LBS matchmaking prototype

Status: shipped 2026-07-14 (P0 demo); packaged Windows client + connected-AI
self-model flow added 2026-07-15. Builds on docs/12 (ADR-012) and docs/14 (ADR-013).

## Packaged Windows client (2026-07-15)

`run_local_app.py` → `dist\AI-SlowMatch.exe` (PyInstaller onefile, ~15 MB,
`build_exe.ps1`). Zero-install for end users: double-click, it serves the UI on
**127.0.0.1 only** and opens the browser. The exe bundles:

- the web UI (frozen-mode `_MEIPASS` lookup in `rendezvous_app._default_web_dir`),
- `routes_local_ai.py` — local-only endpoints: connect AI (Ollama local /
  Anthropic API; key in process memory only), synthesize the self-model from
  imported data (anti-flattery contract, JSON output), parse ChatGPT export
  zips (temp file, deleted after), save/load the self-model at
  `~/.ai_slowmatch/self_model.json` + its fingerprint,
- a built-in matchmaking node (single-machine testing); the UI's "Matching
  node (advanced)" field points at a hosted node for real use (the node app
  now sends CORS headers for this).

The UI flow was reordered to the product thesis: **1 Connect AI → 2 import
own data → AI synthesis → editable self-model → save + fingerprint (all
local) → 3 basics (pseudonym/gender/seeking/age/contact/area) → register
auto-attests the saved fingerprint → 4-5 nearby/introductions/match.** When
the same UI is served by a plain node (no `/local/*`), AI features hide and
the manual + copy-prompt path remains.

### App shell (2026-07-15, owner feedback round)

The single scrolling page became a real app: a **first-run wizard** (every
step skippable) and then **Home dashboard + tabbed views** — Home (status
cards), **Chat**, Matching, My Model, Settings (AI tab / Data tab). Key
changes:

- **Chat is the centerpiece**: `/local/ai/chat` runs an interview contract
  (anti-flattery, one question per reply, flaw-analysis framed as patterns +
  practical improvements — never diagnosis/scores) over the user's inlined
  vault context (data folder + notes + current self-model). Template prompt
  chips cover flaw analysis, interview-me, communication style, readiness.
  `/local/ai/refine` distills a conversation into an updated self-model for
  review on the My Model page ("Generate with AI" is the same endpoint with
  an empty conversation).
- **Agent CLIs as backends**: `CliAgentBackend` (chat_backends.py) drives a
  locally installed Claude Code (`claude -p --output-format json`, session
  resume) or Codex CLI (`codex exec`, conversation inlined) — the user's own
  AI app/plan, no separate key. Resolved via `shutil.which` (Windows `.cmd`
  shims) and covered by fake-runner tests.
- **Data folder setting**: `/local/data/config` stores a user-chosen local
  folder (`client_settings.json`; never keys); `.txt/.md/.json` files are
  read at analysis time only. Pasted notes save to the vault
  (`imports/notes.md`). Backend choice persists and auto-reconnects on app
  start via `/local/ai/restore` (Anthropic re-asks for its key — memory-only).

### UX round 2 (2026-07-15): report-first Home + automated matching

- **Home = the AI report.** The self-model renders as the main page (value
  chips, narrative sections, evidence, fingerprint). Manual model editing is
  gone entirely — the model exists only as AI output (chat refine / generate
  from data), per the product thesis. Status cards became first-open prompts.
- **Automated matching.** Preferences (distance via nearby `?precision=3|4`,
  age, gender) + one start button: device location → register (auto-generated
  pseudonym if blank) → attest → a 12 s loop that discovers candidates and
  auto-requests introductions, logged in a timestamped activity feed (mirrored
  on Home). Accepting an introduction is never automated (double-blind consent
  rule). Identity (pseudonym/contact/consent/manual location/node URL) lives in
  Settings › Matching. True AI-to-AI negotiation is deferred to P2/federation:
  cards are private by design, so a node has nothing for an agent to screen.
- **Chat**: voice input via the Web Speech API (shown when the browser
  supports it), a data-first reminder, a zero-data interview mode, and
  `/local/ai/compare` — after a verified match the connected AI automatically
  writes the non-scoring compatibility reflection.
- **Backends**: + Gemini CLI preset and `OpenAICompatChatBackend` for any
  OpenAI-compatible endpoint (Doubao/Volcano Ark, DeepSeek, OpenAI, Kimi);
  keys stay memory-only.

### Deep analysis: the Chat-Analysis Module (system prompt v2, 2026-07-15)

The owner-authored analysis contract lives verbatim in
`src/anti_dating_scam/ai/analysis_contract.py` (evidence-or-silence claims with
per-claim confidence, the six-pass self-report consistency audit,
disclosure-volume guard, cognitive-bias-before-character, no label laundering,
social/dating-market lenses, hard no-scores/no-diagnosis exclusions).
`POST /local/ai/analyze` runs it over the inlined vault (refusing when there is
no data — the contract is evidence-bound) and writes
`reports/social_self_portrait.md` + `.json` (`generated_at` stamped
server-side; a transport addendum has chat backends return the two files as
delimited sections). `GET /local/report` serves it; Home renders it as the
primary "AI report" card; `_inline_context` feeds it into chat/refine/compare
so every downstream stage builds on the audited portrait. Reads are
BOM-tolerant (`utf-8-sig`) for hand-edited vault files.

Never mount `routes_local_ai` on a public node: it holds an AI key in memory
and writes local files. `create_client_app()` is the only place it is wired,
and `run_local_app.py` hard-binds 127.0.0.1.

## What it is

A complete, deployable demo of the location-based rendezvous pillar: the private-node
server (`run_rendezvous_node.py`) now serves a single-file web UI
(`apps/rendezvous_web/index.html`) so end users need **only a browser** — no Python,
no desktop app. The server side needs only `fastapi` + `uvicorn` (the matchmaking
core imports nothing heavier; PySide6 and the risk/journal engine are not loaded).

The demo realizes the owner's product thesis end-to-end:

1. Users enter a **pseudonym** (never a real name) and their **orientation**
   (expressed as `gender` + `seeking_genders`; no orientation label is stored).
2. Location comes from the browser's geolocation service, hashed **on-device** to a
   precision-4 geohash bucket; raw coordinates never leave the client.
3. Appearance, occupation, and income are deliberately absent. Everything beyond the
   Tier-1 gate lives in a **self-model card** the user distills from their own AI
   chats or exported social-media data (pasted or read locally from a file).
4. The card is attested by fingerprint (SHA-256 over canonical JSON, HMAC-signed);
   matching is bulletin-board only; comparison is **local and non-scoring**, with a
   copy-ready prompt for the user's own AI (bring-your-own-AI, ADR-013).

## Server pieces added

- `matchmaking/rendezvous.py`: mutual Tier-1 **gender gate** mirroring the age-gate
  semantics (no seeking set = everyone; unspecified gender passes only unfiltered
  seekers; seeking all known genders normalizes to no filter), plus
  `introductions_for()` — the introduction **inbox**. Without an inbox a recipient
  can never learn a pending introduction's id, so the double-blind flow could not
  complete outside of tests.
- **Access tokens** (post-review hardening): `register` issues a per-registration
  `secrets.token_urlsafe` secret; `authenticate()` is enforced by the routes on
  every other endpoint, so inboxes, match packets (contact channels!), attest,
  respond, and delete cannot be driven by merely *claiming* a pseudonym. Lost
  token = unusable registration until node restart (honest P0 limit, disclosed
  in the UI).
- **Lifecycle hardening** (post-review): initiator "decline" = *withdrawal*
  (introduction removed, pair NOT poisoned — declines only count from the
  recipient); a matched pair cannot receive a second introduction; `nearby`
  excludes declined pairs and pairs with a live introduction (no
  guaranteed-error buttons); `verify-card` requires matched state (no
  fingerprint oracle pre-accept); `unregister` also purges declined-pair records
  naming the pseudonym (docs/06 deletion right beats the decline block);
  geohash accepted only at precision 4-6 (shorter never matches, longer is
  coordinate-grade and never stored); pseudonym/contact are length-bounded with
  control chars and angle brackets rejected (untrusted display strings);
  adults-only age validation (18+, sane seeking ranges); dict iterations are
  snapshotted (sync routes run on a threadpool).
- `models/matchmaking.py`: `gender` / `seeking_genders` on `RegisterRequest`;
  `InboxEntry` / `InboxResponse`.
- `api/routes_matchmaking.py`: passthrough fields + `GET /matchmaking/introductions/{pseudonym}`.
- `api/rendezvous_app.py`: `create_rendezvous_app(web_dir)` — matchmaking router,
  the consent 403 handler, and the static UI mount only. `web_dir=None` = API-only.
- `run_rendezvous_node.py`: serves the UI by default (`--no-ui` to disable);
  `--demo-seed BUCKET` registers three clearly-marked synthetic users
  (`demo_star`, `demo_river`, `demo_moon`) so a lone tester sees a live nearby list.
  They never accept introductions.

## Web UI flow (apps/rendezvous_web/index.html)

Single file, vanilla JS, bilingual (EN / 简体中文 toggle, full translations), no
external assets (works on a LAN with no internet). Steps: register → build/attest
card → nearby → introductions inbox (5 s polling) → match packet (contact reveal) →
card exchange + `/verify-card` fingerprint check → local non-scoring reflection
(shared/differing values, side-by-side texts, discussion prompts) + AI hand-off
prompts. Includes a delete-my-data action (docs/06 deletion rule) and an anti-scam
"slow down" reminder in the match view.

Per-tab identity uses `sessionStorage` (two browser tabs = two demo users);
cards persist per-pseudonym in `localStorage` and never leave the device except the
one-time attest POST (hashed server-side and discarded — see Honest limits).

## Deploy

```bash
pip install fastapi uvicorn
python run_rendezvous_node.py --host 0.0.0.0 --port 8470 [--demo-seed wtw3]
```

- **TLS is required for real use**: browsers only expose geolocation and Web
  Crypto (client-side card hashing) on secure contexts (https:// or localhost).
  On plain http the UI falls back to manual location entry and to sending the
  card once for server-side hashing. Put Caddy/nginx in front.
- State is **in-memory** (P0): a restart clears all registrations. The UI detects
  "Unknown pseudonym" in its poller and resets to the registration step with an
  explanation instead of leaving stale actionable buttons.
- Auth is a **bearer token per registration** (P0): no accounts, no recovery,
  token lives in the browser tab's sessionStorage. Full P2 hardening
  (persistence, rate limits, block/report, real accounts) is tracked in
  docs/12 §6.

## Honest limits (do not oversell in user-facing copy)

- Preferred attest path sends only a client-computed SHA-256 fingerprint — the
  JS canonical-JSON implementation was verified byte-compatible with
  `reports/canonical_json.py` end-to-end (JS-attested lock, Python-verified
  match and tamper verdicts agree). The full-card fallback path still exists
  for non-secure contexts and is disclosed in the UI copy.
- Attestation proves integrity + rewrite history, never truth (ADR-008/ADR-012).
- Prefix geohash matching misses cross-border neighbors (accepted P0 limitation —
  do not "fix" by raising precision; see geo.py docstring).

## Test coverage

`tests/test_matchmaking_rendezvous.py` (gender gate, normalization/validation,
inbox both directions, withdrawal vs decline, matched-pair duplicate block,
nearby exclusions, declined-pair purge on unregister, geohash bounds, adults-only
and clean-text validation, fingerprint attest, verify-requires-match, token auth)
and `tests/test_matchmaking_api.py` (orientation over HTTP, inbox flow, token
rejection, fingerprint attest interop, lean app serves UI + 403 consent +
API-only mode). Full suite: 140 passing. The complete two-user flow — including
withdraw/re-introduce, attacker 400s on inbox/match without a token, local +
server-side verify agreement, tamper detection, delete-reset, and the zh-CN
toggle — was verified in a real browser against a running node. The changes also
went through a multi-agent adversarial review (5 lenses, 3-vote verification);
all confirmed findings were fixed and re-verified.
