# AI-SlowMatch

## English — current direction, October 18, 2026

AI-SlowMatch uses **your own ChatGPT conversation** to understand relationships, friendships,
values and life direction. Your answers remain your own: no founder defaults, personality
scores, guarantees about someone’s honesty, or automatic messages. The owner-approved full
replacement requirements are recorded in [PLAN](PLAN_FOR_ONEPUCHMAN.md) and [AGENTS](AGENTS.md).

**0.7.0 expands the original project; complete two-account acceptance remains blocked.**
The original `onepunchman26/Anti-Dating-App-Scam` repository remains authoritative. The fixed
**0.5.3 `AI-SlowMatch.exe` is unchanged** and remains the legacy/recovery entry. This migration
reuses Python contracts, guarded storage, selected imports and the optional speech adapter;
ChatGPT replaces the standalone app as the primary conversation entry. No new inference
service or parallel product was created.

The [private Site](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site) and local
`slowmatch@slowmatch-local` plugin have different permissions. **Implemented, connected,
actually tested and blocked are recorded separately in [CURRENT_STATUS](CURRENT_STATUS.md).**
Native remote invocation previously hit the platform approval policy; no bypass was used.
The owner has no second independent account, so real two-account cases remain NOT EXERCISED.

| Where | What it does |
|---|---|
| `plugins/slowmatch/` | One progressive Skill for relationship support, self-understanding, direction, profile changes, private reflection and shared activities. |
| `src/anti_dating_scam/{models,services}/work_profile.py` | Correctable private profile, separate dating/friendship summaries, expiry-bound approvals and private candidate explanations. |
| `src/anti_dating_scam/{models,services}/relationship_support.py` | Evidence-linked observations, private reflections, local candidate filters, selected text/audio import, scoped consent, correction and deletion. |
| `src/anti_dating_scam/{models,services}/work_planning.py` | Minimal sharing receipts and a restricted generator that reads only supplied shared preferences and public place evidence. |
| `apps/matching_site/` | Worker/D1 service: per-mode participation, bilateral candidate filters, reminders, separate participant preferences, versioned plans, individual confirmations, withdrawal and optional minimal feedback. |

The everyday path is ChatGPT → SlowMatch → talk → review and approve a separate summary
for each chosen mode → publish → discuss candidates privately → voluntarily share activity
preferences → review two or three options → each person confirms → optional private reflection.
Friendship does not imply romantic intent. A profile update does not publish anything.
No response is unknown, not consent or rejection. A plan does not send an invitation outside
this Site, make a reservation, pay, share location or write a calendar event.

Windows private data defaults to `%LOCALAPPDATA%/AI-SlowMatch/work`, outside Git and OneDrive;
packaged hosts can redirect that path to their local application cache. Files are plaintext.
Full profiles/history, private assessments, relationship observations, raw text/audio and
transcripts stay in this local workflow. OpenAI can process information you choose to use
under your ChatGPT settings; local primary storage is **not** a promise of zero cloud retention.

Sites receives only separately approved, allowlisted objects: a mode-specific matching summary
(alias, adult age band, coarse area and selected public choices), practical activity preferences,
public-source plans and optional feedback choices. Friendship summaries exclude dating/family
goals. Preferences can include voluntary access/diet requirements but never their private
reasons. Consent binds the exact content, purpose, recipient, expiry and withdrawal state.
Server identity comes from Sites authentication. No raw chat, private risk narrative, recording,
transcript, private file path, full-profile vector or private report is accepted by a Site tool.
Copies already seen by other people and platform backups cannot be guaranteed recalled.

For personal help, describe what happened without obtaining the other person's permission.
Ask for a brief suggestion before or during a meeting; nothing records or contacts anyone as
a side effect. Save an observation only when wanted. Text and recollection work without audio.
The optional import accepts selected UTF-8 `.txt`/`.md`, or mono 16 kHz 16-bit WAV of 0.1–30 s.
There is **no native recording feature** in this Work plugin. The optional existing Vosk adapter
needs its installed language model; neither language model is ready on the current runtime.
A supplied/corrected transcript is labelled unverified, not counted as automatic transcription.
Retention is checked on each support operation; there is no background expiry promise. Deleting
managed local material does not delete the external original or the ChatGPT conversation.

