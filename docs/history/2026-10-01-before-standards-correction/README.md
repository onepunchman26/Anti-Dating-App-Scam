# Historical snapshot / 历史快照

English: Superseded on October 2, 2026; current scope is in the root plan.

中文版：2026 年 10 月 2 日起被替代；当前范围以根目录计划为准。

# Anti-Dating-App-Scam / AI-SlowMatch

## English

The desktop flow is **Connect ChatGPT → AI Chat → Start / End → review and save
a private reflection → Share or compare reflections**. Voice input recognizes
speech locally and adds editable text to the answer box; it never sends for you.
There is no duration picker. Questions explore needs, boundaries and ways of relating.
Read the [product direction](../../30_conversation_first_product.md) and
[private exchange and voice design](../../31_private_exchange_voice.md).

Share one reviewed summary as a password-encrypted `.slowmatch` file. Attach it to
your own email and send the password separately. Import your own and the other
person's files for a private discussion of possible common ground, tensions and
unknowns. The app does not send email or rank people. File decryption is local;
choosing ChatGPT for comparison sends only the reviewed summaries online, with
both participants' permission. Local chat histories remain ordinary unencrypted
files. Imports, older interviews and other providers remain under **More tools**.

ChatGPT connection uses the official browser sign-in and optional Plus/Pro plan
authorization, rather than reading the installed ChatGPT app's conversations.
The app cannot verify ChatGPT's extra-credit switch: explicitly disable extra
credits in ChatGPT usage settings and confirm this before enabling model requests.
No API key is needed. Computer Use verified a connected account and its actual
model catalog; the suggested lighter default was GPT-5.6-Luna. Actual ChatGPT
inference and allowance settings still await the owner's confirmation. The default
is a name-based suggestion, not a verified report-quality or cost guarantee.

A local-first personal relationship reflection and scam-awareness prototype.
Private long-term intelligence belongs to the user. A future optional adult
matching network should coordinate limited discovery, not collect conversations.
Current matching code is experimental and not ready for public use.

Read [CURRENT_STATUS.md](../../../CURRENT_STATUS.md) for verified results and next work,
and the [architecture audit](../../16_rehabilitation_audit.md) for the incremental
roadmap. Existing PySide6 and browser interfaces are preserved.

### Install and run

Development requires Python 3.11+. For a fresh checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,desktop]"
.\.venv\Scripts\python.exe run_desktop.py
```

This checkout's repaired environment is `.venv-rehab`; substitute that name above.
The old broken `.venv` was preserved. Windows setup supports an explicit interpreter
and alternate environment: `setup_windows.ps1 -PythonExecutable <path>
-EnvironmentName .venv-rehab -NonInteractive`. Failures stop setup. On other
platforms use the environment's `bin/python`.

The existing browser prototype starts with:

```powershell
.\.venv-rehab\Scripts\python.exe run_local_app.py
```

It opens the browser at `http://127.0.0.1:8471`. Keep it loopback-only. Foreign
browser origins are rejected; this is not authentication against local processes.
PySide6 remains the GUI-first development path.

The desktop keeps long pages inside independent scroll areas, so inactive pages
cannot enlarge the whole window. Keyboard focus reveals off-screen controls;
complete consent wording wraps, and export actions fit in rows. See
[desktop window behavior](../../25_desktop_window_navigation.md).

For the optional older local-AI workflow, open **More tools → Other AI connections**
and explicitly select an installed chat model. A successful connection checks
availability, not report generation.
Complete report regeneration now asks for English and Chinese together at each
narrative field. The app builds the existing report format without inventing
translations. Installed `gemma4:latest` passed one real synthetic portrait and one
criteria regeneration, including strict checks, separate saving and reopening.
Some wording still needs review; this is limited integration acceptance, not general
model certification or validation of every other AI workflow. Qwen3.5 still produced
an invalid portrait, and earlier qwen3.6 CUDA failures remain unresolved. The app
rejects invalid reports while preserving originals. See
[paired bilingual regeneration](../../29_paired_report_generation.md) and
[local recovery and the synthetic CLI check](../../28_local_model_recovery.md).

