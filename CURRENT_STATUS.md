# Current handoff / 当前交接

## English — October 17 migration delivery (verification continued October 18 UTC)

**0.6.0 is implemented in this original repository and deployed as an owner-private
pilot. The complete two-account ChatGPT Work journey is not yet accepted.**
Use the [private Site](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site) and
the installed `slowmatch@slowmatch-local` plugin. The fixed 0.5.3 EXE remains unchanged.
The latest product authority is the October 17 request in [PLAN](PLAN_FOR_ONEPUCHMAN.md)
and [AGENTS](AGENTS.md), superseding GUI-first/offline-only assumptions.

| Module | File/runtime evidence | Reuse or change | Acceptance |
|---|---|---|---|
| Existing desktop/core | Python, PySide6, optional FastAPI; verified root EXE hash still matches 0.5.3 | Preserve recovery and reusable services; ChatGPT becomes the main conversation | Baseline 2,306 passed / 9 skipped; final regression below |
| Local data | Existing ReportReviewService guarded reads, locks, atomic writes and canonical JSON; RelationshipMemory selected-entry imports | New separate profile/draft/approval/private-assessment models reuse these primitives; old memory is not misrepresented as a full profile | Current-chat installed launcher saved revision 1, corrected to 2 and re-read from another process |
| Skills/plugin | Native installer enabled SlowMatch; a new native session actually loaded its Skill | Focused goutoujunshi method adaptation; new life-direction workflow; grilling excluded from end-user package | Discovery passes; independent restricted new-chat persistence remains blocked |
| Matching | Old peer coordinator could store private analysis and old matching used hidden attributes | Reuse requirements and safe patterns, replace hosted flow with permitted-summary-only Worker/D1 service | Local real D1 tests pass; deployed MCP is discoverable; native remote call blocked |
| Source/sync | Original origin remains `onepunchman26/Anti-Dating-App-Scam`; migration branch from `78ea4053e716701a3b501ce37f4d5095b2cc51c4` | `apps/matching_site/` is authoritative; allowlisted one-way mirror feeds the Sites hosting repository | No new product repo, no remote replacement, no private data in the mirror |

Implemented source locations: `plugins/slowmatch/`, `.agents/plugins/marketplace.json`,
`src/anti_dating_scam/{models,services}/work_profile.py`, `work_cli.py`,
`schemas/shareable_profile.schema.json`, `scripts/work_plugin_setup.py`,
`scripts/sites_source_snapshot.py`, and `apps/matching_site/`. The Python-generated
summary schema is identical to the hosted copy. No new AI provider or standalone chat
client was added. The existing provider adapters and fixed legacy binary are preserved.

Local full profile, immutable history, drafts, approvals, outbound summaries and private
assessments default to `%LOCALAPPDATA%/AI-SlowMatch/work`. This Windows packaged host
may resolve that under its private LocalCache. Runtime registration is separate at
`%LOCALAPPDATA%/AI-SlowMatch/work-runtime.json`. These are ordinary local plaintext
files; they are outside Git, OneDrive, plugin packages and website output. Synthetic
verification used a separate `AI-SlowMatch/current-chat-proof` directory. No real archive
was inspected, backed up, migrated or uploaded. Selected legacy memory import is additive
and preserves originals; recovery creates a newer revision rather than silently rolling
the head backward.

Only the approved summary is exportable: alias, adult age band, coarse city/areas,
relationship goal/accepted goals and age bands, controlled value/life-direction/
communication/interest/preference choices, participant visibility, discovery and version
metadata. Approval binds content digest, source revision, destination and audience.
The export reads only its independent receipt and content-free revision metadata, not
the private profile or assessment. It reports **approved_for_upload_not_sent** until
a genuine remote result is separately observed and recorded. The current synthetic
approval remains unuploaded; no publication receipt has been fabricated.

