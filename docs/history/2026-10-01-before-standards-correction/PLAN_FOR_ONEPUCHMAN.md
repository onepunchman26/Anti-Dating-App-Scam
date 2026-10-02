# Historical snapshot / 历史快照

English: Superseded on October 2, 2026; current scope is in the root plan.

中文版：2026 年 10 月 2 日起被替代；当前范围以根目录计划为准。

# AI-SlowMatch — Plan (onepuchman's reading copy) / 计划（观澜击水 专用阅读版）

Bilingual by design — English first, Chinese (中文) below. Live status/checklist lives in `PROGRESS_TRACKER.md`.

## Proposed standards correction — English (2026-10-01; awaiting design confirmation)

This is a reviewable proposal, not a record of implemented changes. The evidence and
challenged assumptions are in [the current audit](../../16_rehabilitation_audit.md).
Earlier requirements below are historical context; they do not authorize expansion
beyond the following product boundary.

**Product boundary:** a Windows relationship copilot with user-controlled Start/End,
supportive conversation, a correctable private understanding of the user, optional
offline voice drafts, and voluntary encrypted-summary exchange/comparison. Preserve
the existing engine, PySide interface and working safeguards. No public discovery,
person rankings, automatic messaging, paid API fallback or network updater in this
correction. Public availability and useful AI output remain separate acceptance gates.

| Phase | Concrete work and dependency | Acceptance and recovery |
|---|---|---|
| S0 — protect and baseline | Preserve selected development sources and Git history; diagnose the fresh concurrent-archive test failure; inventory current executables without replacing them. A one-off 373-file snapshot/restore check is already done; a reusable backup system is still required. | Restore tracked/untracked source into a new empty directory and verify hashes; retain the original failed test log. Never overwrite the working tree or copy private vaults. |
| S1 — one reliable local release | After design confirmation, use one fixed root `AI-SlowMatch.exe` for Desktop. Derive runtime/About/Windows metadata from the project version; give each build its own source/dependency manifest. Gate a staged build on matching-source tests and package checks, then promote it atomically. | Two successive builds retain one root filename. Failed tests/build/smoke, a locked running EXE, interrupted promotion and rollback preserve a usable prior release. A locked app stays open; close it before retrying promotion. |
| S2 — verifiable AI connection | Keep the official Python ChatGPT-plan adapter; adopt Pi interface patterns without adding a Node runtime. Persist model choice, retain requested/reported IDs, show meaningful safe failures, and support bounded cancellation with immediate UI recovery. | Catalog/missing-model/alias/error/timeout/cancel/late-reply tests; explicit mock mode; fresh account catalog and completed synthetic real inference recorded separately when the owner confirms no extra-credit use. Never relabel a model as an upgrade. |
| S3 — conversational coaching and personal model | Replace question-only intake with a useful response and optional question. Preserve question/answer context without using AI words as evidence. Stage and validate the pinned skill update; selectively adopt reviewed coaching modules. Decide the bounded memory scope below before implementing its lifecycle. | Both languages support correction, skipped questions and changed goals. Preferences remain preferences; unknowns are not risk evidence. Any enabled memory is inspectable, opt-in, revocable and deletable, with source/time/supersession records. Prior data formats remain readable. |
| S4 — acceptance and source delivery | Exercise chat → reflection → encrypted file → import → comparison; verify physical microphone input. Consolidate current documents and archive old ones with links. Review and commit safe source in coherent changes, then verify the GitHub branch after push. | Full compile/test/lint gates; actual AI semantic review and microphone evidence clearly separate from mock checks. No release-ready claim while required acceptance fails. No raw logs, private data, credentials or backups pushed. |

Within S1, a single developer command will own snapshot, gates, staging, verification,
promotion and rollback. Product versions change deliberately; build identities include
the commit, dirty flag and source digest. A validated local build may be marked as a
development build; a release tag must identify committed source and passing gates.
Backups live outside the checkout and OneDrive, include a restore manifest, and never
prune an unverified or unmanaged copy. Proposed retention is the latest five verified
source snapshots and three promoted releases, with explicitly pinned copies retained.

Document roles are fixed: README for launching, this plan for approved scope,
PROGRESS_TRACKER for current work, CURRENT_STATUS for the current build/evidence,
OWNER_REVIEW for unresolved decisions, architecture/ADRs for design, and `docs/history/`
for superseded material. Move old material only after preservation and link checks.

**Open design decisions:** (1) place the one executable in this repository's root
(recommended) or in its parent project folder; (2) include a small, separately approved
cross-session memory in S3 (recommended) or explicitly defer it and label sessions as
independent. Recommended memory starts empty, stores only items the user approves,
supports view/correct/pause/revoke/export/delete, and imports no existing private
archives. Full-disk/local-vault encryption is a separate unresolved capability, not
something the encrypted sharing package already provides. Confirm shared understanding
in [Owner review](../../../OWNER_REVIEW.md) before structural implementation.

## 规范整改提案 — 中文版（2026-10-01；等待设计确认）

这是一份可审阅提案，不是已实现清单。证据和经过质疑后修订的假设见
[当前审计](../../16_rehabilitation_audit.md)。下方早期需求作为历史背景保留，不据此扩展本轮产品边界。

**产品边界：** Windows 恋爱军师，用户自主开始／结束，能回应和提供帮助的对话，可纠正的私人用户理解，可选离线语音草稿，以及自愿加密摘要交换／比较。保留已有引擎、PySide 界面和有效的保护措施。本轮不加入公开发现、人物排名、自动发消息、付费 API 后备或联网自动更新。公开可用与 AI 输出有用，分别验收。

| 阶段 | 具体工作及依赖 | 验收与恢复 |
|---|---|---|
| S0 — 保护与基线 | 保护选定开发源码及 Git 历史；诊断本次并发归档测试失败；盘点现有程序，不替换。已完成一次性 373 文件快照及恢复校验，可重复备份机制仍待实现。 | 在全新空目录恢复已跟踪／未跟踪源码并核对哈希；保留首次失败日志。不覆盖工作区，不复制私人资料库。 |
| S1 — 可靠的单一发布入口 | 设计确认后，根目录统一使用桌面版 `AI-SlowMatch.exe`。从项目版本派生运行时／关于页／Windows 元数据，每次构建记录源码及依赖清单。暂存构建必须通过同份源码的测试及程序包检查，再原子替换入口。 | 连续两个版本保持一个根目录文件名。测试／构建／启动失败、程序占用、中断及回滚，均保留可用旧版。被占用的程序继续运行，关闭后重试更新。 |
| S2 — 可核验的 AI 连接 | 保留官方 Python ChatGPT 套餐适配器，借鉴 Pi 接口，不新增 Node 运行环境。记住模型选择，保留请求／返回模型标识，显示有意义且不泄露隐私的错误，限制等待时间并在结束后立即恢复界面。 | 验证列表／模型消失／别名／错误／超时／取消／迟到回复，模拟模式明确标注。所有者确认不使用额外积分后，再单独记录新的账号列表和完整的合成资料真实推理。不靠改名“升级”模型。 |
| S3 — 对话式军师与个人模型 | 将只提问的访谈改为有效回应及可选问题。保留问答上下文，但 AI 文字不能成为用户证据。暂存并验证固定提交的 skill 更新，只引入审阅过的军师模块。先确定下述记忆范围，再实现其生命周期。 | 两种语言均支持纠正、跳题和目标变化。偏好不升级为行为，未知不成为风险证据。启用的记忆可查看、主动授权、撤销和删除，并记录来源／时间／替代关系。旧格式仍可读取。 |
| S4 — 验收与源码交付 | 检查聊天 → 画像 → 加密文件 → 导入 → 比较；验证实体麦克风。整理当前文档，归档旧文档并保留链接。审阅安全源码后分组提交，再核验推送后的 GitHub 分支。 | 完整编译／测试／静态检查；真实 AI 语义审阅与麦克风依据独立于模拟测试。必要验收失败时不称为可发布产品。不推送原始日志、私人资料、凭据或备份。 |

S1 由一个开发者命令负责快照、检查、暂存、验证、正式替换及回滚。产品版本按明确规则递增；构建标识包含提交、未提交标记和源码摘要。经验证的本地构建可标为开发版本，发布标签必须对应已提交源码及通过的检查。备份放在仓库和 OneDrive 之外，附带恢复清单，不清理未经验证或非本机制管理的副本。建议保留最近五份验证过的源码快照及三个正式替换过的版本，手动固定的副本继续保留。

文档职责固定：README 负责启动；本计划负责批准的范围；PROGRESS_TRACKER 负责当前任务；CURRENT_STATUS 负责当前构建与依据；OWNER_REVIEW 负责未决事项；架构／ADR 负责设计；`docs/history/` 保存被替代材料。保护原件并检查链接后才移动历史内容。

**待决设计：**（1）唯一 EXE 放本仓库根目录（推荐），还是上一级项目目录；（2）S3 纳入小范围、逐项确认的跨会话记忆（推荐），还是明确延期并标注各次会话独立。推荐方案从空记忆开始，只保存用户批准的条目，提供查看／纠正／暂停／撤销／导出／删除，不导入现有私人档案。整盘或本地资料库加密仍是单独待解决的能力，不能把加密分享包说成已经提供了它。在[所有者审阅](../../../OWNER_REVIEW.md)确认共同理解后再实施结构调整。

---

Historical plans and checkpoints follow; they are not the current correction backlog / 以下为历史计划与里程碑，不是本轮整改待办。

**Current extension (2026-09-30, English):** The owner has authorized the complete private loop: AI chat with optional offline voice input → review and save a personal relationship reflection → preview a minimal shared summary → create a password-encrypted attachment → exchange it by personally sending email → import both files locally → ask the selected AI for an uncertainty-aware discussion of fit. Speech becomes an editable draft and never sends automatically. Shared files exclude raw transcripts and original quotations; saved local history remains unencrypted. Local decryption does not imply that ChatGPT inference is offline: only explicitly reviewed summaries may go online, with both participants' permission. Computer Use verified the connected account and real model list, with GPT-5.6-Luna suggested as a lighter default; actual ChatGPT output and extra-credit settings await owner confirmation. The hourly schedule remains paused, and this cycle ends at a concrete owner-review checkpoint. Full design: [Private exchange and voice](../../31_private_exchange_voice.md).

**当前扩展（2026-09-30，中文）：** 所有者已授权完整私下流程：AI 聊天及可选离线语音输入 → 审阅并保存个人相处画像 → 预览最小分享摘要 → 生成有密码保护的加密附件 → 由用户亲自用邮件交换 → 在本地导入双方文件 → 请所选 AI 在保留不确定性的前提下讨论相处契合度。语音转为可编辑草稿，不会自动发送。共享文件不含原始对话及原始引文，本地保存历史仍未加密。本地解密不代表 ChatGPT 推理离线；只有经双方许可并明确审阅的摘要才可在线处理。Computer Use 已核验账号连接及真实模型列表，建议 GPT-5.6-Luna 为较轻量默认项；真实 ChatGPT 输出及额外积分设置仍待所有者确认。小时任务保持暂停，本轮将在可供人工审阅的具体里程碑结束。完整设计见[私密交换与语音](../../31_private_exchange_voice.md)。