### Existing capabilities

- Guided onboarding, safety consent, profile detection, home navigation, settings,
  and English/Chinese switching.
- User-supplied ChatGPT ZIP/JSON, memory summaries and manual notes. Summaries are
  partial input, not authoritative personality records.
- Scam-risk reflection, trust-ladder pacing, JSON/Markdown report export and
  schema/hash verification. Hashes do not prove authorship or wrongdoing.
- Editable local profiles and experimental self-portrait/interview tools. Desktop
  vaults use `profile/`, `imports/`, `reports/`; browser self-model conventions
  differ. Default root: `~/.ai_slowmatch`.
- Ollama, cloud chat adapters and installed agent-CLI integrations. The older
  structured registry still has cloud placeholders, while chat adapters are real
  implementations. Keys stay in memory/environment, not ordinary profile fields.
  Live local Ollama synthesis/save/reload/fingerprint was verified with synthetic data.
  Remote providers were tested with injected transports; no paid calls were made.
- Optional assisted browser export: `pip install -e ".[browser]"`. User action and
  platform restrictions apply; never bypass login, CAPTCHA or rate limits.
- Experimental manually exchanged beacons and a node using coarse regions,
  fingerprints and mutual acceptance before contact disclosure.

Synthetic local node demo:

```powershell
.\.venv-rehab\Scripts\python.exe run_rendezvous_node.py --host 127.0.0.1 --port 8470 --demo-seed wtw3
```

Open `http://localhost:8470/`. Node state is in memory; tokens are not complete
accounts, recovery or abuse protection. Adult age and disclosure consent are now
required; these are self-declarations, not identity verification. The node receives
registration metadata (including coarse area and hidden contact) and card fingerprints,
never the compatibility-card contents. Public release still requires further review.

### Privacy and verification

Vaults are currently **plaintext, not encrypted**. Sync folders can leave the device
through their sync provider. Local Ollama is restricted to loopback with no cloud
fallback. External providers receive only explicitly reviewed, editable messages;
review is not automatic anonymization. Keys are never saved with profiles.
Use the local model to avoid paid API calls. See [AI request boundaries](../../17_reviewed_ai_requests.md).

Generated reports require valid schemas, evidence and uncertainty before saving.
Desktop bilingual report text is rendered from validated canonical fields and
source-bound translations; independent model-authored Markdown is not saved.
Structural and language checks do not prove truth or translation accuracy.
Browser app state and in-flight file destinations are isolated; prior AI reports
are references rather than new user evidence. Desktop report viewers provide
evidence review and persistent correction notes, keeping the original report and
its snapshot separate from user annotations. Corrections are not automatically
applied to reports, exports or AI requests. See [review history](../../18_report_review_history.md).
An explicit preview-and-confirm workflow can withdraw selected disputed claims
into a separate bilingual [reviewed copy](../../19_reviewed_report_copies.md).
The copy preserves the originals. A separate preview-and-confirm
[report selection](../../20_active_report_selection.md) activates it for desktop
viewing and interview reference, or returns to the generated report. Changed
versions stop use until reselected; selected reports remain unverified references.
An explicit [user-proposed reinterpretation](../../21_user_proposed_reinterpretation.md)
can also rewrite one corrected claim in a separate copy. Its original citations
stay intact; the wording is attributed to the user and marked unverified,
speculative and low-confidence. Both languages require review. This does not
establish factual support. A separate
[AI-assisted claim revision](../../26_ai_assisted_claim_revision.md) can draft one
interpretation with a local Ollama model after reviewing the exact request. It uses
saved quotations only, retains AI-assisted/unverified attribution after editing,
and requires separate preview, saving and selection.
[Full report regeneration](../../27_full_report_regeneration.md) accepts selected
corrections and explicitly pasted original excerpts, with exact request review and
local Ollama consent. Every quotation must occur in its assigned excerpt; complete
bilingual reports keep old warnings, low confidence and an AI/unverified notice.
Preview, saving and activation remain separate. Excerpt snapshots stay plaintext;
source truth and semantic support still need review. Broad legacy/profile-content
migration and encrypted storage remain incomplete.
The report viewers also offer [Review legacy files](../../22_legacy_report_archives.md):
inspect original text and compatibility diagnostics, then explicitly save an exact-byte
archive. Unsupported fields and malformed files are preserved without conversion,
activation or AI calls. A separate [partial conversion](../../23_legacy_report_conversions.md)
can copy legacy claims that already have complete bilingual wording, evidence and
uncertainty. Review the copied/archive-only ledger, explicitly save, then separately
select the converted report. Missing information is never invented; zero complete
claims cannot be saved as a successful report. **Review only — disable references**
stops report use while preserving files. Full legacy and personal-profile migration
remain unfinished. Regenerate manual requests to receive the current output contract.

