# Data Import, Frontend, and Local-AI Self-Portrait Plan

Agent-facing technical detail behind the new scope in `PLAN_FOR_ONEPUCHMAN.md` (sections "New Scope: Social/Chat Import, Frontend, Self-Portrait"). This doc stays English-only per the bilingual rule in `AGENTS.md` (technical/internal doc, not directly user-facing).

## 1. Social media / chat-app import — feasibility per source

Hard constraint from `AGENTS.md` Privacy-First Rule: **no hidden scraping or cross-platform ingestion without explicit authorization.** That rules out login automation, private API calls, or headless scraping of any platform. The only compliant pattern is the one already used for ChatGPT import: the user manually requests their own official data export from the platform, downloads it themselves, and explicitly selects the file/folder in the app. The app only ever reads files the user already has on disk. This must be the architecture for every source below — no exceptions, even where a "convenient" scraper library exists.

| Source | Official self-export | Format | Notes / V1 feasibility |
|---|---|---|---|
| Instagram / Facebook | Yes — Accounts Center → "Download your information" | ZIP (JSON/HTML), incl. DMs | Up to ~2 weeks turnaround. **V1-ready.** |
| YouTube / Google | Yes — Google Takeout | ZIP (JSON/CSV) | Watch history, comments, playlists. **V1-ready.** |
| X (Twitter) | Yes — Settings → "Download an archive of your data" | ZIP (JSON/HTML) | Multi-day prep time. **V1-ready.** |
| TikTok | Yes — Settings → "Download your data" | JSON | DMs, likes, watch/search history included. **V1-ready.** |
| WhatsApp | Yes, but per-chat only, no bulk export, official cap (10k msgs w/ media, 40k text-only), exits via email/share sheet, not a settings download | .txt + .zip per chat | **V1-ready but limited** — user exports chats one at a time and feeds each file in; document this limitation to the user, don't promise bulk import. |
| WeChat | Partial — official export covers Moments, Favorites, account info via Settings → Privacy → "My Information & Authorizations." **Chat history itself is not server-stored and has no official bulk export.** | ZIP via emailed link + QR auth | **V1: import Moments/Favorites/account info only.** Chat-history import would require either local device backup tools or third-party extractors — both outside the "official export only" rule and not recommended for V1. Revisit only if WeChat ships an official chat-export path. |
| Bilibili, Douyin, Xiaohongshu (RedNote) | No robust, confirmed official personal-data self-export found in research as of June 2026. Search results turned up only third-party scrapers, which violate the no-scraping rule and likely each platform's ToS. | — | **Not supported in V1.** Re-check each platform's own privacy/settings center periodically — Chinese platforms are adding GDPR/PIPL-driven export tools over time, but none confirmed reliable yet. Fallback: let users manually paste/copy text content the same way conversation analysis already works — no scraping needed. |

Recommended build order: Instagram/Facebook, Google Takeout (YouTube), X, TikTok, WhatsApp (per-chat) first — all have stable official export paths and the existing ChatGPT-export importer (`src/anti_dating_scam/engine/chatgpt_export_parser.py`) is a good template to copy. WeChat (partial) next. Bilibili/Douyin/Xiaohongshu stay paste-only until an official export exists.

Each importer should be its own module under `src/anti_dating_scam/engine/importers/`, sharing a common `Importer` interface (parse → normalized snippets + metadata, same shape the profile builder already expects from ChatGPT import). Treat every import as untrusted, potentially large, and potentially containing other people's data (DMs include the other party) — keep the existing "limited snippets only, not full raw retention" pattern from the ChatGPT importer.

## 2. Frontend — "better looking than PySide6" plan

Current state: PySide6 desktop GUI. Functional, but PySide6's default widget look is dated compared to modern web-rendered UI, which is the user's complaint.

Two-step plan, not a single rewrite:

