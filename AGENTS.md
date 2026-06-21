# AGENTS.md

## Mission

Anti-Dating-App-Scam is an AI-SlowMatch prototype for scam awareness and relationship-trust infrastructure. Build tools that help users slow down, preserve autonomy, and avoid unsafe online intimacy patterns.

## Safety Boundaries

- Do not create public personality scores, social-credit rankings, or deterministic "good/bad person" labels.
- Do not advise spying, doxxing, hacking, impersonation, harassment, revenge, or bypassing dating-app moderation.
- Do not encourage users to send money, private images, identity documents, or sensitive information to online-only romantic contacts.
- Do not use gender-hostile language or frame risk as a property of one gender.

## Coding Style

- Use Python 3.11+.
- Keep FastAPI routes thin and put behavior in services.
- Use Pydantic models for API inputs and outputs.
- Keep AI provider code behind interfaces; do not hard-code vendor-specific calls.
- Current phase is GUI-first: PySide6 desktop code should call the core engine, not own business logic.
- The core engine must remain UI-independent so it can later be reused by PySide6, optional FastAPI, Tauri, or a Python sidecar.
- Provider adapters must be isolated behind shared interfaces and registry code.
- All report-like outputs should become schema-valid before export, signing, or verification.

## Testing

- Run `python -m compileall src`.
- Run `pytest`.
- Add tests for safety boundaries, consent checks, and uncertainty-aware outputs when behavior changes.

## Documentation

- Update docs when changing architecture, safety policy, trust-ladder logic, or data governance.
- Keep examples synthetic. Do not commit real user conversations or personal data.

## Privacy-First Rule

- No secret keys in the repo.
- No real user data in tests, examples, docs, or fixtures.
- No hidden scraping or cross-platform ingestion without explicit authorization.
- Prefer deletion, export, minimization, and local-first design paths.

## Project Memory And Documentation Rule

Every future Codex task that changes architecture, schemas, safety policy, provider system, report format, or GUI flow must update:

- `docs/AI_DEVELOPMENT_LOG.md`;
- the relevant ADR in `docs/DECISION_RECORDS.md`;
- `docs/FUTURE_CODEX_TASKS.md` if task status changes;
- relevant schema docs if data format changes.

Architecture direction:

- GUI-first for the current phase.
- Core engine remains UI-independent.
- Provider adapters stay isolated.
- Reports should be schema-valid before export, signing, or verification.
- No secrets.
- No real user data in the repo.
- No gender-hostile wording.
- No public personality score.
- No deterministic "good/bad person" labels.