Older vaults with `profile.mpm.md` or `profile.json` directly in their root now have
an explicit [profile layout migration](../../24_profile_layout_migration.md). Opening
the old folder offers literal preview and confirmation before copying exact bytes
into `profile/`. Originals remain intact; existing destination content is never
merged or overwritten. Unsupported JSON stays blocked for review. The profile
viewer keeps the JSON companion read-only and separate from the Markdown draft.

No public personality scores, deterministic
person labels, diagnoses, spying, doxxing, harassment, hidden uploads, or advice
to send money or sensitive information to online-only contacts are acceptable.
Risk signals support reflection; they are not verdicts about people.

```powershell
.\.venv-rehab\Scripts\python.exe -m compileall src
.\.venv-rehab\Scripts\python.exe -m pytest -q
.\.venv-rehab\Scripts\python.exe -m ruff check src tests
```

Tests isolate home directories and disable AI autoconnection; desktop startup is
tested offscreen. The wheel includes desktop/browser resources and installed launch
commands; Windows portable builds are locally smoke-tested. See
[packaging instructions](../../../packaging/README.md). Remaining priorities are broader
legacy/profile-content migration, encryption, browser report
translation and wider consent-based evaluation.
Public deployment/release requires explicit approval and privacy/reliability validation.

## 中文版

桌面主流程现为**连接 ChatGPT → AI 聊天 → 开始 / 结束 → 审阅并保存私密画像
→ 分享或比对相处画像**。语音输入在本机识别，文字加入可编辑回答框，不会代你发送。
无需选择聊天时长，问题围绕需要、边界与相处方式。详见
[聊天优先产品构想](../../30_conversation_first_product.md)及
[私密交换与语音设计](../../31_private_exchange_voice.md)。

将一份经审阅摘要导出为有密码保护的 `.slowmatch` 加密文件，由你自己附加到邮件，
并通过另一渠道发送密码。在本机导入自己及对方的文件，私下讨论可能的契合点、分歧与未知。
应用不发送邮件，也不为人排名。文件在本机解密；选择 ChatGPT 比较时，经双方许可，
仅将审阅过的摘要发送在线处理。本地聊天历史仍是普通未加密文件。导入、原有访谈及
其他提供方保留在**更多工具**。

连接采用官方浏览器登录及可选的 Plus/Pro 套餐使用授权，不读取已安装 ChatGPT 应用的
既有对话。本应用无法核验 ChatGPT 的额外积分开关；启用模型请求前，请在 ChatGPT 用量
设置中关闭额外积分，并明确确认。无需 API 密钥。Computer Use 已核验账号连接成功
及其真实模型列表，所建议的轻量默认项为 GPT-5.6-Luna。真实 ChatGPT 推理与额度设置
仍等待所有者确认；默认项只是根据名称作出的建议，不是报告质量或费用保证。

这是一个本地优先的个人关系反思与诈骗风险认知原型。长期私密智能属于用户；未来可选的
成年人匹配网络应协调有限发现，而非收集对话。当前匹配代码属于实验，不适合公共使用。

请阅读 [CURRENT_STATUS.md](../../../CURRENT_STATUS.md) 了解验证结果和下一任务，参阅
[架构审计](../../16_rehabilitation_audit.md) 了解渐进路线图。现有 PySide6 与浏览器界面均予保留。

### 安装与运行