| Required acceptance | Result and evidence |
|---|---|
| 1. Installation/discovery | **Installed and discovered:** local native Codex plugin install plus actual Skill read. Hosted plugin provisioned/already installed; native `slowmatch_channel_check` discovered. **Remote invocation blocked** by `MCP tool call requires approval, but approval policy is never`. Broad ChatGPT Work distribution eligibility remains unverified. |
| 2. Local persistence | **Verified in this current chat across processes:** installed launcher read empty state, saved revision 1, corrected to revision 2, re-read 2, drafted/approved/exported summary and saved/re-read private assessment. **Restricted new session unresolved:** three bounded attempts returned `storage_unavailable`; Windows owner-ACL and packaged AppData redirection were investigated. Do not repeat blind attempts or claim that environment passed. |
| 3. Upload scope | **Local contract/export/storage checks pass:** synthetic private marker absent from outbound and candidate objects, extra/private fields rejected, Python/JS digest agreement. **Actual authenticated hosted summary request and stored object not exercised** because native call approval is blocked. |
| 4. Two real accounts | **NOT EXERCISED:** owner explicitly has no second account. Local synthetic identities are never counted as two accounts. |
| 5. Private explanation | **Current-chat synthetic local path passes:** analysis used own corrected claim plus peer's permitted summary, included unknowns and respectful questions, saved and re-read locally. No hosted private-report endpoint. **Two real participants' full path not exercised.** |
| 6. Authorization/malicious content | **Local logic tests pass:** owner-scoped D1, rejected self-declared IDs/private fields/prompt-injection labels, exact JSON MIME and Origin checks, bounded bodies and candidates. **Real cross-account permission enforcement not exercised.** Identity relies on supported Sites dispatch. |
| 7. Update/withdrawal | **Local real D1 tests pass:** stale writes fail, replay cannot resume a pause, deletion clears content, tombstone rejects an old summary even with refreshed server revision; rejoining needs a newly approved higher summary version. **Hosted lifecycle not exercised.** |
| 8. Failure/recovery | **Tests pass:** invalid JSON, interrupted/local failed writes, stale revisions, approval mismatch and storage failure do not report success. Network/expired-session UI explains unconfirmed operations. **Real expired-login/network recovery remains untested.** |
| 9. Original compatibility | Existing EXE hash unchanged: `9280e8b464d91b85249c6af26b9e5390e9a358dbe3e7ccbc3b8494d919fb2978`; old data untouched; unrelated `.vscode/` and `paper/` preserved. Final regression status below. |

Verification: compilation, Ruff for new Python, 43 focused Python checks (1 OS symlink
skip), 5 Node/D1 checks, TypeScript and application ESLint/build passed. An earlier full
run returned 2,341 passed / 10 skipped / 1 failure because the in-memory schema predated
a schema-file update during that run; the focused final contract check passes. Final
full regression passed: **2,349 passed, 10 skipped, zero failures** in 781.38 seconds.
The existing Starlette/httpx
deprecation warning is unrelated and preserved.

Sites project: `appgprj_6ad4306f79e88191bbbd502f495ec501`. The source helper pushes only
the allowlisted mirror and packages the same build; `source-map.json` records file hashes.
Production schema migrations are additive and published migrations stay immutable.
The Site stays owner-private; no external viewers were added. Current deployed source,
version and outcome are recorded in the [sanitized receipt](docs/evidence/2026-10-17-work-sites-migration.json).

Tomorrow's minimum actions (no passwords or manual token copying):

1. Set the app speed selector to **Standard** if it still shows Fast/1.5×; this setting
   was requested but no supported current-chat speed-control tool is available.
2. In the intended local ChatGPT Work chat, select SlowMatch and allow the normal
   platform prompt for its synthetic channel check. Then verify write → read, approved
   synthetic publication → reread → withdrawal through that user's native tools.
   The blocked test session's approval policy was not changed or bypassed.
3. Verify local read → correction → reread in that intended new chat with its normal
   local-execution permissions. Current-chat success does not erase the restricted
   session failure. Broader installation needs actual eligible account/UI evidence.
4. When a second independent account becomes available, add only that account to the
   private Site through normal sharing, then run the two-account cases above. This is
   deferred, not a requirement to create an account tonight.

Recovery: use the unchanged fixed EXE for its legacy functions. Keep the migration
branch and use a separate checkout of `78ea405` when old source is needed; do not reset
over unrelated work. New private state is separate and must not be copied into Git.
Necessary source synchronization is tracked in PROGRESS_TRACKER; hourly automation
remains paused. No purchase, public-audience expansion, contact or real-data publication.
Implementation commit `67b0853` was pushed normally to `origin/codex/chatgpt-sites-migration`.
Only the preserved unrelated `.vscode/` and `paper/` folders remain outside tracked work.

## 中文版 — 10 月 17 日迁移交付（验证延续至 UTC 10 月 18 日）

