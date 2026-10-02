> English: This dated record preserves the earlier audit/design. The implemented October 2 correction and current evidence are in [standards correction](32_standards_correction.md) and [current status](../CURRENT_STATUS.md).
>
> 中文版：本文保留早期审计／设计。10 月 2 日已实施整改及当前依据见[规范整改](32_standards_correction.md)和[当前状态](../CURRENT_STATUS.md)。

# Rehabilitation audit and architecture / 渐进修复审计与架构

## Current standards audit — English (2026-10-01)

**Status: audit and proposed correction complete; structural implementation awaits
the requested grilling design confirmation.** The executable, application source and
installed skill have not been replaced. The authoritative proposal is the new opening
section of [the owner plan](../PLAN_FOR_ONEPUCHMAN.md); current decisions are in
[Owner review](../OWNER_REVIEW.md). Everything below the historical boundary in this
document is an earlier checkpoint, not today's backlog.

### Scope, preservation and evidence

The parent project folder contains this development repository, a separate private
vault and local assistant configuration. This audit covered application source,
development documentation, build artifacts, Git metadata and the installed skill.
Private vault contents were excluded. This was not a complete secret/history scan
or a claim that every legacy subsystem is ready for users.

Before documentation edits, 373 selected development files were saved outside the
checkout and OneDrive; all 373 restored file hashes matched. A complete Git history
bundle was verified and restored into a new bare repository; the development branch
resolved to `e29311cacea47f3de91c7eb143f94b11739569be`. The source snapshot excludes
papers, caches, runtime data and private vaults. Its SHA-256 is
`ff51729888bd034f199ad493b5b7e40a8659d1321adce0b7a4708725669c817d`.
The local location/manifest is recorded in `build/standards-audit-source-safeguard.json`.
This is a one-off safeguard, not an implemented recurring backup system.

The fresh full suite returned **2115 passed, 1 failed, 9 skipped**, one dependency
deprecation warning, in 445.07 seconds. Compilation of `src`/`apps` and full
source/app/test Ruff checks passed. An isolated rerun, 20 synthetic repetitions and
41 targeted archive/history tests passed, but do not erase the original failure.
No real AI inference or microphone recording was performed.

### Confirmed findings and practical consequences

| Priority / ID | Evidence | Consequence and required correction |
|---|---|---|
| P1 / R1 | No root EXE; four names under `dist/`. `build_exe.ps1:6` defaults to Web; `packaging/build_windows.ps1:7` permits arbitrary artifact names. | The owner must guess which program to open. Make one fixed root Desktop EXE; preserve old artifacts with provenance before archiving them. The existing plain `dist/AI-SlowMatch.exe` is the older browser product. |
| P1 / R2 | `pyproject.toml:7` and package `__init__.py:3` both contain `0.1.0`; all four EXEs lack FileVersion/ProductVersion/ProductName. Desktop `app.py:20` sets no application version/About. | Use one product-version source and derive application, Windows and release metadata. Distinguish version from build/source identity. |
| P1 / R3 | `packaging/build_windows.ps1:47,81,86` builds directly into `dist` before smoke verification; CI `build-apps.yml:20–27` has no matching-source test dependency. | Failed builds can affect an existing artifact; no reusable promotion/rollback gate exists. Build in staging, verify, then atomically promote after the running app is closed. |
| P1 / R4 | At audit start: 37 tracked modifications, 220 untracked files, no staged changes or tags. Remote feature-branch HEAD equals local `e29311c…`; many recent services, packaging files and workflows are untracked. | Remote equality covers the old baseline, not recent development. Preserve, review and coherently commit safe source before claiming GitHub synchronization. |
| P1 / T1 | Fresh full-suite legacy-archive concurrency failure. Controlled Windows handle/path reproduction also rejects a legitimate pending-directory rename: `report_review.py:164–165,257–260`, `legacy_reports.py:567`. | Add a deterministic test for rename during path resolution and narrowly handle the valid transition. Do not broadly swallow path errors or weaken symlink/reparse checks. Files remained intact; the next read passed. The original failure's exact cause is still unproven. |
| P1 / A1 | `ai/chatgpt_backend.py:205–214` drops reported model, response ID and usage. An offline probe accepted a deliberately different reported model, with zero network attempts. | Preserve a typed result with requested/reported IDs, provider, completion and safe usage metadata. Handle documented aliases explicitly. This proves a verification gap, not actual server substitution. |
| P1 / A2 | `chatgpt_auth.py:239–268` blocks on stream reads; `reflection_chat_screen.py:216–230,316–326` keeps busy controls after End. | End can leave Start unavailable. Add request cancellation and an overall deadline; immediately detach cancelled work from UI readiness. Late replies must not alter a newer session. Local cancellation cannot guarantee server-side usage has stopped. |
| P1 / A3 | `reflection_chat.py:490–501` includes all user answers but only the last two AI questions, without per-answer linkage. | Earlier short answers such as “yes” can lose their meaning. Preserve question/answer context, while AI questions remain ineligible as evidence. |
| P1 / P1 | `reflection_chat.py:81,167` requires only a bilingual question; `save()` at line 738 creates a session reflection plus plaintext transcript. | This is adaptive intake, not the full supportive conversation or maintained personal model. Add useful responses and optional questions, followed by a separate, user-controlled model lifecycle. Existing legacy correction tools do not complete this new flow. |
| P2 / A4 | Model recommendation is a name heuristic (`chatgpt_models.py:23`); selection is only in memory (`chatgpt_connect_screen.py:226–230`, `ai_settings.py:16–31`). | Retain account-specific model choice, refresh availability, and label unmeasured recommendations honestly. Never upgrade by changing a display name. |
| P2 / A5 | `providers/registry.py:6–24` contains placeholders and maps unknown provider names to Mock; primary ChatGPT uses a separate path. Streaming/UI errors lose useful distinctions. | Introduce consistent capability/error contracts; unknown providers fail explicitly. Keep demo/test Mock clearly selected. There is no evidence this older registry replaces primary ChatGPT replies. |
| P2 / R5 | Strong existing package receipt checks 181 runtime files/29 modules, but its one-cycle helper is ignored under `build/`; dependency constraints are not enforced. `pip/cache` is addable. | Preserve package verification, make it reusable, record source/dependency/build inputs, and review staged contents. Do not claim reproducible builds or a clean publication audit yet. |
| P2 / D1 | `docs/30_conversation_first_product.md` says comparison is absent; current code/docs31 implement it. `packaging/README.md` and CURRENT_STATUS name different EXEs. Older future-task docs still request the initial shell. | Consolidate document authority; archive old checkpoints with redirects after preservation. Do not keep adding competing “current” instructions. |