On a prepared Windows checkout with Python 3.11+, dependencies and the supported Codex installer,
run `python scripts/work_plugin_setup.py install` once. Daily use needs no manually started
server or copied tokens. The local launcher uses `work-runtime.json` outside source to invoke
the existing core. `slowmatch-work schema` describes actual operations. The hosted Site plugin
must be connected through the account’s normal platform UI and approvals. Local Codex installation
does not prove distribution eligibility on arbitrary ChatGPT Work accounts.

Website publishing uses an allowlisted, one-way hosting source mirror; `apps/matching_site/`
stays authoritative. Published migrations are immutable. [Current evidence](CURRENT_STATUS.md)
contains validation and minimal deferred owner actions; [progress](PROGRESS_TRACKER.md) remains
bilingual. The existing hourly automation remains paused.

Thanks to the supplied Sites/Vinext starter, retained MIT build/CSS sources, Vosk and the
method references including goutoujunshi. Developer grilling is excluded. The Canadian DOJ
reference informed behavior/context distinctions, not diagnosis or legal conclusions.
[Credits, revisions, licenses and exact reuse](docs/39_open_source_credits.md).

## 中文版 — 当前方向，2026 年 10 月 18 日

AI-SlowMatch 使用**你自己的 ChatGPT 对话**理解关系、友谊、价值观与人生方向。每个人的答案
以本人为准，不套用创始人默认值、不打人格分、不保证他人诚实，也不自动发消息。所有者批准的
完整替代要求已记录在 [PLAN](PLAN_FOR_ONEPUCHMAN.md) 与 [AGENTS](AGENTS.md)。

**0.7.0 继续扩展原项目；完整双账户验收仍受外部条件阻挡。**原
`onepunchman26/Anti-Dating-App-Scam` 仓库继续作为源码权威。固定的
**0.5.3 `AI-SlowMatch.exe` 未改变**，保留旧功能和恢复入口。本次复用 Python 结构、受保护读写、
选定导入与可选语音适配器，以 ChatGPT 为主要对话入口；没有另造推理服务或平行产品。

[私有网站](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)与本机
`slowmatch@slowmatch-local` 插件的权限不同。**已实现、已连接、已实测和受阻分别记在
[CURRENT_STATUS](CURRENT_STATUS.md)**。原生远程调用此前被平台审批策略阻止，未绕过；
所有者暂时没有第二个独立账号，真实双账户场景明确“尚未实测”。

| 位置 | 用途 |
|---|---|
| `plugins/slowmatch/` | 单一按需 Skill，覆盖关系支持、自我理解、方向、档案修改、私人复盘与共同活动。 |
| `src/anti_dating_scam/{models,services}/work_profile.py` | 可纠正的私人档案、独立恋爱／交友摘要、带期限批准和私人候选解释。 |
| `src/anti_dating_scam/{models,services}/relationship_support.py` | 有证据关联的观察、私人复盘、本机候选筛选、选定文字／音频导入、分项授权、纠正与删除。 |
| `src/anti_dating_scam/{models,services}/work_planning.py` | 最小共享批准记录；受限生成器只读取传入的共享偏好和公开地点依据。 |
| `apps/matching_site/` | Worker／D1 服务：分模式参与、双向候选筛选、提醒、各人独立偏好、版本化方案、各自确认、退出与可选最少反馈。 |

日常路径：ChatGPT → SlowMatch → 聊天 → 分别审阅并批准所选模式的摘要 → 发布 → 私下讨论候选 →
自愿分享活动偏好 → 比较两三个方案 → 各自确认 → 可选私人复盘。交友不代表恋爱意向，档案更新
不会自动发布。无回应是未知，不代表同意或拒绝。计划不会向站外发送邀请、订位、付款、共享位置或写入日历。

Windows 私人资料默认存于 `%LOCALAPPDATA%/AI-SlowMatch/work`，与 Git、OneDrive 分离；
打包宿主可能重定向到本机应用缓存。文件目前为明文。完整档案／历史、私人解释、关系观察、原始
文字／音频和转写留在本机工作流。OpenAI 可按 ChatGPT 设置处理本人选择使用的信息；本机主存
**不等于零云端留存承诺**。