**0.6.0 已在原仓库实现并部署为仅所有者可访问的私有试运行版；完整双账户 ChatGPT Work
流程尚未验收通过。**入口为[私有网站](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)
及已安装的 `slowmatch@slowmatch-local` 插件。固定 0.5.3 EXE 未改变。
[PLAN](PLAN_FOR_ONEPUCHMAN.md) 与 [AGENTS](AGENTS.md) 已更新 10 月 17 日权威方向，
替代 GUI 优先／必须离线的旧假设。

| 模块 | 文件／运行证据 | 复用或改造决定 | 验收方式 |
|---|---|---|---|
| 原桌面／核心 | Python、PySide6、可选 FastAPI；根目录 EXE 哈希仍为已验证的 0.5.3 | 保留恢复与可复用服务，以 ChatGPT 为主要聊天入口 | 基线 2,306 项通过／9 项跳过；最终回归见下 |
| 本机数据 | 既有 ReportReviewService 受保护读写、锁、原子写与规范 JSON；RelationshipMemory 按项导入 | 新档案／草稿／批准／私人分析复用这些基础；不把旧短记忆冒充完整档案 | 当前聊天调用已安装启动器，保存版本 1、纠正为 2，换进程重读 |
| Skills／插件 | 原生安装器启用 SlowMatch；新的原生会话确实读取 Skill | 按需改编 goutoujunshi 方法，新写人生方向流程，终端用户包不含 grilling | 发现通过；独立受限新会话的持久化仍受阻 |
| 匹配 | 旧 peer coordinator 可保存私密分析，旧匹配使用隐藏属性 | 复用需求与安全模式，托管链路改为仅允许摘要的 Worker／D1 | 本地真实 D1 测试通过，远程工具可发现，实际调用受阻 |
| 源码／同步 | 原 origin 仍为 `onepunchman26/Anti-Dating-App-Scam`；从 `78ea4053e716701a3b501ce37f4d5095b2cc51c4` 建迁移分支 | `apps/matching_site/` 为权威，允许列表单向镜像送入 Sites 托管源码库 | 未另造产品仓库、未更换远端、镜像不含私人资料 |

实现位置为 `plugins/slowmatch/`、`.agents/plugins/marketplace.json`、
`src/anti_dating_scam/{models,services}/work_profile.py`、`work_cli.py`、
`schemas/shareable_profile.schema.json`、`scripts/work_plugin_setup.py`、
`scripts/sites_source_snapshot.py` 与 `apps/matching_site/`。Python 生成的摘要结构与网站副本
一致，未新增 AI 服务商或独立聊天客户端，既有适配器和固定旧程序保留。

完整档案、不可变历史、草稿、批准、出站摘要和私人分析默认位于
`%LOCALAPPDATA%/AI-SlowMatch/work`；本 Windows 打包宿主可能将其解析到自身 LocalCache。
运行配置另存 `%LOCALAPPDATA%/AI-SlowMatch/work-runtime.json`。这些是普通本地明文文件，
位于 Git、OneDrive、插件包和网站产物之外。合成验收使用独立的
`AI-SlowMatch/current-chat-proof` 目录。未检查、备份、迁移或上传任何真实旧档案。
选定旧记忆的导入是追加式并保留原件；恢复会创建更高修订号，不暗中把指针退回旧版本。

可导出的只有批准摘要：化名、成年年龄段、粗略城市／区域、关系目标／接受目标及年龄段、
受控价值观／人生方向／沟通／兴趣／偏好选项、参与者范围、匹配状态及版本信息。
批准绑定内容哈希、来源修订、目标与受众。导出只读取独立批准记录与不含正文的修订元数据，
不读取私人档案或报告。在真实远程结果另行观察并记录前，状态明确为
**approved_for_upload_not_sent（已批准导出，尚未发送）**。本轮合成批准仍未上传，未伪造发布记录。