开发需要 Python 3.11 或以上版本。全新仓库安装方式：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,desktop]"
.\.venv\Scripts\python.exe run_desktop.py
```

本仓库已恢复的环境名为 `.venv-rehab`，请替换上方环境名。旧损坏环境 `.venv` 已保留。
Windows 安装支持指定解释器和环境：`setup_windows.ps1 -PythonExecutable <路径>
-EnvironmentName .venv-rehab -NonInteractive`。失败会停止安装。其他平台使用环境内的 `bin/python`。

已有浏览器原型的启动方式：

```powershell
.\.venv-rehab\Scripts\python.exe run_local_app.py
```

浏览器打开 `http://127.0.0.1:8471`。必须保持仅回环访问。其他浏览器来源会被拒绝，但这不是
对本地进程的身份认证。PySide6 仍为 GUI 优先的开发路径。

桌面的长页面现位于各自独立的滚动区域中，未显示页面不会再撑大整个窗口。键盘焦点会
带出屏幕外的控件，完整同意文字换行显示，导出操作分行排列。
详见[桌面窗口行为](../../25_desktop_window_navigation.md)。

使用可选的原有本地 AI 流程时，请在**更多工具 → 其他 AI 连接**中明确选择已安装的聊天模型。
连接成功只说明可用性，
不代表报告生成通过。完整报告重新生成现让模型在每个叙述字段同时提供英文和中文，
由应用建立既有报告格式，不补造翻译。本机已安装的 `gemma4:latest` 已分别通过一份
真实合成画像及一份择偶标准重新生成，包括严格校验、单独保存和重读。部分措辞仍需复核；
这是有限集成验收，不是普遍模型认证，也不代表其他所有 AI 流程均已验证。Qwen3.5 仍生成了
无效画像，此前 qwen3.6 的 CUDA 故障也未解决。应用会拒绝无效报告并保留原件。详见
[成对双语重新生成](../../29_paired_report_generation.md)及
[本地恢复与合成数据 CLI 检查](../../28_local_model_recovery.md)。

### 现有能力

- 引导、安全同意、档案检测、主页导航、设置与中英文切换。
- 用户提供的 ChatGPT ZIP/JSON、记忆摘要与手动笔记。摘要只是部分输入，不是权威人格档案。
- 诈骗风险反思、信任阶梯节奏、JSON/Markdown 导出与 Schema/哈希验证。哈希不能证明作者或不当行为。
- 可编辑本地档案与实验性自我画像/访谈。桌面档案库使用 `profile/`、`imports/`、`reports/`；
  浏览器自我模型约定不同。默认根目录为 `~/.ai_slowmatch`。
- Ollama、云端聊天适配器与已安装代理 CLI。旧结构化注册表仍有云端占位项，聊天适配器则
  已实际实现。密钥保存在内存/环境变量，不写入普通档案字段。已用合成数据验证真实本地
  Ollama 的生成、保存、重读与指纹链路；远端使用模拟传输测试，未调用付费服务。
- 可选辅助浏览器导出：`pip install -e ".[browser]"`。要求用户操作并遵守平台限制，
  不得绕过登录、验证码或频率限制。
- 实验性手动交换信标和会合节点，使用粗粒度区域、指纹，并在双方接受后披露联系方式。

合成本地节点演示：

```powershell
.\.venv-rehab\Scripts\python.exe run_rendezvous_node.py --host 127.0.0.1 --port 8470 --demo-seed wtw3
```

打开 `http://localhost:8470/`。节点状态保存在内存；令牌不等于完整账号、恢复或滥用防护。
现已要求成年年龄与披露同意，但属于自行声明，不是身份核验。节点接收登记元数据
（包括粗略区域与隐藏联系方式）以及卡片指纹，不接收兼容性卡片正文。仍未达到公共发布条件。

### 隐私与验证

档案库目前为**明文，尚未加密**；同步目录可能经同步服务离开设备。本地 Ollama 被限制为回环地址，
不会回退至云端。外部提供方只能接收用户逐次审核并可编辑的消息；审核不等于自动彻底匿名化。
密钥不会与档案一起保存。使用本地模型可避免付费 API 调用。详见[AI 请求边界](../../17_reviewed_ai_requests.md)。

