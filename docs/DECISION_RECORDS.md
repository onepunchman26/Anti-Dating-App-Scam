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

## ADR-012: Thin Rendezvous Server For Nearby Discovery (Amends ADR-001 Scope)

Status: Accepted (owner decision, 2026-07-06)

Context: The compatibility pillar (`docs/11_compatibility_matching_plan.md`) was designed
strictly peer-to-peer, which only works for two people already in contact. The owner now
wants nearby-location matchmaking between strangers, while keeping all profile data local,
with the platform authenticating exchanged matching information so users cannot privately
alter cards or craft per-target personas.

Decision: Add an **optional online rendezvous server** that is a bulletin board and a
notary, never a profile database. It stores only: pseudonym, client-derived coarse geohash
bucket, Tier-1 gate ranges, a contact channel hidden until mutual accept, and compatibility
card **fingerprints** with attestation history. Cards themselves travel person-to-person
(email/QR/file), encrypted, never through the server. Attestation provides tamper-evidence
and history transparency — explicitly not truth verification (same stance as ADR-008).

Consequences: ADR-001 stands for all personal data (local-first); this ADR narrowly
authorizes server-side *rendezvous metadata*. ADR-009 still forbids scoring: the server
gates only on location bucket + mutual Tier-1 ranges and never ranks. Discovery requires
the requester to have an attested card (no browsing without skin in the game). Full design:
`docs/12_rendezvous_matchmaking_plan.md`.

## ADR-013: Decentralized Rendezvous — No Single Operator, Minimal Server

Status: Accepted (owner decision, 2026-07-06)

Context: ADR-012's thin rendezvous server still implied one hosted service. The owner
requires that the rendezvous layer not depend on a server owned or rented by one person,
that it can ride on existing social platforms (Facebook, 小红书, etc.), and that server
requirements stay minimal because users bring their own AI for all analysis.

Decision: Three deployment models, no privileged operator. (A) **Private nodes** — the
node is a trivially self-hostable artifact (`run_rendezvous_node.py`, single small
machine); communities run their own, like private game servers, and users choose node
URLs. (B) **Platform relay, serverless** — armored, checksummed "beacon" text blocks
(`matchmaking/beacon.py`) that users post and copy **manually** on platforms they already
use; the app parses and matches locally; contact flows through the platform's own DMs;
no scraping or login automation, ever. (C) **Federation** of nodes — designed, deferred
until P1 keypair signatures exist.

Consequences: no single point of control or failure; the platform account becomes the
identity anchor in Model B (post timestamp = public witness), with honest limits — the
checksum stops corruption/casual edits, not determined forgery, until P1 Ed25519
signatures. Nodes must stay small (bulletin board + notary only); anything needing real
compute belongs client-side with the user's connected AI. Full design:
`docs/14_decentralized_rendezvous.md`.
