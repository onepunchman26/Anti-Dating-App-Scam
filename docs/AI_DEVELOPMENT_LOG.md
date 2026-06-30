# AI Development Log

## Entry Template

Date:
Branch:
Codex task:
Intent:
Files changed:
Tests run:
Result:
Known limitations:
Next task:
Safety review:

## Initial Entry

Date: 2026-06-21
Branch: docs/project-architecture-memory
Codex task: Create durable project planning, architecture memory, and future-Codex scheduling documents.
Intent: Preserve the long-term direction of AI-SlowMatch without relying on chat history.
Files changed:
- `docs/ARCHITECTURE_MEMORY.md`
- `docs/PROJECT_PHASES.md`
- `docs/DECISION_RECORDS.md`
- `docs/FUTURE_CODEX_TASKS.md`
- `docs/VOCABULARY.md`
- `docs/SAFETY_BOUNDARIES.md`
- `docs/AI_DEVELOPMENT_LOG.md`
- `AGENTS.md`
Tests run:
- `python -m compileall src apps`: exited successfully, but reported `Can't list 'apps'` because the docs-only branch has no GUI app directory yet.
- `pytest`: failed in this shell because `pytest.exe` is not on PATH.
- `python -m pytest`: passed, 12 tests passed with 1 existing FastAPI/TestClient deprecation warning.
Result: Documentation archive created to record local-first, GUI-first, provider-agnostic, schema-valid, signed-report project direction.
Known limitations: This task does not implement PySide6 GUI, local profile schemas, provider adapters, report signing, or Tauri migration code. The `apps/` directory is still future work.
Next task: Build the PySide6 minimal GUI shell or add JSON Schema validation, depending on whether UI or data contracts should come first.
Safety review: Docs reinforce no public scoring, no deterministic accusations, no hidden scraping, no retaliation features, and no real user data in the repo.

## Runnable Desktop MVP Entry

Date: 2026-06-21
Branch: feat/runnable-local-python-desktop-mvp
Codex task: Add a runnable local Python desktop MVP.
Intent: Shift the immediate runnable product path from FastAPI-first to `python run_desktop.py` launching a PySide6 local-first trust tool.
Files changed:
- `run_desktop.py`
- `apps/desktop_pyqt/`
- `src/anti_dating_scam/engine/`
- `src/anti_dating_scam/reports/`
- `src/anti_dating_scam/providers/`
- `src/anti_dating_scam/schemas/`
- `examples/`
- `tests/`
- `README.md`
- `docs/QUICKSTART_LOCAL_APP.md`
- `docs/CHATGPT_DATA_IMPORT.md`
- `docs/PERSONAL_PROFILE_FORMAT.md`
- `docs/VERIFIABLE_REPORTS.md`
- `docs/SAFETY_BOUNDARIES.md`
- `pyproject.toml`
Tests run:
- `python -m compileall src apps run_desktop.py`: passed.
- `pytest`: initially failed because `pytest.exe` was not on PATH in this shell.
- `pytest` after adding the user Python Scripts directory to PATH: passed, 26 tests passed with 1 existing FastAPI/TestClient deprecation warning.
- `python run_desktop.py` before PySide6 install: showed the expected clear dependency message.
- `pip install -e ".[desktop]"`: failed in this Windows environment because PySide6 hit a Windows Long Path support limitation during install.
Result: Root launcher, PySide6 app scaffold, local profile generation, ChatGPT export metadata parsing, risk analysis, trust ladder evaluation, provider settings placeholders, schema validation, JSON/Markdown report export, and hash-based integrity verification are implemented.
Known limitations: PySide6 GUI was not launched in this environment because installing PySide6 failed due Windows Long Path support. Hash-based report signing is an MVP integrity check, not full cryptographic keypair signing. Provider adapters beyond Mock are placeholders and make no remote calls.
Next task: Resolve local PySide6 installation on Windows or add a CI-friendly GUI smoke test, then implement real local keypair signing.
Safety review: The MVP requires consent before analysis in the GUI, processes ChatGPT export files locally, avoids real user data in repo fixtures, uses non-accusatory risk language, and keeps provider API keys out of tracked files.

## Assisted Browser Export Architecture

