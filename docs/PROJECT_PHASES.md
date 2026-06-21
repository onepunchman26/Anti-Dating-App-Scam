# Project Phases

## Phase 0 - Paper And Concept Alignment

- Align the repository with the AI-SlowMatch paper concept.
- Define ethics boundaries.
- Define vocabulary.
- Preserve the idea that the project is relationship trust infrastructure, not a dating app.

## Phase 1 - Python Core Engine

- Scam risk analyzer.
- Trust ladder engine.
- Safety policy.
- Mock provider.
- Tests for core risk, consent, and refusal behavior.

## Phase 2 - PySide6 Desktop GUI

- Local conversation input.
- Risk report view.
- Trust ladder view.
- Provider settings.
- Report export and verify view.

## Phase 3 - Local Document System

- Personal relationship profile JSON.
- Risk report JSON.
- Trust ladder JSON.
- JSON Schema validation.
- Markdown export.

## Phase 4 - Verifiable Reports

- Canonical JSON.
- Input hash.
- Prompt hash.
- Local keypair.
- Signature.
- Verification UI.
- Disclaimer that signature proves integrity and source only.

## Phase 5 - AI Provider Plugin System

- OpenAI adapter.
- Anthropic adapter.
- Gemini adapter.
- Ollama or local model adapter.
- Schema-constrained output.
- Provider registry.

## Phase 6 - Optional Local API Server

- Preserve FastAPI as an optional local server.
- Keep it out of the main product path.
- Use it for local automation, experiments, or integration tests.

## Phase 7 - Tauri Plus Python Sidecar

- Tauri GUI.
- Python engine as sidecar.
- Local file access through a controlled bridge.
- Stronger packaging.

## Phase 8 - Rust/Tauri Security Layer

- Signing and verification.
- Secure local storage.
- Key management.
- Packaging and update integrity.

## Phase 9 - Evaluation And Governance

- Synthetic test cases.
- Consented user testing only.
- False positive and false negative evaluation.
- Bias and safety review.
- Privacy red team.
