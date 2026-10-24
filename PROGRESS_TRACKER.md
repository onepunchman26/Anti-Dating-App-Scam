Onboarding layout correction / 首次设置布局修正 (2026-10-23)

- ✅ Implemented and locally exercised: three shortcuts moved to Friends & groups; ChatGPT availability → optional official download → pinned Codex installation instruction. Copy readback, language-state preservation, separate social destinations and mobile layout passed. Python 2,637 / 11 skipped; Node 52; TypeScript/build passed. Private Site publication pending.
- ✅ 已实现并本机实测：三个入口移至好友与群组；是否已有 ChatGPT → 按需官方下载 → 固定版本 Codex 安装指令。复制回读、语言切换保留步骤、不同社交跳转和手机布局通过。Python 2,637／11跳过，Node 52，TypeScript／构建通过。等待原私有网站发布。

Delivered voice checkpoint / 语音交付检查点 (2026-10-23)

- ✅ 0.8.6 published, public-download installed/launched and repeated with the same helper; owner-private Site deployment succeeded. Final package has 29 passing EXE checks; real English synthetic recognition and local playback completion passed. Physical mic, Chinese recognition, complete spoken turn and independent accounts remain NOT ACCEPTED. See CURRENT_STATUS and docs/VOICE_VALIDATION.md.
- ✅ 0.8.6已发布、公开下载安装／启动并复用同一助手；原私有网站部署成功。最终包29项EXE检查、真实英语合成识别及本机朗读完成通过。实体麦克风、中文识别、完整语音回合和独立账号仍未验收，详见CURRENT_STATUS及docs/VOICE_VALIDATION.md。

Earlier implementation checkpoint / 此前实施检查点

- ⏳ 0.8.6: local dictation, editable drafts, opt-in turn-based send/read, bounded recording and local-only playback implemented and connected. Real English synthetic audio passed through the original recognizer and authenticated loopback API. Browser UI/recognition readiness passed; file chooser is blocked by extension file access. Physical microphone, complete voice turn and independent accounts are not accepted. Packaging/installed validation in progress. A real interview failure from null optional question was diagnosed and corrected without relaxing evidence checks.
- ⏳ 0.8.6：已实现并接通本机听写、可编辑草稿、明确开启的逐轮发送／朗读、有时限录音及本机声音。真实英语合成音频通过原识别器及认证本机接口；浏览器界面／识别就绪通过，文件选择受扩展文件权限阻挡。实体麦克风、完整语音回合和独立账号尚未验收。正在打包及验证安装产物；已定位并修复空问题为null导致的真实访谈失败，证据校验保留。

Latest checkpoint / 最新检查点

- ⏳ October 22 voice iteration started: reuse the existing local speech service for explicit dictation and local reply reading; verify a turn-based spoken workflow separately from full-duplex voice. ChatGPT-plan audio/transcription is explicitly unsupported by the current official flow. Keep private audio out of Sites and never enable the microphone automatically.
- ⏳ 10月22日语音迭代已开始：复用现有本机语音服务，接入主动听写及本机回复朗读；逐轮语音流程与实时双向语音分别验收。官方当前套餐接入明确不支持音频／转写。私人音频不进入Sites，不自动打开麦克风。

- ✅ Continuity increment delivered October 22 as 0.8.5: original requirements mapped, existing support/reflection connected, real final EXE generation/save/correction/restart exercised, corrected public bootstrap launched, owner-private Site version 14 deployed. Remaining legacy-web and independent-account gaps are explicit; see CURRENT_STATUS.
- ✅ 核心连续性增量10月22日以0.8.5交付：整理原要求、接通原支持／复盘，最终EXE真实生成／保存／纠正／重启已测；修正后的公开安装器启动成功，私有网站第14版已部署。旧功能网页接入及独立账号缺口明确保留，详见CURRENT_STATUS。

- ✅ 0.8.4 usability repair delivered: original GitHub release, verified public-download install/reinstall/launch, desktop shortcut, local Chrome AI chat and private review, server-side city/age/interest filters and owner-private Site version 13. Independent B/C and fresh-account acceptance remain NOT TESTED; hosted-to-loopback is not accepted. See CURRENT_STATUS.
- ✅ 0.8.4易用性修复已交付：原GitHub发布、公开下载校验与安装／重装／启动、桌面快捷方式、本机Chrome真实AI聊天和私人分析、服务端城市／年龄／兴趣筛选及私有网站第13版。独立B／C和新账号验收仍未实测，托管页直连本机未通过。详见CURRENT_STATUS。