| 必须验收项 | 结果与证据 |
|---|---|
| 1. 安装与发现 | **已安装、可发现：**原生 Codex 安装并实际读取本地 Skill；Sites 插件已创建／报告已安装，原生 `slowmatch_channel_check` 可发现。**远程调用受阻：**工具要求批准，但测试会话审批策略为 never。面向其他 ChatGPT Work 账号的分发资格尚未验证。 |
| 2. 本地持续性 | **当前聊天跨进程通过：**已安装启动器读空档案、保存版本 1、纠正为 2、重读 2，再草拟／批准／导出摘要及保存／重读私人分析。**受限新会话未解决：**三次有界尝试返回 `storage_unavailable`，已检查 Windows 所有者 ACL 与打包 AppData 重定向；不再盲目重试，也不声称其通过。 |
| 3. 上传范围 | **本地结构／导出／存储检查通过：**合成私密标记不进入出站或候选对象，拒绝额外／私人字段，Python／JS 哈希一致。**真实认证的托管摘要请求及存储对象尚未实测：**原生调用批准受阻。 |
| 4. 两个真实账户 | **尚未实测：**所有者明确暂时没有第二账户；不把本地合成身份算作真实双账户。 |
| 5. 私人解释 | **当前聊天合成本机链路通过：**使用本人纠正条目与对方允许摘要，保留未知及尊重对方的问题，保存后重读；服务端没有私人报告接口。**两位真实参与者完整路径尚未实测。** |
| 6. 越权与恶意内容 | **本地逻辑测试通过：**按所有者约束 D1、拒绝自报身份／私人字段／注入标签、严格 JSON MIME 与 Origin、限制正文和候选数量。**真实跨账户权限尚未实测。**身份依赖受支持的 Sites 入口验证。 |
| 7. 更新与撤回 | **本地真实 D1 测试通过：**旧写入冲突，旧重放不能恢复暂停，删除清空内容，即使刷新服务版本也不能重发旧摘要；重新加入须新批准更高摘要版本。**托管生命周期尚未实测。** |
| 8. 失败与恢复 | **测试通过：**非法 JSON、本机中断／写入失败、版本冲突、批准不符及存储失败不会报成功；网络／过期登录界面说明操作未确认。**真实登录过期／网络恢复尚未实测。** |
| 9. 原项目兼容 | EXE 哈希未变：`9280e8b464d91b85249c6af26b9e5390e9a358dbe3e7ccbc3b8494d919fb2978`；旧数据未动，保留无关 `.vscode/`、`paper/`。最终回归见下。 |

验证：编译、新 Python 的 Ruff、43 项定向 Python（1 项操作系统符号链接跳过）、5 项 Node／D1、
TypeScript、应用 ESLint 与构建通过。较早一次完整运行得到 2,341 项通过／10 项跳过／1 项失败，
原因是运行期间更新了结构文件而进程仍持有旧定义；最终定向结构检查已通过。
最终固定 Python 源码完整回归通过：**2,349 项通过、10 项跳过、零失败**，用时 781.38 秒。
既有一项 Starlette／httpx 弃用警告保留，与迁移无关。

Sites 项目：`appgprj_6ad4306f79e88191bbbd502f495ec501`。受支持的源码工具只推送允许列表镜像，
打包同一份构建；`source-map.json` 记录文件哈希。数据库采用追加迁移，已部署迁移不改写。
网站仍仅所有者可访问，未新增外部访客。实际部署源码、版本及结果见
[脱敏交付记录](docs/evidence/2026-10-17-work-sites-migration.json)。

明天最少操作（不需密码或手动复制令牌）：

1. 如 App 仍显示 Fast／1.5×，将速度选择器改为 **Standard**。已收到此要求，但没有可控制当前聊天
   速度的受支持工具，不能声称已经替你切换。
2. 在目标本机 ChatGPT Work 聊天中选择 SlowMatch，完成平台对合成通道检查的正常批准；再通过本人
   原生工具验证“写入→读取、批准合成摘要→发布→重读→撤回”。未修改或绕过受阻测试会话的审批策略。
3. 在目标新会话的正常本机执行权限下验证“读取→纠正→重读”。当前聊天成功不消除受限会话失败；
   更广泛安装还须实际账号资格与界面证据。
4. 以后有第二个独立账号时，再通过正常分享仅授权该账号访问私有站，并执行上述双账户验收。
   这项已延期，不要求今晚注册账号。

回退：既有功能继续用固定旧 EXE；保留迁移分支，需要旧源码时单独检出 `78ea405`，不能 reset
覆盖无关工作。新私人状态独立，不得复制进 Git。必要源码同步见 PROGRESS_TRACKER；小时自动化
保持暂停。本轮未购买、扩大公开受众、联系候选或发布真实资料。
实现提交 `67b0853` 已正常推送到 `origin/codex/chatgpt-sites-migration`；跟踪文件之外仅保留
原有无关的 `.vscode/` 与 `paper/` 文件夹。

---

The following is historical release evidence. / 以下为历史版本证据。

## English

