# Decision Records

## ADR-015: Independent Modes, Private Support and Consent-Bound Shared Activities

Status: Accepted direction from the owner's full October 17 replacement attachment
(`New Text Document (3).md`). Amends ADR-014; implementation and real acceptance remain
separately recorded in the current status/progress documents.

### English

Context: The replacement request explicitly includes friendship, relationship support,
private observations/protective filtering, joint activities, preparation, user-initiated
in-meeting help and private reflection with optional consented audio. Completing a first
match does not finish this scope. The earlier summary-only service needs a narrow, explicit
extension; this must not expose full profiles or turn the Site into an AI intermediary.

Decision:

- Extend the existing repository, Python storage/CLI and Sites Worker/D1. Romance and
  friendship have independent participation, versioned summary, visibility and reciprocal
  conditions; friendship opt-in cannot imply romantic consent. Unknowns remain unknown.
- Keep raw material/audio/transcripts, private observations, risk reasons, assessments and
  reflection local. Authorized OpenAI analysis is permitted under actual service settings;
  local execution does not imply zero cloud retention. No automatic migration of real data.
- Permit Sites only individually approved minimal planning preferences, plan versions,
  confirmations and selected shared feedback in addition to summaries/necessary state.
  Approval binds person, version, purpose, audience, expiry and withdrawal; A cannot approve B.
- Construct joint context from approved objects alone, through a restricted builder or
  genuinely isolated supported context. Never load private profiles then rely on a secrecy
  instruction. Shared feedback uses individual approved contributions, not merged reports.
- New plan versions invalidate old confirmations. Missing input/confirmation stays pending.
  Withdrawal stops future shared access/generation and clears controlled caches; previously
  disclosed copies cannot be recalled. Generating a plan is not permission to contact,
  reserve, buy, pay, write a calendar, record or track location.
- Use behavior/source/context/repetition/uncertainty to distinguish mismatch, unclear evidence
  and concrete risk. No diagnoses, personality verdicts, lie scores or global private-risk
  rankings. Personal help never requires peer consent; clear threats do not require mediation
  or another meeting. The same boundary applies when the user pressures another person.
- Keep the unified Skill small with progressive references. Adapt verified methods with
  provenance; exclude mandatory MBTI/scores, gender defaults and developer grilling from
  ordinary user conversations. Render the owner-approved warning at its required UI points.
- Verify location hints, real place lookup, map display, file input, microphone and transcription
  separately. Text/recollection is always a supported design path. Joint audio requires
  distinct recording/transcription/cloud-processing consent and retention/shared-report choices.
  Native voice is not a plugin recording API, and an external API is not assumed prepaid.

Consequences: Reuse the deployment/channel evidence from `e742c0a` without claiming it proves
new features. Full-profile/private-report upload remains forbidden. The twenty replacement
acceptance categories require real available channels and clear external blockers. The source
authority, one-way hosted mirror and verified 0.5.3 recovery binary decisions remain unchanged.

### 中文版

背景：完整替代要求明确包含交友、关系支持、私人观察／保护筛选、共同活动、准备、本人主动中途帮助及
可选同意音频的私人复盘。首次匹配不代表本次范围完成。原“只存摘要”服务需要狭窄明确扩展，不能因此
暴露完整档案或让网站成为 AI 中转站。

决策：

- 扩展现有仓库、Python 存储／CLI 和 Sites Worker/D1。恋爱／朋友各自有参与、版本化摘要、可见性和
  双向条件，朋友同意不推出恋爱许可，未知保持未知。
- 原材料／音频／转写、私人观察、风险原因、分析和复盘留本机。按实际服务设置允许获准 OpenAI 分析，
  本机执行不表示云端零保留，不自动迁移真实资料。
- 在摘要／必要状态之外，仅允许 Sites 保存各自批准的最小安排偏好、计划版本、确认及选定共享反馈。
  批准绑定本人、版本、用途、受众、到期和撤回，A 不能代 B 批准。
- 共同上下文只由获准对象通过受限构建器或真正隔离的受支持上下文构建，不能先读私密档案再靠保密指令。
  共享反馈只用各人批准的贡献，不合并私人报告。
- 新计划使旧确认失效，缺失输入／确认保持待定。撤回停止未来共享读取／生成并清受控缓存，已披露副本
  无法收回。生成计划不授权联系、预订、购物、付款、日历、录音或位置跟踪。