Sites 只接收另行批准且符合允许字段的对象：分模式匹配摘要（化名、成年年龄段、粗略地区和所选
公开选项）、实际活动偏好、附公开来源的方案及可选反馈选择。交友摘要不含择偶／家庭目标；安排
需求可自愿包括无障碍／饮食要求，但不包含私人原因。批准绑定具体内容、用途、接收者、期限与撤回
状态，身份由 Sites 登录验证。网站工具不接收原始聊天、私人风险叙述、录音、转写、私密路径、完整
档案向量或私人报告。无法保证收回对方已看过的内容或平台备份。

本人可直接描述经历并求助，无须先取得对方许可。见面前或中途可以请求简短建议，咨询不会顺带录音
或联系任何人；需要时再保存观察。不用音频也能通过文字和回忆复盘。可选导入接收指定 UTF-8
`.txt`／`.md`，或 0.1–30 秒、单声道 16 kHz／16-bit WAV。此 Work 插件**没有原生录音功能**。
复用的可选 Vosk 适配器需要安装相应语言模型，当前运行环境的中英文模型均未就绪。本人提供／纠正
的转写标记为未核验，不能算自动识别成功。每次支持操作检查保留期限，不承诺后台到期清理；删除
本机受管材料不会删除外部原文件或 ChatGPT 对话。

准备好 Windows 源码、Python 3.11+、依赖和受支持的 Codex 安装器后，运行一次
`python scripts/work_plugin_setup.py install`。日常不用手动启动服务器或复制令牌。本机启动器用
源码外的 `work-runtime.json` 调用已有核心；`slowmatch-work schema` 列出实际操作。托管网站插件
需通过账号正常的平台界面连接和批准；本机 Codex 安装不能证明所有 ChatGPT Work 账号均有分发资格。

网站通过允许列表生成单向托管源码镜像，权威仍是 `apps/matching_site/`；已发布迁移不可修改。
[当前依据](CURRENT_STATUS.md)记录验证与最少人工操作，[进度](PROGRESS_TRACKER.md)同步双语。
既有小时自动化继续暂停。

感谢 Sites／Vinext 模板、保留的 MIT 构建／CSS 源码、Vosk 与 goutoujunshi 等方法参考；开发用
压力测试 Skill 不进入终端产品。加拿大司法部资料用于行为／情境区分，不是诊断或法律结论。
[来源、版本、许可及确切复用范围](docs/39_open_source_credits.md)。

## Historical 0.5.3 desktop workflow — English

A Windows relationship copilot: start or end a conversation whenever you choose,
explore your needs and boundaries, and review a private, tentative self-reflection.
Optional adult discovery uses private stated priorities. There are no public personality scores or automatic messages.

