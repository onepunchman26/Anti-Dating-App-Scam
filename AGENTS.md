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
- **Bilingual rule (human-facing docs):** any document meant for the project owner or end user to read directly — `PLAN_FOR_ONEPUCHMAN.md`, `PROGRESS_TRACKER.md`, `README.md`, onboarding/help text in the app UI — must be provided in **English and Simplified Chinese**, in full (not machine-gloss snippets). Use either two clearly labeled full sections (English first, then "中文版") or side-by-side tables; never silently drop one language when updating the other.
- Technical/internal docs in `docs/` (architecture, ADRs, schemas, taxonomy) are agent-facing and may stay English-only unless a human-facing doc references them directly.
- `PROGRESS_TRACKER.md` is agent-maintained: whenever a task in this project changes status (started, blocked, done), update its checklist in both languages in the same edit — don't let it drift out of sync with actual work.
- **No real name in any file.** Never write the project owner's real/legal name into any file in this repo (code, docs, commit messages, filenames). If a name must appear (e.g., "reading copy for ___"), use the pseudonyms only: **onepuchman** (English) and **观澜击水** (Chinese).

## Privacy-First Rule

- No secret keys in the repo.
- No real user data in tests, examples, docs, or fixtures.
- No hidden data collection: process only data the user has explicitly provided; never
  scrape, exfiltrate, or transmit third-party platform content or vault contents.

## Inherited rules

This project inherits the global safety, privacy, and publishing rules from the control
center (`setup/ai/rules/`): `safety-boundaries.md`, `privacy-and-secrets.md`,
`redaction-standard.md`, `publishing-hygiene.md`. The Safety Boundaries and Privacy-First
sections above are this project's local statement of those shared defaults; keep only
project-specific rules here and defer to the apex for the rest.