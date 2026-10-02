# Historical snapshot / 历史快照

English: Superseded on October 2, 2026; current scope is in the root plan.

中文版：2026 年 10 月 2 日起被替代；当前范围以根目录计划为准。

# Start here / 从这里开始

## Current private-loop Desktop (2026-09-30) — English

Open **AI-SlowMatch-Desktop-Next.exe**. The earlier Desktop executable remains beside
it for recovery. This is a local portable app; no Python installation is needed.
Choose your language, read the consent page and select a local folder. An empty
folder is enough. Long pages scroll, and Tab reveals the focused button.

1. **Connect ChatGPT.** The connected account gets a green animated success badge.
   Its actual model list loads without running inference. The suggested lighter
   default in the observed account was **GPT-5.6-Luna**; you can choose another
   available model. This is a name-based suggestion, not a report-quality guarantee.
   Open ChatGPT usage settings, disable extra-credit use for this app, then truthfully
   confirm that setting here. The app cannot check the remote switch for you.
   Choose **Use ChatGPT for AI Chat** to enter chat. This uses online ChatGPT through
   your authorized plan and cannot read your old ChatGPT conversations.
2. **AI Chat.** Press **Start**, answer one question at a time, skip or change topic
   freely, and press **End** whenever desired. Each online request shows the answers
   to be sent for your review. End discards late answers; it cannot retract a request
   already sent. No duration or market setup is required.
3. **Voice input.** During a conversation, choose **Voice input**, select English
   or Simplified Chinese, and download that language's free offline model once
   (about 40–42 MB). Recording starts only when you press **Start recording**. Press
   **Stop and transcribe**, edit the recognized words, and choose **Use this text**.
   This adds text to your answer draft; press **Send** separately. Audio stays in
   memory on this computer and is not saved or sent to ChatGPT. If no microphone is
   detected or access fails, the dialog says so. This development machine detected
   no microphone; real English recognition used synthetic speech, while a physical
   recording and spoken Chinese still need your device check.
4. **Create my reflection.** After End, generate the reflection, review the wording,
   original quotations and unknowns, then separately **Save this reflection**.
   All interpretations remain tentative. Saved chat history is an ordinary
   unencrypted local copy; the later attachment does not encrypt that history.
5. **Share or compare reflections.** Choose one saved reflection and review exactly
   what its shared summary contains. Export a new `.slowmatch` attachment with a
   password or passphrase of 12–256 characters. It contains bilingual tentative
   narratives and limitations, without the raw conversation, original quotations
   or account credentials. Existing destinations are not replaced. Attach the file
   to an email to your chosen recipient; send the password through a separate channel.
   The app does not send email or upload the file.
6. **Import and discuss.** Select your own file or saved reflection and the other
   person's encrypted file, enter the passwords, and inspect both summaries. Confirm
   permission for each person before comparison. Local decryption is automatic only
   after your selected-file action; ChatGPT analysis separately sends the exact
   reviewed summaries online. The result discusses possible common ground, tensions,
   unknowns and practical questions, with no score or final dating verdict. Stop
   discards late results. An optional offline guide is static guidance, not AI output.

For this build, use **PRIVATE_LOOP_BUILD_SNAPSHOT.json** and
**PRIVATE_LOOP_SHA256SUMS.txt**, plus **START_HERE_CURRENT.md**. Earlier executable,
guide and snapshots remain historical artifacts. The current results and owner-review
items are in `CURRENT_STATUS.md`; this milestone does not establish general model
quality, actual ChatGPT inference or successful email delivery.

## 当前私下完整流程桌面版（2026-09-30）— 中文版

打开 **AI-SlowMatch-Desktop-Next.exe**。原桌面程序仍保留在旁边，方便恢复。这是本地
便携应用，不需要安装 Python。选择语言、阅读同意页并选择本地文件夹，空文件夹也够用。
长页面可以滚动，按 Tab 会显示当前获得焦点的按钮。

1. **连接 ChatGPT。** 已连接账号会显示绿色成功动画。真实模型列表会自动加载，
   不调用推理。当前观察到的账号建议 **GPT-5.6-Luna** 为较轻量默认项，你也可以选择
   其他可用模型。这只是基于名称的建议，不是报告质量保证。打开 ChatGPT 用量设置，
   关闭此应用的额外积分使用，再在这里如实确认；应用无法替你核验远端开关。点击
   **用 ChatGPT 开始 AI 聊天**即可进入聊天。它通过你授权的套餐在线使用 ChatGPT，
   无法读取你此前的 ChatGPT 对话。