October 16, 2026: **0.5.3 delivered to the fixed root `AI-SlowMatch.exe`.**
The old 0.5.1 app exited normally; atomic replacement succeeded. The root SHA-256
matches the verified candidate, and native About displays 0.5.3, source `daf91b78c998`
and expandable open-source credits. Build `327aa8c8aba44ae884dd75666a497037`, SHA-256
`9280e8b464d91b85249c6af26b9e5390e9a358dbe3e7ccbc3b8494d919fb2978`.
Frozen-source compile/lint, **2,305 tests (10 skips)**, package audit and isolated
startup passed; one upstream Starlette/httpx deprecation warning remains.
The actual EXE completed **four real synthetic Qt turns**, relevant follow-ups,
requested pause, End without inference, Back and reopening chat with Start enabled.
Native Computer Use observed a real displayed reply. The app-owned saved Codex login
was reused without new browser authorization. Requested model: `gpt-6-luna`; upstream
actual model and token usage remain unreported. The current Codex runtime
0.163.0-alpha.10.2 also passed loopback-only hostile-tool isolation (not real inference).

The compact setup keeps model, allowance confirmation and Enter AI Chat visible;
login is hidden once authorized. Unconfigured chat offers an enabled setup action.
Route/model survive navigation and language rebuild; billing consent does not persist
across processes or transfer between routes. Ten real synthetic turns were completed
across this repair's three runs: an initial two-turn run exposed a duplicated follow-up,
then corrected source and packaged four-turn runs passed. Failed evidence is retained;
exact repeated question suffixes now render once. No real private archive was read.
[Release receipt](docs/evidence/2026-10-16-chat-release.json) ·
[Packaged real chat](docs/evidence/2026-10-16-codex-packaged-gui.json) ·
[Source real chat](docs/evidence/2026-10-16-codex-source-gui-retry.json).

[Sources, licenses and thanks](docs/39_open_source_credits.md) are in README and About;
GitHub's bilingual description also thanks goutoujunshi, CodexMonitor, Pi, Chatbox and
OpenAI Codex. Hourly automation stays paused. Physical microphone/Chinese playback
remain separate owner checks. No spending, paid API key, email, recruitment or public
software deployment occurred. This is a local functional text-chat acceptance, not
psychological validation or verification of every available model.

Historical October 15, 2026 (UTC): **0.5.2 has passed verification; replacement awaits closing
the running 0.5.1 app.** The separate official local Codex connection
completed a real three-turn synthetic interview with relevant follow-ups, using the
owner-confirmed included allowance. The original SIWC route still returns HTTP 520.
The new adapter isolates its home/workspace/tools and persists only its own managed
login. Model catalogs are candidates; upstream reported model IDs remain unknown.
61 focused checks pass. Frozen-source compile/lint, **2,296 tests (10 skips)**, package
audit and isolated startup passed. The actual packaged EXE completed four real
synthetic Qt turns: model selection, displayed answers, relevant follow-ups, requested
pause, End without inference and Back all passed. Native Computer Use observed the
packaged conversation with a real reply. [Packaged receipt](docs/evidence/2026-10-15-codex-packaged-gui.json).
Build `52ee54e439524476859e85d98c69144c`, source `bdb1a44e8062`, SHA-256
`1d30faf1821a3a90c88e7020a2aa3c2f23a2a2a6660bf4c3f48b707c0d964f8a`.
Windows blocked replacement while the old app remained open; the old EXE is intact.
No process was forcibly closed. See [integration and evidence boundaries](docs/38_codex_chat_recovery.md).

Previous delivery, October 14, 2026: **0.5.1 at the fixed root `AI-SlowMatch.exe`.** Real account catalog
requests reproduced HTTP 520 after successful authorization; no real inference was
attempted in this repair. This is an account-authorized endpoint failure, not evidence
of a universal outage or an obsolete model name. The UI now exposes the status and a
manual Reload models action without repeating OAuth. It refuses unavailable/stale model
selections and clears the success badge if token renewal invalidates the connection.
94 focused synthetic checks pass, including failure → retry → model → chat in both
languages. Full frozen-source checks passed: **2,270 tests, 10 skips**, one upstream
Starlette/httpx warning, compilation, lint, embedded package audit and isolated startup.
The owner closed the old app before atomic replacement; the root hash matches the
verified candidate. Native packaged About shows 0.5.1 and source `f41e56152c2d`.
Build: `3cd7f492a310496ca5e1a51c8ad3de3d`; SHA-256:
`5475356223774595e087d82ee7acb1b3a005d091aeba8134bef4b8ed43699e41`.
The [release receipt](docs/evidence/2026-10-14-catalog-release.json) and
[live failure record](docs/evidence/2026-10-14-catalog-diagnosis.json) distinguish local
repair from still-blocked real chat. The dirty flag is from preserved unrelated folders.
See the [diagnosis and verification boundaries](docs/37_chatgpt_catalog_recovery.md).