Date: 2026-06-21
Branch: feat/assisted-local-browser-export-architecture
Codex task: Add a compliant local browser-assisted export automation module.
Intent: Add user-assisted local export support for the user's own AI chat history without creating a stealth scraper, login bypasser, cookie/token extractor, or data exfiltration tool.
Browser automation safety boundaries:
- visible/headed browser sessions for real export;
- manual login only;
- consent required;
- bounded `max_chats_per_run`;
- no cookies, tokens, passwords, localStorage, sessionStorage, hidden API responses, CAPTCHA bypass, private API reverse engineering, uploads, fake evidence, or impersonation;
- session logs record file metadata only, not full chat contents.
Files created:
- `src/anti_dating_scam/browser_export/`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/assisted_browser_export_page.py`
- `docs/ASSISTED_BROWSER_EXPORT.md`
- `docs/CHAT2FILE_AUTOMATION_LIMITS.md`
- `docs/BROWSER_EXPORT_SAFETY.md`
- browser export tests under `tests/`
Tests run:
- `python -m compileall src apps run_desktop.py`: passed.
- `pytest` with the user Python Scripts directory added to PATH: passed, 34 tests passed with 1 existing FastAPI/TestClient deprecation warning.
- `python -m ruff check .`: passed.
Known limitations: Chat2file-assisted mode builds a safe plan but does not force extension popup automation. Playwright is optional and imported lazily. Native visible-page export captures only visible rendered text and may be incomplete.
Next task: Add an end-to-end manual smoke test for Playwright visible browser launch on a machine with Playwright browsers installed, then connect exported visible-page JSON files more deeply into profile generation.
Safety review: The module centers user consent, visible local automation, local files, bounded runs, and refusal of browser secret extraction or platform bypass.

## Desktop Onboarding Flow

Date: 2026-06-21
Branch: feat/desktop-onboarding-flow
Codex task: Refactor the desktop GUI from a tab dashboard into an app-like onboarding flow.
Goal: Make startup feel like a normal consumer app: Welcome, Safety & Consent, Local Profile detection, Agent/API Mode selection, Import Data, Generate/Load Profile, then Home.
Files changed:
- `apps/desktop_pyqt/anti_dating_scam_desktop/main_window.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/app_state.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/profile_store.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/navigation.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/style.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/app_card.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/primary_button.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/secondary_button.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/status_banner.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/step_header.py`
- `src/anti_dating_scam/profile/`
- `docs/GUI_FLOW.md`
- `docs/LOCAL_PROFILE_MPMD.md`
- `docs/AGENT_MODE_VS_API_MODE.md`
Flow implemented:
`Welcome -> Policy -> Profile Detection -> Agent/API Mode -> Import Data -> Generate/Load Profile -> Home`.
Tests run:
- `python -m compileall src apps run_desktop.py`: passed.
- `pytest` with the user Python Scripts directory added to PATH: passed, 41 tests passed with 1 existing FastAPI/TestClient deprecation warning.
- `python -m ruff check .`: passed.
Limitations: GUI interaction tests are limited to non-GUI state/store/converter tests. Existing feature widgets are reused behind home-card screens and still use a compatibility dict bridge internally.
Next task: Add a lightweight GUI smoke test once PySide6 installation is stable on the target Windows machine.
Safety review: Policy appears before import or analysis, local profiles default to `~/.ai_slowmatch/`, Agent Mode avoids automatic API calls, and API Mode is explicitly marked as a placeholder.

## Phase 1 Taxonomy/Onboarding Fixes + Ollama Provider Adapter

Date: 2026-06-28
Codex task: Work Phase 1 ("MVP polish") and the Ollama half of Phase 2 ("Real provider hookup") per `PLAN_FOR_ONEPUCHMAN.md` / `PROGRESS_TRACKER.md`.
Intent: Close the two remaining Phase 1 checklist items, then add the first real (non-placeholder) AI provider adapter.
Changes:
- `src/anti_dating_scam/services/trust_ladder_engine.py`: trust-ladder risk detection previously used its own small hardcoded substring lists (`high_risk_terms`, `pressure_terms`), which had drifted out of sync with the scam-risk analyzer's `RISK_RULES` taxonomy. Refactored to import and reuse `RISK_RULES` (compiled regex, by rule name) as the primary check, keeping the old substring lists as a legacy fallback for backward compatibility.
- `apps/desktop_pyqt/anti_dating_scam_desktop/app_state.py`: fixed a data-loss bug in `sync_from_legacy_dict`. `MainWindow._go_home` is shared by screens that mutate `legacy_state` and screens (profile detection/generation) that write directly to `AppState` and never touch `legacy_state`; the latter case meant `legacy_state["profile"]` was always `None`, and a plain dict `.get()` pull would silently wipe a profile the user just loaded or created. Added a `_present()` helper so a field is only overwritten when the legacy dict actually carries a non-empty value.
- `src/anti_dating_scam/ai/ollama_provider.py` (new): `OllamaClient` — stdlib-only (`urllib`) HTTP wrapper around Ollama's `/api/generate` endpoint, with an injectable `transport` callable so tests don't need a real Ollama install or network access. `OllamaAIProvider` adapts it to the `LLMClient` protocol (`generate_structured`) used by services like `ScamRiskAnalyzer`. Raises `OllamaUnavailableError` rather than silently returning a fake success when the local server can't be reached — consistent with the project's uncertainty-aware-by-default stance.
- `src/anti_dating_scam/providers/ollama_provider.py` (new): `OllamaAIProviderAdapter` adapts the same `OllamaClient` to the `AIProvider` protocol (`.analyze`) used by `providers/registry.py` and the desktop Settings screen. Unlike the `LLMClient` adapter, `.analyze` catches `OllamaUnavailableError` and returns a readable error in the output dict instead of raising, because the Settings screen calls providers synchronously and must not crash on an unreachable local server.
- `src/anti_dating_scam/providers/registry.py`: `get_provider("Ollama")` now returns the real `OllamaAIProviderAdapter` instead of `PlaceholderProvider("Ollama")`. OpenAI/Anthropic/Gemini remain placeholders.
- Tests added: `tests/test_engine_trust_ladder.py` (+3), `tests/test_trust_ladder_engine.py` (+2), `tests/test_app_state.py` (+2), `tests/test_ollama_provider.py` (new, 7 tests covering the client, both adapters, and the unavailable-server path via injected fake transports).
Tests run:
- `python -m compileall src`: passed (sandbox used a Python 3.10 + `sitecustomize.py` polyfill for `enum.StrEnum`/`datetime.UTC` since this sandbox has no Python 3.11; the actual repo still requires Python 3.11+ per `AGENTS.md`).
- `pytest`: 54 passed (up from 41 at the start of this session), no real network access used anywhere.
Result: Both outstanding Phase 1 checklist items are done. Phase 2's Ollama item is done; the cloud-provider item and the local-vs-API UI toggle remain open.
Known limitations: No real Ollama server was actually contacted in this sandbox (no network egress); correctness of the adapter against a live Ollama instance should be smoke-tested by the user once they're working in their normal environment. The desktop Settings screen does not yet show the `OllamaUnavailableError` message to the user in the UI — `ProviderSettingsPage` still only lets the user pick a provider name, it doesn't call `.analyze()` to test connectivity.
Next task: Wire a real cloud LLM provider (OpenAI or Anthropic) behind the same interfaces, then add the user-facing local-vs-API toggle with a privacy explanation.
Safety review: No provider call happens unless explicitly selected by the user; Ollama defaults to `localhost` only; failures are surfaced, never silently swallowed; no API keys or secrets were added to tracked files.

## Bilingual Desktop GUI Pass

Date: 2026-06-30
Codex task: Make the entire PySide6 desktop GUI bilingual (English + Simplified Chinese) per user instruction: "The run_desktop.py gui and all other frontend should also be bilanguege."
Intent: Extend the project's existing bilingual rule (previously scoped to human-facing docs) to cover every user-visible string in the desktop app — window title, screen headers/subtitles, buttons, labels, placeholders, dialog captions, status messages, error messages, and the CLI dependency error in `run_desktop.py`.
Approach: Added a thin `bi(en, zh) -> str` helper in `apps/desktop_pyqt/anti_dating_scam_desktop/i18n.py` that composes `"English / 中文"` display strings at the call site, requiring no locale framework or runtime switching. All widget base classes (`StepHeader`, `StatusBanner`, `PrimaryButton`, etc.) were confirmed to contain no hardcoded text and needed no changes.
Files changed:
- `apps/desktop_pyqt/anti_dating_scam_desktop/i18n.py` (new): `bi()` bilingual helper
- `apps/desktop_pyqt/anti_dating_scam_desktop/main_window.py`: window title
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/welcome_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/policy_consent_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/profile_detection_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/analysis_mode_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/import_data_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/profile_generation_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/home_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/profile_viewer_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/risk_analysis_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/trust_ladder_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/report_export_verify_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/assisted_browser_export_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/screens/provider_settings_screen.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/provider_settings_page.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/conversation_analysis_page.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/trust_ladder_page.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/report_export_verify_page.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/assisted_browser_export_page.py`
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/consent_page.py` (dead/unreferenced widget, still bilingual-ized for consistency)
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/profile_import_page.py` (dead/unreferenced widget, same)
- `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/profile_view_page.py` (dead/unreferenced widget, same)
- `run_desktop.py`: CLI stderr dependency message
Tests run:
- `python -m compileall apps/desktop_pyqt run_desktop.py`: passed (no syntax errors).
- `pytest`: 54 passed, 1 warning — same count as prior session, no regressions (sandbox used Python 3.10 with the established `sitecustomize.py` polyfill for `datetime.UTC` / `enum.StrEnum`).
Result: Every human-visible string in the desktop GUI and its CLI launcher is now displayed in both English and Simplified Chinese.
Known limitations: The bilingual format is static inline composition (`"English / 中文"`), not a runtime locale-switch. If a future phase wants a single-language mode, a locale enum and per-string lookup table would be needed. The `assisted_browser_export_page.py` has a large number of dynamic `setText(...)` status strings; those have been bilingual-ized but were not smoke-tested interactively (requires PySide6 + Playwright, not available in this sandbox).
Next task: Wire a real cloud LLM provider (OpenAI or Anthropic), or add the local-vs-API toggle UI — whichever the user prioritizes next.
Safety review: No logic changes; only display strings were modified. All existing safety boundaries (consent gate, local-only processing, no scraping, no public scores) remain untouched.
