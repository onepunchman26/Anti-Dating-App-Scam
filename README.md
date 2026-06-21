# Anti-Dating-App-Scam / AI-SlowMatch

AI-SlowMatch is a local-first AI-assisted relationship trust, anti-romance-scam, and self-reflection tool. The current phase is a runnable Python + PySide6 desktop MVP, backed by a UI-independent Python engine.

It is not a dating app, cloud platform, AI judge, public score, or replacement for real relationships. It is a local document tool for scam-risk reflection, trust-ladder pacing, profile generation, and verifiable risk reports.

## Install

Core/test dependencies:

```bash
pip install -e ".[dev]"
```

Desktop dependencies:

```bash
pip install -e ".[desktop]"
```

## Run

From the repository root:

```bash
python run_desktop.py
```

If PySide6 is missing, the launcher prints:

```text
PySide6 is required. Install dependencies with: pip install -e ".[desktop]"
```

## What This Tool Does

- Builds a local personal relationship profile document from user-provided notes.
- Imports a local ChatGPT export ZIP or JSON for metadata and limited snippets only.
- Accepts a pasted ChatGPT Memory Summary as one input source.
- Analyzes pasted conversations for uncertainty-aware scam risk signals.
- Evaluates relationship pacing through a trust ladder.
- Exports risk reports as JSON or Markdown.
- Adds hash-based report integrity metadata for local verification.
- Keeps provider settings isolated for future adapters.

## What It Refuses To Do

- No deterministic "this person is definitely a scammer" judgment.
- No psychological diagnosis of real people.
- No public personality score or dating social credit.
- No stalking, doxxing, hacking, impersonation, harassment, revenge, blackmail, or entrapment.
- No hidden scraping of ChatGPT or dating app accounts.
- No uploading user data without explicit action and consent.
- No committed real user data or API keys.

## Desktop Tabs

1. Consent / Safety
2. Import My Profile
3. Generate Local Personal Profile
4. Conversation Risk Analysis
5. Trust Ladder
6. Provider Settings
7. Report Export / Verify

## ChatGPT Export Import

Use the Import My Profile tab to select a local ChatGPT data export ZIP or a local JSON file. The MVP processes the file locally, tries to find `conversations.json`, summarizes metadata, and extracts only limited snippets for profile generation.

The app does not scrape ChatGPT automatically. Users must request their own export from ChatGPT settings or the privacy portal, then choose the file locally.

ChatGPT export ZIPs may contain sensitive account data. Import only your own data and review/redact sensitive information before analysis.

## ChatGPT Memory Summary

You can paste a ChatGPT Memory Summary into the Import My Profile tab. Memory Summary may be incomplete; treat it as one input source, not an authoritative full self-profile.

## Local Profile JSON

The Generate Local Personal Profile tab creates a JSON document with:

- relationship values;
- boundary preferences;
- communication preferences;
- risk tolerance notes;
- trust ladder preferences;
- self-reflection notes;
- uncertainty notes.

This is a local personal relationship profile document. It is not training a personal model.

## Risk Reports

Conversation analysis generates a schema-valid risk report with:

- risk level;
- risk signals;
- uncertainty notes;
- recommended next steps;
- input hash;
- provider/model metadata;
- safety disclaimer.

Risk language must stay non-accusatory. A risk signal is not proof of intent, identity, or wrongdoing.

## Verifiable Reports

The MVP includes hash-based integrity signing. A valid report signature only means the report file was not modified after signing and conforms to the project schema. It does not prove that the submitted conversation is authentic or that any real person committed wrongdoing.

Full cryptographic keypair signing is a future phase.

## Testing

```bash
python -m compileall src apps run_desktop.py
pytest
```

If `pytest` is not on PATH, use:

```bash
python -m pytest
```

## Roadmap

- Now: Python core engine + PySide6 desktop MVP.
- Next: provider plugin adapters and local profile/report schema hardening.
- Next: local signed reports with real keypair verification.
- Later: optional local FastAPI server.
- Later: Tauri + Python sidecar.
- Later: Rust/Tauri security layer for signing, storage, packaging, and update integrity.
