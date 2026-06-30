# Decision Records

## ADR-001: Local-First Instead Of Cloud-First

Status: Accepted

Context: The project handles sensitive relationship conversations, risk reflections, and potentially personal profile documents.

Decision: The product direction is local-first. User data should live in user-owned local files unless a future feature explicitly asks for remote storage with consent.

Consequences: More responsibility moves to local file format design, export, deletion, and verification. The project avoids platform-style data centralization.

## ADR-002: GUI-First Instead Of API-First

Status: Accepted

Context: A FastAPI prototype is useful for tests and contracts, but the user-facing product is a local desktop trust tool.

Decision: The GUI is the primary interaction surface for the current phase. FastAPI is retained only as an optional local API.

Consequences: Core services must stay UI-independent, and API routes should wrap engine behavior rather than own business logic.

## ADR-003: Python Core For Early AI Engine

Status: Accepted

Context: AI providers, schema validation, and safety logic need fast iteration.

Decision: Keep the core engine in Python for early phases.

Consequences: Python remains the source of truth for analyzers, provider adapters, tests, and schema workflows until a later migration justifies moving pieces to Rust or another language.

## ADR-004: PySide6 For Early Desktop GUI

Status: Accepted

Context: The project needs a local desktop GUI before a full Tauri migration is worth the extra build complexity.

Decision: Use PySide6 for the first desktop GUI shell.

Consequences: The GUI can ship quickly while sharing Python models and services. The UI should be modular so a future shell can replace it.

Implementation note 2026-06-21: `apps/desktop_pyqt/` and `run_desktop.py` now provide the first runnable PySide6 MVP path. GUI widgets call the Python core engine and should not own safety or report-generation business logic.

## ADR-005: Future Tauri Plus Python Sidecar Migration

Status: Proposed

Context: Tauri offers a strong desktop shell and Rust integration, but the engine is still evolving.

Decision: Treat Tauri plus Python sidecar as a medium-term migration path.

Consequences: Keep engine APIs clean, file formats stable, and side-effect boundaries explicit so a sidecar bridge can be added later.

## ADR-006: JSON Schema Over XML As Primary Format

Status: Accepted

Context: The project needs inspectable, testable, signable documents that work across Python, Rust, and potential GUI shells.

Decision: Use JSON and JSON Schema as the primary data contract. XML may be optional import/export only.

Consequences: Report, profile, and trust ladder files should validate against JSON Schema before signing or display.

## ADR-007: Provider Plugin Architecture

Status: Accepted

Context: The AI layer must avoid vendor lock-in and hard-coded provider behavior.

Decision: Use provider adapters behind a common interface and a registry.

Consequences: GUI code should select providers through the registry. Provider outputs must be structured and schema-validated before report generation.

## ADR-008: Verifiable Reports Via Signatures, Not Truth Claims

Status: Accepted

Context: Users may need report integrity checks, but the app cannot prove real-world truth.

Decision: Signed reports prove schema-valid content integrity and signing source only.

Consequences: Every signing and verification view must include a disclaimer that signatures do not prove authenticity, completeness, wrongdoing, or relationship safety.

## ADR-009: No Public Personality Score

Status: Accepted

Context: A public score would turn a safety tool into reputation infrastructure or social credit.

Decision: The system must not create public personality scores, deterministic morality labels, or public dating rankings.

Consequences: Any local report should use risk signals and uncertainty notes, not "good person" or "bad person" labels.

## ADR-010: FastAPI Retained Only As Optional Local API

Status: Accepted

Context: Existing FastAPI routes provide useful contracts and tests.

Decision: Keep FastAPI only as an optional local API server.

Consequences: Future work should move core logic into engine modules and keep API code thin. Documentation should not present the app as a cloud backend.

## ADR-011: Ollama Adapter Implemented With Stdlib HTTP, No New Dependency

Status: Accepted

Context: Phase 2 calls for an Ollama (local) provider adapter as the recommended default AI path, since it keeps imported chat/profile data on-device. The project has no existing HTTP client dependency (`httpx` is dev/test-only, used for FastAPI's `TestClient`).

Decision: Implement `OllamaClient` using only Python's stdlib `urllib`, with an injectable `transport` callable so unit tests never need a live Ollama server or network access. Provide two thin adapters around the same client: one for the `LLMClient` protocol (services), one for the `AIProvider` protocol (registry/Settings UI).

Consequences: No new third-party dependency was added for this feature. The `LLMClient`-side adapter raises `OllamaUnavailableError` on failure (services should know loudly if their AI call didn't happen); the `AIProvider`-side adapter instead catches that error and returns a readable error in its output dict, because the Settings screen calls providers synchronously in the UI thread and must not crash. If a richer Ollama feature set (streaming, embeddings, model pull/list) is needed later, revisit whether stdlib `urllib` is still sufficient or whether `httpx` should be promoted to a core dependency.
