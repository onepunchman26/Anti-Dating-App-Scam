# GUI Flow

The desktop GUI now uses a stacked, app-like onboarding flow instead of opening into a dense tab dashboard.

```text
Welcome
  -> Policy
  -> Profile Detection
  -> Agent/API Mode
  -> Import Data
  -> Generate/Load Profile
  -> Home
```

## Startup Flow

1. Welcome introduces AI-SlowMatch as a local relationship trust and anti-scam assistant.
2. Safety & Consent appears before import or analysis.
3. Local Profile Detection checks `~/.ai_slowmatch/profile.mpm.md` and `~/.ai_slowmatch/profile.json`.
4. Existing profiles can continue directly to Home.
5. New or updating users choose Agent Mode or API Mode.
6. Import Data presents source cards instead of technical tabs.
7. Generate Local Profile creates a Markdown Personal Memory Document and JSON companion.
8. Home shows action cards for the main tools.

## Home Actions

- Analyze a Conversation
- Trust Ladder Coach
- View / Edit Local Profile
- Export or Verify Report
- Import More Data
- Settings
- Assisted Browser Export

The goal is one clear next step at a time, with technical controls moved behind action cards.