2. **AI 聊天。** 点击**开始**，逐题回答，可随时跳过或换话题，也可随时**结束**。
   每次在线请求都会让你阅读拟发送回答。结束会丢弃迟到回答，但不能追回已经发出的
   请求。无需选择时长或市场。
3. **语音输入。** 聊天中点击**语音输入**，选择英语或简体中文，首次下载一次对应的
   免费离线模型（约 40–42 MB）。只有点击**开始录音**才会采集。点击**停止并转成文字**，
   修改识别结果，再点**使用这些文字**。文字只加入回答草稿，还需单独点**发送**。
   音频留在本机内存，不保存，也不发给 ChatGPT。没有麦克风或权限失败时会明确提示。
   开发电脑未检测到麦克风；真实英语识别使用了合成语音，实体录音与中文口述仍需要你
   在设备上检查。
4. **生成我的相处画像。** 结束后生成，核对措辞、原始引文与未知，再单独**保存这份
   画像**。解释均是暂定理解。保存的聊天历史是普通未加密本地文件；后面的加密附件
   不会同时加密这份历史。
5. **分享或比对相处画像。** 选择一份已保存画像，审阅拟分享摘要的完整内容。设置
   12–256 字符密码或口令，导出一个新的 `.slowmatch` 附件。它包含双语暂定解释与限制，
   不含原始对话、原始引文或账号凭据，不会替换已有目标文件。由你自己把文件附到邮件，
   并通过另一渠道发送密码。应用不会发邮件或上传附件。
6. **导入并讨论。** 选择自己的包或已保存画像，以及对方的加密文件，输入密码并阅读
   双方摘要。分别确认两个人的许可后再比较。本地解密只在你选择文件后进行；ChatGPT
   分析则另行把准确审阅过的摘要在线发送。结果讨论可能共同点、分歧、未知及实际沟通
   问题，不打分，也不作最终恋爱判决。停止会丢弃迟到结果。可选离线提纲是静态指导，
   不是 AI 输出。

本版本使用 **PRIVATE_LOOP_BUILD_SNAPSHOT.json**、**PRIVATE_LOOP_SHA256SUMS.txt**
及 **START_HERE_CURRENT.md**。旧程序、指南和快照保留为历史产物。最新结果及人工
检查事项见 `CURRENT_STATUS.md`；本里程碑不证明通用模型质量、真实 ChatGPT 推理或
邮件成功送达。

The following conversation checkpoint is historical / 下方聊天里程碑作为历史说明保留。

## Current conversation flow / 当前聊天流程

### English

Double-click `AI-SlowMatch-Desktop.exe`. After language, consent and a local folder,
choose **Connect ChatGPT**. **Continue with ChatGPT** opens your browser for sign-in
and optional plan authorization. Eligible Plus/Pro accounts may use their plan.
This does not read existing ChatGPT conversations or connect to the desktop app's
private files. In ChatGPT usage settings, disable extra credits for this app, then
confirm the setting here. The app cannot independently check that switch.

Open **AI Chat**, press **Start**, and answer one question at a time. Skip or change
topic freely. **End** is available during requests and discards late replies; an
online request already sent may still complete. No duration setup is required.
After ending, choose **Create my reflection**, review the words and quotations,
then separately **Save this reflection**. Saved reflections and transcripts stay in
ordinary local files, without changing earlier reports. Read them through
**Saved reflections**. No fixed number of answers is needed; missing information
remains unknown. No model calls occur just because you open the app or sign in.

The new ChatGPT integration is tested with synthetic account and response fixtures.
Your actual sign-in, plan eligibility and real ChatGPT outputs need your own review.
Previous data import, local-model/manual tools and experiments are under **More tools**.
The optional browser app retains its earlier interface.

For this desktop checkpoint, use `CONVERSATION_BUILD_SNAPSHOT.json` and
`CONVERSATION_SHA256SUMS.txt` to check the executable and this guide. The earlier
`BUILD_SNAPSHOT.json`, checksums, browser executable and Python packages are preserved
historical artifacts and do not certify the new conversation-first desktop build.

### 中文版

双击 `AI-SlowMatch-Desktop.exe`。选择语言、确认同意并选择本地文件夹后，点击**连接
ChatGPT**。**继续使用 ChatGPT**会打开浏览器，由你登录并另行授权套餐使用。符合条件的
Plus/Pro 账号可使用套餐额度；此连接不读取已有 ChatGPT 对话或桌面应用的私人文件。
请在 ChatGPT 用量设置中关闭此应用的额外积分，再回到这里确认；本应用无法独立核验开关。