- 用行为／来源／背景／反复／不确定性区分不合适、材料不清与具体风险，不诊断、不作人格定论、测谎分
  或全站私人风险排名。私人求助不要求对方许可，明确威胁不要求调解或再见面；使用者施压时同样指出。
- 统一 Skill 保持简洁，按需展开参考；有出处地改编已核实方法，普通对话排除必填 MBTI／评分、性别默认
  和开发用穷尽式盘问。获准提醒必须在要求的 UI 位置实际显示。
- 分别核实位置提示、真实地点检索、地图、文件、麦克风和转写。文字／回忆一直是有效设计路径。共同
  音频分别要求录音／转写／云端处理许可及保留／共享选择。原生语音不是插件录音 API，不假定外部 API 已付费。

影响：复用 `e742c0a` 部署／通道证据，不把它当成新功能证明。继续禁止完整档案／私人报告上传。
二十类替代验收要求真实可用链路及明确外部缺口。源码权威、单向托管镜像及已验证 0.5.3 恢复程序保持有效。

## ADR-014: ChatGPT Entry, Local Private Profile, Sites Summary Service

Status: Accepted baseline, amended by ADR-015 (owner requirements, October 17, 2026); implementation
and acceptance are recorded separately in `CURRENT_STATUS.md` and `PROGRESS_TRACKER.md`.

### English

Context: The owner wants to reuse the existing project, use their own ChatGPT
desktop conversation and cloud models, keep the complete profile on their computer,
and share only an explicitly approved summary for an authenticated matching service.
Earlier GUI-first, offline-default and metadata-only rendezvous directions conflict
with this request. They are historical where superseded, not parallel roadmaps.

Decision:

- Make `plugins/slowmatch/` the unified workflow entry. Focused Skills guide the
  conversation and call local tools when supported. The user's own values and
  answers are authoritative; no founder profile defaults.
- Reuse the Python core with versioned private/draft/publication/assessment objects,
  guarded local persistence, corrections and explicit legacy import. New state
  defaults to `%LOCALAPPDATA%/AI-SlowMatch/work`, outside OneDrive and Git.
- Allow the authorized personal context needed for OpenAI cloud analysis. This is
  not permission for Sites to receive raw chats, full profiles or private reports.
- Sites stores only separately approved summary fields and necessary identity,
  visibility and version state. Use its supported Worker/D1 runtime and verified
  request identity, not a client-supplied owner ID. Check both participants' hard
  conditions and explain only shared information. Deep analysis remains local.
- Bind approval to content, destination, audience and version. A draft is not
  approval, a hash is not a signature, and local approval is not remote-write evidence.
- Keep the original repository authoritative. `apps/matching_site/` synchronizes
  one way to the hosted deployment repository required by Sites. Preserve the
  original remote and unrelated work; do not create independently maintained products.
- Retain validated 0.5.3 fixed-EXE/recovery evidence. New 0.6.0 source does not imply
  rebuilding the EXE. No additional main chat client, Ollama migration or Tauri work.

Consequences: Sites introduces intentional remote storage of permitted summaries,
not of complete profiles. Browser access, sign-in, MCP connection, local Skill
installation and two independent accounts require separate proof. Public directory
distribution and local-executor eligibility cannot be assumed from owner installation.
Routine authorized work continues while blocked external prerequisites are reported
accurately. No private data migration has been performed merely by adopting this ADR.

### 中文版

背景：所有者要求复用原项目，在自己的 ChatGPT 桌面对话中使用云端模型，完整档案以本人电脑为主存，
只把独立批准的摘要交给认证匹配服务。旧 GUI 优先、默认离线和仅保存会合元数据的方向与此冲突，
被替代部分保留为历史，不作为并行路线。

决策：

- `plugins/slowmatch/` 成为统一工作流入口，按需 Skills 引导聊天并在支持时调用本机工具。
  每个人的价值观和答案以本人为准，不设置创始人档案默认值。
- 复用 Python 核心，使用分开的版本化私人档案／草稿／发布记录／私人分析、受保护本地持久化、
  纠正和明确旧数据导入。新状态默认位于 OneDrive 和 Git 之外的 `%LOCALAPPDATA%/AI-SlowMatch/work`。
- 允许 OpenAI 云端处理已授权任务所需个人资料，不代表允许 Sites 获取原始聊天、完整档案或私人报告。
- Sites 仅保存独立批准的摘要字段和必要身份、可见性、版本状态。使用受支持的 Worker/D1 与验证后的
  请求身份，不信任客户端自报所有者。检查双方硬条件，只解释共享信息，深入分析留在本人工作流。