- ✅ Relationship-first interview 0.8.3 delivered on `codex/relationship-first-interview`, rollback `7b16cd7`: bounded short questions, private drafts, remembered corrections/skips and optional exploration. Four real synthetic AI requests, 29 EXE checks and public-download installation/registration passed. Site version12 remains owner-private. Python2,583 / 11 skipped; final interview25; bootstrap41 / 1 skipped; Site37 + timeout3. Hosted IAB connection attempted but not accepted; retryable timeout verified. Independent B/C, fresh-account and licensing gates remain open; see CURRENT_STATUS.
- ✅ 关系优先访谈0.8.3已交付，分支 `codex/relationship-first-interview`，回退 `7b16cd7`：有上限的短问题、私人草稿、修正／跳过记忆及可选探索。四次真实合成AI、29项EXE及公开下载安装／登记通过。网站第12版仍为所有者私有。Python2,583／11跳过，最终访谈25、安装器41／1跳过、网站37加超时3。托管IAB连接已尝试但未验收，可重试超时已验证；独立B／C、新账号及许可限制仍开放，详见CURRENT_STATUS。

- ✅ Friends/groups 0.8.2 delivered: Site version10, original GitHub prerelease, public download/repeat installation and plugin registration passed. Three synthetic browser identities confirmed the same plan; source/browser/EXE each completed real OpenAI generation. Python2,571 / 11 skipped, Site37, focused62, bootstrap41 / 1 skipped and29 EXE checks passed. Independent B/C and hosted HTTPS-to-loopback remain NOT EXERCISED; see CURRENT_STATUS.
- ✅ 好友群组0.8.2已交付：网站第10版、原GitHub预发布、公开下载／重复安装及插件登记通过。三个合成浏览器身份确认同一方案；源码／浏览器／EXE分别完成真实OpenAI生成。Python2,571／11跳过、网站37、针对性62、安装器41／1跳过及29项EXE检查通过。独立B／C及托管HTTPS到本机助手仍未实测，详见CURRENT_STATUS。

# Progress tracker / 进度追踪

Updated / 更新：2026-10-19。Agent-maintained; change both languages together / 代理维护，状态须同步更新双语。

## English

- ✅ Friends/groups supplement feasible implementation and delivery complete on `codex/friends-groups`, rollback `9e0876c`. Stable IDs, friend consent, private 2–8 person groups, shared conditions and revision-bound proposals reuse platform identity, local AI and guarded planning. Latest full conversation read; attachment body unavailable. Real B/C acceptance remains blocked by unavailable accounts, not replaced by synthetic evidence.

- ✅ Web onboarding feasible delivery: `codex/web-onboarding-local`, rollback `d6255d0`; original core reused, real source/browser/EXE inference and restart pass. Guided review, separate shared form and reciprocal cities implemented; 2,562 Python / 11 skipped, 31 Node, final focused 59, bootstrap 41 / 1 skipped. Site version 9 deployed, hosting source `1aacfbf`; v0.8.1 prerelease published from clean package source `98ae73a`, 148 files. 29 isolated EXE calls and public-download installation/official plugin registration pass. ⚠ Hosted HTTPS browser-to-loopback acceptance needs the owner's sign-in; independent B, fresh-account setup and general hybrid-distribution eligibility remain unverified. The new attachment body was unavailable; the complete latest conversation was read. See WEB_COMPANION_VALIDATION.

- ✅ UI supplement delivered: original repository checked at `2d21f43`; isolated branch `codex/sites-ui-language`. Deployed version 6 and real components audited. Whole-interface language selection, clearer navigation and responsive layouts implemented; both-language browser checks at 360/768/1440, state preservation and local service workflows passed. Python 2,549/11 skipped, Site 25 and localization 3 passed. Production build/package passed; same owner-private Site deployed as version 7, hosting source `4b3ef64`. Actual browser bilingual persistence/both-mode reads/plans/health and native read-only health passed. Source implementation `e4d6f06`; independent account B remains unexercised.