进入 **AI 聊天**，点击**开始**，逐题回答，也可以跳过或换话题。请求处理中仍可**结束**，
迟到回复会被丢弃；已经发出的在线请求可能仍会完成。无需预选时长。结束后选择**生成我的
相处画像**，核对措辞及引文，再单独**保存这份画像**。画像和对话保存为普通本地文件，
不修改原有报告；通过**已保存画像**重读。没有固定回答数量，缺失信息会保持未知。
仅打开应用或登录不会调用模型。

新 ChatGPT 接入使用合成账号与回复测试；你的真实登录、套餐资格及真实模型输出仍需你
亲自查看。原有导入、本地模型、手动工具和实验放在**更多工具**，可选浏览器版保留旧界面。

本桌面里程碑使用 `CONVERSATION_BUILD_SNAPSHOT.json` 和 `CONVERSATION_SHA256SUMS.txt`
核对程序及本指南。先前的 `BUILD_SNAPSHOT.json`、校验和、浏览器程序及 Python 安装包作为
历史产物保留，不用于证明新聊天优先桌面版已通过验证。

The following sections describe optional earlier tools / 以下说明介绍可选的原有工具。

## English

Double-click `AI-SlowMatch-Desktop.exe` to open the desktop app. No Python
installation is needed. This package contains the app only: it includes no AI
model, API key, personal data, or payment information.

Optional assisted-browser export is not bundled. Import files you have exported
yourself, or use a source installation with the separate browser dependency.

Long desktop pages scroll within the window. Use the scrollbar or mouse wheel to
reach later sections; Tab moves keyboard focus and reveals the focused control.
Consent text stays complete and wraps to the available width. Export actions use
multiple rows. Merely scrolling or focusing a control never confirms consent.

1. Choose your language, read the consent screen, and choose a local vault folder.
2. Open **Connect Your AI**, select **Ollama**, and use an already installed model
   at the local address `http://127.0.0.1:11434`. Ollama must be running. This keeps
   model execution on your computer. Remote AI requests require explicit disclosure
   review and may incur provider charges. Enter an already installed chat model's
   exact name in **Ollama model**. Connection success does not verify report generation.
   If a larger model fails, explicitly choose an available smaller local model and
   review a new request; this does not download a model or certify its reports.
   The bounded full-report regeneration check used already installed `gemma4:latest`;
   that result does not cover every other report/interview workflow.
3. Use **Add Data** to select only the material you want processed. Start with
   synthetic notes. Then open **Understand Yourself**, followed by the criteria
   interview. Read and correct generated conclusions before relying on them.
4. **Offline Tools** are available without a running model. They are not a
   substitute for a connected AI interview.

In either desktop report viewer, open **Review evidence & corrections** to inspect
claims and quoted sources. Saving a correction keeps a separate local annotation
and plaintext snapshot of the original report. These notes survive restart;
they do not automatically change the report, exported card or future AI input.

To withdraw a disputed claim, save its correction first, then choose **Create
reviewed copy**. Select the saved corrections, preview the complete bilingual
copy, and confirm **Save reviewed copy**. The copy omits those claims; portrait
copies also omit consistency findings, headlines and summaries, and criteria
copies omit fictional candidate profiles. It adds no replacement facts and makes
no AI call. Other content still needs review. Reopen it under **Saved copies**.
The current selection stays unchanged. Each saved copy retains plaintext source
snapshots and correction records in the vault.

To propose different wording, choose **Rewrite one disputed claim** within
**Create reviewed copy**. Select one saved correction, read the original quotations,
and enter English and Simplified Chinese wording. Review the before/after and full
bilingual preview, then explicitly confirm saving. The new wording is labeled a
user-proposed, unverified interpretation with low confidence and speculation;
the original quotations are retained, not verified as support for the new wording.
Dependent findings or fictional candidates are removed. No AI runs, no correction
note is automatically promoted to fact, and saving does not activate the copy.

For a local AI draft of one disputed claim, use the AI-assisted interpretation
action in **Create reviewed copy**. Select a saved correction, prepare and read
the exact request, and explicitly consent to the connected local Ollama model.
Review/edit both languages, inspect the full preview and confirm saving separately.
The result keeps AI-assisted, quote-limited, unverified attribution even after editing;
its confidence is low and its type is speculation. Only saved quotations are used,
not new source documents. External API and agent-CLI adapters are not supported
for this action. A draft cannot replace originals, activate itself or become new
owner evidence.

