# Deep Compatibility Profile & Decentralized Exchange Plan

Agent-facing technical detail behind the matching pivot described in `PLAN_FOR_ONEPUCHMAN.md`. English-only per the bilingual rule in `AGENTS.md` (technical/internal doc).

## 0. What this is, precisely, and what it is not

User-clarified model (do not drift from this): this is **not** a centralized matching platform. There is no server-side database of users, no discovery feed, no algorithm that searches a population and surfaces candidates. People still find each other entirely on their own, through whatever channel they already use (real life, friends, other dating apps, social media). What this feature adds is a way for two people who are *already* in contact to:

1. each build a private "Deep Compatibility Profile" locally, on their own device;
2. optionally export a redacted, shareable subset of it directly to the other person (file, QR code, link — peer-to-peer, no server in the middle);
3. import the other person's shared profile into their own local app;
4. run a local-only comparison that produces a non-scoring reflection report — alignment points, divergence points, discussion prompts — never a percentage match or ranking.

This keeps the existing "no public personality score," "no deterministic good/bad labels," and local-first architecture fully intact. It is additive to the anti-scam/trust-ladder pillar, not a replacement for it — both pillars should feel like one coherent tool (you vet the person for risk *and* explore real compatibility, without ever leaving your own device or trusting a third-party server with either).

## 1. Why this is the right shape (not a centralized algorithm)

Research context: established compatibility-matching products (eHarmony, OkCupid) run centralized, proprietary algorithms that are widely criticized as scientifically unvalidated for predicting long-term compatibility, and prone to optimizing for superficial similarity (shared opinions, demographics) rather than the deeper complementary traits that actually sustain relationships. Decentralized/Web3 dating apps exist (e.g., Matchpool-style blockchain projects) but are early-stage, low-adoption, and mostly focused on identity/reputation via blockchain rather than this project's actual goal: privacy-preserving, locally-run deep-compatibility comparison between two specific people who already know each other. No mature product was found doing this specific thing — it remains genuine whitespace, not a re-implementation of an existing category leader.

## 2. Deep Compatibility Profile — schema split

Two explicit tiers, stored and labeled separately so the "basic but necessary" filters never get confused with the actual compatibility signal:

**Tier 1 — Basic gating filters** (practical/material, used only as a yes/no or range gate, never scored or weighted against compatibility):
- Location / general geography
- Age range
- Income / financial-stability range
- Education level
- Marital/relationship history (incl. children)
- Health & lifestyle basics (smoking/drinking, fertility/children plans, major conditions relevant to shared life planning)

**Tier 2 — Deep compatibility dimensions** (the actual point of the feature, intentionally excluding wealth/status/interests/hobbies as primary signals):
- Core values and life priorities
- Long-term life goals and vision for the relationship (e.g., partnership style, family plans, geographic flexibility)
- Attachment style and emotional needs
- Communication style and conflict-resolution approach
- Boundaries and non-negotiables / deal-breakers
- Self-reflection notes (already exists in the current profile builder — extend, don't replace)

Interests/hobbies/wealth/status may still be *recorded* if the user wants (people aren't purely values-machines), but the comparator must never present them as primary compatibility signals or use them to compute anything resembling a score — this is the explicit design reaction to "Tinder-style" superficial matching the user is pushing back on.

Implementation: extend the existing `src/anti_dating_scam/profile/` models (`mpmd_profile.py`, `profile_json.py`, `profile_markdown.py`) and `engine/personal_profile_builder.py` with these two tiers as new structured sections, rather than building a parallel profile system.

## 3. Decentralized exchange mechanism

No server. The export artifact is a new file type — a "Shareable Compatibility Card" — built the same way existing signed reports are built (reuse `reports/signer.py`, `reports/canonical_json.py`, `reports/export_markdown.py` as the template): a schema-valid, hash-signed local file containing only the Tier 1 fields the user chooses to disclose plus a redacted/summarized version of Tier 2 (not raw journal/self-reflection text — a structured summary).

Exchange transport options to support, roughly in order of implementation simplicity:
1. **File-based** — export a `.json`/`.md` card, send it however the two people already communicate (AirDrop, email, messaging app) — zero new infrastructure.
2. **QR code** — encode the card (or a fetch-pointer to it) as a QR code for fast in-person exchange — good fit for a "we just met, want to compare notes" moment.
3. **Local-network direct transfer** (later) — discover-and-send over the same Wi-Fi/Bluetooth, skipping manual file handling — nice-to-have, not required for V1.

Both the export step and the import step must require explicit user action and consent each time (no auto-sync, no background sharing) — wire through the existing `ConsentManager`/`SafetyPolicy` services already in the codebase.

## 4. Local comparison engine

New service, e.g. `engine/compatibility_comparator.py`, deterministic-first (same philosophy as `scam_risk_analyzer.py` — rule-based core, optional LLM-assisted narrative layer behind the existing provider abstraction, local Ollama provider recommended default per the earlier frontend/AI plan in `docs/10_data_import_and_frontend_plan.md`).

Output shape — a Compatibility Reflection, not a score:
- Tier 1 status: which basic filters align vs. don't (simple gate, shown plainly, not blended into Tier 2).
- Tier 2 alignment points: where both profiles' values/goals/styles converge.
- Tier 2 divergence points: where they differ, framed neutrally as "worth discussing," never as a deficiency.
- Suggested discussion prompts generated from the divergence points (consistent with the project's coaching/reflection tone, not a verdict).

No aggregate percentage, no pass/fail verdict, no ranking against anyone else — this is a hard constraint carried over from the existing safety boundaries in `AGENTS.md` ("no public personality score," "no deterministic good/bad person labels") and must be enforced the same way for compatibility as it already is for scam risk.

## 5. Open questions to resolve before building (flag, don't guess)

- Exact redaction rules for what Tier 2 summary content leaves the device by default (safest default: nothing leaves until the user reviews and confirms the generated card).
- Whether the comparator should ever be allowed to ingest a counterpart's *raw* imported social/chat/self-portrait data (from the Phase 3 importers in `docs/10_data_import_and_frontend_plan.md`) or strictly only their deliberately-shared Compatibility Card — recommend the latter; never let one person's bulk imported data leak into a comparison meant for two consenting parties.
- How disputes/asymmetric exchange are handled (one person shares, the other declines) — recommend the comparator simply refuses to run until both cards are present locally, no partial output.

## 6. Build order (fits after Phase 3/4 in `docs/10_data_import_and_frontend_plan.md`)

1. Extend profile schema with Tier 1 / Tier 2 fields.
2. Build Shareable Compatibility Card export/import (file-based first).
3. Build the local comparator service (deterministic core).
4. Add the LLM-assisted narrative layer (local Ollama default, opt-in cloud API) for the discussion-prompt generation.
5. QR-code exchange as a UI nice-to-have once the new PyWebView UI (Phase 4) exists.