Thanks to [goutoujunshi](https://github.com/powerycy/goutoujunshi) for coaching ideas,
[CodexMonitor](https://github.com/Dimillian/CodexMonitor) and
[Pi](https://github.com/earendil-works/pi) for integration design references,
[Chatbox](https://github.com/chatboxai/chatbox) for product-flow comparison, and
[OpenAI Codex](https://github.com/openai/codex) for the external app-server runtime.
[Sources, revisions, licenses and exact reuse scope](docs/39_open_source_credits.md)
are also available offline in About. Client code from these reference projects is not bundled.

**Open `AI-SlowMatch.exe` in this repository's root folder.** This fixed filename is
the current Desktop entry. Copies under `dist/` are older development artifacts;
archives under `releases/` are for recovery. See About for the version and build ID.

1. Choose **Connect ChatGPT**. The installed Codex connection is suggested on first
   setup; it reuses this app's own login when available. Select a model, confirm
   Codex extra credits/top-ups are off, then click **Enter AI Chat**. The default
   favors a lighter model (`gpt-6-luna` in the verified catalog). **Connection options
   & help** contains model reload and the alternative standard ChatGPT route.
   Each route uses its own allowance confirmation. The app remembers the route and
   model, never billing consent across restarts. A login badge alone is not a chat
   test. See the [connection and repair evidence](docs/39_open_source_credits.md).
2. Enter **AI Chat → Start**. Answer, ask for advice, correct, skip or change topics.
   Review what goes online before sending. **End** stops accepting pending replies immediately.
3. **Voice input** uses the selected microphone and a local English/Chinese speech
   model. Review the recognized draft and press Send yourself. Speech-model download
   is explicit and free; missing devices or models are shown instead of simulated speech.
   **Read latest reply** uses an installed local system voice; **Stop playback**, Send,
   Voice input, End and leaving the screen interrupt it. A Chinese system voice must
   be installed to read Chinese. Playback never switches to a paid cloud service.
4. After End, choose **Create my reflection**, review the original quotations and
   both languages, then separately choose Save. This is a low-confidence interpretation,
   not a diagnosis or verified personality model.
5. **My approved notes** starts empty and disabled. Enable it only if you want an
   evolving personal model. Chat can then suggest up to three changes: **Review proposed
   updates** shows the text, original quotes, context, alternatives and uncertainty.
   Nothing is saved until you approve that individual item. “No update” is valid.
   Distinguish your reports from AI hypotheses; correct, question, reject, export or
   delete stored items. Deletion/correction also removes dependent interpretations.
   Up to 20 short entries are retained; only relevant notes appear in the sending
   review. **Session only** ignores the saved model and disables new proposals.
   Approved memory provides background, never fresh evidence for a separate portrait.
6. **Introductions & invitations** adds adult introductions, local discovery and revocable comparison links.
   Follow the complete [peer workflow guide](docs/35_adult_peer_workflow.md). The built-in node runs
   on this computer only; no public hosting is configured. The private model never goes to the node.
7. **Share or compare reflections** is the earlier optional file workflow. It previews a minimal summary and saves a password-
   encrypted `.slowmatch` attachment. Send it yourself, with the password separately.
   Import both participants' voluntarily shared files, obtain both permissions, and
   review the selected summaries before an AI discussion of fit. No match score is produced.
8. **Saved videos & interests** imports a collection in one operation: a prepared export,
   URL list, or selected notes folder. Filter the preview, approve the batch's AI scope,
   and review separate interest groups and reflection drafts. Confirm, edit, merge or
   reject groups; only adopted wording enters enabled memory. Pause/resume, manual retry
   and Undo import are available. Start with the [synthetic sample](examples/video_batch/mixed.json)
   and read the [batch guide and supported sources](docs/36_saved_video_batches.md).

ChatGPT processing is online and does not read existing ChatGPT conversations. Local
saved chat/reflection/notes and video-batch files are **not encrypted**; sharing attachments and the new approved-snapshot coordinator are encrypted.
Deleting notes cannot retract exported or already transmitted copies. No paid API
fallback, automatic email, public deployment or hourly work is enabled.

[Current evidence](CURRENT_STATUS.md) · [Approved scope](PLAN_FOR_ONEPUCHMAN.md) ·
[Progress](PROGRESS_TRACKER.md) · [Owner checks](OWNER_REVIEW.md) ·
[Build and recovery](packaging/README.md) · [Architecture](docs/32_standards_correction.md)

Developers: Python 3.11+; the verified Windows build uses Python 3.12. Install project
desktop/dev dependencies with the Windows constraint file. `python run_desktop.py`
launches source; `./release.ps1 build` backs up, tests, builds and updates the fixed entry.

## 中文版 — 0.5.3 历史桌面流程

这是一款 Windows 恋爱军师：用户随时开始或结束聊天，探索自己的需要与边界，
再审阅私密、暂定的相处画像。成年人可按需启用发现，使用私密明确偏好排序，不设公开人格分数，不自动发消息。

感谢 [goutoujunshi／狗头军师](https://github.com/powerycy/goutoujunshi) 的军师理念、
[CodexMonitor](https://github.com/Dimillian/CodexMonitor) 与
[Pi](https://github.com/earendil-works/pi) 的集成设计参考、
[Chatbox](https://github.com/chatboxai/chatbox) 的产品流程参考，以及
[OpenAI Codex](https://github.com/openai/codex) 的外部 app-server 程序。
[来源、版本、许可与确切借鉴范围](docs/39_open_source_credits.md)也可在软件“关于”离线查看，
没有打包上述参考客户端的源码。

**打开本仓库根目录的 `AI-SlowMatch.exe`。** 固定文件名就是当前桌面入口。
`dist/` 中是较早的开发产物，`releases/` 中的归档用于恢复；“关于”页面显示版本和构建编号。

1. 选择**连接 ChatGPT**。首次设置建议已安装的 Codex 通道；存在本应用专属登录时
   可复用。选好模型，确认 Codex 额外积分／自动充值已关闭，再点击**进入 AI 聊天**。
   默认优先轻量模型（已验证目录中为 `gpt-6-luna`）。**连接选项与帮助**中可重新加载
   模型或改用标准 ChatGPT 通道；不同通道需要各自的套餐确认。应用记住通道与模型，
   不跨重启保存费用确认。登录成功标识不等于已验证聊天，见[连接修复与证据](docs/39_open_source_credits.md)。
2. 进入 **AI 聊天 → 开始**。可以回答、求建议、纠正、跳过或换话题；发送前审阅
   将要联网处理的内容。**结束**会立即停止接纳待处理回复。
3. **语音输入**使用所选麦克风及本地中／英文语音模型。核对识别草稿后，自行点击发送。
   下载语音模型需要主动选择且免费；缺少设备或模型时会明确提示，不用模拟语音冒充成功。
   **朗读最新回复**使用已安装的本机系统声音；**停止朗读**、发送、语音输入、结束或离开页面
   都会打断播放。中文朗读需要已安装中文系统声音，不会转用付费云端语音。
4. 结束后选择**生成我的相处画像**，核对原文引用和中英表达，再单独选择保存。
   画像是低置信度解读，不是诊断或已验证的人格模型。
5. **我批准的记忆**初始为空并关闭。如果希望逐渐建立个人模型，可以主动启用。聊天随后
   可提出最多三条更新，点击**审核建议更新**查看文字、原话、情境、其他解释及不确定性；
   每条都需要明确批准才保存，“无需更新”也是有效结果。区分自己的陈述和 AI 假设，可纠正、
   质疑、拒绝、导出或删除；纠正／删除也会移除依赖它的解释。最多保留 20 条简短条目，
   仅相关记忆出现在发送审核中。**仅本次会话**忽略已存模型并关闭新候选。
   已批准记忆只作背景，不能作为另行生成画像的新证据。
6. **介绍与邀请**新增成年人介绍、本机发现和可撤销比较链接，完整操作见[邀请流程指南](docs/35_adult_peer_workflow.md)。
   内置节点仅在当前电脑运行，尚未配置公开托管，私人模型不会发送到节点。
7. **分享或比对相处画像**是此前可选文件流程，会先预览最小摘要，再生成密码加密的 `.slowmatch` 附件。
   邮件由你自行发送，密码另行告知。导入双方自愿提供的文件、取得双方许可并审阅待发摘要后，
   可请 AI 讨论相处契合度，不生成人格或匹配分数。
8. **收藏视频与兴趣**一次导入整个集合：已准备的导出、链接列表或选定笔记文件夹。
   先筛选预览，批准整批 AI 范围，再分别审阅兴趣分组和反思草稿；可采纳、编辑、合并或拒绝。
   只有明确采纳的表述进入已启用记忆。支持暂停／继续、手动重试及撤销导入。
   可从[合成样例](examples/video_batch/mixed.json)开始，操作与平台限制见[批量指南](docs/36_saved_video_batches.md)。

ChatGPT 在线处理，但不会读取原有 ChatGPT 聊天记录。本地保存的对话、画像、记忆和视频批次
**未加密**，分享附件和新增批准快照协调库经过加密。删除记忆不能撤回已导出或发送的副本。
未启用付费 API 后备、自动邮件、公开部署或每小时任务。

[当前依据](CURRENT_STATUS.md) · [批准范围](PLAN_FOR_ONEPUCHMAN.md) ·
[进度](PROGRESS_TRACKER.md) · [人工检查](OWNER_REVIEW.md) ·
[构建与恢复](packaging/README.md) · [架构](docs/32_standards_correction.md)

开发环境要求 Python 3.11+，已验证的 Windows 构建使用 Python 3.12。按 Windows
依赖约束安装桌面及开发依赖。`python run_desktop.py` 启动源码版；`./release.ps1 build`
负责备份、测试、构建和更新固定入口。
