# AI-SlowMatch

## English

A Windows relationship copilot: start or end a conversation whenever you choose,
explore your needs and boundaries, and review a private, tentative self-reflection.
There is no public ranking, personality score, partner feed or automatic messaging.

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
4. After End, choose **Create my reflection**, review the original quotations and
   both languages, then separately choose Save. This is a low-confidence interpretation,
   not a diagnosis or verified personality model.
5. **My approved notes** starts empty. Add or correct up to 20 short notes explicitly;
   enable reuse only if wanted. You can pause/revoke, export or delete them. Notes
   appear in the sending review and are never portrait evidence.
6. **Share or compare reflections** previews a minimal summary and saves a password-
   encrypted `.slowmatch` attachment. Send it yourself, with the password separately.
   Import both participants' voluntarily shared files, obtain both permissions, and
   review the selected summaries before an AI discussion of fit. No match score is produced.

ChatGPT processing is online and does not read existing ChatGPT conversations. Local
saved chat/reflection/notes files are **not encrypted**; only sharing attachments are.
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
再审阅私密、暂定的相处画像。不提供公开排名、人格分数、对象推荐流或自动发消息。

**打开本仓库根目录的 `AI-SlowMatch.exe`。** 固定文件名就是当前桌面入口。
`dist/` 中是较早的开发产物，`releases/` 中的归档用于恢复；“关于”页面显示版本和构建编号。

1. 选择**连接 ChatGPT**，在浏览器授权，从账号实际提供的模型中选择，并确认已在
   ChatGPT 用量管理中关闭此应用的额外积分。应用只记住模型选择，不保存或冒认费用确认。
2. 进入 **AI 聊天 → 开始**。可以回答、求建议、纠正、跳过或换话题；发送前审阅
   将要联网处理的内容。**结束**会立即停止接纳待处理回复。
3. **语音输入**使用所选麦克风及本地中／英文语音模型。核对识别草稿后，自行点击发送。
   下载语音模型需要主动选择且免费；缺少设备或模型时会明确提示，不用模拟语音冒充成功。
4. 结束后选择**生成我的相处画像**，核对原文引用和中英表达，再单独选择保存。
   画像是低置信度解读，不是诊断或已验证的人格模型。
5. **我批准的记忆**初始为空。最多逐项新增或纠正 20 条简短记忆，按需启用复用，
   可暂停／撤销、导出或删除。发送前会展示这些条目，记忆不能作为新画像的证据。
6. **分享或比对相处画像**会先预览最小摘要，再生成密码加密的 `.slowmatch` 附件。
   邮件由你自行发送，密码另行告知。导入双方自愿提供的文件、取得双方许可并审阅待发摘要后，
   可请 AI 讨论相处契合度，不生成人格或匹配分数。

ChatGPT 在线处理，但不会读取原有 ChatGPT 聊天记录。本地保存的对话、画像和记忆
**未加密**，只有分享附件经过加密。删除记忆不能撤回已导出或发送的副本。
未启用付费 API 后备、自动邮件、公开部署或每小时任务。

[当前依据](CURRENT_STATUS.md) · [批准范围](PLAN_FOR_ONEPUCHMAN.md) ·
[进度](PROGRESS_TRACKER.md) · [人工检查](OWNER_REVIEW.md) ·
[构建与恢复](packaging/README.md) · [架构](docs/32_standards_correction.md)

开发环境要求 Python 3.11+，已验证的 Windows 构建使用 Python 3.12。按 Windows
依赖约束安装桌面及开发依赖。`python run_desktop.py` 启动源码版；`./release.ps1 build`
负责备份、测试、构建和更新固定入口。