- ✅ R8 available distribution work: GitHub About/homepage/Topics and main updated; v0.8.0 prerelease published. Public-download bootstrap plus repeat installation/official registration pass; final package passes 29 isolated EXE calls including interruption/retry. Core baseline 2,491 passed / 10 skipped; Site 25; final distribution 52; bootstrap 41 / 1 skipped. Private Site version 6 confirmed. Current existing Codex conversation now passes installed setup-Skill reading, native authenticated health/both-mode reads and a bound local synthetic probe. ⚠ Independent clean desktop, fresh native ChatGPT invocation, account B and an actual released-version upgrade failure remain unverified; PS5.1 is policy-blocked. No impersonation or contact.

### Historical 0.7 implementation checkpoint

The current distribution status is R8 above; the following records preserve earlier evidence.

- ✅ R1–R2: adopted the complete owner-approved replacement requirements in the original repository. Reused 0.6 data/guarded I/O/CLI; added independent dating/friendship summaries and expiry without changing the fixed 0.5.3 EXE or real private data.
- ✅ R3–R4 implementation: mode-specific bilateral matching, exact visible Site reminder, private observations/reflection/filtering and scoped selected-material lifecycle. 0.7 local plugin installed, 13 files verified against source; actual separate-process workflow preserved correction and independent approvals. Seven synthetic semantic examples were authored/reviewed in the current conversation, not claimed as new-chat integration tests.
- ✅ R5–R6 executable scope: isolated shared-input generator, individual planning preferences, versioned proposals/confirmations/withdrawal and optional selected feedback. Two public venues actually checked; installed launcher generated/exported/withdrew a synthetic sourced plan. Local UI rendered both source cards and kept preview unuploaded. Selected text/audio correction/retention/deletion passed; actual speech transcription returned unavailable, not a success.
- ✅ R7 verification/private deployment: **2,444 Python passed / 10 skipped / zero failures**, 18 Node/local D1 tests, compile, Ruff, TypeScript, ESLint and production build passed. Same owner-private Site deployed as saved version 4 (0.7.0), source `4c5bb5e`; real signed-in hosted summary and plan-list reads passed. No production test users or hosted writes.
- ⛔ External acceptance: second independent account unavailable (NOT EXERCISED); native hosted MCP invocation remains approval-blocked; restricted new-chat storage and broad Work distribution unresolved. No native recorder; missing speech models prevent verified recognition. Real hosted write/lifecycle, cross-account and expired-login/network recovery remain untested. Current-chat Standard speed setting cannot be changed by an available tool.
- ✅ Final autonomous delivery: bilingual acceptance/handoff and sanitized 0.7 receipt complete. Implementation `d84de81` pushed normally and verified on `origin/codex/chatgpt-sites-migration`; unrelated work preserved. External acceptance above remains open. Required owner/environment actions are deferred in CURRENT_STATUS, with no questions tonight. Hourly automation remains paused.

### Historical 0.6 migration checkpoint

- ✅ M1 audit/protection: original repository/remote verified at `78ea405`, unrelated work preserved, `codex/chatgpt-sites-migration` created. Native Skill installation/discovery and current-chat local persistence proved with synthetic data. October 17 Work + Sites direction supersedes EXE-first assumptions.
- ✅ M2 local implementation: versioned profile, provenance/correction/history, selected legacy import, exact approved-summary export and private assessments implemented and tested. Current-chat launcher saved and re-read revision 2 plus a private synthetic assessment. No real private archive read or published.
- ✅ M3–M4 implementation/private deployment: Worker/D1 summary service, native MCP, bilateral filters, no-score reasons, bounded discovery, pause/delete and revoked-version protection implemented; private Site deployed. Local D1 tests and build/static checks pass.
- ⛔ M1/M3/M4 actual platform gates: restricted new-chat storage still fails; native remote tool discovered but call blocked by approval policy; real authenticated hosted publication and lifecycle unverified. Two-account acceptance NOT EXERCISED because no second account is available. No bypass or fabricated success.
- ✅ M5 autonomous delivery: bilingual docs/credits and acceptance record complete; final regression **2,349 passed / 10 skipped / zero failures**, plus Node/D1, compile, lint, typecheck and build passed. Implementation `67b0853` synchronized normally to `origin/codex/chatgpt-sites-migration`; preserved unrelated untracked work. External acceptance gates above remain open; owner actions deferred until tomorrow and existing automation stays paused.