For a complete report, open the full-report regeneration action in **Create reviewed
copy**. Select one to ten saved corrections and paste one to five original excerpts
you are authorized to provide (12,000 characters each; 24,000 total). Confirm their
original-note status, prepare/read the exact request, and explicitly consent to one
local Ollama request. Review the full English/Chinese preview, then separately
confirm saving. Each quote must match its assigned excerpt exactly; old warnings,
low confidence and an AI-regenerated/unverified notice remain. This checks quote
membership, not factual truth or semantic support. Empty claim lists can indicate
insufficient evidence. No fictional candidates are generated. Changing inputs requires
a new review; canceling discards the reply but may wait for the model. The version 0.4
copy keeps plaintext pasted excerpts and source snapshots. Saving never activates it
or overwrites originals. This works with valid current-format reports; arbitrary
legacy/profile-content migration remains unfinished.

To use a saved copy, open **Select active report** in the report viewer. Choose a
copy or **Original report / restore original**, preview it, then confirm **Use this
report**. The choice affects desktop viewing and later interview references, and
requires a new choice if its source is regenerated or changed. Cards stay unchanged.
If a report changes during an interview, your draft and conversation are kept;
explicitly start a new interview after choosing a valid report. Earlier conversations
remain readable in that window only, so copy any text you need before closing it.

For an old or unreadable report, choose **Review legacy files** in either report
viewer. Inspect the original files and diagnostics, preview, then explicitly confirm
saving a separate archive. HTML/Markdown are displayed as literal text; malformed
or non-UTF-8 files retain their original bytes. This does not convert or activate
reports, verify their claims, or call AI. Archives remain plaintext in your vault;
review them under saved archives even after originals change. Personal-profile
migration is not included. From a saved archive, open the conversion dialog and choose **Preview conversion**.
Only existing complete bilingual claims with evidence and uncertainty can be copied;
everything else remains in the archive. Review the ledger and both report languages,
then explicitly save. At least one complete claim is required. Saving does not select
the report: use **Select active report** and confirm separately. Converted reports are
partial and unverified; correction tools still address the original report only.
Changing any original member blocks use of an older conversion, though it can still
be read as history. **Legacy review only / disable active report references** stops report references
without deleting files or falling back to the old report. To resume, explicitly
select a valid conversion or regenerate and select a valid current report.
Regenerate manual-agent requests to receive the current report format; existing
request files are not silently rewritten. This workflow makes no AI calls.

For a legacy vault with profile files directly in its root, use **Open Existing
Vault Folder**. Review the exact original text and diagnostics, then explicitly
confirm copying into `profile/`. Originals stay in place; other vault contents are
not moved. An existing nonempty `profile/`, invalid text or unsupported JSON blocks
migration without dropping fields. Canceling keeps your current vault and draft.
This copies the layout only; it does not regenerate a profile or verify its claims.
The profile viewer keeps **JSON companion (read only)** separate from the Markdown
draft. Markdown saving does not update JSON automatically; an empty placeholder
cannot be saved as a profile. No AI runs during migration.

**Model acceptance scope (2026-09-28):** full-report regeneration now generates each
English/Chinese narrative together, and the app builds the existing report format.
One real local `gemma4:latest` portrait and one criteria sample passed strict checks,
separate saving and reopening. Their synthetic notes do not establish general model
reliability; some Chinese wording still needs review. The core flow made real model
calls; GUI checks used injected replies. Qwen3.5 produced an invalid portrait, and
earlier qwen3.6 CUDA startup failures remain unresolved. Other report/interview paths
retain their previous generation contract and separate validation history.
No automatic retry, format fallback or cloud request occurs in full regeneration.
Invalid output preserves originals and report selection. **Human review is required:**
structure does not prove factual support or translation fidelity. Source documentation:
[paired bilingual regeneration](../../../29_paired_report_generation.md) and the
[local recovery guide and synthetic CLI check](../../../28_local_model_recovery.md).
The CLI requires a source installation; it is not a bundled executable command.
During background AI work, closing the window or changing languages waits for
the active work and its result callbacks to finish.

The local vault uses ordinary files; it is not encrypted by this app. A vault
inside a cloud-synced folder can be copied by your sync provider. Choose its
location deliberately. Matching features remain experimental and are not a
public dating service.