Previous delivery, October 2, 2026: **S7, root `AI-SlowMatch.exe`, version 0.5.0.**
Hourly automation `ai-slowmatch` stays PAUSED; owner instructions start further work.
The [S6 handoff](docs/history/2026-10-02-before-video-batches/CURRENT_STATUS.md)
retains earlier release, invitation and voice evidence.

Home → **Saved videos & interests** supports bulk exports/lists/prepared notes,
selection by platform/collection/date, canonical deduplication, optional public-title
lookup, batch-scoped AI approval, checkpointed processing, pause/resume/manual retry,
separate interests/reflections, grouped editing/merging/adoption into existing memory,
source inspection and reversible imports. No second personality database was added.
The packaged conversation Skill is version 4. Start with the
[synthetic sample](examples/video_batch/mixed.json) and [bilingual guide](docs/36_saved_video_batches.md).

Full frozen-source release gates passed: **2,257 tests, 10 skips**, one upstream
Starlette/httpx deprecation warning; compilation, lint, embedded code/resources/native
dependencies and isolated EXE startup all passed. Native Computer Use verified the
populated source UI, separate draft categories, controls and Back, then packaged startup
and About (0.5.0 / cdfe34db1594). Build: `64f479a89311475e862617f865c7153a`;
SHA-256: `0f648929e97e3421efe8d1a3636b2197bcc55cc14ab79b9fde514940f91505aa`. The
[sanitized release record](docs/evidence/2026-10-02-video-batch-release.json) and local
`releases/current.json` identify the exact binary. The dirty flag reflects preserved
unrelated untracked folders. Older verified releases were retained for rollback.
The bilingual handoff, restore-verified source backup and GitHub source delivery are
complete. The isolated packaged inspection exited normally. The EXE/private data were
not uploaded; source is on `codex/standards-correction`. Await owner review, with no new scope.

**Evidence:** 88 focused cases pass, including connected English/Chinese Qt journeys,
failure/restart/late-reply handling, scope changes, duplicate evidence, grouped correction,
merge, surviving support and cascading deletion. Six real ChatGPT-plan calls used only
synthetic materials with extra credits disabled and no automatic retries: three item
calls and three synthesis attempts. The first claimed recurring interest from one item;
the second duplicated a theme. Both were rejected and retained as failures. The final
result contains three interests and one separate reflection draft with exact quotes
and tentative wording; memory adoption and undo passed. All six requested/reported
GPT-5.6-Luna IDs agreed. This small sample does not establish psychological validity.
[Initial receipt](docs/evidence/2026-10-02-video-batch-plan.json) ·
[Second attempt](docs/evidence/2026-10-02-video-batch-corrected.json) ·
[Successful synthesis](docs/evidence/2026-10-02-video-batch-final.json).

The synthetic counts are **4 unique imported, 1 full supplied-text, 2 partial,
1 skipped, 0 failed, 1 duplicate**. Final synthesis reused three validated item results.
“Full” describes supplied text, not watching or verifying an entire video. Public
YouTube example-title lookup passed; TikTok returned HTTPError. Bilibili and generic
sources need prepared input. No private account export or vault was read.
The 1,000-video bound, excerpt/synthesis limits and omitted-theme counts are disclosed.

Batch checkpoints and adopted memory are unencrypted local files, excluded from Git
and source backups. Only selected minimized excerpts and derived groups reach the
approved AI recipient. Repeated imports add no evidence weight; drafts do not silently
become beliefs. Undo removes batch support and dependent interpretations, not originals
or earlier disclosures. Source was backed up and restore-verified before edits.
Existing unrelated `.vscode/` and `paper/` are preserved and excluded.

Physical microphone/Chinese playback remain owner checks: previously zero microphones
and no Chinese system voice were exposed. The adult invitation node remains local-only;
managed HTTPS hosting, eligibility/identity assurance and operations policy are unresolved
external integrations. No spending, paid API, deployment, email, recruitment or recurring
task was added. See [owner review](OWNER_REVIEW.md).

## 中文版