- ✅ 0.5.3 implementation: compact connection handoff, recoverable chat setup, active-route preservation, exact duplicate-question display fix, current-runtime isolation and bilingual source credits. 176 focused checks (3 skips) and four real synthetic Qt turns passed. Old 0.5.1 exited normally.
- ✅ 0.5.3 delivery: 2,305 tests (10 skips), compile/lint, package/startup checks and four real packaged Qt turns passed. The fixed root EXE was atomically replaced and its hash/About verified. GitHub description and bilingual README/About credits updated; source handoff complete.

- ✅ ChatGPT connection fix: reproduced authenticated catalog HTTP 520; added safe diagnostics, manual catalog retry, placeholders and valid-selection gating. 94 focused synthetic checks and native source-window error/retry inspection passed.
- ✅ 0.5.1 verification: frozen-source compile/lint, 2,270 tests (10 skipped), package audit and isolated EXE startup passed.
- ✅ 0.5.1 replacement: owner closed the old app; the fixed root EXE was atomically updated and its SHA-256 matches the verified build. No forced termination.
- ✅ Live interview implementation: the direct SIWC endpoint still returns HTTP 520 after reauthorization. An isolated official Codex connection completed three real synthetic service turns and four real Qt turns, including relevant follow-ups, requested pause, End and Back. Earlier failures are retained. 61 focused checks and runtime tool isolation pass.
- ✅ 0.5.2 verification: frozen-source compile/lint, 2,296 tests (10 skips), embedded package audit and isolated startup passed. The packaged EXE completed four real synthetic Qt turns; native inspection observed a real displayed reply.
- ✅ 0.5.2 replacement superseded: its previously blocked candidate is historical; 0.5.3 is now the delivered root executable.

- ✅ S7 implementation: collection import/filter/deduplication, supplied-content analysis, bounded interest/reflection synthesis, grouped review and reversible existing-memory adoption. Official source capabilities recorded; 88 focused checks pass. Six real synthetic plan calls produced a final useful collection result; two failed syntheses are preserved.
- ✅ S7 release: fixed 0.5.0 EXE, 2,257 tests passed/10 skipped; compile, lint, package and isolated startup passed. Native completed-result/source and packaged About inspection passed; old releases retained.
- ✅ S7 handoff: bilingual owner checks, restore-verified source backup and GitHub delivery completed; packaged manual inspection exited normally. Hourly task remains paused for owner review.

- ✅ S6 local implementation: adult introductions, separate snapshots, persistent invitation permissions, reciprocal discovery/private ordering, local worker and integrated Qt/API/model flow. Real HTTP/Qt tests and three useful real model samples verified; first two empty introduction replies preserved as functional failures.
- ✅ S6 release: fixed 0.4.0 EXE; 2,228 tests passed, 10 skips; compile/lint/package/isolated node startup passed. Native packaged About verified. Restore-verified source backup exists; older releases retained.
- ✅ S6 handoff: bilingual acceptance record, verified source backup and GitHub source delivery completed; hourly task remains paused for owner review.
- ⬜ S6 external service: no deployed HTTPS coordinator, verified identity/age or email integration. See owner review; do not claim cross-device/public readiness.

- ✅ S5 implementation: runtime Skill v2, evidence-linked model candidates, relevant retrieval, explicit approvals, session-only mode, cascading correction/deletion, and interruptible local playback in the existing architecture.
- ✅ S5 release: 0.3.0 fixed EXE; 2,187 tests passed (10 skips); compile/lint/package/startup passed. Fourteen new real service calls accepted plus one direct diagnostic; one failed follow-up remains explicitly documented. Bilingual handoff, verified source backup and GitHub delivery completed.
- ⬜ S5 device acceptance: no microphone or Chinese system voice is exposed in this environment. English local recognition and playback states were checked; physical input, Chinese speech and audible quality remain manual checks.

