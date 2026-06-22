# Quickstart: Local Desktop App

## Install

From the repository root:

```bash
pip install -e ".[desktop]"
```

For tests:

```bash
pip install -e ".[dev]"
```

## Run

```bash
python run_desktop.py
```

The app opens a PySide6 desktop window with a screen-by-screen onboarding flow.

```text
Welcome
  -> Safety & Consent
  -> Local Profile Detection
  -> Agent/API Mode
  -> Import Data
  -> Generate/Load Profile
  -> Home
```

## First Local Test

1. Start at Welcome and continue to Safety & Consent.
2. Accept the consent checkbox.
3. Let the app detect whether `~/.ai_slowmatch/profile.mpm.md` exists.
4. Choose Agent Mode for the current prototype.
5. Import notes or a local export.
6. Generate and save `profile.mpm.md` and `profile.json`.
7. Enter Home and choose Risk Analysis or Trust Ladder.

## Local-First Rule

The MVP processes user-selected text and files locally. It does not automatically scrape ChatGPT, dating apps, messages, contacts, or profiles.