- 批准绑定内容、目的地、受众和版本。草稿不是批准，哈希不是签名，本机批准不是远程写入证明。
- 原仓库继续作为权威，`apps/matching_site/` 单向同步至 Sites 要求的托管部署仓库。保留原远端和他人
  工作，不建立独立维护的并行产品。
- 保留已验证的 0.5.3 固定 EXE 与恢复证据。0.6.0 新源码不表示 EXE 已重建，不另做主聊天客户端、
  Ollama 迁移或 Tauri 工作。

影响：Sites 有意远程保存获准摘要，不保存完整档案。网页访问、登录、MCP 连接、本机 Skill 安装和
两个独立账号均需分别证明。不能凭所有者安装推断公开目录分发或本机执行资格。常规获准工作继续推进，
外部缺口如实记录。接受本决策本身不表示已经迁移真实私人数据。

## Earlier decisions (read with ADR-014) / 早期决策（以 ADR-014 为准）

## ADR-001: Local-First Instead Of Cloud-First

Status: Accepted for complete private profiles; remote-summary scope amended by ADR-014.

Context: The project handles sensitive relationship conversations, risk reflections, and potentially personal profile documents.

Decision: The product direction is local-first. User data should live in user-owned local files unless a future feature explicitly asks for remote storage with consent.

Consequences: More responsibility moves to local file format design, export, deletion, and verification. The project avoids platform-style data centralization.

## ADR-002: GUI-First Instead Of API-First

Status: Superseded by ADR-014; retained as historical desktop direction.

Context: A FastAPI prototype is useful for tests and contracts, but the user-facing product is a local desktop trust tool.

Decision: The GUI is the primary interaction surface for the current phase. FastAPI is retained only as an optional local API.

Consequences: Core services must stay UI-independent, and API routes should wrap engine behavior rather than own business logic.

## ADR-003: Python Core For Early AI Engine

Status: Accepted

Context: AI providers, schema validation, and safety logic need fast iteration.

Decision: Keep the core engine in Python for early phases.

Consequences: Python remains the source of truth for analyzers, provider adapters, tests, and schema workflows until a later migration justifies moving pieces to Rust or another language.

## ADR-004: PySide6 For Early Desktop GUI

Status: Retained for legacy/recovery utilities; primary entry superseded by ADR-014.

Context: The project needs a local desktop GUI before a full Tauri migration is worth the extra build complexity.

Decision: Use PySide6 for the first desktop GUI shell.

Consequences: The GUI can ship quickly while sharing Python models and services. The UI should be modular so a future shell can replace it.

Implementation note 2026-06-21: `apps/desktop_pyqt/` and `run_desktop.py` now provide the first runnable PySide6 MVP path. GUI widgets call the Python core engine and should not own safety or report-generation business logic.

## ADR-005: Future Tauri Plus Python Sidecar Migration

Status: Deferred; not part of the ADR-014 migration.

Context: Tauri offers a strong desktop shell and Rust integration, but the engine is still evolving.

Decision: Treat Tauri plus Python sidecar as a medium-term migration path.

Consequences: Keep engine APIs clean, file formats stable, and side-effect boundaries explicit so a sidecar bridge can be added later.

## ADR-006: JSON Schema Over XML As Primary Format

Status: Accepted

Context: The project needs inspectable, testable, signable documents that work across Python, Rust, and potential GUI shells.

Decision: Use JSON and JSON Schema as the primary data contract. XML may be optional import/export only.

Consequences: Report, profile, and trust ladder files should validate against JSON Schema before signing or display.

## ADR-007: Provider Plugin Architecture

Status: Accepted

Context: The AI layer must avoid vendor lock-in and hard-coded provider behavior.

Decision: Use provider adapters behind a common interface and a registry.

Consequences: GUI code should select providers through the registry. Provider outputs must be structured and schema-validated before report generation.

## ADR-008: Verifiable Reports Via Signatures, Not Truth Claims

Status: Accepted

Context: Users may need report integrity checks, but the app cannot prove real-world truth.

Decision: Signed reports prove schema-valid content integrity and signing source only.

Consequences: Every signing and verification view must include a disclaimer that signatures do not prove authenticity, completeness, wrongdoing, or relationship safety.

## ADR-009: No Public Personality Score

Status: Accepted

Context: A public score would turn a safety tool into reputation infrastructure or social credit.

Decision: The system must not create public personality scores, deterministic morality labels, or public dating rankings.