- ✅ Owner approved the plan and confirmed extra credits disabled for synthetic plan-usage tests.
- ✅ S0: protected existing work and Git history; reproduced and fixed the Windows pending-directory rename race; focused regression checks passed.
- ✅ S1: one root Desktop EXE, unified version/About metadata, frozen-source build gates, external verified backups, recoverable atomic promotion, rollback and guarded retention.
- ✅ S2: model selection persistence, typed requested/reported receipts, safe error categories, independent cancellation with bounded readers, and real streaming-output compatibility implemented.
- ✅ S3: response plus optional question, linked recent context, reviewed skill fast-forward and pinned app policy, individually approved bounded notes with full lifecycle implemented.
- ✅ S4 autonomous work: 2,154 tests passed (10 skips); compile/lint/package/isolated startup passed; native GUI checks and twelve real semantic samples reviewed; bilingual documents consolidated and source synchronized to GitHub.
- ⬜ Owner acceptance: physical microphone capture, spoken Chinese, audible playback and subjective usefulness. These are separate from synthetic audio and model checks.

Hourly automation stays paused. No purchase, paid API key, real private archive, email delivery or public deployment was used. The [prior tracker](docs/history/2026-10-01-before-standards-correction/PROGRESS_TRACKER.md) is historical, not an extra backlog. Current evidence belongs in [CURRENT_STATUS](CURRENT_STATUS.md).

## 中文版

- ✅ 好友／群组补充可执行的实现与交付已完成：分支 `codex/friends-groups`，回退 `9e0876c`。稳定ID、好友确认、2–8人私人群组、共享条件和版本绑定方案复用平台身份、本机AI及计划授权边界。已读最新完整对话，附件正文不可用。真实B／C验收因账号不可用仍受阻，不以合成证据替代。

- ✅ 网页新手引导的可执行交付：`codex/web-onboarding-local`，回退 `d6255d0`；复用原核心，源码／浏览器／EXE 真实推理与重启通过。实现私人审阅、独立共享表单和双向城市条件；Python 2,562／11 跳过、Node 31、最终针对性 59、安装器 41／1 跳过。Site 第 9 版已部署，托管源码 `1aacfbf`；v0.8.1 预览已发布，包来自干净源码 `98ae73a`，148 个文件。29 项独立 EXE 调用、公开下载安装及官方插件登记通过。⚠ 托管 HTTPS 浏览器到本机助手需本人登录后验收；独立 B、全新账号设置及混合发行资格尚未验证。新附件正文不可用，已读取最新完整对话。详见 WEB_COMPANION_VALIDATION。

- ✅ UI 补充已交付：原仓库核对至 `2d21f43`，独立分支 `codex/sites-ui-language`；已审计部署第 6 版及真实组件。完整界面语言选择、清晰导航与响应式布局已实现；双语 360／768／1440 浏览器、状态保留和本机服务流程通过，Python 2,549 项通过／11 项跳过，Site 25 项与语言 3 项通过。生产构建／打包通过，同一所有者私有站已部署第 7 版，托管源码 `4b3ef64`；真实浏览器双语持久性／双模式读取／计划／自检及原生只读健康调用通过。原项目实现 `e4d6f06`，独立 B 账号仍尚未实测。

- ✅ R8 可执行分发工作：GitHub About／主页／Topics 与 main 已更新，v0.8.0 已预发布；公开下载引导及重复安装／官方注册通过，最终包通过 29 次隔离 EXE 调用，含中断重试。核心基线 2,491 项通过／10 项跳过，Site 25 项、最终分发专项 52 项、下载引导 41 项通过／1 项跳过，私有 Site 第 6 版已确认；当前已有 Codex 会话已通过安装的 setup Skill 读取、本人认证的原生健康／双模式读取及绑定本机合成探针。⚠ 独立干净桌面、新会话原生 ChatGPT 调用、B 账号及真实已发布版本升级失败仍未验证；PS5.1 被策略阻止。不冒充、不联系他人。

### 历史 0.7 实现检查点

当前分发状态见上方 R8；以下条目保留早期证据。