The following direction records the earlier conversation checkpoint / 下方方向记录此前聊天里程碑。

**Current direction (English):** The new local flow is AI Chat → Start → answer, skip or change topic → End whenever you choose → optionally Create my reflection → separately confirm Save. The report is private, provisional and low confidence, citing only words typed in that conversation. Saved sessions can be read separately; in-place editing, deletion and cross-session updating remain future work. The sole main connection is ChatGPT: official sign-in and separate plan authorization are implemented and synthetic-tested, but no real account or model has verified them. You must confirm plan eligibility and disable extra-credit use for this app in ChatGPT settings; the app cannot verify that switch. Dated sections further down record older and advanced routes, including matching proposals; they do not supersede this main flow. Read [Conversation-first product](../../30_conversation_first_product.md) in English and Chinese.

**当前方向（中文）：** 新的本地流程是 AI 聊天 → 开始 → 回答、跳过或换话题 → 随时结束 → 可选择生成我的相处画像 → 再单独确认保存。报告私密、暂定、低置信度，只引用本次对话中亲自输入的原话。已保存会话可单独读取；原地编辑、删除和跨会话更新仍待实现。主连接只提供 ChatGPT：官方登录及单独套餐授权已写入代码并完成合成测试，但尚未用真实账号或模型验证。你须自行确认套餐资格，并在 ChatGPT 设置中关闭此应用的额外积分使用；本应用无法核验该开关。下文按日期保留旧版与高级路线，包括匹配方案，不覆盖此处的主流程。中英双语完整设计见[以对话为先的产品方向](../../30_conversation_first_product.md)。

---

# ENGLISH

## What the project actually is

Not a dating app. It's a local-first desktop tool that helps someone slow down and check their own risk while talking to a stranger they met online: it analyzes pasted conversations for scam-pattern signals, tracks relationship pacing through a "trust ladder" (stranger → low-pressure chat → verified → safe-to-meet), builds a private profile document, and exports a signed risk report. Everything runs on the user's machine; nothing is uploaded automatically.

Current state: this is real, not just docs. ~2,400 lines of working Python (engine, PySide6 desktop GUI, FastAPI routes, report signing, browser-export helper), 19 test files, all wired into a working desktop MVP you can run today (`python run_desktop.py`).

## Does a mature competitor already exist?

Close, but not the same product.

