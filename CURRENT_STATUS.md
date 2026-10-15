# Current handoff / 当前交接

## English

October 15, 2026 (UTC): **0.5.2 real-chat recovery is in verification; the fixed
root EXE is still 0.5.1 until promotion.** The separate official local Codex connection
completed a real three-turn synthetic interview with relevant follow-ups, using the
owner-confirmed included allowance. The original SIWC route still returns HTTP 520.
The new adapter isolates its home/workspace/tools and persists only its own managed
login. Model catalogs are candidates; upstream reported model IDs remain unknown.
61 focused checks pass. Full frozen-source gates and packaged real Qt acceptance
remain pending. See [integration and evidence boundaries](docs/38_codex_chat_recovery.md).

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

2026 年 10 月 15 日（UTC）：**0.5.2 真实聊天修复正在验收；正式替换前，根目录 EXE
仍为 0.5.1。**独立的官方本机 Codex 连接已用所有者确认的套餐额度完成三轮真实合成
访谈并作相关追问；原 SIWC 通道仍返回 HTTP 520。新适配器隔离目录、工作区及工具，
保存本应用自己的独立登录。模型列表是候选目录，上游返回模型 ID 仍未知。
61 项定向检查通过，冻结源码全量检查和打包版真实 Qt 验收尚未完成。
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