**Step A (near-term, low risk):** Swap PySide6's raw widgets for a Python-served HTML/CSS/JS UI rendered in an embedded webview, without leaving Python. Candidates:
- **PyWebView** — lightweight, wraps the OS-native webview (WebKit/WebView2), lets you build the UI in plain HTML/CSS/JS or a small framework (e.g., a single-file Tailwind+Alpine.js page), call back into Python directly. Smallest migration effort from the current screen-by-screen PySide6 structure since the underlying engine/services don't change at all — only the presentation layer.
- **Flet** or **NiceGUI** — Python-native frameworks that render a modern (Flutter-style or web-based) UI while you write only Python. Good alternative if avoiding HTML/CSS entirely is preferred; less flexible for fully custom design than raw HTML+Tailwind.

Recommended for Step A: **PyWebView + Tailwind CSS** (CDN or vendored, no build step) — fastest path to a visibly modern UI while keeping 100% of the existing Python engine/services/tests untouched.

**Step B (the project's own long-term plan, already in `docs/08_roadmap.md`):** Tauri + Python sidecar. Tauri renders a real React/Svelte/Tailwind frontend natively (small binaries, ~8MB installers, fast cold start per 2026 benchmarks) while the existing Python engine runs as a local sidecar process the Tauri shell talks to over local HTTP (the FastAPI routes already being built in Phase 2 are exactly this interface). This is more engineering effort (packaging a Python sidecar inside a Rust-based Tauri app) but is the right end state for a polished, installable product. Don't start this until the FastAPI contract (`/risk/analyze`, `/trust-ladder/evaluate`, `/journal/summarize`, plus new import/self-portrait endpoints) is stable — Tauri just becomes a client of it.

Do not jump straight to Tauri before Step A — validate the new screens (import center, self-portrait view, progress tracker UI) cheaply in PyWebView first, then port the proven layout to Tauri later.

## 3. Local AI agent vs. API for self-portrait / personality model

The provider abstraction already exists (`src/anti_dating_scam/providers/`, `ai/provider.py`, registry pattern) — this feature is "add a provider," not "build new infrastructure."

- **Local (recommended default):** Add an Ollama provider adapter implementing the existing `LLMClient`/provider interface. Self-portrait generation runs entirely on the user's machine against a local model (e.g., a small instruct model sized to the user's hardware). Aligns with the project's local-first/privacy-by-architecture identity — no imported social/chat data ever leaves the device, which matters a lot given how sensitive that combined dataset is (DMs, watch history, dating chats, all in one place). Tradeoffs to disclose to the user: needs reasonable local hardware (the security/privacy literature notes Ollama's default bind is local-only — keep it that way, never expose 0.0.0.0 without explicit user action and a warning), and local model quality is currently behind top cloud models for nuanced synthesis.
- **API (opt-in, not default):** Reuse existing provider registry to add real cloud providers behind the current mock interface. Must require explicit per-session consent given the sensitivity of self-portrait input data, and should support redaction/minimization before anything is sent off-device — consistent with `ConsentManager`/`SafetyPolicy` already in the codebase.

Self-portrait/personality model output should follow the same constraints already in `AGENTS.md`: no public score, no deterministic personality "diagnosis," framed as a private, editable reflection document (it slots naturally next to the existing `profile.mpm.md` / `profile.json` personal profile files) rather than a fixed psychological label.

## 4. Build order tying it together

1. Importer interface + Instagram/Facebook + Google Takeout + X + TikTok + WhatsApp(per-chat) modules, reusing the ChatGPT-import pattern.
2. PyWebView + Tailwind UI pass over existing screens (no new features yet — prove the look/feel upgrade first).
3. New "Import Center" and "Self-Portrait" screens in the new UI.
4. Ollama provider adapter (local-first self-portrait generation) + opt-in cloud-API provider behind existing registry.
5. Re-evaluate Tauri migration once the above is stable and FastAPI contract covers all new endpoints.

This order keeps every step shippable and testable on its own, instead of one large rewrite.