`AI-SlowMatch.exe` is the optional local browser client. It opens
`http://127.0.0.1:8471`; keep its console window open while using it and press
Ctrl+C there to stop. Desktop and browser clients are separate interfaces.

If you have the source checkout, installation/build instructions and limitations
are in `packaging/README.md`. These local executables are unsigned prototypes;
no upload, public release, or provider purchase is included.

## 中文版

桌面长页面可在窗口内滚动。使用滚动条或鼠标滚轮查看后续内容；Tab 移动键盘焦点并显示
对应控件。同意文字完整保留并按可用宽度换行，导出操作分多行排列。仅滚动或移动焦点
不会确认同意。

双击 `AI-SlowMatch-Desktop.exe` 即可打开桌面应用，无需安装 Python。本安装包只包含
应用本身，不包含 AI 模型、API 密钥、个人数据或支付信息。

本包不包含可选的辅助浏览器导出组件。请导入你自行导出的文件；如需该可选组件，
请使用源码安装并另行配置浏览器依赖。

1. 选择语言，阅读同意页面，并选择一个本地档案库文件夹。
2. 打开**连接你的 AI**，选择 **Ollama**，使用已经安装的模型；本地地址为
   `http://127.0.0.1:11434`，Ollama 需要正在运行。这样模型会在你的计算机上执行。
   远程 AI 请求必须经过明确的披露审核，也可能产生提供方费用。请在 **Ollama 模型**中
   填写已安装聊天模型的准确名称。连接成功不代表报告生成通过。如果较大模型失败，
   请明确选择本机已有的较小模型并重新复核请求；这不会下载模型，也不代表其报告已经认证。
   有限范围的完整报告重新生成检查使用本机已安装的 `gemma4:latest`，该结果不覆盖其他所有报告或访谈流程。
3. 通过**添加数据**只选择你希望处理的材料。建议先使用合成笔记，再进入**了解你自己**
   和择偶标准访谈。使用生成结论之前，请先阅读并修正其中的不准确内容。
4. 没有运行模型时可以使用**离线工具**；它不能替代连接 AI 后的访谈功能。

在桌面报告查看器中打开**复核证据与更正**，可检查主张及来源引文。保存更正会另行保留本地
批注和原始报告的明文快照，重启后仍可查看；这些批注不会自动改变报告、导出卡片或后续 AI 输入。

如需撤回争议主张，请先保存对应更正，再选择**生成复核副本**。勾选已保存的更正，预览完整
双语副本，然后确认**保存复核副本**。副本会移除这些主张；画像副本还会移除一致性分析、
概括标题和摘要，择偶标准副本还会移除虚构候选人档案。此操作不添加替代事实，也不调用 AI。
其他内容仍需复核。可以在**已保存副本**中重新打开；当前选择保持不变。每份副本都会
在档案库中保留明文来源快照和更正记录。

如需提出不同措辞，请在**生成复核副本**中选择**改写一条争议主张**。选择一条已保存更正，
阅读原始引文，输入英文及简体中文措辞。复核前后对照与完整双语预览，再明确确认保存。
新措辞标为用户提出、未经核验的解释，类型为猜测、置信度为低；保留原引文，但不证明它们
支持新措辞。相关一致性发现或虚构候选人会被移除。此操作不调用 AI，不会自动将批注当成
事实，保存也不会启用副本。

如需由本地 AI 起草一条争议主张，请使用**生成复核副本**中的 AI 辅助解释操作。选择已保存
更正，准备并阅读准确请求，明确同意调用已连接的本地 Ollama 模型。复核或编辑两种语言，
查看完整预览，再单独确认保存。即使编辑后，结果仍标为 AI 辅助、仅依据已有引文、未经
核实，固定为低置信度推测。仅使用已保存引文，不读取新的来源文档；此操作不支持外部
API 或代理命令行适配器。草稿不能替换原件、自行启用或成为新的用户证据。

如需完整报告，请打开**生成复核副本**中的完整报告重新生成操作。选择一至十条已保存
更正，粘贴一至五份你有权提供的原始摘录（每份最多 12,000 字符，合计最多 24,000）。
确认它们属于原始笔记，准备并阅读准确请求，再明确同意一次本地 Ollama 请求。查看完整
中英预览，另行确认保存。每条引文须精确匹配对应摘录；保留旧警示、低置信度及 AI
重新生成/未经核实说明。这只检查引文存在性，不证明事实真实或语义支持。空主张列表可能
表示证据不足，不生成虚构候选人。输入变化后须重新复核；取消会丢弃回复，但可能需要等待
模型结束。0.4 版本副本保留明文摘录和来源快照；保存不自动启用，也不覆盖原件。此操作
适用于有效的当前格式报告；任意旧格式/档案内容迁移仍待完成。