### Today's model evidence and Pi assessment

The app uses official ChatGPT-plan authorization and the public Responses endpoint;
it does not control the ChatGPT desktop app or read its conversations. On October 1,
the app's own service renewed its existing authorization once and fetched its model
catalog once: **GPT-6-Astra, GPT-5.6-Sol, GPT-5.6-Terra, GPT-5.6-Luna, GPT-5.5**.
No 6.1 entry was returned. The transport prohibited inference. The safe receipt is
`build/standards-audit-account-catalog.json`. A listed model is not proof of a
completed request or useful output. Official documentation distinguishes the account
catalog from Codex app-server's potentially bundled/cached catalog:
[models/inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
[app-server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server).

The default selects a light-sounding name from this actual catalog, explaining Luna
5.6 without a hardcoded version. No speed, quality or plan-consumption comparison
has validated that recommendation. The spoken label “So AI” was not found as a
provider in the examined AI/desktop source and is not treated as a new dependency.
Local speech recognition remains separate: this plan-sharing route does not expose
the audio/transcription APIs ([preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)).

Pi was inspected at commit `8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d`, package
version **0.99.2**, a TypeScript/Node project requiring Node >=22.19.0. This is source
snapshot provenance, not a verified npm release. Reuse its provider contracts,
credential-store separation, stream events, cancellation and error patterns within
Python. Its OpenAI provider starts from a static catalog, and its OAuth choices
differ from this app's identity validation; wholesale replacement is not justified.
See the pinned [README](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/README.md),
[package](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/package.json),
[provider](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/src/providers/openai.ts),
[OAuth](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/src/auth/oauth/openai-chatgpt.ts).

### Coaching skill provenance and selective adaptation

Installed `~/.codex/skills/goutoujunshi` is clean at
`30d11e2894d1939c035ef9a32617f4ba365397c2` (July 21). Its configured origin redirects
to `shengjidaguai-china/goutoujunshi`; upstream main is
`6db7354a4002dc7c448a9c87ffdad8132570c9d3` (September 15), **31 commits ahead, zero
behind**. No update has been performed. The installed license is PolyForm
Noncommercial; the pinned upstream [license](https://raw.githubusercontent.com/shengjidaguai-china/goutoujunshi/6db7354a4002dc7c448a9c87ffdad8132570c9d3/LICENSE)
is MIT, with the change recorded in its [changelog](https://raw.githubusercontent.com/shengjidaguai-china/goutoujunshi/6db7354a4002dc7c448a9c87ffdad8132570c9d3/CHANGELOG.md).

Retain empathy, facts/inferences/unknowns, reciprocity, boundaries, optional next
steps and evidence-aware correction. Exclude mandatory person scores, compulsory
MBTI intake, gender-based initiative defaults and automatic pursuit assumptions.
The newer memory/ChatLab tools are not automatically authorized to read user data.
Its SQLite memory is not disk encryption. Back up the old checkout, stage the pinned
update, validate in synthetic isolated storage, then switch; app integration is a
separate reviewed, versioned module allowlist with commit/license/file hashes.
The main reflection path does not currently load this skill; only older coaching
routes load six mutable local files (`api/routes_local_ai.py:1096–1235`).

### Grilling: challenged assumptions and revised plan

| Challenge | Revision and acceptance |
|---|---|
| “One more renamed EXE solves delivery.” | One complete fixed root EXE, staged verification, safe lock handling and exact rollback; no network updater or extra launcher component. Test two successive promotions and failure recovery. |
| “Newer name or successful login proves AI works.” | Separate sign-in, catalog, completed inference and semantic acceptance. Preserve reported model and reject incomplete streams; validate real synthetic conversations separately. |
| “Passing 2116 tests proves this release.” | Today's full suite has a failure. Preserve evidence, fix the confirmed race narrowly, then rerun focused and full gates on frozen source. |
| “Installing Pi or updating the skill will fix the product.” | Keep Python/PySide; selectively adopt reviewed patterns/content. Add coaching responses and user-model lifecycle explicitly; do not import foreign data stores or a whole prompt. |
| “An exported reflection is a trained personal AI.” | Model records are revisable observations/preferences/inferences with sources, time, uncertainty and supersession. Optional memory requires view/correct/pause/revoke/export/delete and separate cloud consent. |
| “A push or a backup folder means work is protected.” | Restore source and Git into empty locations; commit only reviewed safe contents; verify remote commit. Keep backups and private data out of publication. |

The phase dependency is **S0 preservation/failing baseline → S1 fixed release → S2
AI connection reliability → S3 coaching/controlled model → S4 real acceptance and
source delivery**, with detailed work, recovery and acceptance in the owner plan.
README owns launch instructions; the plan owns approved requirements; tracker owns
current work; status owns current evidence; Owner review owns decisions; architecture
and ADRs own design; `docs/history/` will hold preserved superseded material.

Two decisions remain: fixed EXE in this repository root or its parent (recommend
repository root), and bounded opt-in cross-session memory now or explicitly deferred
(recommend individually approved memory with complete lifecycle controls). The local
grilling skill requires shared-understanding confirmation before acting. Existing
authorization covers investigation and safeguards; structural changes await that
design confirmation. Real inference still needs the truthful extra-credit setting
confirmation, and microphone acceptance needs an available device. No paid API,
private-data import, public deployment, messaging or hourly resumption is proposed.

This review changes only the opening audit/status/plan/review/tracker documentation
plus ignored local evidence helpers and receipts. Evidence includes
`standards-audit-pytest.log`, `standards-audit-pending-handle-race.log`,
`standards-audit-model-provenance.py/.json`, and `standards-audit-validation.json`
under `build/`. Existing Desktop and Desktop-Next hashes remain unchanged. No commit,
push, new EXE, skill installation or claim of completed real AI acceptance is made.

## 当前规范审计 — 中文版（2026-10-01）

**状态：审计及整改提案完成；按照要求的 grilling 流程，结构性实施等待共同设计确认。**
程序、应用源码及已安装 skill 尚未替换。正式提案位于[所有者计划](../PLAN_FOR_ONEPUCHMAN.md)的新开篇，当前决定见[所有者审阅](../OWNER_REVIEW.md)。本文历史分界线以下均为此前里程碑，不是今天的待办。

### 范围、保护与验证依据

上一级项目目录包含开发仓库、独立私人资料库和本地助手配置。本轮审查应用源码、开发文档、构建产物、Git 元数据及已安装 skill，未检查私人资料库内容。这不是完整的秘密信息／历史扫描，也不代表所有旧子系统都已适合用户使用。

文档修改前，已在仓库及 OneDrive 之外保存 373 个选定开发文件，恢复后 373 项哈希全部一致。完整 Git 历史包通过校验，并在新建裸仓库中恢复；开发分支对应 `e29311cacea47f3de91c7eb143f94b11739569be`。源码快照排除论文、缓存、运行数据及私人资料库，其 SHA-256 为 `ff51729888bd034f199ad493b5b7e40a8659d1321adce0b7a4708725669c817d`。本地位置及清单记录在 `build/standards-audit-source-safeguard.json`。这是一次性保护，不是已实现的定期备份系统。

本次全量测试 **2115 项通过、1 项失败、9 项跳过**，另有一项依赖弃用提示，用时 445.07 秒。`src`／`apps` 编译及源码／应用／测试全范围 Ruff 通过。单独重跑、20 次合成重复诊断和 41 项归档／历史定向测试通过，但不能抹掉首次失败。本轮未调用真实 AI 推理或麦克风录音。

### 已确认问题及实际影响

| 优先级／编号 | 证据 | 影响及整改要求 |
|---|---|---|
| P1／R1 | 根目录无 EXE，`dist/` 有四种名称；`build_exe.ps1:6` 默认构建 Web，`packaging/build_windows.ps1:7` 允许任意产物名称。 | 用户需要猜测打开哪个程序。统一固定根目录桌面 EXE，保留旧产物及来源后再归档。目前普通名称 `dist/AI-SlowMatch.exe` 实际是旧浏览器产品。 |
| P1／R2 | `pyproject.toml:7` 及包 `__init__.py:3` 分别写死 `0.1.0`；四个 EXE 均无 Windows 文件版本／产品版本／产品名称；桌面 `app.py:20` 未设置应用版本或关于页。 | 使用唯一产品版本来源，派生程序、Windows 及发布信息；产品版本与构建／源码身份分别记录。 |
| P1／R3 | `packaging/build_windows.ps1:47,81,86` 在启动检查前直接构建进 `dist`；CI `build-apps.yml:20–27` 不依赖同份源码的测试成功。 | 失败构建可能影响已有产物，缺少可重复的正式替换及回滚检查。先暂存、验证，应用关闭后再原子替换。 |
| P1／R4 | 审查开始时有 37 项已跟踪修改、220 个未跟踪文件，无暂存及标签；远端功能分支与本地旧提交 `e29311c…` 一致，多项新服务、打包及工作流未跟踪。 | 远端一致仅覆盖旧基线，不包含近期开发。保护、审阅并分组提交安全源码后，才能称 GitHub 已同步。 |
| P1／T1 | 新全量测试的旧报告并发归档失败；受控 Windows 句柄／路径测试另复现合法暂存目录改名被拒绝：`report_review.py:164–165,257–260`、`legacy_reports.py:567`。 | 增加“路径解析期间改名”的确定性测试，只修复合法转换。不能宽泛吞掉路径错误或削弱符号链接／重解析点检查。文件完整、下次读取通过；尚未证明首次失败的精确原因。 |
| P1／A1 | `ai/chatgpt_backend.py:205–214` 丢弃返回模型、响应编号及用量。离线重现接受了故意标为另一模型的回复，网络尝试为零。 | 返回结构化结果，保留请求／返回模型、提供方、完成状态及安全用量信息，明确处理有文档依据的别名。这证明核验缺口，不代表真实服务曾偷换模型。 |
| P1／A2 | `chatgpt_auth.py:239–268` 阻塞读流；`reflection_chat_screen.py:216–230,316–326` 在结束后仍保持忙碌控制。 | 结束后开始按钮可能继续不可用。增加请求取消及总等待上限，立即解除旧请求对界面的占用，阻止迟到回复影响新会话。本地取消不能保证服务端处理或用量立即停止。 |
| P1／A3 | `reflection_chat.py:490–501` 发送全部用户回答，但只带最近两个 AI 问题，没有逐条问答关联。 | 早先的“是”等短回答可能丢失含义。保留问答上下文，同时禁止 AI 问题成为用户证据。 |
| P1／P1 | `reflection_chat.py:81,167` 只允许返回双语问题；第 738 行 `save()` 保存会话画像及明文对话。 | 当前是自适应访谈，不是完整支持式聊天或持续个人模型。增加有效回应及可选问题，再实现独立、受用户控制的模型生命周期。旧报告纠正工具不等于新流程已完成这些能力。 |
| P2／A4 | 默认推荐按名称启发判断（`chatgpt_models.py:23`）；选择只存内存（`chatgpt_connect_screen.py:226–230`、`ai_settings.py:16–31`）。 | 按账号保存选择、刷新可用范围，如实标记未经实测的推荐，不能靠显示名升级。 |
| P2／A5 | `providers/registry.py:6–24` 有占位提供方，未知名称回到 Mock；主 ChatGPT 使用独立路径。流错误到界面时丢失有效分类。 | 建立一致的能力及错误契约；未知提供方明确失败；模拟模式须明确选择。没有证据表明该旧注册表替换了主 ChatGPT 回复。 |
| P2／R5 | 现有程序包已检查 181 个运行文件及 29 个模块，但一次性核验脚本放在被忽略的 `build/`，依赖约束未强制使用，`pip/cache` 可被误加入 Git。 | 保留核验能力并形成可重复流程，记录源码／依赖／构建输入，审阅暂存内容。目前不能称为可复现构建或已通过发布隐私审计。 |
| P2／D1 | `docs/30_conversation_first_product.md` 称比较未实现，当前代码及 docs31 已实现；`packaging/README.md` 与 CURRENT_STATUS 指向不同 EXE；旧未来任务仍要求创建最初界面。 | 统一文档权威来源，保护后归档旧里程碑并保留跳转，停止新增互相冲突的“当前”说明。 |

### 今日模型依据与 Pi 评估

应用使用官方 ChatGPT 套餐授权及公开 Responses 接口，不控制 ChatGPT 桌面，也不读取其中的聊天。10 月 1 日，通过应用自身服务正常续期已有授权一次、查询模型目录一次，返回 **GPT-6-Astra、GPT-5.6-Sol、GPT-5.6-Terra、GPT-5.6-Luna、GPT-5.5**，未返回 6.1。传输层禁止推理调用，安全回执为 `build/standards-audit-account-catalog.json`。列出模型不代表请求已完成或回答有用。官方说明区分账号目录与 Codex app-server 可能内置／缓存的目录：[模型与推理](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)、[app-server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)。

默认项从真实目录中按名称挑选较轻量模型，因此会出现 Luna 5.6，而非写死了旧版本。目前没有速度、质量或套餐消耗比较验证该推荐。在所检查的 AI／桌面源码中，没有名为“So AI”的提供方，暂不将口述名称当作新增依赖。语音识别仍独立于此连接；套餐共享路线不提供录音／转写 API（[预览限制](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)）。

Pi 检查固定在提交 `8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d`，包版本 **0.99.2**，技术栈为 TypeScript／Node，要求 Node >=22.19.0。这是源码快照依据，不是已核实的 npm 发布版本。建议在 Python 中借鉴提供方契约、凭据存储分离、流事件、取消及错误模式。其 OpenAI 提供方从静态目录起步，OAuth 选择也与本应用身份验证不同，不应整体替换。固定来源：[README](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/README.md)、[包配置](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/package.json)、[提供方](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/src/providers/openai.ts)、[OAuth](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/src/auth/oauth/openai-chatgpt.ts)。

### 军师 skill 来源及选择性适配

本地 `~/.codex/skills/goutoujunshi` 工作区干净，位于 7 月 21 日提交 `30d11e2894d1939c035ef9a32617f4ba365397c2`。配置来源重定向至 `shengjidaguai-china/goutoujunshi`，上游主分支为 9 月 15 日提交 `6db7354a4002dc7c448a9c87ffdad8132570c9d3`，**领先 31 次提交、落后零次**。本轮未更新。本地许可为 PolyForm Noncommercial，固定上游[许可](https://raw.githubusercontent.com/shengjidaguai-china/goutoujunshi/6db7354a4002dc7c448a9c87ffdad8132570c9d3/LICENSE)为 MIT，[更新记录](https://raw.githubusercontent.com/shengjidaguai-china/goutoujunshi/6db7354a4002dc7c448a9c87ffdad8132570c9d3/CHANGELOG.md)记录了变更。

保留共情、事实／推断／未知的区分、互惠、边界、可选下一步及有证据的纠正；排除强制人物评分、必填 MBTI、按性别设定主动性及默认追求假设。新增记忆／ChatLab 工具不因此获得读取用户资料的授权，SQLite 记忆也不是磁盘加密。先备份旧检出，暂存固定版本，在隔离合成环境验证后切换；应用集成另用经审阅的模块白名单，记录提交、许可及文件哈希。主反思聊天目前没有加载此 skill，只有旧教练路径读取六份可变本地文件（`api/routes_local_ai.py:1096–1235`）。

### Grilling：质疑及修订结果

| 质疑 | 修订及验收 |
|---|---|
| “再换个 EXE 名称就解决交付。” | 使用完整的固定根目录 EXE，暂存验证、安全处理占用、按原字节回滚，不加入联网更新或额外启动器组件。验证连续两次替换及失败恢复。 |
| “名称更新或登录成功就证明 AI 可用。” | 登录、目录、完整推理、语义验收分别记录；保留返回模型，拒绝不完整流，另外验证合成资料的真实聊天。 |
| “2116 项测试通过就代表本版通过。” | 今天全量测试有失败。保留依据，只修复已确认的并发问题，再在冻结源码上重跑定向及全量检查。 |
| “安装 Pi 或更新 skill 会自动修好产品。” | 保留 Python／PySide，只采用审阅过的模式及内容；明确实现军师回应及用户模型生命周期，不引入外部资料存储或整份提示词。 |
| “导出画像就是训练了个人 AI。” | 模型记录是可修订的观察／偏好／推断，包含来源、时间、不确定性及替代关系。可选记忆必须支持查看／纠正／暂停／撤销／导出／删除，云处理另行授权。 |
| “推送过或有备份目录就代表工作受保护。” | 在空位置恢复源码及 Git；只提交审阅过的安全内容并核对远端提交；备份和私人资料不发布。 |

阶段依赖为 **S0 保护及失败基线 → S1 固定发布 → S2 AI 连接可靠性 → S3 军师对话及受控模型 → S4 真实验收及源码交付**，具体工作、恢复及验收见所有者计划。README 负责启动；计划负责批准需求；进度表负责当前工作；状态负责当前依据；所有者审阅负责决定；架构及 ADR 负责设计；`docs/history/` 将保存被替代材料。

两项决定仍待确认：固定 EXE 放仓库根目录还是上一级（推荐仓库根目录）；本轮纳入受限主动授权的跨会话记忆，还是明确延期（推荐逐项批准且具完整管理能力的记忆）。本地 grilling skill 要求共同理解确认后再实施。已有授权覆盖调查及保护措施，结构改动等候设计确认。真实推理仍需如实确认额外积分设置，麦克风验收需可用设备。本提案不包含付费 API、私人资料导入、公开部署、发消息或恢复小时触发。

本轮只修改审计／状态／计划／审阅／进度文档开篇，并增加被忽略的本地证据辅助程序及回执。依据包括 `build/` 下 `standards-audit-pytest.log`、`standards-audit-pending-handle-race.log`、`standards-audit-model-provenance.py/.json` 及 `standards-audit-validation.json`。已有 Desktop 及 Desktop-Next 程序哈希未变；未提交、推送、生成新 EXE、安装 skill，也未宣称真实 AI 验收已完成。

---

## Historical material — not the current backlog / 历史材料——不作为当前待办

## Latest private-flow checkpoint — English (2026-09-30)

The desktop now connects explicit reflective chat, optional offline speech drafts,
separate portrait saving, selected-summary encrypted attachments, in-memory import
and consensual comparison. Provider and cryptographic behavior remain in shared
services. The model-facing contract and reviewed decoder schema now agree; invalid
outputs fail closed. Final gates: 2116 passed, nine Windows link-permission skips,
compilation/full lint pass, and Desktop source/native-dependency audit passed.
Actual local model comparisons remain unaccepted, and larger-model CUDA startup
failed. This is a verified implementation and package, not completed real AI
acceptance or public release.

The next required work is owner confirmation of disabled ChatGPT extra credits,
synthetic real-account chat/portrait/comparison acceptance, and physical microphone
plus spoken Chinese verification. Preserve the failed local-model receipts rather
than weakening validation. Hourly automation stays paused; the next cycle requires
the owner's instruction. Details: [current status](../CURRENT_STATUS.md),
[owner review](../OWNER_REVIEW.md), [exchange and voice](31_private_exchange_voice.md).

## 最新私下流程里程碑 — 中文版（2026-09-30）

桌面已连接明确开始的探索聊天、可选本地语音草稿、独立画像保存、自选摘要加密附件、
内存导入及双方许可下的比较。提供方与加密逻辑仍位于共享服务。模型看到的格式与经审阅
的解码格式现已一致，无效输出会安全拒绝。最终验收：2116 项通过、9 项因 Windows
链接权限跳过，编译／全范围静态检查通过，桌面源码与原生依赖核验通过。实际本地模型
比较仍未被接纳，较大模型的 CUDA 启动失败。本轮已核验实现与程序包，不代表完成真实
AI 验收或公开发布。

下一步需要所有者确认 ChatGPT 额外积分已关闭，用合成资料验收真实账号聊天／画像／
比较，并验证实体麦克风与中文口述。保留本地模型失败依据，不通过放松校验来制造成功。
小时自动任务保持暂停，下一周期需要所有者指令。详情见[当前状态](../CURRENT_STATUS.md)、
[所有者审阅](../OWNER_REVIEW.md)及[交换与语音](31_private_exchange_voice.md)。

The foundation audit below is historical / 下方基础审计作为历史记录保留。

## English

This document preserves the foundation audit snapshot below. Later shared-provider,
matching-boundary, isolated-state and packaging repairs are tracked in
`../CURRENT_STATUS.md` and `../PROGRESS_TRACKER.md`. The current provenance
milestone adds persistent desktop evidence review and version-bound correction
annotations; see `18_report_review_history.md`. A further bounded workflow withdraws
disputed claims into separately reviewed copies; see `19_reviewed_report_copies.md`.
Explicit version-bound selection now connects these copies to readers and interview
references; see `20_active_report_selection.md`. A separately confirmed user-proposed
reinterpretation can now edit one claim with unchanged quotations and mandatory
uncertainty; see `21_user_proposed_reinterpretation.md`. Legacy reports now have
exact-byte archives and literal review, and manual handoffs use current bundle
schemas; see `22_legacy_report_archives.md`. Complete legacy claims can now be
partially converted, separately selected or explicitly disabled for references;
see `23_legacy_report_conversions.md`. Unsupported content stays archived.
Explicit flat-profile layout migration now copies compatible original bytes into
`profile/`, with preview, confirmation and no overwrite; see `24_profile_layout_migration.md`.
Desktop navigation now isolates page sizing with retained scroll viewports, wraps
complete consent text and reveals focused controls; see `25_desktop_window_navigation.md`.
One disputed claim can now receive an explicitly reviewed local AI suggestion,
saved as a version 0.3 quote-limited, unverified copy with persistent AI attribution;
see `26_ai_assisted_claim_revision.md`. Complete current-format reports can now be
regenerated from explicitly pasted excerpts and saved corrections after local request
review, with exact per-source quotations, retained warnings and separate version 0.4
copies; see `27_full_report_regeneration.md`. Source authenticity and semantic support
are not verified. Arbitrary legacy/profile-content migration and encrypted recovery
remain unfinished.

The bounded local recovery milestone separates CUDA startup, generation-grammar
compatibility and report-quality failures. A tighter model-facing string limit
repairs the observed grammar rejection without narrowing stored-artifact validation.
The reusable single-call synthetic check preserves originals and selections; final
live outputs still fail localization. Next work reduces the model's bilingual
mapping burden while retaining exact request review and full validation. See
`28_local_model_recovery.md`; prompt tuning alone is not acceptance.

Full regeneration now uses strict per-field English/Chinese pairs and deterministic
projection into the unchanged canonical format. Two real local Gemma4 synthetic
samples passed the complete integration path; wording caveats remain. Old histories
and exact request review stay intact. See `29_paired_report_generation.md`. Fresh
report/interview generation retains its earlier contract and is the next AI-chain
integration target; mocked GUI checks remain distinct from actual provider runs.


### Scope and evidence

2026-09-28: inventory and targeted inspection of all subsystem families, followed
by the existing automated suite and new foundation regressions. No real vault
contents or credentials were read. Findings below distinguish executable evidence
from risks inferred from code. Historical progress entries are context, not fresh
validation of live providers or installed executables.

### Architecture map (current)

```text
run_desktop.py -> PySide6 MainWindow / screens
                 -> engine facades -> services -> models / safety / consent
                 -> ProfileStore -> plaintext profile/import/report files
                 -> desktop ai_backend -> Ollama / Anthropic / agent CLI

run_local_app.py -> loopback FastAPI + LocalBrowserBoundary -> browser UI
                 -> routes_local_ai (orchestration + storage + global backend)
                 -> ai/chat_backends -> Ollama / cloud APIs / agent CLI
                 -> plaintext vault (different document contracts)

run_rendezvous_node.py -> public-node FastAPI -> routes_matchmaking
                       -> RendezvousService -> in-memory registrations,
                          tokens, contacts, coarse buckets, fingerprints,
                          introductions and consent state

main.py -> optional risk/trust/journal/matchmaking API -> services
reports/ -> JSON Schema validation + canonical hash/integrity verification
providers/ -> structured-output registry/adapters (cloud entries placeholders)
browser_export/ -> optional user-assisted local export tools
matchmaking/beacon.py -> versioned manual exchange + checksum
```

### Preserve, repair, and contain

| Subsystem | Evidence / disposition |
| --- | --- |
| Risk, consent, trust ladder | Preserve. Engine modules wrap services intentionally; they are not automatically redundant. Existing safety/uncertainty tests pass. |
| Reports and schemas | Preserve validation/canonicalization. Hashes detect changes, not authorship. Package JSON resources; add installed-wheel checks next. |
| Export/import and browser helpers | Preserve parsers and bounded export guards. Optional Playwright workflow not exercised live. No hidden scraping added. |
| PySide6 GUI | Preserve. Actual launcher/event loop passed an isolated smoke test. Startup probes, navigation and document flows require visual/interaction review. |
| Browser client | Preserve as an existing experiment. Local HTTP boundary repaired; large HTML and large local routes still combine presentation/orchestration concerns. Do not declare it the replacement primary GUI. |
| Profile storage | Repair incrementally. Desktop profile, self-portrait, and browser self-model contracts differ. No encrypted repository or complete provenance/correction layer. Preserve legacy files when migrating. |
| Provider infrastructure | Preserve Protocols, registry, injected transports, CLI stdin/session regression fixes. Desktop and core chat transports duplicate logic and have differing behavior. The structured registry's placeholders coexist with working chat adapters. |
| Generic hybrid router | Not located by checkout filename/content inspection. Desktop autodetection is not a demonstrated generic privacy-aware router. Locate original artifact before building a replacement. |
| Matching, geo, beacon | Preserve coarse buckets, mutual contact gating, synthetic tests, and versioned beacon work. Keep experimental until mandatory adult eligibility, disclosure, limits and abuse controls are tested. |
| Packaging | Keep current scripts as experiments. Existing CI builds node binaries, not proof of a safe complete personal-client installer. No framework rewrite justified. |
| Evaluation | Existing synthetic suite covers scam-risk examples; it does not establish compatibility reasoning, traceability or hallucination resistance across providers. |

### Why iterations can feel unsatisfactory

These are evidence-backed engineering explanations, not a claim about the owner's
subjective experience:

| Category | Concrete evidence and effect |
| --- | --- |
| Architecture | Multiple provider paths, storage layouts, and entry points diverge. A fix in one client need not fix the other. `routes_local_ai.py` owns substantial business logic and mutable globals. |
| Code quality | Setup reused a broken virtual environment and ignored native command exit codes. Raw HTTP errors could echo sensitive data. Both repaired this cycle. |
| UX | README described API mode as a placeholder while chat adapters already make live calls; desktop and browser journeys differ. Feature status and privacy expectations were misleading. |
| Model/prompt | Existing tests document session bleed, long command-line failures and hollow output. Those fixes are preserved. Free-form parsing and data inside system context still weaken reliable contracts. |
| Incomplete implementation | Encrypted storage, provenance/correction, cloud minimization, adult eligibility and disclosure rules are not complete. More screens do not close those gaps. |
| Test foundation | Existing tests were valuable, but no normal push/PR test CI or global home isolation existed. New suite runs without reading personal vaults and covers startup and local browser boundaries. |

### Threat review and remaining release blockers

Foreign websites could access local browser routes through inherited wildcard
CORS. The new middleware rejects mismatched Origin/port, non-loopback Host and
cross-site/same-site fetch metadata before execution, including preflights. A
local non-browser process may still call the API; do not expose it publicly.

Untrusted profiles, imports and model replies remain data, never authority.
Existing arbitrary role dictionaries and system-context concatenation need a
typed request boundary. Schema parsing alone does not establish truthful evidence.
Cloud minimization must include names, contact channels, precise locations,
identifiers and financial information; pattern substitution alone cannot promise
complete redaction. CLI agents with vault access require equivalent disclosure
controls rather than an assumed exemption.

Server compromise can expose stored contact metadata and tokens; tokens in query
strings may appear in logs. Fake clients can claim arbitrary ages and submit large
or malformed content. Authentication, bounded requests, rate limits, opt-in
field disclosure, deletion and protocol negotiation remain necessary. No public
release is justified by the passing foundation suite.

### Prioritized roadmap and success criteria

| Priority | Small milestone | Success criteria |
| --- | --- | --- |
| P0 completed cycle | Isolated environment/tests; loopback browser boundary; safe HTTP errors; honest setup failures; documentation | Compile, 205 tests, core/test lint pass locally; no rewrite. Remote CI still unverified. |
| P0 next | Configuration/resource checks; app-owned service state; token-safe logs; dependency reproducibility | Fresh install contains schemas; separate app instances do not share private state; no credentials in logs; tested dependency constraints. |
| P1 next | Reuse generic router; shared typed requests and disclosure policy | Mocked transports prove local-only stays local, cloud receives only reviewed minimized data, and untrusted content cannot become system messages. |
| P1 | Versioned personal profile with fact/inference/hypothesis, evidence, confidence and timestamps; encrypted storage strategy | Reject unsupported output before saving; lossless legacy migration; inspect/correct an inference; round-trip/recovery tests. Choose key recovery before migrating private data. |
| P2 | Natural conversation and correction UX using core services | One coherent owner journey; correction survives restart; explanations distinguish evidence and uncertainty; no personality scores. |
| P3 | Ephemeral candidate analysis + owner feedback learning | Candidate identifiers discarded by default; structured alignment/conflicts/unknowns/questions; eight synthetic evaluation scenarios below pass. |
| P4 | Minimal language-neutral exchange schemas, consent and coarse discovery | Adult eligibility mandatory, fields default private, mutual-consent tests, bounded untrusted payloads, version rejection, deletion and network-error tests. |
| P5 | Installable distribution and onboarding | Clean-machine launch without Python knowledge; bundled resources; local mode without server; signed update design and explicit release review. |
| P6/P7 | Closed adult testing, then possible public network | Reliability/privacy review, abuse response and explicit human approval; never automatic deployment. |

Future matching evaluation cases: obvious alignment, hard mismatch, ambiguity,
conflicting preferences, missing data, sensitive input, injected profile text,
and contradictory owner history. Assess schema validity, evidence traceability,
unsupported-claim rejection, privacy, and consistency. Use fictional adults only.

## 中文版

下文保留基础审计时的状态快照。之后的共享提供方、匹配边界、独立状态及打包修复记录于
`../CURRENT_STATUS.md` 和 `../PROGRESS_TRACKER.md`。当前来源追踪里程碑增加了桌面端
持久证据复核和绑定版本的更正批注，详见 `18_report_review_history.md`。
进一步的限定流程可以撤回争议主张并保存独立复核副本，详见 `19_reviewed_report_copies.md`。
明确绑定版本的报告选择现将副本接入查看与访谈参考，详见 `20_active_report_selection.md`。
另行确认的用户重述现可在保留引文、强制不确定性标记的条件下改写一条主张，详见
`21_user_proposed_reinterpretation.md`。旧报告现可逐字节存档及原文复核，手动交接也已使用当前
报告结构，详见 `22_legacy_report_archives.md`。已有完整内容的旧主张现可部分转换，另行
选择或明确停用参考，不支持内容仍保留在存档中，详见 `23_legacy_report_conversions.md`。
扁平个人档案现可预览、确认后原样复制到 `profile/`，拒绝覆盖，详见
`24_profile_layout_migration.md`。桌面导航现以保留的滚动视口隔离页面尺寸，完整同意文字
可以换行，聚焦控件会显示在可视区域，详见 `25_desktop_window_navigation.md`。
一条争议主张现在可以通过明确审核获取本地 AI 建议，保存为 0.3 版本、仅依据已有引文且
未经核实的副本，并持续保留 AI 归属，详见 `26_ai_assisted_claim_revision.md`。
现在可以从明确粘贴的摘录和已保存更正重新生成完整当前格式报告，先复核本地请求，
逐来源检查精确引文、保留旧警示，并另存 0.4 版本副本，详见
`27_full_report_regeneration.md`。不核实来源真实或语义支持。任意旧格式/档案内容迁移及
加密恢复仍未完成。

有限范围的本地恢复里程碑将 CUDA 启动、生成语法兼容性和报告质量故障分开记录。
收紧模型生成字符串上限修复了已观察到的语法拒绝，不收紧已保存产物的校验范围。
可复用的单次合成检查保留原件及当前选择；最终真实输出仍未通过本地化校验。
下一步降低模型生成双语映射的负担，同时保留准确请求复核及完整校验。
详见 `28_local_model_recovery.md`；仅调整提示词不等于验收通过。

完整重新生成现使用逐字段严格中英对，并按确定规则转换为不变的规范格式。两份真实
本地 Gemma4 合成样例通过完整集成路径，措辞限制仍需复核。旧历史及准确请求审核保持
完整，详见 `29_paired_report_generation.md`。全新报告/访谈生成保留此前契约，是下一步
AI 链路集成目标；模拟界面检查继续与实际提供方运行分开记录。


### 范围与证据

2026-09-28：对全部子系统类别进行清单检查及重点审阅，然后运行现有测试和新增基础回归测试。
未读取真实档案库内容或凭据。下述结论区分实际执行证据与代码分析发现的风险。历史进度记录
仅作为背景，不能代表本轮重新验证了真实提供方或已安装可执行文件。

### 当前架构图

```text
run_desktop.py -> PySide6 MainWindow / screens
                 -> engine 外观层 -> services -> 模型 / 安全 / 同意检查
                 -> ProfileStore -> 明文档案、导入材料与报告
                 -> 桌面 ai_backend -> Ollama / Anthropic / 代理 CLI

run_local_app.py -> 回环 FastAPI + LocalBrowserBoundary -> 浏览器界面
                 -> routes_local_ai（编排、存储和全局后端状态）
                 -> ai/chat_backends -> Ollama / 云端 API / 代理 CLI
                 -> 明文档案库（使用不同文档契约）

run_rendezvous_node.py -> 公共节点 FastAPI -> routes_matchmaking
                       -> RendezvousService -> 内存中的注册、令牌、联系方式、
                          粗粒度区域、指纹、引荐和同意状态

main.py -> 可选风险 / 信任阶梯 / 日志 / 匹配 API -> services
reports/ -> JSON Schema 验证 + 规范化哈希与完整性检查
providers/ -> 结构化输出注册表与适配器（云端条目仍为占位）
browser_export/ -> 可选的用户辅助本地导出工具
matchmaking/beacon.py -> 带版本的手动交换与校验和
```

### 保留、修复与限制范围

| 子系统 | 证据与处理方向 |
| --- | --- |
| 风险、同意与信任阶梯 | 保留。engine 对 services 的封装是有意设计，不能直接视为重复代码。现有安全与不确定性测试通过。 |
| 报告与 Schema | 保留验证及规范化。哈希只能检测改动，不能证明作者身份。本轮声明 JSON 打包资源，下一步验证安装后的 wheel。 |
| 导入导出与浏览器辅助工具 | 保留解析器和有限导出防护。未实测可选 Playwright 流程，未新增隐蔽抓取。 |
| PySide6 界面 | 保留。真实启动器与事件循环已通过隔离测试；启动探测、导航及文档流程仍需视觉与交互检查。 |
| 浏览器客户端 | 保留现有实验。本轮修复本地 HTTP 边界；较大的 HTML 和本地路由仍混合界面与编排职责，不宣称其已取代主要桌面界面。 |
| 档案存储 | 渐进修复。桌面档案、自我画像与浏览器自我模型契约不同，缺少加密存储和完整来源/修正层。迁移应保留旧文件。 |
| 提供方基础设施 | 保留 Protocol、注册表、可注入传输，以及 CLI 标准输入和会话回归修复。桌面与核心聊天传输重复且行为不同；结构化注册表的占位项与实际聊天适配器并存。 |
| 通用混合路由器 | 本仓库文件名与内容检查未定位到。桌面自动检测不等于已经验证的通用隐私路由器。替代之前先定位原有实现。 |
| 匹配、地理区域与信标 | 保留粗粒度区域、双方同意后披露联系方式、合成测试及版本化信标。在成年资格、披露、限制与滥用防护通过测试前保持实验性质。 |
| 打包 | 保留当前实验脚本。已有 CI 构建节点程序，并不能证明完整个人客户端安装器安全可用，没有证据支持更换框架。 |
| 评估 | 现有合成集覆盖诈骗风险案例，尚不能证明跨提供方的兼容性推理、可追溯性或抗幻觉能力。 |

### 既往迭代可能不理想的原因

以下是基于证据的工程解释，不代表对所有者主观体验作出判断：

| 类别 | 具体证据与影响 |
| --- | --- |
| 架构 | 多套提供方路径、存储布局与入口分化，一处修复未必覆盖另一客户端。`routes_local_ai.py` 承担大量业务逻辑和可变全局状态。 |
| 代码质量 | 安装脚本复用损坏环境且忽略原生命令退出码；原始 HTTP 错误可能回显敏感信息。本轮已修复。 |
| 用户体验 | README 将 API 模式描述为占位，但聊天适配器已可真实调用；桌面与浏览器流程不同，功能状态和隐私预期容易误导。 |
| 模型与提示词 | 现有测试记录了会话串扰、命令行过长与空输出问题，相关修复已保留。自由格式解析及系统上下文中的数据仍削弱契约可靠性。 |
| 未完成实现 | 加密存储、来源/修正、云端最小化、成年资格与披露规则未完成，增加界面不能解决这些缺口。 |
| 测试基础 | 现有测试有价值，但此前缺少常规 push/PR 测试 CI 和全局主目录隔离。现已可在不读取私人档案库的情况下验证启动与本地浏览器边界。 |

### 威胁审阅与尚存发布障碍

本地浏览器接口此前继承通配符 CORS，外部网站可能访问这些接口。新中间件在执行前拒绝
不匹配的 Origin/端口、非回环 Host 及跨站/同站但不同源的请求元数据，包括预检请求。
本地非浏览器进程仍可调用 API，因此不能将其公开暴露。

不可信档案、导入内容和模型回复始终应是数据，而非权限来源。现有任意角色字典及系统上下文
拼接需要类型化请求边界。能够解析 Schema 不能证明证据真实。云端最小化应涵盖姓名、联系
方式、精确位置、身份标识和财务信息；仅靠模式替换不能保证完整脱敏。可访问档案库的 CLI
代理也必须受等效披露控制，不能假定它们例外。

服务器泄露可能暴露联系方式元数据与令牌；查询参数令牌可能进入日志。恶意客户端可任意
声明年龄或提交超大、异常内容。仍需认证、请求限额、频率限制、字段级自愿披露、删除和
协议协商。基础测试通过不构成公共发布依据。

### 优先路线图与验收标准

| 优先级 | 小里程碑 | 验收标准 |
| --- | --- | --- |
| P0 本轮完成 | 隔离环境/测试、本地浏览器边界、安全 HTTP 错误、可靠安装失败提示、文档 | 本地编译、205 项测试、核心/测试静态检查通过；未重写。远端 CI 尚待验证。 |
| P0 下一步 | 配置与资源检查、应用独立服务状态、令牌安全日志、依赖可复现性 | 全新安装含 Schema；不同应用实例不共享隐私状态；日志不含凭据；依赖约束经测试。 |
| P1 下一步 | 复用通用路由器、共享类型化请求与披露策略 | 模拟传输证明纯本地不出设备、云端仅接收审核后的最小数据、不可信内容不能成为系统消息。 |
| P1 | 版本化个人档案，包含事实/推断/假设、证据、置信度及时间戳；加密存储策略 | 保存前拒绝不支持的输出；无损迁移旧文件；能检查与修正推断；往返及恢复测试。迁移私密数据前确定密钥恢复方案。 |
| P2 | 由核心服务支持的自然对话与修正体验 | 一个连贯的使用流程；重启后修正保留；解释区分证据与不确定性；无人格评分。 |
| P3 | 临时候选人分析与所有者反馈学习 | 默认丢弃候选人标识；结构化输出一致点、冲突、未知项与问题；通过下列八类合成评估。 |
| P4 | 最小跨语言交换 Schema、同意与粗粒度发现 | 成年资格必填、字段默认私密、双方同意测试、不可信载荷限额、版本拒绝、删除与网络错误测试。 |
| P5 | 可安装发行版与引导 | 全新机器无需理解 Python 即可启动；资源完整；本地模式无需服务器；签名更新设计及明确发布审查。 |
| P6/P7 | 封闭成年测试，再考虑公共网络 | 可靠性与隐私审阅、滥用响应和明确人工批准；不得自动部署。 |

未来匹配评估包括：明显一致、硬约束冲突、模糊情况、偏好矛盾、信息缺失、敏感输入、档案
文本注入，以及所有者历史矛盾。检查 Schema 有效性、证据可追溯性、拒绝无依据结论、隐私
行为与一致性。仅使用虚构成年人。
