# Future Codex Tasks

This backlog is designed for future Codex sessions. Each task should update `docs/AI_DEVELOPMENT_LOG.md` when completed or materially changed.

## Build PySide6 Minimal GUI Shell

Goal: Create the first local desktop shell with tabs for risk analysis, trust ladder, provider settings, and report export/verify.

Files likely involved: `apps/desktop_pyqt/main.py`, `apps/desktop_pyqt/anti_dating_scam_desktop/app.py`, `apps/desktop_pyqt/anti_dating_scam_desktop/main_window.py`, `pyproject.toml`.

Acceptance criteria: The app opens locally, shows all required tabs, and exits cleanly.

Test command: `python -m compileall src apps`

Safety notes: Do not add cloud accounts, analytics, hidden scraping, or real sample data.

## Connect GUI To ScamRiskAnalyzer

Goal: Let the conversation tab run local risk analysis through the Python engine.

Files likely involved: `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/conversation_input.py`, `src/anti_dating_scam/services/scam_risk_analyzer.py`, tests.

Acceptance criteria: Consent is required, output shows risk level, signals, uncertainty notes, and safe next steps.

Test command: `pytest`

Safety notes: Keep wording non-accusatory and refuse abusive requests.

## Add Provider Settings Screen

Goal: Add a local settings tab for Mock, OpenAI placeholder, Anthropic placeholder, Gemini placeholder, and Ollama placeholder.

Files likely involved: `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/provider_settings.py`, `src/anti_dating_scam/providers/registry.py`.

Acceptance criteria: Provider choices display, API key field exists, and the UI warns not to commit secrets.

Test command: `python -m compileall src apps`

Safety notes: Never commit real keys or write secrets to tracked files.

## Add Local Profile JSON Editor

Goal: Create and edit local personal relationship profile documents.

Files likely involved: `src/anti_dating_scam/schemas/personal_profile.schema.json`, `src/anti_dating_scam/engine/personal_profile_builder.py`, GUI widgets.

Acceptance criteria: Profile JSON validates against schema and contains no real sample secrets.

Test command: `pytest tests/test_schema_validation.py`

Safety notes: Do not call this "training a personal model."

## Add Report Export As JSON And Markdown

Goal: Export schema-valid risk reports to JSON and readable Markdown.

Files likely involved: `src/anti_dating_scam/reports/export_markdown.py`, `src/anti_dating_scam/engine/report_generator.py`, GUI export view.

Acceptance criteria: JSON report validates, Markdown includes disclaimer, and outputs are generated locally.

Test command: `pytest`

Safety notes: Reports must not contain deterministic accusations.

## Add JSON Schema Validation

Goal: Implement reusable validation for profile, risk report, and trust ladder schemas.

Files likely involved: `src/anti_dating_scam/reports/schema_validator.py`, `src/anti_dating_scam/schemas/*.json`, tests.

Acceptance criteria: Valid fixtures pass and malformed fixtures fail with useful errors.

Test command: `pytest tests/test_schema_validation.py`

Safety notes: Provider output must not become trusted report data until validated.

## Add Local Report Signing

Goal: Canonicalize reports, hash them, sign locally, and attach signature metadata.

Files likely involved: `src/anti_dating_scam/reports/canonical_json.py`, `src/anti_dating_scam/reports/signer.py`, tests.

Acceptance criteria: Signing is deterministic over canonical content and signed reports still validate.

Test command: `pytest tests/test_report_signing.py`

Safety notes: Signature proves integrity and source only, not truth.

## Add Report Verification Screen

Goal: Add a GUI flow to verify report schema, hash integrity, and signature status.

Files likely involved: `apps/desktop_pyqt/anti_dating_scam_desktop/widgets/report_verifier_view.py`, `src/anti_dating_scam/reports/verifier.py`.

Acceptance criteria: UI reports valid, modified, unknown signer, and invalid schema states.

Test command: `pytest`

Safety notes: Always display the signature limitation disclaimer.

## Add Ollama Provider

Goal: Implement a local-model provider adapter for Ollama.

Files likely involved: `src/anti_dating_scam/providers/ollama_provider.py`, `src/anti_dating_scam/providers/registry.py`.

Acceptance criteria: Adapter returns structured dict output and handles unavailable local service gracefully.

Test command: `pytest tests/test_provider_registry.py`

Safety notes: Local model output must pass schema validation before report generation.

## Add OpenAI Provider

Goal: Implement an OpenAI provider adapter behind the provider interface.

Files likely involved: `src/anti_dating_scam/providers/openai_provider.py`, `.env.example`, provider tests.

Acceptance criteria: No hard-coded keys, structured output path exists, and missing key errors are clear.

Test command: `pytest tests/test_provider_registry.py`

Safety notes: Do not log prompts or API keys by default.

## Add Tauri Migration Research Scaffold

Goal: Document how Tauri plus Python sidecar would work before implementing it.

Files likely involved: `docs/08_migration_to_tauri.md`, `docs/DECISION_RECORDS.md`.

Acceptance criteria: Research doc lists bridge options, packaging concerns, file access rules, and security boundaries.

Test command: `git diff --stat`

Safety notes: Do not start a Tauri rewrite before schemas and desktop flows stabilize.

## Add Tauri Prototype Shell

Goal: Create a minimal Tauri shell that can eventually call the Python engine.

Files likely involved: `apps/tauri/`, docs.

Acceptance criteria: Prototype launches and contains no duplicate business logic.

Test command: `cargo check` if Rust tooling exists, plus `python -m compileall src`.

Safety notes: Keep sensitive file access behind explicit user actions.

## Add Python Sidecar Bridge

Goal: Define a command protocol between Tauri and the Python engine.

Files likely involved: `src/anti_dating_scam/sidecar/`, `apps/tauri/src-tauri/`.

Acceptance criteria: Bridge can run a risk analysis command with synthetic input and return schema-valid JSON.

Test command: `pytest`

Safety notes: Validate all inputs and outputs at the bridge boundary.

## Move Report Signing To Rust

Goal: Move signing and verification to a Rust/Tauri layer after Python behavior is proven.

Files likely involved: `apps/tauri/src-tauri/`, `src/anti_dating_scam/reports/`, tests.

Acceptance criteria: Rust signing matches canonical JSON expectations and Python tests verify interoperability.

Test command: `cargo test` and `pytest`

Safety notes: Do not change the signature disclaimer.

## Add Privacy Red-Team Checklist

Goal: Expand privacy review into a repeatable checklist.

Files likely involved: `docs/07_evaluation_plan.md`, `docs/SAFETY_BOUNDARIES.md`.

Acceptance criteria: Checklist covers local files, logs, provider calls, reports, GUI screenshots, and fixtures.

Test command: `git diff --stat`

Safety notes: Assume relationship data is sensitive by default.

## Add Synthetic Dataset Generator

Goal: Generate synthetic scam, low-risk, and ambiguous cases for evaluation.

Files likely involved: `src/anti_dating_scam/evaluation/`, `examples/`, tests.

Acceptance criteria: Generator emits no real personal data and labels expected risk levels.

Test command: `pytest`

Safety notes: Do not create manipulative scam scripts; use defensive synthetic summaries.

## Add User Consent Flow

Goal: Make consent explicit in GUI and document workflows before analysis or persistence.

Files likely involved: GUI widgets, `src/anti_dating_scam/services/consent_manager.py`, docs.

Acceptance criteria: No analysis, save, export, or provider call occurs without explicit user action.

Test command: `pytest`

Safety notes: Consent must be clear, revocable in future storage phases, and separate from provider API use.