- ✅ R1–R2：在原仓库采用所有者批准的完整替代要求，复用 0.6 数据／受保护读写／CLI，增加独立恋爱／交友摘要与期限，固定 0.5.3 EXE 和真实私人数据不变。
- ✅ R3–R4 实现：分模式双向匹配、准确可见网站提醒、私人观察／复盘／筛选及限定材料生命周期。0.7 本机插件已安装，13 文件与源码核对一致，实际跨进程流程保留纠正及独立批准。七个合成语义样例在当前对话编写／审阅，不冒充新聊天集成测试。
- ✅ R5–R6 可执行范围：隔离共享输入生成器、各自安排偏好、版本化方案／确认／撤回及可选选定反馈。实际核对两个公开地点，安装启动器生成／导出／撤回合成有来源计划；本地界面呈现两张来源卡，预览未上传。选定文字／音频纠正／保留／删除通过，实际语音转写返回不可用，未计为成功。
- ✅ R7 验证／私有部署：**Python 2,444 通过／10 跳过／零失败**，18 项 Node／本地 D1、编译、Ruff、TypeScript、ESLint、生产构建通过。同一所有者私有站部署为保存版本 4（0.7.0），源码 `4c5bb5e`；真实登录托管摘要及计划列表读取通过，未植入生产测试用户或托管写入。
- ⛔ 外部验收：没有第二独立账号（尚未实测）；原生托管 MCP 调用仍受审批阻止，受限新聊天存储／广泛 Work 分发未解决。无原生录音器，缺语音模型导致无法验证识别。真实托管写入／生命周期、跨账户及登录过期／断网恢复未实测；当前没有工具更改本聊天 Standard 速度设置。
- ✅ 本轮自主交付：双语验收／交接及 0.7 脱敏回执完成，实现 `d84de81` 已正常推送并在 `origin/codex/chatgpt-sites-migration` 核实，保留无关工作。上方外部验收仍未完成；必要本人／环境操作列于 CURRENT_STATUS 留待明天，今晚不提问，小时自动化继续暂停。

### 0.6 迁移历史检查点

- ✅ M1 审计／保护：核实原仓库／远端与 `78ea405` 回退点，保留无关工作，建立 `codex/chatgpt-sites-migration`。原生 Skill 安装／发现及当前聊天本机持久化已用合成资料证明；10 月 17 日 Work + Sites 方向替代 EXE 优先假设。
- ✅ M2 本机实现：带版本档案、来源／纠正／历史、选定旧记忆导入、具体批准摘要导出与私人分析均已实现并测试。当前聊天启动器保存后重读版本 2 与合成私人分析，未读取或发布真实私人档案。
- ✅ M3–M4 实现／私有部署：Worker／D1 摘要服务、原生 MCP、双向条件、无评分解释、有限发现、暂停／删除及撤回版本保护已实现，私有站已部署；本地 D1 测试与构建／静态检查通过。
- ⛔ M1／M3／M4 实际平台关卡：受限新会话存储仍失败；原生远程工具可发现但审批策略阻止调用；真实认证托管发布与生命周期尚未验证。没有第二账户，双账户验收明确“尚未实测”，未绕过或伪造成功。
- ✅ M5 自主交付：双语文档／致谢及验收记录已完成；最终回归 **2,349 项通过／10 项跳过／零失败**，另有 Node／D1、编译、静态、类型检查与构建通过。实现提交 `67b0853` 已正常同步到 `origin/codex/chatgpt-sites-migration`，保留无关未跟踪工作。上方外部验收仍未完成；用户操作留到明天，既有自动化继续暂停。

- ✅ 0.5.3 实现：集中连接步骤、可用聊天设置入口、保持已选通道、去除完全相同追问的重复显示、新版运行程序隔离及双语来源致谢。176 项定向检查（3 项跳过）和四轮真实合成 Qt 访谈通过；旧版 0.5.1 正常退出。
- ✅ 0.5.3 交付：2,305 项测试（10 项跳过）、编译／静态、打包／启动及四轮真实打包 Qt 访谈通过。固定根目录 EXE 已原子替换并核对哈希／关于页；GitHub 简介及双语 README／关于致谢已更新，源码交接完成。

