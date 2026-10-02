# AI-SlowMatch

## English

A Windows relationship copilot: start or end a conversation whenever you choose,
explore your needs and boundaries, and review a private, tentative self-reflection.
Optional adult discovery uses private stated priorities. There are no public personality scores or automatic messages.

**Open `AI-SlowMatch.exe` in this repository's root folder.** This fixed filename is
the current Desktop entry. Copies under `dist/` are older development artifacts;
archives under `releases/` are for recovery. See About for the version and build ID.

1. Choose **Connect ChatGPT**, authorize in your browser, choose an account-listed
   model and confirm that this app's extra credits are disabled in ChatGPT Manage usage.
   The app remembers the model choice, but never remembers or asserts billing consent.
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

## 中文版

这是一款 Windows 恋爱军师：用户随时开始或结束聊天，探索自己的需要与边界，
再审阅私密、暂定的相处画像。成年人可按需启用发现，使用私密明确偏好排序，不设公开人格分数，不自动发消息。

**打开本仓库根目录的 `AI-SlowMatch.exe`。** 固定文件名就是当前桌面入口。
`dist/` 中是较早的开发产物，`releases/` 中的归档用于恢复；“关于”页面显示版本和构建编号。

1. 选择**连接 ChatGPT**，在浏览器授权，从账号实际提供的模型中选择，并确认已在
   ChatGPT 用量管理中关闭此应用的额外积分。应用只记住模型选择，不保存或冒认费用确认。
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