2026 年 10 月 16 日：**0.5.3 已交付至固定根目录 `AI-SlowMatch.exe`。**旧版 0.5.1
正常退出，原子替换成功。根目录 SHA-256 与验证构建一致，原生关于页显示 0.5.3、
源码 `daf91b78c998`，并可展开开源来源。构建 `327aa8c8aba44ae884dd75666a497037`，
SHA-256：`9280e8b464d91b85249c6af26b9e5390e9a358dbe3e7ccbc3b8494d919fb2978`。
冻结源码编译／静态检查、**2,305 项测试（10 项跳过）**、打包审计及隔离启动通过；
保留一项上游 Starlette/httpx 弃用警告。实际 EXE 完成**四轮真实合成 Qt 访谈**，
包括相关追问、要求暂停、结束且不额外推理、返回和重新进入后可开始。
Computer Use 观察到实际显示的真实回复。本应用专属 Codex 登录直接复用，无需再次
浏览器授权。请求模型为 `gpt-6-luna`；上游实际模型和 token 用量仍未提供。
本机新 Codex 0.163.0-alpha.10.2 另通过仅回环模拟服务的恶意工具隔离检查，
该隔离检查不等于真实推理。

设置页将模型、套餐确认与进入聊天集中显示，授权后隐藏重复登录按钮。未配置的聊天
提供可用设置入口；导航和切换语言保留通道／模型，费用确认不跨进程保存或跨通道转移。
本轮三次测试共完成十轮真实合成推理：最初两轮发现追问重复，修正后源码与打包各四轮
通过。失败记录保留，完全相同的末尾追问只显示一次，未读取真实私人档案。
[发布记录](docs/evidence/2026-10-16-chat-release.json) ·
[打包真实聊天](docs/evidence/2026-10-16-codex-packaged-gui.json) ·
[源码真实聊天](docs/evidence/2026-10-16-codex-source-gui-retry.json)。

[来源、许可与致谢](docs/39_open_source_credits.md)已加入 README 和关于页，GitHub
双语简介也致谢狗头军师、CodexMonitor、Pi、Chatbox 与 OpenAI Codex。小时任务继续
暂停，实体麦克风／中文播放仍需单独人工验收。未消费、使用付费 API key、发送邮件、
招募或公开部署软件。这是本地文字聊天功能验收，不是心理学效度或全部模型的验证。

历史记录，2026 年 10 月 15 日（UTC）：**0.5.2 已通过验收；正在等待关闭运行中的 0.5.1 后替换。**
独立的官方本机 Codex 连接已用所有者确认的套餐额度完成三轮真实合成
访谈并作相关追问；原 SIWC 通道仍返回 HTTP 520。新适配器隔离目录、工作区及工具，
保存本应用自己的独立登录。模型列表是候选目录，上游返回模型 ID 仍未知。
61 项定向检查通过；冻结源码编译／静态检查、**2,296 项测试（10 项跳过）**、嵌入包
审计及隔离启动均通过。实际打包 EXE 完成四轮真实合成 Qt 访谈：模型选择、显示回答、
相关追问、要求暂停、结束且不额外推理及返回均通过。Computer Use 观察到打包界面中的
真实回复，见[打包验收记录](docs/evidence/2026-10-15-codex-packaged-gui.json)。
构建 `52ee54e439524476859e85d98c69144c`，源码 `bdb1a44e8062`，SHA-256
`1d30faf1821a3a90c88e7020a2aa3c2f23a2a2a6660bf4c3f48b707c0d964f8a`。
旧版仍在运行，Windows 阻止替换；旧 EXE 完好保留，未强制关闭程序。
详见[集成与证据边界](docs/38_codex_chat_recovery.md)。

上次交付，2026 年 10 月 14 日：**0.5.1 交付至根目录固定 `AI-SlowMatch.exe`。**真实账号在授权成功后读取模型列表时
复现 HTTP 520；本轮未尝试真实推理。这说明带账号授权的接口请求失败，并不能证明全网
故障或模型名称过旧。界面现已显示具体状态，并提供无需重复 OAuth 的“重新加载模型”。
模型失效或未选中时不会启用聊天；续期导致连接失效时会清除成功标识。
94 项定向合成测试通过，包括中英文“失败 → 重试 → 选模型 → 聊天”流程。冻结源码的
完整检查通过：**2,270 项测试、10 项跳过**，一项上游 Starlette/httpx 警告，编译、
静态检查、嵌入包审计及隔离启动均通过。所有者关闭旧版后完成原子替换，根目录文件
哈希与已验证构建一致；原生打包关于页显示 0.5.1，源码 `f41e56152c2d`。
构建：`3cd7f492a310496ca5e1a51c8ad3de3d`；SHA-256：
`5475356223774595e087d82ee7acb1b3a005d091aeba8134bef4b8ed43699e41`。
[发布记录](docs/evidence/2026-10-14-catalog-release.json)与
[真实失败记录](docs/evidence/2026-10-14-catalog-diagnosis.json)分别记录本地修复和仍受阻的
真实聊天；dirty 标记来自保留的无关文件夹。详见[诊断与验证边界](docs/37_chatgpt_catalog_recovery.md)。

