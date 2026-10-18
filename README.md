# AI-SlowMatch

## English — current direction, October 17, 2026

AI-SlowMatch is moving the existing relationship copilot into **your own ChatGPT
desktop workflow**. Talk about relationships, communication, values and life
direction; maintain a correctable local profile; separately approve a small matching
summary for Sites; discuss candidates privately in your own ChatGPT conversation.
Your answers define your profile. There are no founder-default values, public
personality scores, automatic messages, or guarantees about another person.

The original `Anti-Dating-App-Scam` repository remains the product and source
authority. The October 17 requirements replace the older GUI-first and offline-only
assumptions. Existing Python services and guarded storage are reused. The verified
**0.5.3 `AI-SlowMatch.exe` remains the recovery/legacy entry**; the **0.6.0 source
migration is not a new EXE build**. The historical desktop workflow below remains
available for its existing functions.

The intended daily path is **ChatGPT → AI-SlowMatch → chat → review and approve a
summary when ready → publish → inspect candidates → discuss privately**. This is
being implemented, not a claim that the whole path has passed acceptance. Native
Codex discovery of the installed `slowmatch` Skill has been observed. The
[private Sites pilot](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site) has a
successful deployment of the summary UI, authenticated MCP service, D1 storage and
reciprocal matching code; this is not complete-product acceptance. Current-chat local
tools saved, corrected and re-read a synthetic profile and private assessment.
Sites provisioned its MCP plugin; native discovery succeeded, but invocation was
blocked by the test session's approval policy. A separate restricted new-chat local
storage probe also remains blocked. **Two-account acceptance is not exercised: no second account is
available.** See [current evidence](CURRENT_STATUS.md) for the latest verified results.

| Component | Source and purpose |
|---|---|
| Unified workflow | `plugins/slowmatch/`: focused Skills, references and plugin packaging; use the bundled instructions instead of pasting several long prompts. |
| Local contracts | `src/anti_dating_scam/models/work_profile.py`: separate private profile, summary draft, approved publication record and private assessment. |
| Local operations | `src/anti_dating_scam/services/work_profile.py` and `src/anti_dating_scam/work_cli.py`: guarded local I/O; `python -m anti_dating_scam.work_cli --help` lists implemented commands in an installed source environment. |
| Matching service | `apps/matching_site/`: Sites-supported Worker source for authentication, permitted summaries, visibility and reciprocal filters; delivery status is tracked separately. |

Full profiles and private assessments default to `%LOCALAPPDATA%/AI-SlowMatch/work`
on Windows, outside the source repository and OneDrive. The runtime resolves the
actual local application-data location; packaged Windows hosts may redirect it.
Local state is plaintext and separated into `profile/`, `drafts/`, `publications/`,
`assessments/` and `outbound/`. No real legacy archive has been migrated in this task.
Migration must select old input explicitly and preserve its original bytes.

OpenAI may process the task-relevant personal information you choose to use in
ChatGPT under your service settings. **Sites receives only the approved summary**:
alias, adult age band, selected city/areas, relationship goal, accepted goals and age
bands, selected value/life-direction/communication/interest tokens, preferences,
participant visibility, discoverability and version metadata. It receives no raw
chat, source quotes, detailed private history, private assessment or full-profile
embedding. City/area filters do not claim kilometre accuracy. A draft is not consent;
approval records bind the exact summary version. A local approval is not proof of
successful remote publication.

Installation is a separate step from creating a ZIP. On this machine initialization
and native Codex installation have completed. For a prepared Windows checkout with
Python 3.11+, the project dependencies and the supported `codex` plugin installer,
run `python scripts/work_plugin_setup.py install` once from the repository. This
registers the existing core and installs `slowmatch@slowmatch-local`; no local web
server is needed for daily use. Open a local chat, select SlowMatch and ask it to
read the profile before saving a correction. This Codex installer does not prove
arbitrary ChatGPT Work accounts can install the local package. The hosted
`AI-SlowMatch · 慢慢相识` plugin must also be connected under your own account through
the platform's normal plugin connection and approval UI. Another participant must use their own account and supported
installation/connection path; an owner's private plugin does not prove general
availability. Daily use must not require copying tokens or starting several services.

Thanks also to the supplied OpenAI Sites starter and shadcn contributors. The Sites
build integration and vendored CSS are actual bundled source with retained MIT
notices; this differs from the method-only references below. The focused plugin
adapts goutoujunshi methods, excludes developer-only grilling, and includes an
original life-direction workflow because no separate installed planning Skill was
found. Exact sources, revisions and reuse scopes are in the credits register.

[Approved migration plan](PLAN_FOR_ONEPUCHMAN.md) · [Progress](PROGRESS_TRACKER.md) ·
[Current evidence and recovery](CURRENT_STATUS.md) · [Sources and credits](docs/39_open_source_credits.md)

## 中文版 — 当前方向，2026 年 10 月 17 日

AI-SlowMatch 正在把现有恋爱军师迁入**你自己的 ChatGPT 桌面工作流**。通过聊天探索关系、
沟通、价值观与人生方向，持续维护可纠正的本机档案；另行批准少量匹配摘要交给 Sites，
再在自己的 ChatGPT 对话中私下讨论候选。档案答案以本人为准，不套用创始人的默认价值观，
不设公开人格分数，不自动发消息，也不保证他人的人品或关系安全。