生成报告在保存前必须通过结构、证据和不确定性字段校验。桌面双语报告由经过校验的结构化字段
及与来源绑定的译文渲染，不保存模型另行创作的 Markdown。结构与语言检查不证明事实或翻译准确。
浏览器应用状态和进行中请求的文件目的地已隔离，旧 AI 报告仅作为参考，不能充当新的用户证据。
桌面报告查看器提供证据复核和持久更正批注，将原报告及其快照与用户批注分开保存。
更正不会自动应用于报告、导出内容或 AI 请求。详见[纠错历史](../../18_report_review_history.md)。
通过明确预览和确认，可以撤回选中的争议主张，生成独立的双语[复核副本](../../19_reviewed_report_copies.md)。
副本保留原件。通过另行预览与确认的[报告选择](../../20_active_report_selection.md)，可将其用于
桌面查看和访谈参考，或返回生成报告。版本变化后须重新选择才能继续使用；所选报告仍是未经
核验的参考。另行明确提出的[用户重述](../../21_user_proposed_reinterpretation.md)，可以在独立
副本中改写一条已保存更正的主张；原引文保持完整，新措辞明确归属于用户，并标为未经核验、
猜测及低置信度，两种语言均须复核。这不证明事实支持。另行使用
[AI 辅助主张修订](../../26_ai_assisted_claim_revision.md)，可以在审核准确请求后，由本地
Ollama 模型起草一条解释。它只使用已保存引文，编辑后仍保留 AI 辅助/未经核实归属，并要求
分开预览、保存及选择。
[完整报告重新生成](../../27_full_report_regeneration.md) 接收所选更正及明确粘贴的原始摘录，
先准确审核请求，再同意本地 Ollama 调用。每条引文必须出现在对应摘录中；完整双语报告
保留旧警示、低置信度及 AI/未经核实说明。预览、保存和启用仍分开进行。摘录快照仍为
明文；来源真实与语义支持仍需复核。更广泛的旧格式/档案内容迁移与加密存储仍待完善。
报告查看器还提供[复核旧版文件](../../22_legacy_report_archives.md)：检查原文及兼容性诊断，
明确确认后保存精确字节存档。不支持的字段或坏格式文件会完整保留，不进行转换、启用或 AI
调用。另行打开[部分转换](../../23_legacy_report_conversions.md)，可以复制原本就有完整双语
表述、证据及不确定性信息的旧主张。先复核复制与仅存档字段的清单，明确保存，再单独选择
转换报告。不会编造缺失信息；没有完整主张时，不能保存为空壳成功报告。**仅复核——停用参考**
会停止报告使用并保留文件。完整旧格式及个人档案迁移仍未完成；请重新生成手动请求以获得
当前输出契约。

对于直接在根目录保存 `profile.mpm.md` 或 `profile.json` 的旧档案库，现提供明确的
[个人档案布局迁移](../../24_profile_layout_migration.md)。打开旧目录后先按原文预览，确认
后将精确字节复制到 `profile/`。原件保留，目标已有内容时不合并、不覆盖。不受支持的 JSON
会阻止迁移并保留供复核。档案查看器现将 JSON 作为独立只读内容，不占用 Markdown 草稿。

禁止公共人格评分、确定性人物标签、诊断、监视、人肉搜索、骚扰、隐藏上传，以及建议向网恋对象
转账或发送敏感信息。风险信号用于反思，不是对人的判决。

```powershell
.\.venv-rehab\Scripts\python.exe -m compileall src
.\.venv-rehab\Scripts\python.exe -m pytest -q
.\.venv-rehab\Scripts\python.exe -m ruff check src tests
```

测试隔离主目录并禁用 AI 自动连接；桌面启动采用无界面验证。wheel 现包含桌面、浏览器资源与
安装后的启动命令，Windows 便携程序也进行了本地启动验证，详见[打包说明](../../../packaging/README.md)。
后续重点是更广泛的旧格式/档案内容迁移、加密、浏览器报告翻译，
以及更广泛且经过同意的评估。
公共部署或发布仍须明确审核并验证隐私与可靠性。