如需使用副本，请在报告查看器中打开**选择当前报告**，选择副本或**原报告 / 恢复原报告**，
预览后确认**使用这份报告**。选择影响桌面查看与后续访谈参考；来源重新生成或变化后须
再次选择，卡片保持不变。访谈途中报告变化时会保留草稿和对话，请选择有效报告后明确开始
新访谈。先前对话仅在该窗口中可读，关闭前请复制需要保留的文字。

遇到旧版或无法读取的报告时，请在任一报告查看器中选择**复核旧版文件**。检查原文件与
诊断，预览后明确确认，另存独立存档。HTML/Markdown 按字面文本展示；坏格式或非 UTF-8
文件仍保留全部原始字节。此操作不转换或启用报告、不核实主张，也不调用 AI。存档仍是档案
库内的明文文件，原件变化后也可在已保存存档中复核；本功能不包括个人档案迁移。从已保存
存档打开转换窗口并选择**预览转换**：只复制已有完整双语表述、证据和不确定性信息的主张，其余内容
仍在存档中。复核字段清单及两种语言报告后明确保存，至少须有一条完整主张。保存不会
自动选用报告，请通过**选择当前报告**另行确认。转换报告是部分内容且未经核实，更正工具仍
只针对原报告。任一原始成员变化后，旧转换不能继续使用，但仍可作为历史打开。
**仅复核旧文件 / 停用当前报告参考**会停止报告参考，不删除文件，也不退回旧报告。恢复使用时，请明确
选择有效转换，或重新生成并选择有效的当前报告。请重新生成手动代理请求以获得当前报告
格式，已有请求文件不会被静默改写。整个转换流程不调用 AI。

如果旧档案文件直接位于档案库根目录，请选择**打开现有档案库文件夹**，复核原文与诊断，
再明确确认复制到 `profile/`。原件留在原处，其他档案内容不移动。目标 `profile/` 已有
内容、文本无效或 JSON 不受支持时会阻止迁移，不丢弃字段。取消会保留当前档案库和草稿。
此操作只迁移目录布局，不重新生成档案，也不核实其中主张。档案查看器中的
**JSON 配套文件（只读）**与 Markdown 草稿分开；保存 Markdown 不自动更新 JSON，
空白提示不能保存为档案。迁移过程不调用 AI。

**模型验收范围（2026-09-28）：**完整报告重新生成现将每句中英叙述一起生成，由应用建立
既有报告格式。真实本地 `gemma4:latest` 的一份画像和一份择偶标准样例通过了严格校验、
单独保存和重读。合成笔记样例不证明模型普遍可靠，部分中文措辞仍需复核。核心流程调用了
真实模型；界面检查使用注入回复。Qwen3.5 仍生成了无效画像，此前 qwen3.6 的 CUDA 启动
故障尚未解决。其他报告/访谈路径保留此前的生成契约，验证历史单独记录。
完整重新生成不自动重试、降级格式或请求云端，无效输出保留原件和当前报告选择。
**仍需人工审核：**结构通过不证明事实支持或翻译准确。源码文档提供
[成对双语重新生成说明](../../../29_paired_report_generation.md)及
[本地恢复指南与合成数据 CLI 检查](../../../28_local_model_recovery.md)。
CLI 需要源码安装，不是打包可执行程序内置的命令。
后台 AI 任务运行期间，关闭窗口或切换语言会等待正在执行的任务及其结果回调结束。

本地档案库使用普通文件，应用不会为其加密。放在云同步目录中的档案库可能被同步服务
复制，因此请有意识地选择保存位置。匹配功能仍处于实验阶段，不是公开的交友服务。

`AI-SlowMatch.exe` 是可选的本地浏览器客户端，会打开 `http://127.0.0.1:8471`。
使用期间请保留其终端窗口，退出时在该窗口按 Ctrl+C。桌面端和浏览器端是两个不同界面。

如果你有源码目录，可在 `packaging/README.md` 查看安装、构建方法和限制。这些本地
可执行文件是未签名原型；本包不包含上传、公开发布或购买提供方服务的操作。