上次交付为 2026 年 10 月 2 日：**S7，根目录 `AI-SlowMatch.exe`，版本 0.5.0。**`ai-slowmatch` 小时任务继续暂停，只按所有者指令
开始后续工作。[S6 交接](docs/history/2026-10-02-before-video-batches/CURRENT_STATUS.md)保留此前发布、邀请和语音证据。

主页 → **收藏视频与兴趣**支持整批导出／链接／已准备笔记，按平台／集合／日期筛选，规范化
去重，可选公开标题查询，整批 AI 范围批准，逐项进度保存，暂停／继续／手动重试，独立兴趣
与反思分组，分组编辑／合并／采纳到现有记忆，查看来源及撤销导入。没有另建人格数据库，
应用内对话 Skill 更新为版本 4。可从[合成样例](examples/video_batch/mixed.json)和
[完整双语指南](docs/36_saved_video_batches.md)开始。

冻结源码的完整发布检查通过：**2,257 项测试通过、10 项跳过**，一项上游 Starlette/httpx
弃用警告；编译、静态检查、嵌入代码／资源／原生依赖和隔离 EXE 启动均通过。Computer Use
验证了有实际结果的源码界面、独立草稿分类、操作按钮与返回，以及打包版启动和关于页
（0.5.0／cdfe34db1594）。构建：`64f479a89311475e862617f865c7153a`；
SHA-256：`0f648929e97e3421efe8d1a3636b2197bcc55cc14ab79b9fde514940f91505aa`。
[脱敏发布记录](docs/evidence/2026-10-02-video-batch-release.json)与本机 `releases/current.json`
对应确切二进制。未提交标记反映保留的无关未跟踪目录；已验证旧版继续保留供回滚。
双语交接、恢复验证过的源码备份及 GitHub 源码交付完成；隔离打包版检查正常退出。
没有上传 EXE 或私人数据，源码在 `codex/standards-correction`，现等待人工验收，不新增范围。

**验证依据：**88 项定向检查通过，包括完整中英文 Qt 流程、失败／重启／迟到回复、范围变化、
证据去重、分组纠正、合并、保留仍有效支持及联动删除。关闭额外积分后，仅用合成材料真实
调用 ChatGPT 套餐六次，无自动重试：三次条目分析、三次集合综合。第一次从单项推断反复
兴趣，第二次重复主题；均被拒绝并保留失败记录。最终得到三组兴趣、一份独立反思，具有
原文来源及暂定措辞，记忆采纳／撤销通过。六次请求／返回 GPT-5.6-Luna 均一致，少量样本
不能证明心理科学效度。[初次记录](docs/evidence/2026-10-02-video-batch-plan.json) ·
[第二次尝试](docs/evidence/2026-10-02-video-batch-corrected.json) ·
[成功综合](docs/evidence/2026-10-02-video-batch-final.json)。

合成计数为 **4 项不同导入、1 项完整处理所供文本、2 项部分处理、1 项跳过、0 项失败、
1 项重复**，最终综合复用三项验证过的分析。“完整”只指所供文本，不表示观看或核实完整
视频。YouTube 公开示例标题获取成功，TikTok 返回 HTTPError；Bilibili 和通用来源需要准备
好的输入。未读取私人账户导出或资料库。单批 1,000 项、片段／综合限制和遗漏主题均已披露。

批次进度及采纳记忆是未加密本地文件，从 Git 和源码备份排除。只有选定最小片段及衍生分组
发送到批准的 AI 接收方。重复导入不增加证据权重，草稿不会默认为信念；撤销移除本批支持
及依赖解释，不删除原文件或收回先前披露。修改前已备份源码并验证恢复，保留无关
`.vscode/` 和 `paper/`，不纳入交付。

实体麦克风／中文播放仍需所有者验收：此前检测到零个麦克风且无中文系统声音。成年人邀请
节点仍仅本机使用；受管理 HTTPS 托管、资格／身份核验和运营规则是待定外部整合。没有消费、
付费 API、公开部署、邮件、招募或新增周期任务，见[人工审阅](OWNER_REVIEW.md)。
