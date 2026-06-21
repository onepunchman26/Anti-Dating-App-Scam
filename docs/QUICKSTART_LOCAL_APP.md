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

The app opens a PySide6 desktop window with tabs for consent, profile import, profile generation, risk analysis, trust ladder evaluation, provider settings, and report export/verification.

## First Local Test

1. Open Consent / Safety and check the consent box.
2. Open Import My Profile and paste synthetic self-profile notes.
3. Open Generate Local Personal Profile and click Generate Profile.
4. Open Conversation Risk Analysis and paste a synthetic conversation.
5. Open Report Export / Verify to export or sign the generated report.

## Local-First Rule

The MVP processes user-selected text and files locally. It does not automatically scrape ChatGPT, dating apps, messages, contacts, or profiles.