Consequences: Any local report should use risk signals and uncertainty notes, not "good person" or "bad person" labels.

## ADR-010: FastAPI Retained Only As Optional Local API

Status: Accepted for the existing FastAPI code; ADR-014 adds a separate Sites Worker summary service.

Context: Existing FastAPI routes provide useful contracts and tests.

Decision: Keep FastAPI only as an optional local API server.

Consequences: Future work should move core logic into engine modules and keep API code thin. Documentation should not present the app as a cloud backend.

## ADR-011: Ollama Adapter Implemented With Stdlib HTTP, No New Dependency

Status: Historical implementation retained; recommended-default direction superseded by ADR-014.

Context: Phase 2 calls for an Ollama (local) provider adapter as the recommended default AI path, since it keeps imported chat/profile data on-device. The project has no existing HTTP client dependency (`httpx` is dev/test-only, used for FastAPI's `TestClient`).

Decision: Implement `OllamaClient` using only Python's stdlib `urllib`, with an injectable `transport` callable so unit tests never need a live Ollama server or network access. Provide two thin adapters around the same client: one for the `LLMClient` protocol (services), one for the `AIProvider` protocol (registry/Settings UI).

Consequences: No new third-party dependency was added for this feature. The `LLMClient`-side adapter raises `OllamaUnavailableError` on failure (services should know loudly if their AI call didn't happen); the `AIProvider`-side adapter instead catches that error and returns a readable error in its output dict, because the Settings screen calls providers synchronously in the UI thread and must not crash. If a richer Ollama feature set (streaming, embeddings, model pull/list) is needed later, revisit whether stdlib `urllib` is still sufficient or whether `httpx` should be promoted to a core dependency.

## ADR-012: Thin Rendezvous Server For Nearby Discovery (Amends ADR-001 Scope)

Status: Historical (owner decision, 2026-07-06); first-version service scope superseded by ADR-014.

Context: The compatibility pillar (`docs/11_compatibility_matching_plan.md`) was designed
strictly peer-to-peer, which only works for two people already in contact. The owner now
wants nearby-location matchmaking between strangers, while keeping all profile data local,
with the platform authenticating exchanged matching information so users cannot privately
alter cards or craft per-target personas.

Decision: Add an **optional online rendezvous server** that is a bulletin board and a
notary, never a profile database. It stores only: pseudonym, client-derived coarse geohash
bucket, Tier-1 gate ranges, a contact channel hidden until mutual accept, and compatibility
card **fingerprints** with attestation history. Cards themselves travel person-to-person
(email/QR/file), encrypted, never through the server. Attestation provides tamper-evidence
and history transparency — explicitly not truth verification (same stance as ADR-008).

Consequences: ADR-001 stands for all personal data (local-first); this ADR narrowly
authorizes server-side *rendezvous metadata*. ADR-009 still forbids scoring: the server
gates only on location bucket + mutual Tier-1 ranges and never ranks. Discovery requires
the requester to have an attested card (no browsing without skin in the game). Full design:
`docs/12_rendezvous_matchmaking_plan.md`.

## ADR-013: Decentralized Rendezvous — No Single Operator, Minimal Server

Status: Historical (owner decision, 2026-07-06); first-version hosting direction superseded by ADR-014.

Context: ADR-012's thin rendezvous server still implied one hosted service. The owner
requires that the rendezvous layer not depend on a server owned or rented by one person,
that it can ride on existing social platforms (Facebook, 小红书, etc.), and that server
requirements stay minimal because users bring their own AI for all analysis.

Decision: Three deployment models, no privileged operator. (A) **Private nodes** — the
node is a trivially self-hostable artifact (`run_rendezvous_node.py`, single small
machine); communities run their own, like private game servers, and users choose node
URLs. (B) **Platform relay, serverless** — armored, checksummed "beacon" text blocks
(`matchmaking/beacon.py`) that users post and copy **manually** on platforms they already
use; the app parses and matches locally; contact flows through the platform's own DMs;
no scraping or login automation, ever. (C) **Federation** of nodes — designed, deferred
until P1 keypair signatures exist.

Consequences: no single point of control or failure; the platform account becomes the
identity anchor in Model B (post timestamp = public witness), with honest limits — the
checksum stops corruption/casual edits, not determined forgery, until P1 Ed25519
signatures. Nodes must stay small (bulletin board + notary only); anything needing real
compute belongs client-side with the user's connected AI. Full design:
`docs/14_decentralized_rendezvous.md`.
