# Roadmap

## Phase 0: Docs And Architecture

- Define AI-SlowMatch vision.
- Document social theory, safety policy, data governance, and evaluation.
- Create provider-neutral AI layer.
- Add synthetic examples and tests.

## Phase 1: Local Risk Analyzer Prototype

- Expand deterministic risk taxonomy.
- Improve evidence extraction.
- Add local-only journal persistence behind explicit consent.
- Add export and delete flows before long-term retention.

## Phase 2: FastAPI Endpoints And Mock AI Provider

- Stabilize `/risk/analyze`, `/trust-ladder/evaluate`, and `/journal/summarize`.
- Keep `MockAIProvider` as the default.
- Add provider configuration without committing secrets.
- Add contract tests for API responses.

## Phase 3: Optional Frontend Dashboard

- Create a lightweight `apps/web` dashboard if needed.
- Prioritize paste-to-analyze, trust ladder display, journal summary, export, and delete controls.
- Avoid swiping, feeds, public profiles, and engagement loops.

## Phase 4: Privacy-Preserving Local-First Storage

- Explore local-first encrypted storage.
- Add clear data retention settings.
- Add model-call audit transparency.
- Keep cross-platform ingestion disabled unless explicitly authorized.

## Phase 5: Evaluation With Synthetic And Consented Data Only

- Build synthetic benchmark cases.
- Run false positive and false negative analysis.
- Conduct bias and explainability checks.
- Run privacy and safety red-team exercises.
