# Agent Mode Vs API Mode

Both modes are now fully wired (2026-07-06) behind one interface:
`apps/desktop_pyqt/anti_dating_scam_desktop/ai_backend.py`, selected in the GUI's
**Connect AI** screen and used by every AI feature (self-portrait, live criteria
interview). The manual copy-paste prompt flow remains as an advanced fallback.

## Agent Mode (Claude Code CLI) — automated

- The app launches the user's installed Claude Code CLI headlessly
  (`claude -p <prompt> --permission-mode acceptEdits`) with the **vault as the
  working directory**.
- The agent itself reads vault files and writes the reports — the strongest mode,
  because nothing has to be inlined into a context window.
- Chat (the live interview) uses `claude -p --output-format json` with `--resume`
  to keep one conversation session.
- Requires Claude Code on PATH; availability is detected and reported in the UI.

## API Mode — automated

Two providers, both orchestrated *by the app*: it inlines size-capped vault data,
sends the same contracts Agent Mode uses, parses delimited output, and saves the
report files itself.

- **Ollama (local, recommended default):** `/api/chat` on `localhost:11434`.
  Nothing leaves the device. Connection test lists installed models.
- **Anthropic API (explicit opt-in cloud):** `/v1/messages`. The privacy note in
  the UI states plainly that size-capped vault text is sent per task. The API key
  lives in **process memory only** (or `ANTHROPIC_API_KEY`); it is never written
  to disk — `ai_settings.py` persists only non-secret fields and asserts on it.

## Manual Mode — fallback

The original flow: the app writes the request contract into the vault and shows a
copyable prompt. Always available; useful when no backend is reachable.

## Shared properties

- One interface (`check()` / `chat()` / `run_task()`), injectable transports and
  CLI runners so tests never touch the network or a real CLI.
- All AI work runs on background threads (`workers.py`); the GUI stays responsive.
- Consent, safety boundaries, and the anti-sycophancy interview contract are
  identical in every mode — the mode changes *where* the model runs, never the
  rules it follows.
