# Agent Mode Vs API Mode

AI-SlowMatch currently supports two user-facing analysis modes in the onboarding flow.

## Agent Mode

Agent Mode is the recommended prototype mode.

In Agent Mode:

- the app does not make automatic provider API calls;
- the user manually controls what files are shared with Codex or another AI/coding agent;
- local exported documents can be reviewed, redacted, and selectively provided;
- the mode is good for development, testing, and iterative profile improvement.

Agent Mode keeps responsibility visible: the user chooses what to import, export, and share.

## API Mode

API Mode is a future direct-provider integration path.

In API Mode:

- the user supplies their own provider API key;
- provider calls must remain opt-in;
- the app must not upload data without explicit consent;
- OpenAI, Anthropic, Gemini, Ollama, and local model adapters can be added later.

In the current MVP, API Mode is selectable but only shows a placeholder warning. No real API call is made unless provider code is explicitly configured in a future task.