- ✅ ChatGPT 连接修复：复现带授权的模型接口 HTTP 520，增加安全诊断、手动重载、占位提示及有效模型选择检查。94 项定向合成测试及原生源码窗口的错误／重试检查通过。
- ✅ 0.5.1 验证：冻结源码编译／静态检查、2,270 项测试（10 项跳过）、打包审计及隔离 EXE 启动均通过。
- ✅ 0.5.1 替换：所有者关闭旧版后，固定根目录 EXE 已原子更新，SHA-256 与验证构建一致；未强行终止程序。
- ✅ 真实访谈实现：标准 SIWC 接口重新授权后仍返回 HTTP 520。隔离的官方 Codex 连接完成三轮真实合成服务测试及四轮真实 Qt 测试，包括相关追问、要求暂停、结束与返回；保留早期失败。61 项定向检查及实际运行程序的工具隔离检查通过。
- ✅ 0.5.2 验证：冻结源码编译／静态、2,296 项测试（10 项跳过）、嵌入包审计及隔离启动通过。打包 EXE 完成四轮真实合成 Qt 访谈，原生检查观察到实际回复。
- ✅ 0.5.2 替换已由新版完成：此前受阻候选保留为历史，根目录现已交付 0.5.3。

- ✅ S7 实现：集合导入／筛选／去重、所供正文分析、有限兴趣／反思综合、分组审阅与可撤销的现有记忆采纳。已记录官方平台能力，88 项定向检查通过；六次真实合成套餐调用最终得到可用结果，保留两次综合失败。
- ✅ S7 发布：固定 0.5.0 EXE，2,257 项通过／10 项跳过；编译、静态、打包及隔离启动通过。实际结果源码界面和打包关于页检查通过，旧版本保留。
- ✅ S7 交接：双语人工检查、恢复验证过的源码备份及 GitHub 交付完成，打包版人工检查正常退出。小时任务继续暂停，交给所有者验收。

- ✅ S6 本机实现：成年人介绍、独立快照、持久化邀请权限、双向发现／私密排序、本机工作进程与 Qt／API／模型整合。真实 HTTP／Qt 流程和三个可用真实模型样本已验证；最初两次空白介绍作为功能失败保留。
- ✅ S6 发布：固定 0.4.0 EXE；2,228 项通过、10 项跳过；编译／静态／打包／隔离节点启动通过，实际打包关于页已验证。源码备份恢复通过，旧版本保留。
- ✅ S6 交接：双语验收记录、已验证源码备份和 GitHub 源码交付完成；小时任务继续暂停，等待所有者审阅。
- ⬜ S6 外部服务：尚未部署 HTTPS 协调节点、身份／年龄核验或邮件整合，见人工审阅；不可宣称跨设备／公开服务已就绪。

- ✅ S5 实现：在现有架构加入运行时 Skill v2、带证据的个人模型候选、相关检索、明确批准、仅本次会话、联动纠正／删除及可中断本机朗读。
- ✅ S5 发布：固定 EXE 更新到 0.3.0；2,187 项测试通过（10 项跳过），编译／静态／打包／启动通过。新增 14 次真实服务调用接纳及一次直接诊断，另一次后续失败已明确记录。双语交接、已验证源码备份及 GitHub 交付完成。
- ⬜ S5 设备验收：当前环境没有麦克风或中文系统声音；英文离线识别及朗读状态已检查，实体输入、中文语音及可听质量仍需人工。

- ✅ 所有者已批准计划，并确认关闭额外积分，可用套餐内额度测试合成资料。
- ✅ S0：保护现有工作及 Git 历史，复现并修复 Windows 暂存目录改名并发问题；定向回归检查通过。
- ✅ S1：根目录单一桌面 EXE、统一版本／关于页、冻结源码构建检查、外部已验证备份、可恢复的原子替换、回滚及有保护的保留策略。
- ✅ S2：记住模型选择、类型化请求／返回记录、安全错误分类、有限后台读取及独立取消、真实流式正文兼容均已实现。
- ✅ S3：回应加可选问题、关联近期上下文、审阅后的 skill 快进更新及固定应用策略、逐项批准的有限记忆及完整生命周期均已实现。
- ✅ S4 自主工作：2,154 项测试通过（10 项跳过），编译／静态／打包／隔离启动检查通过；已审阅原生界面检查及十二次真实语义样本，整理双语文档并同步源码到 GitHub。
- ⬜ 人工验收：实体麦克风录音、中文口述、可听朗读及主观实用性；这些与合成音频、模型检查分别验收。

小时任务保持暂停。本轮未购买服务、使用付费 API key、读取真实私人档案、发送邮件或公开部署。
[旧进度表](docs/history/2026-10-01-before-standards-correction/PROGRESS_TRACKER.md)仅为历史，不另作待办。
当前证据以 [CURRENT_STATUS](CURRENT_STATUS.md) 为准。