原 `Anti-Dating-App-Scam` 仓库继续作为产品和源码权威。10 月 17 日要求替代旧有“GUI
优先”和“必须离线”的假设，复用已有 Python 服务与受保护读写工具。已验证的
**0.5.3 `AI-SlowMatch.exe` 保留为恢复／旧功能入口**；**0.6.0 是本次源码迁移，并不表示
已经重建 EXE**。下方历史桌面流程仍说明旧程序的既有功能。

目标日常路径是 **ChatGPT → AI-SlowMatch → 聊天 → 准备好后预览并批准摘要 → 发布 →
查看候选 → 私下讨论**。这条路径正在实现，不能据此声称整体验收通过。已观察到原生 Codex
发现并加载所安装的 `slowmatch` Skill。[私密 Sites 试运行站点](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)
已成功部署摘要界面、带认证的 MCP 服务、D1 存储与双向匹配代码，但不表示完整产品验收通过。
当前聊天中的本机工具已保存、纠正并重读合成档案与私人分析。Sites 已创建 MCP 插件，原生工具
可被发现，但测试会话的审批策略阻止了调用；独立受限新会话的本机存储探针也仍受阻。
**双账号验收未实测：没有第二账号。**
最新验证结果以[当前依据](CURRENT_STATUS.md)为准。

| 组件 | 源码与用途 |
|---|---|
| 统一工作流 | `plugins/slowmatch/`：按需加载的 Skills、参考与插件打包；使用随包流程，不把多份长提示词直接拼接。 |
| 本机结构 | `src/anti_dating_scam/models/work_profile.py`：分开的完整私人档案、摘要草稿、批准发布记录和私人匹配分析。 |
| 本机操作 | `src/anti_dating_scam/services/work_profile.py` 与 `src/anti_dating_scam/work_cli.py`：受保护的本地读写；安装源码环境后运行 `python -m anti_dating_scam.work_cli --help` 查看实际命令。 |
| 匹配服务 | `apps/matching_site/`：Sites 支持的 Worker 源码，处理身份、允许摘要、可见性与双向条件；交付状态单独记录。 |

Windows 上的完整档案和私人报告默认存入 `%LOCALAPPDATA%/AI-SlowMatch/work`，与源码仓库及
OneDrive 分离。运行时会解析实际本机应用数据目录，Windows 打包宿主可能重定向该位置。
本地状态目前为明文，分别放入 `profile/`、`drafts/`、`publications/`、`assessments/` 与
`outbound/`。本任务未迁移真实旧档案；迁移必须明确选择旧输入并保留原始文件。

你选择在 ChatGPT 中使用的相关个人信息，可按你的服务设置交给 OpenAI 分析。
**Sites 只接收已批准摘要**：化名、成年年龄段、自选城市／区域、关系目标、接受的目标与年龄段、
选定的价值观／人生方向／沟通／兴趣选项、偏好、参与者可见范围、发现状态和版本元数据。
不会收到原始对话、来源引文、详细私人经历、私人分析或完整档案向量。城市／区域筛选不声称
精确公里距离。草稿存在不等于获准发布；批准记录绑定具体摘要版本，本地批准也不证明远程发布成功。

安装与生成 ZIP 是不同步骤。这台电脑已完成初始化与原生 Codex 安装。其他 Windows 源码环境须有
Python 3.11+、本项目依赖与受支持的 `codex` 插件安装器；在仓库运行一次
`python scripts/work_plugin_setup.py install`，即可注册原核心并安装 `slowmatch@slowmatch-local`。
日常不需要启动本机网站服务。新开支持本机执行的聊天、选择 SlowMatch，先请它读取档案，再保存纠正。
此 Codex 安装器不证明任意 ChatGPT Work 账号都能安装本机包。托管的 `AI-SlowMatch · 慢慢相识`
插件仍须用本人账号，通过平台正常插件连接与审批界面接入。其他参与者必须使用自己的账号和受支持的安装／连接路径；
所有者拿到私人插件不证明它已经向所有人开放。日常使用不应要求复制令牌或手动启动多个服务。

同时感谢 OpenAI Sites 所供模板和 shadcn 贡献者。Sites 构建集成与附带 CSS 是实际打包的源码，
保留 MIT 许可，与下方仅借鉴方法的参考不同。插件改编 goutoujunshi 方法，不包含仅供开发审查的
grilling；未找到独立已安装规划 Skill，因此人生方向流程由本项目新写。确切来源、版本和使用范围
记录在致谢登记中。

[已批准迁移计划](PLAN_FOR_ONEPUCHMAN.md) · [进度](PROGRESS_TRACKER.md) ·
[当前依据与恢复](CURRENT_STATUS.md) · [来源与致谢](docs/39_open_source_credits.md)

---

The following is the preserved 0.5.3 desktop workflow, not the new plugin's acceptance
record. / 以下保留 0.5.3 桌面使用流程，不是新插件的验收记录。

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