| Product | What it does | Gap vs. yours |
|---|---|---|
| **Social Catfish** (~$27/mo) | Reverse image/identity search + AI "chat checker" that scans pasted messages for fraud signals | Cloud-based, paid, focused on *investigating the other person*, not on pacing your own behavior or keeping data local |
| **Bitdefender Scamio** (free) | General-purpose AI chatbot: paste any message/link/image, get a scam verdict | Generic scam detector, not dating-specific, no relationship pacing, no profile/journal, no local-only guarantee |
| **Bark / Aura** | Parental/gaming monitoring — scans kids' or gamers' chats for predators | Wrong audience, surveillance model (monitoring someone *else's* chats), not self-directed |
| Dating platforms (Tinder, Bumble, Hinge) | ID verification, in-app AI moderation | Only covers in-app chat; useless once a scammer moves you to WhatsApp/WeChat/Telegram, which is where most scam money actually moves |

No existing product combines: local-first/no-cloud privacy, a pacing model (trust ladder) instead of a one-shot verdict, a personal reflection profile, and a deliberately non-accusatory/non-scoring stance. That's your whitespace.

## Matching pivot — soulmate-finding, not swiping (clarified scope)

You asked to shift focus toward actually helping people find a soulmate, weighted toward deep compatibility (values, life goals, emotional/communication style) over superficial factors (wealth, status, interests, hobbies) — while still allowing a few necessary basic filters (location, age, income, and now also education, marital/relationship history, and health/lifestyle basics).

Clarified model, and it matters: this is **not** a centralized matching platform. There's no database of users, no discovery feed, no algorithm that searches a population and suggests candidates. People still find each other entirely on their own, the same way they always have. What gets added is a **decentralized, peer-to-peer compatibility comparison**: each person builds a private "Deep Compatibility Profile" on their own device, and — only when both people explicitly agree — they exchange a redacted, shareable summary of it directly with each other (a file, a QR code — no server involved) and run a local, on-device comparison. The output is a non-scoring reflection (where you align, where you differ, discussion prompts) — never a percentage match or ranking, which keeps this consistent with the project's existing "no public personality score" rule.

Why this shape and not a real matching pool: established compatibility algorithms (eHarmony, OkCupid) are centralized, proprietary, and well-documented to skew toward superficial similarity over actually-predictive compatibility, with no independent science backing their match quality. Decentralized/blockchain dating apps exist but are early-stage and focused on identity/reputation, not this specific "compare two already-connected people, locally, privately" use case. Nobody is doing the thing you're describing — that's good news for differentiation, and it also avoids the much harder, much riskier problem of needing a critical mass of users on a platform (which is what "full matching platform" would require, and which would conflict with the project's local-first identity and safety stance). Full technical plan: `docs/11_compatibility_matching_plan.md`.

Anti-scam/trust-ladder work stays the core of the product, per your direction — this is a second pillar added alongside it, sharing the same local-first, non-scoring, consent-gated philosophy, not a replacement for it.

### Update (2026-07-06): an online rendezvous server joins the picture

You decided the matching pillar also needs an **online platform for nearby matchmaking** — while all personal data still stays local. Reconciled design (recorded as ADR-012, full detail in `docs/12_rendezvous_matchmaking_plan.md`): the server is a *bulletin board and a notary, never a profile database*. It stores only a pseudonym, a coarse client-derived location bucket (raw coordinates never leave your device), basic Tier-1 filter ranges, a contact channel that stays hidden until **both** sides accept an introduction, and cryptographic **fingerprints** of compatibility cards. The cards themselves travel person-to-person (auto-composed email, QR, file), never through the server. The fingerprint attestation is your anti-"perfect persona" mechanism: cards are hash-locked when an introduction is created, so any edit after matching is detected by the other side's app, and how often someone rewrites their card is visible as a plain fact. Honest limit: this proves *integrity and history*, not *truth* — catching fabrication remains the job of the anti-scam pillar. A working prototype (geohash buckets, HMAC attestation, double-blind introductions, match verification) now lives behind the local API with tests; real cryptography, deployment, and GUI screens are the next phases.

### Update (2026-07-06): decentralized rendezvous — no single server owner

You required that the matching layer not depend on a server owned or rented by one person, that it can ride on existing platforms (Facebook, 小红书…), and that server requirements stay minimal since users bring their own AI. Recorded as ADR-013, designed in `docs/14_decentralized_rendezvous.md`, and shipped in two of three models: **(A) Private nodes** — anyone can run their own rendezvous node with one command (`python run_rendezvous_node.py`), like hosting a private game server; a Raspberry Pi is enough because the node is only a bulletin board + notary, while all AI/data processing runs on each user's device with their own connected AI. **(B) Platform relay, no server at all** — the app generates a small armored "beacon" text block (pseudonym, coarse area bucket — never coordinates — basic filters, card fingerprint, checksum) that you post *yourself* in a community you trust; others paste it into their app, which checks the mutual basics locally; contact then flows through the platform's own DMs, and card fingerprints from the beacon give the same anti-swap protection as the server's locks. No scraping, ever — humans copy text by hand, which also keeps it platform-ToS-safe. **(C) Federation** between community nodes is designed but waits for real cryptographic signatures (P1). New home-screen entry: "Matching Beacon Exchange (beta)".

### Update (2026-07-06): connected AI — the copy-paste era is over

You asked for the app to feel like a mature product: connect an AI once, then everything runs with one click. Done. The Home screen now guides you through numbered steps (1 Connect AI → 2 Add Data → 3 Understand Yourself → 4 Discover Criteria). **Connect AI** supports three real backends: *Claude Code (agent)* — the app drives your installed CLI and the agent works directly inside the vault; *Ollama (local)* — a model on your own machine, nothing leaves your device; *Anthropic API* — explicit opt-in cloud, with the key held in memory only and never written to disk. Once connected: "Generate Self-Portrait Now" is one click, and the criteria interview happens **inside the app as a live chat** — the AI asks you questions turn by turn (still bound by the no-flattery contract), shows you the realistic candidate profiles, and "Finish & Save Reports" writes everything to the vault automatically. The old copy-paste prompts remain as an "advanced/manual" fallback. All AI work runs on background threads, so the app never freezes.

### Update (2026-07-06): criteria discovery interview — the AI that won't just agree with you

You also asked for smarter AI after data import: an **interactive Q&A** that digs into your data, then **realistic ideal-partner profiles to choose from** — because what you *pick* reveals your real criteria better than what you *say* — with the hard rule that the AI must not conform to your views (objective, even incisive). This now exists as the second stage of self-understanding: Home → "Discover Your Real Criteria" writes an interview contract for your agent. The agent interviews you one question at a time (targeting gaps, contradictions, and forced trade-offs), then shows 5–7 candidate vignettes where every option has genuine costs and none is best at everything, and finally writes a **stated-vs-revealed** synthesis (`reports/mate_criteria.md`, bilingual) that names your contradictions plainly and sorts your criteria into deal-breakers / strong preferences / things you claimed mattered but traded away cheaply. That file feeds the compatibility card and matching. Full design: `docs/13_criteria_discovery_interview.md`.

## Target market — and why Chinese-speaking users belong in it from day one

English and Mandarin Chinese are, combined, the two largest first+second-language populations in the world — building bilingually from the start is the single highest-leverage market decision available here, not a later localization task.

Romance-scam demand evidence in English-speaking markets: FTC reports **$1.16B** lost to romance scams in the first 9 months of 2025 alone (up 22% YoY in complaint volume), median loss ~$2,200, older adults nearly twice as likely to report six-figure losses.

Demand evidence in Chinese-speaking markets is arguably even stronger: so-called "pig-butchering" scams (杀猪盘 — a term that originated in Chinese-language scam communities before spreading globally) have moved an estimated **$75B+** globally since 2020, with major scam-operation infrastructure historically tied to Chinese-speaking criminal networks operating out of Southeast Asia. Chinese courts alone show hundreds of documented 杀猪盘 prosecutions. This isn't an adjacent market — it's arguably the origin market for the exact scam pattern this tool is built to catch, which makes Chinese-language support a credibility issue, not just a reach issue.

## Is it feasible?

**Technically:** yes, low risk for the existing scope. It's a Python desktop app with a deterministic + optional-LLM engine — no novel ML research required, no infra to scale (local-first), working MVP already passes tests. The new scope items below (import, frontend, self-portrait) are each independently feasible — see the breakdown.

**As a business:** local-first + privacy-first is a genuine differentiator but also a monetization constraint. Realistic paths: free/open-source with optional paid features (cloud provider, advanced reports), or a niche play aimed at the over-50 demographic (English-speaking markets) and at Chinese-speaking communities directly affected by 杀猪盘-style scams — both audiences respond to "calm, non-accusatory, private" positioning better than a flashy app.

## New scope you asked to add — summary (full technical plan in `docs/10_data_import_and_frontend_plan.md`)

**1. Import your own social media / chat history / AI chat history.** Feasible *only* via each platform's own official "download your data" export — not scraping, not login automation (this is a hard line from the project's own privacy rules, and also the only legally safe approach). Official export exists and is V1-ready for: Instagram/Facebook, YouTube/Google Takeout, X (Twitter), TikTok, and WhatsApp (per-chat, with size limits). WeChat only officially exports Moments/Favorites/account info — not full chat history, since WeChat doesn't store chat history server-side. Douyin, Xiaohongshu (RedNote), and Bilibili have **no confirmed official self-export** as of this research — these stay on a manual paste-in fallback (same mechanism the app already uses for pasted conversations) until/unless that changes. I'm not going to wire up scrapers for these even though they exist online — that would break this project's own no-scraping rule and likely each platform's terms of service.

**2. Better-looking frontend.** PySide6 is the honest bottleneck you're feeling. Two-step fix: short-term, swap the visual layer to a Python-embedded webview (PyWebView) running a modern HTML/Tailwind UI — keeps 100% of your existing engine untouched, fastest visible improvement. Long-term — and this matches what your own roadmap docs already proposed — migrate to Tauri (a Rust-based shell rendering a real React/Svelte frontend, ~8MB installers, fast startup) with the Python engine running as a local sidecar. Don't skip straight to Tauri; prove the new screens cheaply first.

**3. Local AI agent vs. API for a self-portrait / personality model.** Your codebase already has a provider-abstraction layer built for exactly this choice — it just needs a local provider added. Recommended default: **Ollama** (a local LLM runtime) — the self-portrait gets generated entirely on-device, nothing about your imported social/chat/dating history ever leaves your machine, which matters a lot once all that data lives in one place. Cloud API stays available as an explicit opt-in for people who want stronger model quality and accept sending redacted data off-device. Output is framed the same way the rest of this project already insists on: a private, editable reflection document — not a score, not a diagnosis.

## Roadmap (live checklist now in `PROGRESS_TRACKER.md`)

1. Polish the existing MVP (taxonomy, trust-ladder edge cases, GUI rough edges).
2. Real provider hookup — add the Ollama local provider first, real cloud API second.
3. Build the V1-ready importers (Instagram/FB, Google Takeout, X, TikTok, WhatsApp) using the existing ChatGPT-import pattern as the template; WeChat partial import next.
4. Extend the profile schema with Tier 1 basic filters + Tier 2 deep-compatibility dimensions, then build the Shareable Compatibility Card export/import and the local comparator (`docs/11_compatibility_matching_plan.md`).
5. PyWebView+Tailwind UI pass; add Import Center, Self-Portrait, and Compatibility Comparison screens.
6. Closed pilot with 5–10 consenting users (in pairs, since the compatibility feature needs two people per test) — include both English- and Chinese-speaking testers given the market case above.
7. Decide distribution model (open-source vs. small paid version) based on pilot feedback.
8. Only then revisit Tauri migration, FastAPI server hardening, signed-keypair reports — these stay in `docs/08_roadmap.md` as later-phase material.

## Housekeeping

27+ markdown files in `docs/` for the current code size is a heavy ratio — keep them (agents use them for context), but you personally only need this file + `PROGRESS_TRACKER.md` + `README.md`. New technical depth from this round of planning lives in `docs/10_data_import_and_frontend_plan.md`, agent-facing, not required reading for you.

On "add to skill as rule" — I can't create or edit a reusable Claude skill from inside this session (that requires Settings → Capabilities on your end). What I did instead: added the bilingual-documentation requirement directly into this project's own `AGENTS.md`, so any future agent session working in this repo will follow it automatically, which gets you the same practical outcome.

---

# 中文版

## 这个项目到底是什么

这不是一个交友 App。它是一个本地优先的桌面工具，帮助用户在和网上认识的陌生人聊天时放慢节奏、检查自身风险：分析粘贴进来的对话，识别诈骗模式信号；通过「信任阶梯」（陌生人 → 低压力聊天 → 身份核实 → 可安全见面）跟踪关系推进节奏；生成私密的个人档案文档；导出带签名的风险报告。所有处理都在用户自己的设备上完成，不会自动上传任何数据。

目前状态：这不只是文档堆砌，是真实可运行的项目。已有约 2400 行可运行的 Python 代码（核心引擎、PySide6 桌面界面、FastAPI 路由、报告签名、浏览器导出辅助工具），19 个测试文件，全部接入到一个今天就能运行的桌面 MVP 中（运行命令：`python run_desktop.py`）。

## 市面上是否已有成熟的同类产品？

接近，但不完全相同。

| 产品 | 它能做什么 | 与你的项目的差距 |
|---|---|---|
| **Social Catfish**（约 27 美元/月） | 反向图片/身份搜索 + AI「聊天检测器」，扫描粘贴的消息找诈骗信号 | 云端、付费、关注点是「调查对方」，而非帮你管理自己的节奏，也不保证数据留在本地 |
| **Bitdefender Scamio**（免费） | 通用 AI 聊天机器人：粘贴任意消息/链接/图片，给出诈骗判断 | 通用诈骗检测器，不针对交友场景，没有关系节奏管理、没有个人档案/日记功能，也不保证纯本地 |
| **Bark / Aura** | 家长监控/游戏监控——扫描孩子或玩家的聊天记录找猎食者 | 受众完全不同（监控「别人」的聊天，不是自我管理），监控模式而非自主使用模式 |
| 交友平台（Tinder、Bumble、Hinge） | 身份验证、App 内 AI 审核 | 只覆盖 App 内聊天；一旦诈骗者把你转移到 WhatsApp / 微信 / Telegram，这些防护就失效了，而诈骗资金恰恰主要在这些场景流失 |

目前没有任何产品同时具备：本地优先/无云端隐私、节奏管理模型（信任阶梯）而非一次性判断、私密反思档案、刻意保持的「非指控性、不打分」立场。这正是你的市场空白点。

## 匹配方向的调整——找灵魂伴侣，而不是「刷脸式」匹配（范围已明确）

你要求把项目重心转向真正帮人找到灵魂伴侣，更看重深层兼容性（价值观、人生目标、情感与沟通方式），而不是表面因素（财富、地位、兴趣、爱好）——同时保留几项必要的基础筛选条件（地点、年龄、收入，现在再加上教育程度、婚姻/恋爱历史，以及健康与生活方式基础信息）。

明确后的模式很关键：这**不是**一个中心化的匹配平台。没有用户数据库，没有「发现」信息流，没有算法在用户池里搜索并推荐候选人。人们依然完全靠自己去认识对方，方式和以前一样。新增的是一种**去中心化、点对点的兼容性比对**：每个人在自己的设备上建立私密的「深层兼容性档案」——只有当双方都明确同意时，才会把经过脱敏处理的、可分享的摘要直接交换给对方（文件、二维码——不经过任何服务器），然后在本地完成比对。输出结果是一份不打分的反思报告（哪些地方契合、哪些地方不同、可以讨论的话题）——绝不是百分比匹配度或排名，这与本项目「不做公开人格评分」的原则保持一致。

为什么是这种形态而不是真正的匹配池：成熟的兼容性算法（如 eHarmony、OkCupid）都是中心化、专有的，且已被充分证明更倾向于「表面相似度」而非真正具有预测力的兼容性，也没有独立科学研究能证实它们的匹配效果。去中心化/区块链交友 App 也存在，但仍处于早期阶段，关注点是身份/信誉，并不是你描述的这种「让两个已经互相认识的人，在本地、私密地做比对」的具体场景。目前没有人在做你描述的这件事——这对差异化是好消息，同时也避免了「真正的匹配平台」所需要的更难、更高风险的问题：需要在平台上积累足够多的用户（这正是「完整匹配平台」方案所要求的，也与本项目本地优先的定位和安全立场相冲突）。完整技术方案见 `docs/11_compatibility_matching_plan.md`。

按你的要求，反诈骗/信任阶梯功能依然是产品的核心——这是在其之上新增的第二支柱，沿用同样的本地优先、不打分、需双方同意的理念，而不是取代它。

### 更新（2026-07-06）：新增一个在线「会合」服务器

你决定匹配支柱还需要一个**用于附近匹配的在线平台**——同时所有个人数据仍然保留在本地。协调后的设计（已记录为 ADR-012，完整细节见 `docs/12_rendezvous_matchmaking_plan.md`）：这个服务器是*一块公告板加一位公证人，绝不是档案数据库*。它只存储：化名、由客户端本地计算的粗粒度位置格（原始坐标永远不离开你的设备）、第一层基础筛选范围、一个在**双方**都接受引荐之前保持隐藏的联系方式，以及兼容性卡片的加密**指纹**。卡片本身通过点对点传递（应用自动撰写的邮件、二维码、文件），绝不经过服务器。指纹认证就是你要的防「完美人设」机制：引荐建立时卡片即被哈希锁定，匹配之后的任何修改都会被对方的应用检测出来，而某人改写卡片的频率也会作为客观事实呈现。诚实的边界：这只能证明*完整性与历史*，不能证明*真实性*——识别编造内容仍然是反诈支柱的职责。一个可运行的原型（geohash 位置格、HMAC 认证、双盲引荐、匹配校验）已连同测试放在本地 API 后面；真正的密码学、部署和图形界面是接下来的阶段。

### 更新（2026-07-06）：去中心化会合——不依赖任何单一服务器所有者

你要求匹配层不能依赖某一个人拥有或租用的服务器，要能借助现有社交平台（Facebook、小红书……），并且服务器要求保持最低——因为用户自带 AI。已记录为 ADR-013，设计见 `docs/14_decentralized_rendezvous.md`，三种模式中已交付两种：**（A）私有节点**——任何人一条命令即可自建会合节点（`python run_rendezvous_node.py`），如同开一个游戏私服；一台树莓派就够用，因为节点只是公告板+公证人，所有 AI/数据处理都在每个用户自己的设备上、用自己接入的 AI 完成。**（B）平台中继，完全无服务器**——应用生成一小段护甲「信标」文本（化名、粗粒度区域格——绝不含坐标——基础筛选、卡片指纹、校验和），由你**自己**发布到信任的社区；他人粘贴进应用后在本地双向核对基础条件；后续联系走平台自带私信，信标中的卡片指纹提供与服务器锁定同样的防调包保护。永不抓取——一切由人手动复制，这同时也符合各平台的服务条款。**（C）社区节点联邦互联**已完成设计，待真正的密码学签名（P1）后再建。主页新增入口：「匹配信标交换（测试版）」。

### 更新（2026-07-06）：AI 已接入——复制粘贴的时代结束了

你要求这个应用像成熟产品一样：连接一次 AI，之后一切一键完成。已实现。主页现在以编号步骤引导（1 连接 AI → 2 添加数据 → 3 了解你自己 → 4 发现择偶标准）。**「连接 AI」**支持三个真实后端：*Claude Code（代理）*——应用驱动你已安装的命令行，代理直接在档案库内工作；*Ollama（本地）*——模型跑在你自己的机器上，数据不离开设备；*Anthropic API*——需明确选择的云端方案，密钥仅保存在内存中、绝不写入磁盘。连接之后：「立即生成自我画像」一键完成；择偶标准访谈**直接在应用内以实时聊天进行**——AI 逐轮向你提问（仍受不奉承契约约束）、展示现实候选画像，「结束并保存报告」自动把一切写入档案库。旧的复制提示词流程保留为「高级/手动」备选。所有 AI 任务都在后台线程运行，应用不会卡顿。

### 更新（2026-07-06）：择偶标准发现访谈——一个不会一味附和你的 AI

你还要求在数据导入之后有更聪明的 AI：先进行**交互式问答**深挖你的数据，再给出**现实的理想伴侣画像供你挑选**——因为你*选什么*比你*说什么*更能揭示真实标准——并且硬性要求 AI 不得迎合你的观点（保持客观，甚至一针见血）。这已作为自我理解的第二阶段落地：主页 →「发现你的真实择偶标准」会为你的代理写入一份访谈契约。代理会逐题访谈你（针对信息缺口、矛盾点和强制取舍），然后展示 5–7 份候选画像——每一份都有真实代价、没有任何一份全面占优——最后写出一份**「口头 vs 实际」**综合报告（`reports/mate_criteria.md`，中英双语），直陈你的矛盾，并把你的标准分为：不可妥协项 / 强偏好 / 你声称重要却轻易舍弃的部分。该文件将输入兼容性档案卡与匹配流程。完整设计见 `docs/13_criteria_discovery_interview.md`。

## 目标市场——以及为什么中文用户从第一天起就该是核心受众

英语和中文（普通话）合计是全球第一语言加第二语言人数最多的两个语言群体——从一开始就做中英双语，是目前能做出的杠杆最高的市场决策，而不是「以后再本地化」的次要任务。

英语市场的诈骗需求证据：美国联邦贸易委员会（FTC）数据显示，仅 2025 年前 9 个月，浪漫诈骗造成的损失就达 **11.6 亿美元**（投诉量同比增长 22%），中位损失约 2218 美元，老年人报告六位数损失的可能性几乎是年轻人的两倍。

中文市场的需求证据可能更强：所谓「杀猪盘」诈骗（这一说法最早就源自中文网络诈骗圈，后才扩散到全球）自 2020 年以来已在全球转移了约 **750 亿美元以上**的资金，主要诈骗园区基础设施历史上与活跃在东南亚的中文犯罪网络密切相关。仅中国法院系统就有数百份涉及「杀猪盘」的判决文书。这不是一个「附带」市场——可以说，这正是这类诈骗模式的「发源地市场」，因此支持中文不只是为了扩大用户覆盖面，更关乎产品的可信度。

## 这个项目是否可行？

**技术上：** 对现有范围而言，可行且风险低。这是一个 Python 桌面应用，核心是「确定性规则 + 可选 LLM」引擎——不需要原创的机器学习研究，无需扩容基础设施（本地优先），现有 MVP 已经能跑通测试。下面列出的新增功能（数据导入、前端、自我画像）每一项都各自可行——具体拆解见下文。

**作为一个产品/生意：** 本地优先 + 隐私优先是真正的差异化优势，但也限制了变现方式。比较现实的路径：开源 + 可选付费功能（云端模型、高级报告），或者聚焦细分人群——英语市场的 50 岁以上群体，以及直接受「杀猪盘」类诈骗影响的中文社群——这两类人群都更认可「冷静、不指控、私密」的定位，而不是花哨的 App 风格。

## 你要求新增的范围——摘要（完整技术方案见 `docs/10_data_import_and_frontend_plan.md`，仅英文，供 AI 代理使用）

**1. 导入自己的社交媒体 / 聊天记录 / AI 对话历史。** 唯一可行且合规的方式是通过各平台**官方的「下载我的数据」导出功能**——绝不抓取、绝不自动登录（这是本项目隐私规则的硬性底线，也是唯一合法安全的做法）。已确认有官方导出且第一版可直接支持的平台：Instagram/Facebook、YouTube/Google Takeout、X（推特）、TikTok，以及 WhatsApp（按单个聊天导出，有数量上限）。微信目前官方导出仅覆盖朋友圈、收藏、账号信息——**不包含完整聊天记录**，因为微信聊天记录本身不存储在服务器端。抖音、小红书、哔哩哔哩截至本次调研**没有找到可靠的官方个人数据导出渠道**——这些平台暂时只能走「手动粘贴文本」这条路（也就是 App 现有的对话分析功能本来就支持的方式），除非未来情况有变。即便网上能找到第三方抓取工具，我也不会接入——那会违反本项目自己的「禁止抓取」规则，也很可能违反各平台的服务条款。

**2. 更好看的前端界面。** PySide6 确实是你感觉到的瓶颈，这个判断没错。建议分两步走：短期方案——把界面层换成基于 Python 内嵌网页视图（PyWebView）的现代化 HTML/Tailwind 界面，现有引擎代码 100% 不需要改动，是见效最快的视觉升级方式。长期方案——这与你自己的路线图文档中早就提到的方向一致——迁移到 Tauri（基于 Rust 的外壳，渲染真正的 React/Svelte 前端，安装包约 8MB，启动速度快），Python 引擎作为本地「side car」子进程运行。不要直接跳到 Tauri 那一步；先用低成本的方式把新界面（导入中心、自我画像）验证清楚再迁移。

**3. 用本地 AI 还是 API 来生成自我画像/性格模型。** 你的代码库里已经有专门为这种选择设计的「服务商抽象层」，只需要新增一个本地服务商适配器即可。推荐默认方案：**Ollama**（本地大语言模型运行环境）——自我画像完全在用户设备本地生成，导入的社交/聊天/交友历史数据永远不会离开用户的电脑——一旦这些数据都汇聚到一起，这一点格外重要。云端 API 作为「需要用户主动选择」的可选项保留，给那些希望模型效果更强、并接受将脱敏数据发送到设备外的用户使用。输出形式延续本项目一贯的原则：是一份私密、可编辑的反思文档，不是打分，也不是诊断结论。

## 路线图（实时进度清单见 `PROGRESS_TRACKER.md`）

1. 打磨现有 MVP（诈骗分类细节、信任阶梯边界情况、界面流程中的细节问题）。
2. 接入真实的 AI 服务商——先加本地 Ollama 服务商，再加真实云端 API。
3. 按照现有 ChatGPT 导入功能的模式，构建第一版可用的导入器（Instagram/Facebook、Google Takeout、X、TikTok、WhatsApp）；接下来做微信的部分导入功能。
4. 扩展个人档案结构，加入第一层基础筛选条件和第二层深层兼容性维度，然后构建「可分享兼容性卡片」的导出/导入功能与本地比对引擎（详见 `docs/11_compatibility_matching_plan.md`）。
5. 完成 PyWebView + Tailwind 的界面升级；新增「导入中心」「自我画像」「兼容性比对」三个界面。
6. 进行 5–10 人（按对计算，因为兼容性功能需要两人配对测试）的小范围封闭试点——鉴于上面的市场分析，应同时包含中文和英文测试用户。
7. 根据试点反馈，决定发布方式（开源 vs. 小型付费版本）。
8. 在此之后才重新评估 Tauri 迁移、FastAPI 服务端加固、密钥对签名报告等——这些继续留在 `docs/08_roadmap.md` 中作为更后期的内容。

## 日常维护提示

以目前的代码量来说，`docs/` 文件夹下 27 个以上的 Markdown 文件确实偏多——继续保留它们（AI 代理需要用作上下文），但你个人只需要阅读这份文件 + `PROGRESS_TRACKER.md` + `README.md` 就够了。这次新增的技术细节都放在 `docs/10_data_import_and_frontend_plan.md` 中，那份文档是给 AI 代理看的，你不需要读。

关于「把这条规则加进 skill」——我在当前会话里无法创建或修改可复用的 Claude 技能（这需要你自己在 设置 → 功能 中操作）。我换了一种方式达到同样效果：把「双语文档」这条要求直接写进了本项目自己的 `AGENTS.md` 文件中，这样以后任何在这个项目里工作的 AI 代理都会自动遵守这条规则。


## Autonomous iteration update — 2026-09-28 (English)

This update supersedes historical claims about unrestricted agent access, optional
adult eligibility and unvalidated output. Preserve PySide6 and the existing core;
no framework replacement is needed. Existing adapters now share typed requests,
loopback-only local routing and explicit reviewed external disclosure. Imported
text never becomes system instructions. Reports/cards validate before saving.

A real local qwen3.5 synthesis-to-fingerprint journey passed with fictional adult
notes. The qwen3.6 desktop portrait/interview/criteria chain now also passes with
deterministically rendered full English and Simplified Chinese reports. All 429
integrated tests pass. Desktop and browser resources install from a wheel; copied
Windows EXEs passed startup outside the checkout. These establish a usable local foundation,
not completion of the wider roadmap or public-release approval.

Application state and in-flight vault destinations are now isolated; fresh
generation no longer reuses prior AI output as original evidence. Continue with
persistent provenance/corrections and migration, recoverable encrypted storage,
browser report translation/history restoration, broader bilingual evaluations,
then remaining importers and interoperability. Keep matching optional, adult-only
by self-declaration, minimal and consent-gated. Identity and source truth are not
verified by a checksum or schema. Do not spend money, use payment information or
make paid API calls. The continuation task is paused and does not run on a schedule.
It resumes only after the owner explicitly confirms continuation in this chat, then
works through the authorized local scope until a reviewable milestone or important
owner decision. Important owner decisions are collected in CURRENT_STATUS.md for review.

## 自主迭代更新——2026-09-28（中文版）

本更新取代历史文档中关于代理无限制访问、成年资格可选、输出未经校验的旧描述。
保留 PySide6 与已有核心，无需替换框架。已有适配器现共享类型化请求、仅回环本地路由和
明确审核后的外部披露；导入文本不进入系统指令，报告与卡片在保存前验证。

真实本地 qwen3.5 已使用虚构成年笔记跑通生成到指纹的链路；qwen3.6 桌面画像、访谈、择偶
标准链路也已通过，并由确定性渲染器生成完整英文和简体中文报告。该检查点 429 项综合测试通过。
桌面和浏览器资源可从 wheel 安装，Windows 便携程序均通过脱离源码目录的独立启动检查。
这些结果说明本地基础已可用，不代表整个路线图完成
或已获准公共发布。

应用状态和进行中请求的档案目的地现已隔离，全新生成不再复用旧 AI 输出作为原始证据。
继续自主推进可持久保存的档案来源与纠正、迁移、可恢复加密、浏览器报告翻译和历史恢复、
更广泛的双语评估，然后完善剩余导入器与互操作。匹配保持可选、以自行声明限制成年人、
最小披露并受明确同意控制。
哈希和 Schema 不能核验身份或来源真实性。不花钱、不使用支付信息、不调用付费 API。
继续任务现已暂停，不按计划自动运行；只有所有者在本聊天明确确认继续后才会恢复，随后在
已授权的本地范围内推进，直到形成可审阅里程碑或出现重要人工决定。重要决定汇总到
CURRENT_STATUS.md 留待审阅。

## Evidence review milestone — 2026-09-28 (English)

Desktop self-portrait and criteria reports now support persistent evidence review
and separate user correction notes. Saving requires explicit confirmation, keeps
the exact original JSON snapshot, rejects changed versions and preserves drafts.
The original report, exported card and AI inputs are unchanged. Generated history
and linked aliases are excluded from automatic inputs and prior-report references.

The updated integrated gate passed 529 tests; two real-symlink checks were skipped
for Windows privilege limits, while actual junction and hardlink checks passed.
Four-process/16-thread saves, restart and corruption handling, EN/ZH GUI behavior,
compilation and lint passed using synthetic data. There were no new AI calls.
Continue with explicit correction application/regeneration, lossless migration,
encrypted recovery and retention controls. See CURRENT_STATUS.md for package
status and morning decisions; the wider roadmap remains open.

## 证据复核里程碑——2026-09-28（中文版）

桌面的自我画像和择偶标准报告现支持持久证据复核及独立的用户更正批注。保存需要明确确认，
保留精确的原始 JSON 快照，拒绝已变化的版本，并保留草稿。原始报告、导出卡片及 AI 输入
不会改变。自动输入和旧报告参考均排除生成历史及链接别名。

更新后的综合验收为 529 项通过；两项真实符号链接检查受 Windows 权限限制跳过，真实
目录联接与硬链接检查通过。四进程/16 线程保存、重启及损坏处理、中英文界面行为、编译和
静态检查均使用合成数据通过，本轮没有新增 AI 调用。继续推进明确应用纠正或重新生成、
无损迁移、加密恢复与保留控制。程序包状态及明早决定见 CURRENT_STATUS.md；整体路线图
仍有未完成任务。

## Reviewed-copy milestone — 2026-09-28 (English)

Saved corrections now support an explicit selection → bilingual preview → confirmed
save workflow for a separate withdrawal copy. It removes disputed claims and dependent
portrait findings or fictional candidates, while preserving surviving evidence and
translations. It adds no replacement facts, calls no model and leaves the active
report, cards and AI context unchanged. Saved copies retain exact plaintext source
and note snapshots and can be verified and reopened after regeneration.

The integrated gate passed 629 tests, with two Windows symlink-privilege skips.
Four-process saving and fresh-process recovery, eight threaded saves, stale/tampered
preview rejection, all-claim withdrawal, warning preservation, EN/ZH GUI checks,
compilation and lint passed using synthetic data. Both portable programs and the
fresh wheel passed installation/startup checks outside the checkout; all new modules
are bundled. Package status and morning decisions remain in CURRENT_STATUS.md.
Next are supported replacement/regeneration, deliberate
active-report selection and lossless migration, followed by the existing storage and
browser backlog. This milestone does not complete the wider roadmap or authorize release.

## 复核副本里程碑——2026-09-28（中文版）

已保存的更正现支持明确选择 → 双语预览 → 确认保存独立撤回副本的流程。它移除争议主张及
可能依赖这些主张的画像一致性分析或虚构候选人，保留其余证据与译文的对应关系。此功能
不添加替代事实、不调用模型，也不改变当前报告、卡片或 AI 上下文。保存的副本保留精确的
明文来源与批注快照，重新生成原报告后仍可校验并打开。

综合验收为 629 项通过，两项因 Windows 符号链接权限跳过。四进程保存与新进程恢复、八次
线程并发保存、拒绝过期或被改动的预览、撤回全部主张、原有限制说明保留、中英文界面检查、
编译与静态检查均使用合成数据通过。两个便携程序及全新 wheel 均通过脱离源码目录的安装与
启动检查，新模块均已打包。程序包状态和明早决定仍见 CURRENT_STATUS.md。
随后推进有依据的替换或重新生成、明确选择当前报告及无损迁移，再继续既有存储与浏览器待办。
本里程碑不代表整个路线图完成，也不授权公开发布。

## Active-selection milestone — 2026-09-28 (English)

Reviewed copies can now be deliberately selected after preview and confirmation,
or deselected by choosing the current generated report. The core verifies source
and copy versions, records bounded append-only selection events, and preserves
original report files. Desktop viewers, browser desktop fallback and interview
references follow this choice. A stale or damaged choice stops use; the application
does not silently substitute another report. Correction annotations still refer
to the explicitly labeled original source.

Interviews bind the report reference at their start. Changing it blocks old-session
continuation and criteria saving, preserving the draft. An explicitly confirmed
restart retains earlier conversations for reading in the current window; this is
temporary history, not a persistent backup. Mocked provider changes verify stale
replies are rejected before writing results. The existing sequential report writes
are not a transaction against other operating-system processes.

The integrated gate passed 712 tests, with three Windows symlink-privilege skips
and one upstream deprecation warning. Compilation, lint and EN/ZH selection visual
checks passed. Only synthetic fixtures and mocked providers were used; no new
live-model acceptance is claimed. Both portable programs and a clean wheel install
passed outside-checkout startup checks; 154 source hashes and 148 wheel runtime
files match the final source. A final history-text spacing fix passed all 13 affected
tests and both-language visual checks. Package evidence is in CURRENT_STATUS.md.
Supported replacement/regeneration, lossless migration, recoverable encryption and
the existing browser backlog remain. Public release and real-vault migration remain
items for later owner review once concrete demonstrations are ready.

## 当前报告选择里程碑——2026-09-28（中文版）

复核副本现可经过预览和明确确认后启用，也可通过选择当前生成报告来取消启用。核心验证
来源及副本版本，以有界、仅追加的事件记录选择，并保留原始报告文件。桌面查看器、浏览器的
桌面报告回退及访谈参考遵循该选择。选择过期或损坏时停止使用，不会悄悄替换成另一份报告。
更正批注仍针对明确标注的原始来源报告。

访谈开始时绑定报告参考。参考变化会阻止继续旧访谈或保存择偶标准，并保留草稿。明确确认
重启后，先前对话仍可在当前窗口查看；这属于临时历史，不是持久备份。模拟提供方期间的
版本变化测试确认：过期回复会在写入结果之前被拒绝。现有报告仍逐个写入，不构成能够与
其他操作系统进程完全隔离的事务。

综合验收为 712 项通过、3 项因 Windows 符号链接权限跳过，另有一条上游弃用提示。
编译、静态检查及中英文选择界面视觉检查均通过。仅使用合成材料与模拟提供方，不宣称新增
真实模型验收。两个便携程序及全新 wheel 均通过脱离源码目录的启动检查；154 个源码哈希
及 148 个 wheel 运行文件与最终源码一致。最后的历史文字间距修正通过全部 13 项相关测试
及双语视觉检查。程序包证据记录于 CURRENT_STATUS.md。有依据的替换或重新生成、无损迁移、
可恢复加密及既有浏览器待办仍未完成。公开发布与真实档案迁移仍留待具体演示备妥后由所有者审阅。

## User-proposed reinterpretation — 2026-09-28 (English)

The correction workflow now lets the user propose English and Simplified Chinese
wording for one disputed claim, preview the full report and explicitly save a
separate copy. Its quotations, source labels, topic and group remain unchanged.
The new wording is attributed to the user and fixed as unverified speculation with
low confidence. Retaining quotations does not establish support or truth; correction
notes never automatically become facts. No model is called.

Original reports, cards and the active selection remain intact. A separate selection
step can activate the copy. Existing withdrawal copies remain compatible, and both
formats share the same bounded, verified history. Drafts survive stale-save errors;
refreshing cannot automatically retarget them to a different claim. Dependent portrait
findings or fictional candidates are removed, and existing uncertainty is preserved.

The full synthetic gate passed 809 tests, with three Windows symlink-privilege skips
and one upstream deprecation warning. Compilation, lint, backward compatibility,
exact source preservation, changed/damaged inputs, mixed-format concurrent saving,
new-process recovery and bilingual GUI checks passed. A directory-rename race in
history listing was repaired across all three histories and covered by 24
deterministic cases. [Workflow and boundaries](../../21_user_proposed_reinterpretation.md)
explain what is verified. Both portable programs and the fresh wheel passed
outside-checkout startup checks; all 155 runtime source hashes, 149 wheel runtime
files and final artifact checksums were independently verified. Package evidence
remains in CURRENT_STATUS.md.
Evidence-supported model regeneration and legacy migration remain unfinished;
local synthetic work needs no new approval.

## 用户提出的重述——2026-09-28（中文版）

更正流程现允许用户针对一条争议主张提出英文及简体中文措辞，预览完整报告，并明确确认后
另存副本。引文、来源标识、主题及分组保持不变。新措辞明确归属于用户，固定标为未经核实、
低置信度的猜测。保留引文不证明事实支持或真实性；更正批注不会自动成为事实。此流程不调用模型。

原始报告、卡片及当前选择保持完整；另行进行报告选择后才可启用副本。已有撤回副本保持
兼容，两种格式共用同一套有界、可验证的历史。过期保存失败会保留草稿，刷新不能将草稿
自动应用到另一条主张。可能依赖旧主张的画像发现或虚构候选人会被移除，原有不确定性说明保留。

完整合成验收为 809 项通过、3 项因 Windows 符号链接权限跳过，另有一条上游弃用提示。
编译、静态检查、旧版兼容、精确保留来源、损坏或变化的输入、混合格式并发保存、新进程恢复
及双语界面检查通过。三种历史中的目录重命名读取时序问题均已修复，并通过 24 项确定性
测试。[流程与边界](../../21_user_proposed_reinterpretation.md)说明具体核验范围。两个便携程序
及全新 wheel 均通过脱离源码启动检查，155 个运行源码哈希、149 个 wheel 运行文件及最终
产物校验和均已独立验证。程序包证据仍记录于 CURRENT_STATUS.md。有证据支持的模型重新
生成及旧格式迁移仍未完成，本地合成工程无需新增审批。

## Legacy report preservation — 2026-09-28 (English)

Both desktop report viewers now offer **Review legacy files**, including when the
active report is invalid. Users can inspect compatibility diagnostics, exact source
content and an archive preview, then explicitly save a separate immutable snapshot.
Unknown fields, malformed JSON, non-UTF-8 bytes, BOM and line endings are preserved.
HTML and Markdown are displayed literally. This workflow does not invent evidence,
translations or confidence; it does not convert, activate or restore a report.
Originals, cards and the active selection remain unchanged.

The service binds every fixed file's presence and bytes, rejects stale previews,
verifies the complete archive on every read, and uses bounded atomic commits with
thread/process locks. Archives remain excluded from evidence even through direct
subtree selection, hardlinks or directory junctions. Four concurrent writers and a
fresh-process reader passed; bilingual UI checks covered both report types at
940×700 and 1100×760. All fixtures were synthetic and no model was called.
The final gate passed 906 tests with three Windows symlink-privilege skips;
compilation and lint passed. Fresh wheel and copied Desktop/Web executables passed
outside-checkout startup. All 157 runtime source hashes, 151 exact wheel runtime
files and six artifact checksums were independently verified. Detailed evidence
is recorded in CURRENT_STATUS.md.

The audit also found that manual-agent prompts still requested obsolete report
shapes. Their output contracts now derive from the same typed bundles as connected
desktop AI, with validation, exact localization and deterministic bilingual reports.
Existing request files must be regenerated. Prompts do not enforce isolation or
atomic writes by themselves.

This completes the preservation stage only. Current-format conversion and activation
for old reports, personal-profile migration, evidence-supported model regeneration,
recoverable encryption and existing browser work remain unfinished. Snapshots remain
plaintext; future retention/deletion must cover them. No new approval is needed for
local synthetic work. Public release, outside recruitment and real-vault migration
remain on the owner's review list. See [workflow and limits](../../22_legacy_report_archives.md).

## 旧版报告保留——2026-09-28（中文版）

两种桌面报告查看器现提供**复核旧版文件**入口，即使当前报告无效也能使用。可以检查兼容性
诊断、精确原文和存档预览，明确确认后另存不可变快照。未知字段、坏格式 JSON、非 UTF-8
字节、BOM 和换行均保留；HTML 和 Markdown 按字面显示。本流程不编造证据、翻译或置信度，
不转换、启用或恢复报告。原件、卡片及当前选择保持不变。

服务绑定每个固定文件的存在状态和字节，拒绝过期预览，每次重读核验整份存档，采用有界
原子提交及线程/进程锁。直接选择存档子目录、硬链接或目录联接均不能让存档进入原始证据。
四进程并发写入及新进程重读已通过；两种报告均在 940×700 和 1100×760 下完成中英文界面
检查。全部样例为合成数据，本轮未调用模型。最终验收为 906 项通过、3 项因 Windows
符号链接权限跳过，编译与静态检查通过。全新 wheel 及独立桌面/浏览器程序均通过脱离源码
启动检查，157 个运行源码哈希、151 个精确 wheel 运行文件及六项产物校验和已独立验证。
详细证据记录于 CURRENT_STATUS.md。

审计还发现手动代理提示词仍要求旧报告结构，现已改为与应用内桌面 AI 共用的类型化报告
契约，要求先校验、提供精确翻译映射，并确定性生成双语报告。已有请求文件须重新生成；
提示词本身不能强制实现隔离或原子写入。

本阶段仅完成原文保留。旧报告的当前格式转换与启用、个人档案迁移、有证据支持的模型重新
生成、可恢复加密及既有浏览器工作仍未完成。快照仍为明文，后续保留期与删除功能须涵盖。
本地合成工程无需新增审批；公开发布、外部招募及真实档案迁移仍留在所有者审核清单中。
详见[流程与限制](../../22_legacy_report_archives.md)。

## Partial legacy conversion — 2026-09-28 (English)

The preserved legacy archive now supports deterministic partial conversion. Only
claims already containing complete bilingual wording, supported metadata and exact
quoted evidence can be copied. The ledger explains copied and archive-only content;
unknown fields and every original byte remain preserved. At least one complete
claim and complete existing bilingual warnings are required. No absent information
is invented, and no model or original evidence source is read.

Preview and explicit saving create a separate read-only report; a second preview
and confirmation select it for readers and references. Source changes block use
while retaining historical reading. An explicit review-only choice disables report
references without falling back to old content, including when the selected target
is damaged. An intact selection journal remains necessary. Regenerate and explicitly
select a valid current report, or select a valid conversion, to resume. Original
correction tools still target the original report. Cards are unchanged.

The integrated gate passed **1045 tests**, with three Windows symlink-privilege skips
and one upstream deprecation warning; compilation and lint passed. Synthetic checks
cover strict consent, stale/tampered payloads, mixed selection versions, preserved
warnings, zero-claim refusal, evidence exclusion, four-process saving and reopening,
and 40 shared history races. Both report kinds passed English/Chinese GUI flows and
visual checks at two sizes. Captured earlier archives and version 0.1 selections
remain byte-exact and readable.

Desktop/Web executables and the fresh wheel passed startup outside the checkout.
The final package audit verified 159 runtime source hashes, 153 exact wheel files,
11 embedded report service/dialog modules, bilingual instructions and six artifact
checksums. No model calls, private-data access, spending, contact or publication
occurred. All previous uncommitted work remains preserved.

Full historical/profile migration, supported model regeneration, browser translation
and session restoration, and recoverable encryption remain unfinished. Local work
continues without approval. Public release/external testers and any real-vault
encryption migration stay on the morning review list in `CURRENT_STATUS.md`.
See [workflow and limits](../../23_legacy_report_conversions.md).

## 旧报告部分转换——2026-09-28（中文版）

已保留的旧版存档现支持确定性部分转换：仅复制原本已有完整双语表述、受支持元数据及
精确证据引文的主张。字段清单说明已复制与仅存档内容；未知字段和每个原始字节全部保留。
至少须有一条完整主张，已有警示也须具备完整双语内容。不补造缺失信息，不调用模型，
也不读取原始证据来源。

预览并明确保存后生成独立只读报告；须第二次预览与确认，才能选作查看和参考。来源变化
后停止使用，历史仍可阅读。明确的仅复核选项会停用报告参考，不退回旧内容；即使目标
损坏也可停用，但选择记录须完整。恢复时须重新生成并明确选择有效当前报告，或选择有效
转换。原有更正工具仍针对原报告，卡片保持不变。

综合验收 **1045 项测试通过**、3 项因 Windows 符号链接权限跳过，另有一项上游弃用警告；
编译和静态检查通过。合成检查覆盖严格同意、拒绝过期和篡改、混合选择版本、警示保留、
拒绝零主张、证据排除、四进程保存及重读，以及 40 项共享历史时序检查。两种报告通过
中英文界面流程及两种尺寸的视觉检查。修改前捕获的早期存档和 0.1 选择记录仍字节完整、
能够重读。

桌面/浏览器独立程序及全新 wheel 均通过脱离源码启动。最终打包验收核对 159 个运行源码
哈希、153 个精确 wheel 文件、11 个嵌入的报告服务/界面模块、双语说明及六项产物校验和。
未调用模型、未读取私人数据、未花钱、未联系他人或发布；此前未提交工作均已保留。

完整历史格式/个人档案迁移、有依据的模型重新生成、浏览器翻译与会话恢复、可恢复加密
仍未完成。本地工作无需审批即可继续。公共发布/外部试用，以及真实档案的加密迁移，
仍列于 `CURRENT_STATUS.md` 的明早审阅清单。详见[流程与限制](../../23_legacy_report_conversions.md)。

## Explicit personal-profile layout migration — 2026-09-28 (English)

Historical flat profile files can now be reviewed literally and explicitly copied
into `profile/`, retaining original bytes and originals. Both companions, Markdown
alone and JSON alone are supported. Unsupported JSON or a nonempty destination
blocks the operation without discarding fields or overwriting files. Preview binds
the chosen vault, source presence/bytes and destination; publication checks the
complete staged pair and uses a shared lock. This changes layout only, without
inventing translations, evidence or missing profile fields.

Opening a legacy vault defers pointer changes until confirmation and successful
loading. Canceling or a failed switch preserves the previous selection and draft.
The viewer now separates the read-only JSON companion from editable Markdown,
preventing JSON inspection from overwriting the draft. Empty placeholders cannot
be saved. Absent companions clear old values, and native-screen navigation no longer
revives a previous vault's JSON through the legacy state bridge.

The final synthetic gate passed **1168 tests**, with three Windows symlink-privilege
skips and one upstream deprecation warning. Compilation, lint and styled bilingual
checks passed. Core coverage includes four-process competition with one complete
publication, fresh-process reopening, byte preservation, stale/tampered input,
invalid formats, unsafe paths and failed publication. Pending migration folders
cannot become original evidence or report references through direct root selection.

Desktop/Web executables and the fresh wheel were rebuilt and started outside the
checkout. Independent verification covered 161 runtime source hashes, 155 exact
wheel files, 13 required embedded report/profile modules, the bilingual guide and
six checksums. No real profiles were migrated, and no AI, paid service, messaging or
publication was used. Earlier uncommitted work remains intact.

Visual inspection found an existing application-wide minimum size imposed by the
export and beacon pages: removing both changed profile pages leaves it unchanged.
The migration dialogs and separate profile viewer fit their tested dimensions;
full-window sizing is the next repair. Supported model regeneration, broader profile
content migration, recoverable encryption and browser work remain. Public release
and real-vault encryption decisions remain on the morning review list.
See [workflow and limitations](../../24_profile_layout_migration.md).

## 明确的个人档案布局迁移——2026-09-28（中文版）

历史扁平档案文件现在可以按原文复核，并明确复制到 `profile/`，保留精确字节及原件。
支持两个配套文件、仅 Markdown 或仅 JSON。JSON 不受支持或目标非空时阻止操作，不
丢弃字段、不覆盖文件。预览绑定所选档案库、来源存在状态/字节和目标状态；提交前检查
完整暂存文件对，并使用共享锁。此操作只改变布局，不补造翻译、证据或缺失档案字段。

打开旧档案库时，在确认及成功加载前不更改档案库指针。取消或切换失败会保留之前的选择
和草稿。查看器现在分开只读 JSON 配套文件和可编辑 Markdown，避免查看 JSON 覆盖草稿；
空白提示不能保存。缺失配套文件会清除旧值，原生页面导航也不再通过旧状态桥接带回上一
档案库的 JSON。

最终合成验收 **1168 项测试通过**、3 项因 Windows 符号链接权限跳过，另有一项上游弃用
警告。编译、静态及实际样式下的双语检查通过。核心覆盖四进程竞争且只提交一个完整目录、
新进程重读、字节保留、过期/篡改输入、无效格式、不安全路径及发布失败。即使直接选作
输入根目录，迁移暂存目录也不能成为原始证据或报告参考。

桌面/浏览器独立程序及全新 wheel 已重建并通过脱离源码启动。独立核对涵盖 161 个运行
源码哈希、155 个精确 wheel 文件、13 个嵌入的报告/档案模块、双语指南及六项校验和。
未迁移真实档案，未调用 AI、使用付费服务、发送消息或公开发布；此前未提交工作完整保留。

视觉检查发现导出页和信标页造成的既有全局窗口最小尺寸问题：移除本轮修改的两个档案
页面后仍然存在。迁移窗口和独立档案查看器适配已测试尺寸，完整主窗口尺寸将作为下一项
修复。有依据的模型重新生成、更广泛档案内容迁移、可恢复加密及浏览器工作仍未完成。
公共发布和真实档案加密的决定仍列于明早审阅清单。详见[流程与限制](../../24_profile_layout_migration.md)。

## Small-window desktop navigation — 2026-09-28 (English)

The application-wide sizing defect identified above is repaired. Each page now
keeps its own scroll area, so hidden export and beacon pages no longer enlarge the
whole window. Tab or programmatic focus reveals lower controls after layout settles.
Ordinary navigation retains page objects, history and worker ownership; existing
page reloads and language-rebuild limits for unsaved drafts still apply.

Consent disclosures remain complete, initially unchecked native controls, with
wrapping text and keyboard/mouse operation. All five export acknowledgements remain
required. Export buttons occupy rows. Long status paths wrap without truncation or
added invisible characters; markup-like text stays literal. Viewing, scrolling or
resizing a page cannot launch an export, generate a beacon or grant consent.

The integrated synthetic gate passed **1193 tests**, with three Windows
symlink-privilege skips and one upstream deprecation warning. Compilation and
core/test/script plus changed-desktop lint passed. An additional all-desktop scan
found six existing line-length issues in five unrelated files, recorded for later
cleanup. Eight navigation, eleven responsive-control and six MainWindow cases were
added; existing worker-lifecycle regressions also passed. All 80 combinations of
20 pages, two languages and two window sizes (940×700 and 1100×760) kept their
requested dimensions. Five representative whole-window views were independently
inspected using application styles and existing Windows fonts registered for
offscreen rendering. Other display scales, platforms and assistive-technology
combinations remain unverified.

Desktop/Web executables and the fresh wheel were rebuilt and started outside the
checkout. Independent verification confirmed 162 runtime source hashes, 156 exact
wheel files, 15 required embedded modules, the bilingual guide and six checksums.
No model, real vault, paid service, external contact or public deployment was used;
previous uncommitted work remains preserved. This is a local usability milestone,
not new model validation or completion of the whole product roadmap.

Next work continues supported report regeneration and broader legacy/profile
content migration, recoverable encryption and browser translation/session recovery.
The existing morning decisions remain public release/external testing and migration
of real vaults to encryption, each after a concrete reviewable proposal. Local
development remains authorized and the continuation task stays active. See
[workflow and limits](../../25_desktop_window_navigation.md) and `CURRENT_STATUS.md`.

## 小窗口桌面导航——2026-09-28（中文版）

上文发现的全局窗口尺寸问题已修复。各页面现保留自己的滚动区域，未显示的导出页和信标
页不再撑大整个窗口。Tab 或程序设置的焦点会在布局完成后显示下方控件。普通导航保留
页面对象、历史和后台任务归属；各页面原有重新加载行为，以及语言重建对未保存草稿的
限制仍然适用。

同意声明保留完整文字，使用默认未勾选的原生控件，文字可换行，键盘及鼠标操作正常；
导出的五项确认仍全部必需。导出按钮分行排列，长状态路径折行且不截断、不加入不可见
字符；类似标记的内容按原文显示。查看、滚动或调整页面大小不能启动导出、生成信标或
授予同意。

综合合成验收 **1193 项测试通过**、3 项因 Windows 符号链接权限跳过，另有一条上游弃用
警告。编译、核心/测试/脚本及本轮修改的桌面文件静态检查通过。额外的全桌面扫描发现
五个无关文件中的六处既有行长度问题，已记录供后续清理。新增 8 项导航、11 项响应式
控件和 6 项主窗口检查；既有后台任务生命周期回归也通过。20 个页面、两种语言及两种
窗口尺寸（940×700、1100×760）的全部 80 种组合均保持指定尺寸。主代理独立查看五张
代表性整窗视图，使用实际应用样式，并为离屏渲染注册已有 Windows 字体。其他显示缩放、
平台及辅助技术组合仍未验证。

桌面/浏览器独立程序及全新 wheel 已重建，并通过脱离源码目录的启动检查。独立核对确认
162 个运行源码哈希、156 个精确 wheel 文件、15 个必需嵌入模块、双语指南及六项校验和。
未调用模型、读取真实档案库、使用付费服务、联系外部人员或公开部署；此前未提交工作
保持完整。本轮是本地可用性里程碑，不代表新增模型验证或整个产品路线图完成。

接下来继续有依据的报告重新生成、更广泛旧格式/档案内容迁移、可恢复加密，以及浏览器
翻译与会话恢复。明早待审事项仍为公共发布/外部试用，以及真实档案库加密迁移，均先准备
具体可审阅方案。本地开发继续处于已授权范围，自动继续任务保持启用。详见
[流程与限制](../../25_desktop_window_navigation.md)及 `CURRENT_STATUS.md`。

## AI-assisted revision of one disputed claim — 2026-09-28 (English)

A saved correction can now lead to an explicitly reviewed local AI suggestion for
one portrait or criteria claim. The owner reviews the exact request, consents to
one local Ollama generation, edits both language versions, previews the complete
report and separately confirms saving. Activation remains a separate decision.
External API and agent-CLI adapters are rejected for this bounded workflow.

The request contains only the selected prior claim/correction as unverified context
and its stored quotations as a closed, separately identified set. Source labels
are never opened. The model returns wording only; the application preserves
citations/topic/group, fixes low-confidence speculation and retains AI-assisted,
quote-limited, unverified attribution even after editing. Existing warnings remain;
dependent findings and fictional candidates are omitted. This does not establish
source truth, semantic support, translation fidelity or full-report regeneration.

The new version 0.3 copy uses the existing shared lock and complete directory
publication. Original files, cards, history and selection remain intact. Exact
report/translation/candidate/annotation bytes are checked before/after generation
and at preview/save. Request hashes are not proof of model execution. Four captured
pre-change 0.1/0.2 copies reopened with all 53 file hashes unchanged. A four-process
mixed-format write and fresh-process recovery passed. Independent consumers keep
attribution and exclude the derived copy from original evidence.

A native Qt abort was reproduced during cancellation testing. The new dialog uses
QObject-owned result/error slots and its worker closure no longer holds the dialog;
cancel waits for worker settlement and discards the reply. Repeated success/error
dialogs assert UI-thread callbacks before deferred deletion. The exact original
native failure cause was not isolated; existing lifecycle regressions and the
repaired flow pass. Eight styled synthetic EN/ZH workflows at 940×700/1100×760 passed,
and four request/preview views were independently inspected.

One fictional portrait was also tested with actual local `qwen3.6:latest`. The
first structurally valid response overgeneralized frequency/intensity. After
tightening episode scope and translation uncertainty, the second request took
29.75 seconds and stated that one event cannot establish a pattern. Both requests
used synthetic data only; the final draft passed validation, separate save/reopen
and exact preservation checks. This is one example, not a model-quality guarantee;
criteria and GUI transport tests remain mocked. No model download, paid service,
real-vault access, messaging or public deployment occurred. The temporary local
server was stopped afterward.

Current full-suite and package counts are in `CURRENT_STATUS.md`. The new desktop,
browser and wheel packages preserve the existing entry points. The fresh-wheel
smoke uses cached dependencies with package downloads disabled. Broader source-based
regeneration, legacy/profile content migration, recoverable encryption and browser
translation/session restoration remain. Existing morning approval items are unchanged;
local autonomous work continues. See [scope and limitations](../../26_ai_assisted_claim_revision.md).

## 一条争议主张的 AI 辅助修订——2026-09-28（中文版）

已保存的更正现在可以用于明确复核的本地 AI 建议，针对画像或择偶标准中的一条主张。
用户查看准确请求，同意一次本地 Ollama 生成，编辑两种语言，预览完整报告，再单独确认
保存。启用仍需另行决定；此有限流程拒绝外部 API 和代理命令行适配器。

请求仅包含作为未经核实背景的所选旧主张/更正，以及另行标识的固定已有引文集合，不沿
来源标签打开文件。模型只返回措辞；应用保留引文/主题/分组，固定为低置信度推测，即使
编辑后也保留 AI 辅助、仅依据已有引文、未经核实归属。已有警示保留，移除相关衍生发现
及虚构候选人。此流程不证明来源真实、语义支持成立、翻译准确或完整报告已重新生成。

新的 0.3 副本使用既有共享锁与完整目录提交机制，原件、卡片、历史和当前选择保持完整。
生成前后及预览/保存时检查报告/翻译/候选文件/批注的精确字节。请求哈希不证明模型实际
执行。修改前捕获的四份 0.1/0.2 副本均可重读，53 个文件哈希全部不变。四进程混合格式
写入及新进程恢复通过；独立消费者检查确认保留归属，并将衍生副本排除在原始证据之外。

取消测试中复现了原生 Qt 中止。新窗口现使用 QObject 持有的结果/错误槽，后台闭包不再
持有窗口；取消会丢弃回复，并等待线程收尾。连续成功/失败窗口检查确认回调处于界面
线程，随后才延迟销毁。原始原生失败的唯一原因尚未确定；既有生命周期回归和修复流程
均通过。940×700/1100×760 下的八组实际样式中英合成流程通过，四张请求/预览视图另行
独立检查。

一个虚构画像还通过实际本地 `qwen3.6:latest` 验证。首个回复结构有效，但过度延伸了
频率/强度；收紧事件范围及双语不确定性后，第二次请求耗时 29.75 秒，明确说明单个事件
不能证明行为模式。两次请求均只用合成数据，最终草稿通过校验、另存/重读及精确保留
检查。这只是一个样例，不保证模型普遍质量；择偶标准及界面传输测试仍为模拟。未下载
模型、使用付费服务、读取真实档案库、发送消息或公开部署，检查后已停止临时本地服务。

最新全套测试与打包数量见 `CURRENT_STATUS.md`。新的桌面、浏览器和 wheel 包保留原入口；
全新 wheel 检查仅使用已缓存依赖并禁用包下载。更广泛的原始来源重新生成、旧格式/档案
内容迁移、可恢复加密及浏览器翻译/会话恢复仍待完成。原有明早审批事项不变，本地自主
工作继续。详见[范围与限制](../../26_ai_assisted_claim_revision.md)。

## Full report regeneration from explicit excerpts — 2026-09-28 (English)

A complete current-format portrait or relationship-criteria report can now be
regenerated from one to five pasted original excerpts and one to ten saved corrections.
The owner confirms original-note status, reviews the exact local request and approves
one generation, then reviews both languages and separately confirms saving. Activation
remains a separate decision. No evidence files are discovered or followed, and prior
AI claims/corrections are unverified context rather than evidence.

Every quotation must match an exact contiguous span in its identified excerpt.
Unknown source IDs, quotations found only in another excerpt and cross-excerpt splices
are rejected. All claims/findings have low confidence, fictional candidates remain
empty, and unsupported sections need no invented filler. Old warnings and translations
survive alongside an AI-regenerated/unverified notice. These checks do not prove truth,
semantic entailment or translation accuracy; the whole new report needs review.

Version 0.4 copies retain exact pasted excerpts, original snapshots and selected
corrections as plaintext. Saving does not replace originals or alter cards/selection.
Exact source, translation, annotation and request changes invalidate generation or
saving. Separate selection keeps regenerated reports as assistant references; full
excerpt snapshots and private annotations do not enter those references automatically.
Six pre-change 0.1/0.2/0.3 copies reopen with all 74 file hashes unchanged. Mixed versions
also pass four-process publication and a fresh fifth-process reader.

Final review found an inherited HTTP 400 retry in the shared Ollama adapter. Both this
flow and single-claim AI revision now explicitly disable that fallback in the reviewed
request; one confirmation permits one transport request. Ordinary requests retain their
existing policy. New tests cover actual HTTP 400 behavior, strict policy validation and
tampered prepared requests. Cancellation discards replies and safely waits for workers;
input drafts survive stale/failed requests. Empty-claim results say that evidence is
insufficient, rather than presenting a substantive finding.

Eight styled synthetic flows cover both report kinds, languages and window sizes;
the two parent-entry views also fit. Complete consent text and buttons remain visible,
and original bytes and active selection are preserved. Latest full-suite, package and
separately identified real local-model results are in `CURRENT_STATUS.md`. Mocked GUI
checks do not establish live-model reliability.

Three actual local `qwen3.6:latest` synthetic calls were made. Both portrait attempts
failed during CUDA startup before producing a reply; the criteria request passed
structure/save/reopen but changed a stated “want” into a stronger requirement. It ran
before the final retry-policy/notice patch. CPU preflight found less available physical
memory than the model weights, so no fourth call was made. Original files and selection
survived every failure, and the owned local server was stopped. Full-portrait real-model
acceptance remains open; next work first diagnoses this isolated runtime failure.

Next work remains broader legacy/profile-content migration, recoverable encryption,
retention controls and browser translation/session restoration. Existing morning review
items remain public release/external testing and any future real-vault encryption
migration, each after a concrete reviewable proposal. Local autonomous work continues
without spending, private-data access, external messaging or publication. See
[full workflow and limits](../../27_full_report_regeneration.md).

## 根据明确摘录重新生成完整报告——2026-09-28（中文版）

现在可以从一至五份粘贴的原始摘录及一至十条已保存更正，重新生成完整当前格式画像或
择偶标准报告。用户确认原始笔记身份，审核准确的本地请求并批准一次生成，然后复核
两种语言，单独确认保存；启用仍需另行决定。不自动发现或沿路径读取证据文件，旧 AI
主张及更正只作未经核实的背景，不是证据。

每条引文必须精确、连续地出现在其编号对应的摘录中；未知来源编号、只在其他摘录出现
的引文及跨摘录拼接均拒绝。所有主张/发现为低置信度，不生成虚构候选人；缺乏支持的
部分无需编造内容填满。保留旧警示及翻译，并添加 AI 重新生成/未经核实说明。这些检查
不证明事实、语义支持或翻译准确，整份新报告仍需复核。

0.4 版本副本以明文保留精确摘录、原件快照和所选更正。保存不替换原件、不改变卡片或
当前选择。来源、翻译、批注和请求的精确内容变化会使生成或保存失效。单独选择后，
重新生成报告仍只作助手参考，完整摘录快照和私密批注不会自动进入这些参考。六份修改前
的 0.1/0.2/0.3 副本均可重读，74 个文件哈希全部不变；混合版本也通过四进程提交及第五个
新进程重读检查。

最终复核发现共享 Ollama 适配器在 HTTP 400 时存在既有自动重试。此流程和单条主张 AI
修订现均在已复核请求中明确关闭该降级，一次确认只允许一次传输请求；普通请求保留原有
策略。新测试覆盖真实 HTTP 400 分支、严格策略校验及准备后被改动的请求。取消会丢弃
回复并安全等待后台结束；过期或失败时保留输入草稿。空主张结果明确表示证据不足，不会
冒充实质性发现。

八组实际样式合成流程覆盖两类报告、两种语言及两种窗口尺寸，两个父窗口入口视图也均
适配。完整同意文字和按钮保持可见，原件字节和当前选择不变。最新全套测试、打包，以及
另行标明的真实本地模型结果见 `CURRENT_STATUS.md`；模拟界面检查不证明真实模型可靠性。

共执行三次实际本地 `qwen3.6:latest` 合成调用。两次画像请求均在 CUDA 启动时失败，未
生成回复；择偶标准通过结构/保存/重读，但将所表达的“希望”加强为要求。该运行先于最终
重试策略/说明修正。CPU 预检发现可用物理内存小于模型权重，因此未进行第四次调用。
每次失败均保留原件和当前选择，自行启动的本地服务已停止。完整画像的真实模型验收仍
未完成，后续先隔离诊断此运行故障。

后续仍需推进更广泛旧格式/档案内容迁移、可恢复加密、保留控制及浏览器翻译/会话恢复。
明早审批事项仍为公共发布/外部试用，以及未来真实档案加密迁移，均须先备妥可审阅的具体
方案。本地自主工作继续，不花钱、不读取真实私密资料、不对外发消息、不公开发布。详见
[完整流程与限制](../../27_full_report_regeneration.md)。


## Local model recovery and honest acceptance — 2026-09-28 (English)

The recovery milestone separated three failures: intermittent large-model CUDA
startup, a confirmed grammar repetition limit, and incorrect bilingual output.
The application now requests narrative strings of at most 1,000 characters from
the model; the full 8,000-character report validation remains unchanged. Existing
reports and pasted inputs are not truncated. Kind-specific prompts reduce unrelated
instructions, and a reusable source-checkout smoke checks one explicit local call
with built-in fictional notes, isolated temporary state and metadata-only results.

The final synthetic gate passed 1567 tests, with three Windows privilege skips.
Compilation, scoped lint and eight bilingual GUI flows passed. Eight pre-change
copies across versions 0.1–0.4 reopen with 114 unchanged file hashes. Mocked tests
do not count as model acceptance.

Nine real recovery requests used existing local models: seven Qwen3.5 and two
Gemma4. Two criteria samples passed structural saving/reopening before the final
grammar projection; one manually reviewed sample still misplaced a limitation and
repeated workflow instructions. The three final-source samples returned replies
but failed strict localization checks. No failed copy was saved; every original
and active selection remained intact. This confirms the grammar fix and safe
failure handling, not complete report-quality acceptance or a CUDA root-cause fix.
The owned server and remaining owned runner were stopped; no listener remains.

The rebuilt Desktop/Web executables and offline fresh wheel passed outside the
checkout. Independent verification matched 167 runtime hashes, 161 wheel files,
all 21 required embedded modules, nine critical compiled code objects and six
artifact checksums. The guide and source-distribution README match current files.
These installation checks made no model calls and do not change the limitations above.

Next, reduce the model's need to generate duplicate bilingual mappings while
preserving exact request review, one explicitly confirmed request and full source/
localization validation. Do not silently repair translations or add hidden calls.
The broader migration, encryption, retention and browser-history work remains.
Morning review items stay public release/external testing and future migration of
real vaults to encryption, after concrete demonstrations. Local work needs no new
approval. No spending, private-vault access, messaging or publication occurred.
See [the recovery guide and complete evidence](../../28_local_model_recovery.md).

## 本地模型恢复与如实验收——2026-09-28（中文版）

本轮恢复区分了三类故障：大型模型间歇性的 CUDA 启动失败、已确认的语法重复次数上限，
以及错误的双语输出。应用现要求模型生成的叙述字符串不超过 1,000 字符，完整报告的
8,000 字符校验保持不变，不截断已有报告或粘贴输入。按报告类型区分的指令减少无关
内容。新增源码仓库验收工具，使用内置虚构笔记和隔离临时状态，每次只检查一次明确
请求的本地调用，仅保留元数据结果。

最终合成验收通过 1567 项测试，三项因 Windows 权限跳过。编译、专项静态检查及八组
双语界面流程通过。八份修改前的 0.1–0.4 副本可重读，114 个文件哈希不变。模拟测试
不计为模型验收。

本轮恢复共执行九次真实本地请求：七次 Qwen3.5、两次 Gemma4。最终生成结构修正前，
两份择偶标准样例通过结构、保存和重读；其中一份经过人工复核的样例仍将局限性放错
位置，并重复工作流程指令。最终源码的三份样例均返回回复，但未通过严格本地化检查。
没有保存失败副本，全部原件和当前选择保持不变。这证明语法故障已修复、失败处理有效，
不代表报告质量全面通过或 CUDA 根因已经修复。自行启动的服务及遗留自有运行进程
均已停止，未遗留监听。

重建的桌面/浏览器程序及离线全新 wheel 已通过脱离源码验收。独立检查确认 167 个运行
哈希、161 个 wheel 文件、全部 21 个必需嵌入模块、九个关键编译代码对象及六项产物
校验和。双语指南和源码发行包 README 与当前文件一致。安装检查未调用模型，
也不改变上述模型质量限制。

下一步降低模型生成重复双语映射的负担，同时保留准确请求复核、一次明确确认的请求，
以及完整来源/本地化校验。不静默修补翻译，也不增加隐藏调用。更广泛的迁移、加密、
保留控制及浏览器会话工作仍待完成。明早审批事项保持为公共发布/外部试用及未来真实
档案加密迁移，均须先备妥具体演示。本地工作不需要新的批准。本轮未花钱、未读取真实
私密档案、未发送消息，也未公开发布。详见[恢复指南与完整证据](../../28_local_model_recovery.md)。
