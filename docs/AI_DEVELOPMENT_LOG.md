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
