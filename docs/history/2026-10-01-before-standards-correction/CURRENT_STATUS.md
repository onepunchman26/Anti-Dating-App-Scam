# Historical snapshot / 历史快照

English: Superseded on October 2, 2026; current scope is in the root plan.

中文版：2026 年 10 月 2 日起被替代；当前范围以根目录计划为准。

# Current status / 当前状态 — 2026-10-01

## English — standards audit complete; correction plan under review

The owner requested a product, development and release review before further feature
expansion. Read [the evidence audit](../../16_rehabilitation_audit.md),
[the proposed phased correction](../../../PLAN_FOR_ONEPUCHMAN.md), and
[the design decisions](../../../OWNER_REVIEW.md). The proposal is not implemented or approved.

The audit confirms four different EXE names in `dist/`, no fixed root EXE, missing
Windows version metadata, two version constants, and no reusable tested promotion /
rollback pipeline. At audit start, 37 tracked files were modified and 220 files were
untracked. The remote branch matches only the old committed baseline, not these
changes. One external local snapshot preserves 373 selected development files; all
373 restored hashes match, and a separate complete Git history bundle verifies.
This is a one-off safeguard, not an automatic backup system. Papers, caches, private
vaults and runtime data were excluded from the working-source snapshot.

The account model picker is live. A fresh October 1 catalog query returned GPT-6-Astra,
GPT-5.6-Sol, GPT-5.6-Terra, GPT-5.6-Luna and GPT-5.5, with no GPT-6.1 entry. The app's
existing authorization was renewed by its normal service; one catalog request and
zero inference calls were made. Safe evidence is in
`build/standards-audit-account-catalog.json`. The lightweight default is an unmeasured
name heuristic. The adapter discards the response's reported model, and End can leave a
stalled request blocking the next conversation. Current chat is question-only intake;
it does not yet supply the full supportive conversation or maintained user-model
lifecycle. Pi is TypeScript/Node; the proposal reuses its interface ideas in Python.
The installed coaching skill has a verified 31-commit upstream update; it has not
been updated or integrated into the main chat during this review.

**Fresh validation:** compilation of source and apps and full source/app/test Ruff
passed. The full test run returned **2115 passed, 1 failed, 9 skipped**, with one
dependency deprecation warning (445.07 seconds). The failure is concurrent legacy
archive listing; a single focused rerun, 20 isolated diagnostic trials and 41 focused
archive/history-race tests passed. They did not reproduce or resolve the original
failure. Diagnostic evidence is retained locally in `build/standards-audit-pytest.log`.
The earlier 2116-pass package remains historical evidence, not today's green gate.
A separate controlled Windows-handle test reproduced a legitimate staging-directory
rename rejected during path resolution; the archive remained intact and the next
read passed. This establishes a missing concurrency case, while the original failed
run's exact cause remains unproven. See `build/standards-audit-pending-handle-race.log`.

No executable, runtime source, installed skill, Git commits or repository remote
content was changed in this review. Apart from normal renewal of the app-owned
authorization for catalog discovery, no account settings were changed. No real model inference, private-vault inspection
or microphone recording was performed. Real-account inference and microphone
acceptance remain separate outstanding gates. Hourly automation is still **PAUSED**.
Structural implementation awaits the requested grilling design confirmation.

## 中文版 — 规范审查完成；整改计划待审阅

所有者要求先审查产品、开发及发布规范，再继续扩展功能。请阅读
[证据审计](../../16_rehabilitation_audit.md)、[分阶段整改提案](../../../PLAN_FOR_ONEPUCHMAN.md)
及[设计决策](../../../OWNER_REVIEW.md)。提案尚未实施，也尚未批准。

审查确认 `dist/` 中有四个不同名字的 EXE，根目录没有固定入口，Windows 版本信息缺失，版本常量有两处，且没有可重复测试的正式替换／回滚流程。审查开始时，有 37 个已跟踪文件被修改、220 个文件未跟踪；远端分支只与旧提交一致，不包含这些修改。已用外部本地快照保护 373 个选定开发文件，恢复后 373 项哈希全部一致，另一个完整 Git 历史包也通过校验。这是一次性保护，不是自动备份系统。工作源码快照未包含论文、缓存、私人资料库或运行数据。

账号模型列表确实实时获取。10 月 1 日重新查询返回 GPT-6-Astra、GPT-5.6-Sol、GPT-5.6-Terra、GPT-5.6-Luna 和 GPT-5.5，没有 GPT-6.1 条目。应用正常续期了已有授权，查询一次目录，推理调用为零；不含凭据的依据见 `build/standards-audit-account-catalog.json`。轻量默认项仅按名称判断，没有实测支撑。适配器丢弃了响应中的实际模型标识；点击结束后，卡住的请求可能继续阻挡下一次对话。目前聊天仍是只提问的访谈，尚未提供完整的支持式对话及持续用户模型管理。Pi 使用 TypeScript／Node，提案是在 Python 中借鉴接口设计。已核实军师 skill 上游多 31 次提交；本次审查没有更新它，也没有把它接入主聊天。

**本次新验证：** 源码与应用编译、全范围源码／应用／测试 Ruff 检查通过。全量测试为 **2115 项通过、1 项失败、9 项跳过**，另有一项依赖弃用提示，用时 445.07 秒。失败涉及并发读取旧报告归档；单独重跑一次、20 次隔离诊断及 41 项归档／历史并发定向测试均通过，但没有复现或解决原始失败。诊断依据保存在本地 `build/standards-audit-pytest.log`。此前 2116 项通过只属于历史程序包依据，不代表今天已全绿。

另一个受控 Windows 句柄测试复现了遗漏的并发情况：合法暂存目录在路径解析期间改名，被误拒绝；归档仍完整，下一次读取通过。这证明存在需补足的并发处理，但未能证明首次全量失败恰由同一原因造成。依据见 `build/standards-audit-pending-handle-race.log`。

本次审查未修改程序、运行源码、已安装 skill、Git 提交或仓库远端内容；除查询模型目录所需的应用自身正常授权续期外，没有更改账号设置。未进行真实模型推理、私人资料库检查或麦克风录音。真实账号推理与麦克风仍需分别验收。小时自动任务保持 **PAUSED**。按照所要求的 grilling 流程，在设计确认后再进行结构性实施。

---

## Historical package checkpoint — 2026-09-30 / 历史程序包里程碑

## English — implemented private flow, real AI acceptance still blocked

The new **[AI-SlowMatch-Desktop-Next.exe](../../../dist/AI-SlowMatch-Desktop-Next.exe)** is
built and verified. The primary flow now includes **Connect ChatGPT → Start / End
AI Chat → review and save a private reflection → preview and export an encrypted
attachment → open both participants' files → review a private AI comparison**.
Home and AI Chat both link to sharing and comparison. Voice input adds an editable
draft; it never sends automatically. The original executable and previous build
receipts remain unchanged. See [the opening guide](../../../dist/START_HERE_CURRENT.md).

This is **not a completed real-model acceptance checkpoint**. Actual local-model
experiments used fictional answers only. Gemma produced questions, separately saved
portraits and encrypted files that could be imported, but its comparison promoted
unknown information into risk and used quotations from the wrong fields; the
application rejected it. Qwen 3.5 repeatedly violated required report fields or
coverage, or returned an incompatible comparison structure. Some outputs also
strengthened preferences into behavior or implied successful past action. The
installed larger Qwen 3.6 failed during CUDA startup before returning any answer.
No failed comparison was accepted, repaired, retried automatically or presented
as a working AI result. A full current-source, semantically acceptable real AI
chat-to-comparison journey has **not** been demonstrated.

The observed prompt mismatch has been fixed: the model now sees the same final
schema that the reviewed request sends to the decoder. One short statement permits
at most one portrait claim; coverage cannot be empty when claims exist. Comparison
source IDs bind one bilingual field, quotations must match either original language
exactly, and missing information cannot support common-ground, tension or risk
points. These checks and a narrow preference-to-action guard cannot establish all
semantic meanings or translation fidelity. The failed model receipts remain useful
evidence of that limitation, rather than a general claim of model quality.

### Verified implementation and package evidence

- **2116 tests passed; nine Windows link-permission skips**, one existing dependency
  deprecation warning. Compileall, whole source/desktop/test Ruff and diff checks
  pass. The final full suite used the frozen runtime.
- Real Qt tests exercise export/import with actual synthetic encrypted files,
  wrong passwords, tampering, both permissions, exact request review, review-time
  changes, stop, late replies, vault switching and navigation. Forty-four synthetic
  screenshots were reviewed across English/Chinese and 940/1100-pixel windows.
  The built desktop's English/Chinese welcome pages were also inspected with
  Computer Use in an empty synthetic home, then the test window was closed.
- The final package matches **181 runtime file hashes and 29 critical embedded
  modules**. JWT/crypto, all four Vosk native DLLs and both Qt multimedia plugins
  are included and checked. Startup outside the checkout loaded the native voice
  library and enumerated devices without recording. Speech models are installed
  only through the user's separate download action. See
  [build snapshot](../../../dist/PRIVATE_LOOP_BUILD_SNAPSHOT.json) and
  [checksums](../../../dist/PRIVATE_LOOP_SHA256SUMS.txt).
- The actual account screen and account catalog were observed successfully using
  Computer Use. It offered GPT-6-Astra, GPT-5.6-Sol, GPT-5.6-Terra, GPT-5.6-Luna
  and GPT-5.5. The lighter-name default is GPT-5.6-Luna. This observation used
  account discovery, **no ChatGPT inference**. Speed, report quality and plan
  consumption are unmeasured; the extra-credit confirmation was unchecked.
- Real offline English recognition transcribed synthetic speech as
  “i need a little time to think.” Both pinned official English/Chinese models
  were downloaded, checked and loaded. Thirty voice tests pass. This computer
  enumerated **zero microphone inputs**: actual microphone recording and spoken
  Chinese recognition quality have not been verified.

Encrypted `.slowmatch` files contain a selected bilingual reflection summary,
questions and limits, without raw chat, original evidence quotations or credentials.
Narratives may still reveal personal information. Import decrypts in memory and
does not overwrite a portrait. The sender attaches the file using their own email
app and shares the password separately; no email was sent. Encryption is not proof
of identity or compatibility. Ordinary local chat history remains unencrypted.

### Owner actions and continuation

Read **[OWNER_REVIEW.md](../../../OWNER_REVIEW.md)**. The important next steps are to verify
that this app's extra credits are disabled in ChatGPT Usage settings, truthfully
confirm that fact, and test fictional chat/reflection/comparison using the real
account model. A connected microphone is needed for device recording acceptance;
Chinese transcription and actual response quality need your review. Review shared
summaries and both permissions before any private attachment exchange. Automatic
contact, public deployment and real-person matching have not been performed.

The hourly `ai-slowmatch` automation remains **PAUSED**. After this concrete review
checkpoint, work waits for the owner's explicit next instruction. No money, card
information, paid API, real private archive, public deployment or message sending
was used in the development tests. The full bilingual design is in
[private exchange and voice](../../31_private_exchange_voice.md).

## 中文版 — 私下流程已实现，真实 AI 验收仍受阻

新的 **[AI-SlowMatch-Desktop-Next.exe](../../../dist/AI-SlowMatch-Desktop-Next.exe)** 已完成
构建与核验。主流程包含**连接 ChatGPT → 开始／结束 AI 聊天 → 审阅并保存私密画像
→ 预览并导出加密附件 → 打开双方文件 → 审阅私下 AI 相处比较**。首页与 AI 聊天均有
分享和比对入口。语音输入只加入可编辑草稿，不自动发送。原程序及此前构建依据均未改变。
打开步骤见[当前指南](../../../dist/START_HERE_CURRENT.md)。

本轮**尚未完成真实模型验收**。实际本地模型实验只使用虚构回答。Gemma 已生成提问、
独立保存画像并生成可导入的加密文件，但其比较把未知信息写成风险，并引用错误字段，
应用拒绝了结果。Qwen 3.5 多次违反必需的报告字段、覆盖说明，或返回不兼容的比较结构。
部分输出还把偏好加强为实际行为，或暗示用户曾成功实施。已安装的较大 Qwen 3.6 在返回
任何回答前遇到 CUDA 启动错误。失败的比较没有被接纳、自动修复、自动重试，也没有被
展示为可用 AI 结果。**尚未证明当前源码下完整、语义可接受的真实 AI 聊天至比较链路**。

已修复观察到的提示格式不一致：模型现在看到的最终格式，与经审阅请求交给解码器的
格式相同。单条短输入最多一条画像解读；存在解读时，覆盖说明不能为空。比较来源编号
对应一个双语字段，引文必须逐字匹配任一原始语言版本，缺失信息不能支持共同点、差异
或风险点。这些检查以及有限的“偏好变实际行动”检查，不能核验所有语义与翻译准确性。
失败模型记录保留为限制的证据，不能据此宣称通用模型质量已经达标。

### 已验证的实现与程序依据

- **2116 项测试通过，9 项因 Windows 链接权限跳过**，另有一条既有依赖弃用提醒。
  compileall、整个源码／桌面／测试范围的 Ruff 及差异检查通过。最终全量测试使用了
  已冻结的运行源码。
- 真实 Qt 测试用实际加密合成文件验证导出／导入、错误密码、篡改、双方许可、完整请求
  审阅、审阅期间变化、停止、迟到回复、资料库切换与导航。已检查中英文、940／1100
  像素窗口下的 44 张合成界面截图；也用 Computer Use 检查空合成目录中已打包程序的
  中英文欢迎页，随后关闭测试窗口。
- 最终程序匹配 **181 项运行文件哈希及 29 个关键嵌入模块**。JWT／加密、全部四个 Vosk
  原生 DLL 及两个 Qt 录音插件已包含并核对。脱离源码的启动检查加载了语音原生库并枚举
  设备，没有录音。语音模型仅在用户单独选择下载后安装。依据见
  [构建快照](../../../dist/PRIVATE_LOOP_BUILD_SNAPSHOT.json)与
  [校验和](../../../dist/PRIVATE_LOOP_SHA256SUMS.txt)。
- 已用 Computer Use 观察到真实账号页面与模型列表成功，包含 GPT-6-Astra、GPT-5.6-Sol、
  GPT-5.6-Terra、GPT-5.6-Luna 与 GPT-5.5。基于较轻量名称的默认建议是 GPT-5.6-Luna。
  此观察只发现账号模型，**没有进行 ChatGPT 推理**；速度、报告质量与套餐消耗尚未测量，
  额外积分确认当时未勾选。
- 真实英语离线识别将合成语音转写为“i need a little time to think”。固定版本的官方
  英语与中文模型均已下载、校验并加载，30 项语音测试通过。这台电脑枚举到**零个麦克风
  输入**，因此实体录音与中文口述识别质量仍未验证。

加密 `.slowmatch` 文件包含自选双语画像摘要、问题与限制，不含原始聊天、原文证据引证
或凭据，但叙述仍可能透露个人信息。导入只在内存中解密，不覆盖画像。由发送者用自己的
邮件应用附上文件，并另行告知密码；没有发送邮件。加密不能证明身份或契合程度。普通
本地聊天历史仍未加密。

### 你的操作与后续推进

请阅读 **[OWNER_REVIEW.md](../../../OWNER_REVIEW.md)**。下一步的重要操作是核对 ChatGPT
用量设置中此应用的额外积分已关闭、如实确认，再用真实账号模型测试虚构聊天、画像与
比较。设备录音验收需要连接麦克风；中文转写及实际回答质量需要你审阅。任何私密附件
交换前，先审阅共享摘要并取得双方许可。尚未自动联系他人、公开部署或匹配真实人员。

小时自动任务 `ai-slowmatch` 保持 **PAUSED**。交付这一具体审阅版本后，等待所有者
明确给出下一条指令。开发测试没有花钱、使用银行卡、调用付费 API、读取真实私人档案、
公开部署或发送消息。完整双语设计见[私密交换与语音](../../31_private_exchange_voice.md)。

---

# Historical status / 历史状态 — 2026-09-29

## English — conversation-first checkpoint

The owner's current product direction is a relationship copilot: reduce defensive
calculation, understand one's needs and ways of relating, and offer proportionate
behavior-based risk support. The first release now follows **Connect ChatGPT → AI
Chat → Start / End → Create my reflection → review → Save**. There is no market or
duration selection, and an empty local folder is sufficient. Prior import, manual,
local-model and matching experiments remain in **More tools**. The portrait Back
button now retains its navigation history through language changes.

The chat core asks one question at a time. End invalidates pending work immediately
and does not generate or save anything. A request already sent online may still be
processed; its late answer is discarded. Reflection generation and saving are
separate actions. Only this session's original typed words can support quotations;
AI questions are context, never evidence. All interpretations are provisional and
low confidence. Both languages are stored; the UI shows the selected language with
the original quotations before saving. Saved sessions have a separate history and
do not overwrite old reports. In-place editing, deletion and cross-session updating
of these new records are future work.

ChatGPT browser sign-in, PKCE, separately authorized plan access, protected app-owned
credentials and the provider adapter are implemented. Development uses synthetic
OAuth/response fixtures only. No real login, account eligibility or model quality
has been verified. This route does not read the ChatGPT desktop app or existing
conversations. The user must inspect ChatGPT Usage settings and disable this app's
extra credits before enabling chat; the app cannot enforce that remote setting.
No automatic fallback or retry is made. Opening the app or signing in does not infer.

The final regression gate passed **1889 tests**, with **eight Windows link-permission
skips** and one dependency deprecation warning. Compileall and Ruff pass. The rebuilt
`dist/AI-SlowMatch-Desktop.exe` passed startup outside the checkout in a temporary
synthetic home. Its 174 runtime hashes, 21 critical embedded modules and JWT/crypto
dependencies match the frozen source; the current guide matches the package. See
`dist/CONVERSATION_BUILD_SNAPSHOT.json` and `dist/CONVERSATION_SHA256SUMS.txt` for this
Desktop-only evidence. Earlier Web/wheel/source packages and their old snapshot are
preserved historical artifacts. Previous Desktop and guide bytes have a verified
backup. No actual model request is part of this checkpoint. See the complete bilingual
[product concept and research](../../30_conversation_first_product.md) and
[current opening guide](../../../packaging/GETTING_STARTED.md).

### Owner review before the next manually authorized cycle

1. Sign in through **Continue with ChatGPT**, inspect plan access and disable extra
   credits. Confirm that the account actually offers this app's requested allowance.
2. Try a short synthetic conversation first: review the outgoing text, Start/End,
   question quality, evidence and translations, and the portrait Back button. Decide
   whether the copilot feels useful and easy to stop.

The hourly automation remains paused. This checkpoint is authorized by the owner's
current request; after delivery it waits for the owner's review and explicit next
instruction. Public recruitment or deployment is outside this checkpoint. Local
saved files are ordinary, unencrypted files and sync folders may upload them.

## 中文版 — 聊天优先里程碑

当前产品方向是恋爱军师：帮助用户减轻防御性计算，了解自己的需要和相处方式，并根据
具体行为提供适度风险支持。第一版主流程现为**连接 ChatGPT → AI 聊天 → 开始／结束
→ 生成我的相处画像 → 审阅 → 保存**。无需选择市场或聊天时长，空本地文件夹即可开始。
原有导入、手动、本地模型及匹配实验保留在**更多工具**。画像返回键现能在语言切换后
保留导航历史。

聊天核心一次提出一个问题。结束会立即使待处理工作失效，不自动生成或保存；已经发往
在线服务的请求可能仍会被处理，但迟到回答会被丢弃。生成画像与保存是独立操作。引文
只能来自本次会话用户亲自输入的原话，AI 提问仅作背景，不是证据。所有解释均为低置信
的暂定理解。保存两种语言，界面按所选语言显示，并在保存前呈现原始引文。会话单独保存
为历史记录，不覆盖旧报告。新记录的原地编辑、删除与跨会话更新留待后续。

已实现 ChatGPT 浏览器登录、PKCE、独立套餐授权、受保护的本应用凭据及提供方适配器。
开发只用合成 OAuth／回复数据，未验证真实登录、账号资格或真实模型质量。此连接不读取
ChatGPT 桌面应用或既有聊天。启用前，用户须在 ChatGPT 用量设置中关闭此应用的额外
积分；应用无法强制核验远端开关。不自动切换连接或重试；打开应用或登录不会调用模型。

最终回归验收已有 **1889 项通过**，**8 项因 Windows 链接权限跳过**，另有一项依赖弃用
提示；compileall 与 Ruff 通过。重建的 `dist/AI-SlowMatch-Desktop.exe` 已在源码目录外、
临时合成主目录中通过启动检查。174 项运行源码哈希、21 个关键嵌入模块及 JWT／加密
依赖与冻结源码一致，指南也与安装包一致。本桌面版本的依据见
`dist/CONVERSATION_BUILD_SNAPSHOT.json` 和 `dist/CONVERSATION_SHA256SUMS.txt`。
先前 Web／wheel／源码包及旧快照作为历史产物保留，旧桌面程序及指南已有验证过的备份。
本里程碑没有真实模型请求。
详见完整双语[产品构想与研究](../../30_conversation_first_product.md)及
[当前打开指南](../../../packaging/GETTING_STARTED.md)。

### 下一轮人工授权前的审阅

1. 通过**继续使用 ChatGPT**登录，核对套餐授权并关闭额外积分，确认真实账号是否提供
   此应用所请求的额度。
2. 先用虚构内容聊一小段，检查发送内容、开始／结束、提问质量、画像引文与翻译，以及
   画像返回键，再判断军师是否有帮助、是否容易停止。

每小时自动任务保持暂停。本轮依据所有者当前请求推进，交付后等待审阅及明确的新指令。
公开招募或部署不属于本里程碑。本地文件仍未加密，同步文件夹可能将它们上传。

---

# Earlier checkpoint / 先前里程碑 — 2026-09-28

The following records refer to the previous implementation and package snapshot.
They are historical evidence, not validation of the new conversation-first build.
以下记录对应先前实现及安装包快照，作为历史依据保留，不代表新聊天版本已通过相同验证。

## English

Full current-format portrait/criteria regeneration passed the **1720-test gate**.
The owner selects saved corrections and pastes original excerpts, reviews the exact
local request, then separately confirms generation, saving and activation. Every quote
must occur exactly in its assigned excerpt; all claims remain low confidence. Complete
bilingual version 0.4 copies retain old warnings and an AI-regenerated/unverified notice.
Originals, cards and active selection stay unchanged. No evidence files are discovered
or opened. See [full regeneration and limits](../../27_full_report_regeneration.md).

Full regeneration now asks the model for each narrative's English and Chinese
together. The app copies both into the existing canonical/localization format,
then runs all original validators. It neither invents translations nor repairs
invalid replies. Exactly one reviewed local call remains; old prepared requests
require fresh review. Saved version 0.4 copies and other generation workflows keep
their existing contracts. See [paired generation](../../29_paired_report_generation.md).

Three real synthetic requests were made on the final paired implementation.
Qwen3.5's portrait reply omitted evidence and was rejected (8.56 seconds).
Installed `gemma4:latest` passed one portrait (15.70 seconds) and one criteria
sample (3.39 seconds), including exact per-source quotations, complete bilingual
mapping, separate saving/reopening and original/nonempty-selection preservation.
Manual inspection found narrow episode/preference claims and no invented candidates.
Translation still needs review: “asked” became “要求”, some phrasing was stilted,
and the English photos referent was ambiguous. This is limited real integration
acceptance, not general semantic certification. GUI checks used injected replies;
the real calls exercised the core smoke flow, not live GUI clicks.

Ten pre-change copies reopen with 154 file hashes unchanged. Both captured old
prepared requests reject before transport. The owned local service and runner
were stopped; no listener remains on port 11434. Earlier grammar/localization
failures and unproven large-model CUDA causes remain documented in
[the historical recovery record](../../28_local_model_recovery.md). Those failures
are not retroactively accepted by the new samples.

The earlier AI-assisted revision of one disputed claim supports exact request review,
explicit local generation, editable bilingual wording and separately confirmed
copies. Saved quotations stay unchanged; annotations remain context. AI attribution,
low-confidence speculation and source-version checks persist through saving and
selection. It does not regenerate a full report or verify original sources.
See [AI-assisted revision](../../26_ai_assisted_claim_revision.md).

One earlier real local `qwen3.6:latest` single-claim portrait sample passed generation, validation,
separate saving/reopening and exact original/selection preservation. Manual review
of the first response found frequency/intensity overreach; after tightening the
instructions, the second request took **29.75 seconds** and explicitly rejected a
pattern inference from one event. Two synthetic requests were made in total.
This is limited acceptance, not a general reasoning or translation guarantee;
that milestone's criteria drafting and UI transport tests used mocks.

The earlier small-window milestone passed 1193 tests. All 20 pages
keep the requested 940×700 or 1100×760 window in both languages. Each page scrolls
independently, keyboard focus reveals lower controls, consent wording stays complete,
export actions occupy rows and long status paths wrap without losing characters.
Ordinary navigation retains page objects, history and background workers. Existing
page reloads and language-rebuild draft limits remain. See
[window navigation](../../25_desktop_window_navigation.md).

Explicit profile layout migration remains available. Historical
root-level profile files now have literal preview and confirmation before exact-byte
copying into `profile/`. Originals remain; nonempty destinations and unsupported JSON
block copying. Cancel/error preserves the selected vault and draft. JSON inspection
has a separate read-only tab, preventing accidental Markdown replacement; switching
vaults no longer revives an absent companion from the old screen cache.
See [migration scope](../../24_profile_layout_migration.md).

The earlier partial legacy conversion remains available. Both report viewers
now copy only old claims with complete existing evidence, uncertainty and bilingual
wording into a separately confirmed report. Unsupported content stays exactly in
the linked archive; zero complete claims cannot become a successful report.
Saving never activates a copy. Separate selection enables the partial, unverified
report; explicit review-only mode disables references without a legacy fallback.
Originals and cards stay intact. Conversion reads no original evidence and calls no model.
Full legacy and personal-profile content migration remain unfinished.

Manual portrait/criteria handoffs now use the same generated schemas as connected
AI, with validated localization and deterministic bilingual rendering. Existing
request files need regeneration; a manual prompt cannot enforce isolation or writes.

Desktop/browser executables and the fresh wheel have been rebuilt and verified
outside the checkout. The new build contains 167 runtime source hashes and
161 exact wheel runtime files; final independent artifact checks are recorded below.
Full legacy conversion and personal-profile content migration remain unfinished.

### Usable local checkpoint

The existing architecture is preserved: PySide6 desktop, UI-independent core,
optional local browser application and experimental matching node. This is a
substantial local-product checkpoint, not completion of the entire roadmap or
approval for public matching.

- A real local **qwen3.5:latest** journey passed with fictional adult notes:
  connect → synthesize → validate → save/reload → fingerprint → adult registration
  → fingerprint-only attestation. After warm-up it took **4.11 seconds**. The
  initial thinking-only failure was repaired with local output controls. A real
  browser click test also generated, saved and displayed a Chinese model.
  Sparse-input testing exposed unsupported extrapolation and reused AI evidence;
  the repaired fresh-generation path uses original notes only. Final UI testing
  preserved unknowns, saved a new fingerprint and connected the default installed
  model without a download. This is one synthetic example, not a truth guarantee.
- Typed AI requests accept only data roles; imports and knowledge packs cannot
  enter system instructions. External sending requires an editable disclosure
  review per request, including destination and instructions. Cancellation sends
  nothing. Local transports enforce loopback, disable proxies/redirects and
  reject cloud routing, including the older structured-provider path.
- Desktop/core adapters are shared. CLI availability checks make no model calls;
  direct CLI vault access and resumed sessions are disabled. Unsupported CLI
  isolation fails closed. No paid API calls were used for this work.
- Reports/cards require valid structures, evidence and uncertainty before saving
  or hashing. Invalid output preserves old files. Legacy documents need explicit
  correction/regeneration before sharing under the new contract. The updated
  visual portrait renders evidence, sources, confidence and coverage gaps.
- Desktop self-portrait and criteria viewers now provide evidence review and
  persistent correction notes. Explicit saving retains an exact original JSON
  snapshot and separate annotation; stale versions are rejected and drafts survive
  refresh. Notes are not automatically applied to reports, exports or AI requests.
  Original-evidence and prior-report readers reject history aliases, hardlinks and
  Windows junctions. See [review history](../../18_report_review_history.md).
- Saved corrections can now drive a previewed withdrawal copy. Surviving claims
  retain their evidence and translations; dependent portrait findings or fictional
  criteria candidates are removed. Explicit confirmation saves exact source and
  correction snapshots with verified reports as one complete directory. Changed
  source/translation/note bytes invalidate the preview. Historical copies reopen
  after regeneration; original reports, cards and AI inputs remain unchanged.
  See [reviewed copies](../../19_reviewed_report_copies.md).
- Explicit report selection now binds a reviewed copy or the current generated
  report to its verified source version without changing original writer paths.
  Desktop viewers, browser desktop fallback and manual/interview references use
  that choice. Stale or damaged selections fail closed. A damaged copy can be
  deliberately deselected; a damaged journal requires separate recovery. A report
  change blocks continuing or saving an old interview; drafts and previous
  conversations survive an explicitly confirmed restart within the current window.
  See [active report selection](../../20_active_report_selection.md).
- **Rewrite one disputed claim** adds an explicitly user-authored EN/ZH proposal
  to a separate copy. Evidence, topic and group stay fixed; dependent findings or
  fictional candidates are removed and existing caveats preserved. Saving leaves
  originals, cards and active selection intact. Drafts survive stale errors, and
  refresh cannot silently retarget another claim. Version 0.1 withdrawal copies
  and new version 0.2 reinterpretation copies share verified history and selection.
  See [user-proposed reinterpretation](../../21_user_proposed_reinterpretation.md).
- **Review legacy files** preserves the fixed original report members and every
  unknown field under a separate immutable archive. Missing/invalid companions
  are diagnosed separately from the primary JSON shape. Literal original views
  do not execute HTML or links; non-UTF-8 data retains exact bytes. Preview binds
  presence and absence, rejects stale inputs and requires explicit confirmation.
  Archives verify every member on reopening and remain excluded from evidence.
  See [legacy report archives](../../22_legacy_report_archives.md).
- **Convert supported archived claims** adds a copied/archive-only field ledger,
  complete bilingual partial reports and explicit separate saving/selection.
  Existing warnings survive; absent evidence or translations are not supplied.
  Converted reports remain read-only, with correction tools targeting originals.
  A source change blocks use, but saved conversions remain readable as history.
  **Legacy review only** disables report references even when the target is damaged,
  provided the selection journal is intact. Resuming requires an explicit valid
  selection. See [conversion and limits](../../23_legacy_report_conversions.md).
- Matching requires explicit consent and adult age, bounds requests and beacons,
  rejects full cards at the node, and carries credentials in Authorization
  headers. Node instances are isolated and concurrent identity operations are
  guarded. Comparison/rehearsal separately require both-party purpose consent.
  These are declarations, not verified identity, age or source truth.
- The wheel now includes desktop/browser resources and launch commands. Clean
  sdist-to-wheel installation, installed Qt startup and loopback HTTP startup
  passed. Windows packaging repairs cover a conflicting ICU DLL and non-ASCII
  console output. Final desktop and browser EXEs passed copied-file startup tests
  outside the checkout; all 161 wheel runtime files match current source exactly.
  The frozen desktop includes all twenty-one required report/profile/navigation modules,
  including the full-regeneration contract, service and dialog. All 167 runtime
  source hashes are bound in the build snapshot.
  See [quickstart](../../../dist/START_HERE.md) and [build evidence](../../../dist/BUILD_SNAPSHOT.json).

### Verification

The paired-generation milestone adds 131 wire/projection cases, 18 independent
consumer integration cases and four old-wire/review rejection cases. Every narrative
path, exact evidence, language requirement and input/output limit is checked;
overflow rejects instead of dropping content. Ten historical copies across versions
0.1–0.4 and both old reviewed requests were independently checked. Eight current
styled GUI flows and two parent views passed; both-language request/preview images
were inspected. All GUI responses here are injected, separate from the three real
local model requests above.

The local recovery milestone adds 31 synthetic smoke tests, ten prompt-scope and
malformed-response regressions, and eight generation-grammar regressions. Longer
valid reports still parse/save/reopen without truncation; old prepared requests
cannot reuse consent after the generation schema changes. Final GUI checks reran
eight styled flows and two parent views; the coordinator inspected both-language
request screens. Eight pre-change copies across versions 0.1–0.4 reopen with all
114 file hashes unchanged. These checks are distinct from the nine real model
requests and their failures documented above.

Latest integrated synthetic suite: **1720 passed, 3 skipped** (233.11 seconds). Source compilation and
core/test/script lint passed, together with scoped desktop/packaging lint.
The three real-symlink tests were skipped because this Windows account lacks the
required privilege; real junction, hardlink and simulated reparse tests passed.
One upstream Starlette/httpx deprecation warning remains.
An additional all-desktop lint scan found six existing line-length findings in five
unrelated files; scoped checks for every desktop file changed this milestone passed.
Qt dialogs were exercised for approve/edit/cancel; the Chinese home was rendered
and visually inspected using a temporary home. No real vault was read or changed.

The earlier annotation milestone includes four-process and 16-thread concurrent
saves. The withdrawal-copy milestone covers four concurrent writer processes, recovery
in a fifth fresh process, eight threaded saves, exact translation reindexing,
withdrawal of all claims, unchanged originals, stale/tampered input, write failures
and preservation of existing uncertainty. Both report kinds passed EN/ZH GUI
flows and visual checks at 940×700 and 1100×760. The active-selection milestone
adds strict confirmation, concurrent/stale selection rejection, bounded journal
integrity, corrupt-copy recovery, consistent consumers and report-version checks
before/after mocked provider calls. GUI checks cover preserving drafts, discarding
stale replies, explicitly restarting interviews and reading earlier conversations.
Selection and interview screens passed EN/ZH visual checks at both sizes. After a
final history-text spacing correction, all 13 affected interview tests, compilation,
scoped lint and both-language history views passed again.

The reinterpretation milestone covers exact citations and mandatory attribution,
strict consent, tampering and source-version rejection, failed writes, four-thread
saves, mixed withdrawal/reinterpretation writes in four processes and recovery
in a fresh process. Two pre-change withdrawal copies were independently reopened
with every saved byte hash unchanged. All three histories passed 24 deterministic
directory-rename/path-safety cases after the concurrent listing repair. Both report
kinds passed EN/ZH preview/save/reopen and visual checks at 940×700 and 1100×760.
The legacy-archive milestone adds 52 core cases, 16 independent consumer cases,
a four-writer/fresh-reader process test, 14 GUI cases, six shared-schema manual
handoff regressions and eight new history interleavings. All four histories now
pass 32 deterministic race/path cases. Unknown and malformed content, exact
BOM/CRLF bytes, strict consent, source presence changes, tampering, bounded storage,
write failure and preserved originals/selection passed. Both report kinds passed
EN/ZH visual checks at 940×700 and 1100×760; four views were independently inspected.
The partial-conversion milestone adds 60 core cases, 47 selection cases, 13 GUI
cases, ten evidence-exclusion cases, a four-writer/fresh-reader process check and
eight history interleavings. Five history types pass 40 race/path cases. Both
report kinds passed EN/ZH preview/save/select/disable and visual checks at both
sizes; root independently inspected three views. Pre-change archives and version
0.1 selection records for both report kinds reopened with exact objects and every
byte hash unchanged. Version 0.2 selection events coexist without rewriting them.
Those archive/conversion iterations made no AI calls. Their mock results remain
separate from the new single-claim local sample above and the earlier full-chain
acceptance runs below.

Profile layout migration passed 76 core cases, including four competing writer
processes with one complete publication and fresh-process reopening. Focused GUI/store
checks passed 38 cases; profile viewing/cache checks passed 15 and migration-directory
evidence exclusion passed six. Tests cover BOM/CRLF preservation, strict schema and
confirmation, destination conflicts, stale/tampered sources, staged identity/byte
changes, failed publication, atomic pointer replacement and unchanged originals.
Migration dialogs fit 940×700 and 1100×760 under the real application styles in both
languages; the separate JSON view fits 940×700 with its Markdown save action disabled.

The global window-minimum defect is repaired. Eight navigation, eleven responsive
control and six actual MainWindow cases were added; the four existing process-level
worker-lifecycle regressions also pass. All 80 page/language/size combinations kept
the requested window dimensions. Checks cover keyboard focus, retained drafts during
ordinary return navigation, complete unchecked consent, all five export requirements,
literal long-path wrapping and language rebuilds. Five representative whole-window
views were independently inspected with application styles and registered existing
Windows fonts for offscreen rendering. Sizes are Qt logical pixels; other display
scales, native platforms and assistive-technology combinations remain unverified.

The AI-assisted revision milestone adds 38 core cases, a four-process mixed-format
save/fresh-reader test, 52 request-service cases, five independent consumer cases and
23 GUI cases. Four captured pre-change 0.1/0.2 copies reopened with all 53 file
hashes unchanged. Eight styled EN/ZH workflows at both sizes passed request review,
mocked generation, preview/save/reopen and unchanged originals/selection; four views
were independently inspected. A reproducible intermittent native Qt abort prompted
dialog-owned result/error slots and removal of the dialog from the worker closure.
Repeated-dialog checks assert UI-thread callbacks and settlement before deletion;
existing destructive worker-lifecycle regressions also pass. The precise original
native abort cause was not isolated. This milestone used synthetic data only.
The fresh-wheel smoke used an existing cache containing 44 wheels with package downloads
disabled, then checked resources, Qt startup, loopback HTTP and origin rejection.

The full-regeneration milestone adds 59 core cases, 93 request cases, five independent
consumer cases and 39 GUI cases, plus ten shared/single-claim policy regressions.
Six captured pre-change 0.1/0.2/0.3 copies reopen with all 74 file hashes unchanged.
Four processes can publish all four copy versions together; a fresh fifth process
verifies them. Both report kinds preserve old warnings/translations, enforce exact
per-source quotes and remain excluded from original-evidence discovery. Eight styled
EN/ZH flows and two parent-entry views fit the tested sizes; eight images were independently
inspected. A shared HTTP 400 schema fallback discovered during final review is now
explicitly disabled in both reviewed AI revision requests. Strict Boolean validation,
exact request binding and actual one-transport-call failures are covered; ordinary
requests retain their previous fallback behavior. Synthetic UI runs use mocked models.

After the final fix, rebuilt copied Desktop/Web executables and a fresh offline wheel
passed outside the checkout. Independent checks verified 167 runtime hashes, 161 exact
wheel files, all twenty-one required embedded modules and six artifact checksums. Nine
critical embedded module code objects match freshly compiled current source exactly,
including both request services, shared policy/adapter, report-bundle projection and full-copy UI/core.
The packaged bilingual guide and sdist README match source. No runtime changes followed
this acceptance; legacy artifacts and existing uncommitted work remain preserved.

The browser-side real local chain passed structurally. The earlier live desktop
portrait → interview → criteria chain passed strict schema, quotation and complete
localization-map checks with installed **qwen3.6:latest** in **74.03 seconds**, with
three requests and no retry. Deterministic rendering now creates both English and
Simplified Chinese reports from validated canonical fields. Manual review of this
synthetic sample found grounded claims, explicit gaps and no invented candidate
choices. Translation quality still needs review; one interview term was awkward.
The timing is one local run, not a benchmark. Qwen3.5 and Gemma4 had additional
desktop format failures, which were safely rejected. Native model grammar is not a
guarantee: application validation remains mandatory. Remote model calls, Linux
native GUI, macOS, public deployment and external-user usability remain unverified.

### Run locally

```powershell
.\.venv-rehab\Scripts\python.exe run_desktop.py
# Optional local browser interface:
.\.venv-rehab\Scripts\python.exe run_local_app.py
```

Choose Ollama and explicitly select an already installed local chat model. Availability
and earlier successes do not establish full-report reliability; review the
[current model limitations](../../28_local_model_recovery.md). Start Ollama
locally before connecting; the temporary service for this check was stopped afterward.
No model download or paid
service is required on this machine. Source-independent Windows executables live
in `dist/`: **AI-SlowMatch-Desktop.exe** is the main entry point and
**AI-SlowMatch.exe** is the optional browser client. See [packaging](../../../packaging/README.md).

Reproduce checks:

```powershell
.\.venv-rehab\Scripts\python.exe -m compileall src
.\.venv-rehab\Scripts\python.exe -m pytest -q
.\.venv-rehab\Scripts\python.exe -m ruff check src tests scripts
# Opt-in live tests use temporary synthetic vaults only:
.\.venv-rehab\Scripts\python.exe scripts/smoke_local_ai.py --model qwen3.5:latest
.\.venv-rehab\Scripts\python.exe scripts/smoke_desktop_ai.py --model qwen3.6:latest --timeout 600
.\.venv-rehab\Scripts\python.exe scripts/smoke_full_report_regeneration.py --kind self_portrait --model qwen3.5:latest --timeout 240
```

### Next autonomous work

1. Carry the simpler bilingual format into fresh desktop report generation where
   appropriate, then run a bounded real portrait → interview → criteria chain.
   Preserve fictional-exercise consent/provenance and reviewed single-call boundaries.
   Broader semantic/translation evaluation and the large-model CUDA cause remain open.
2. Continue full legacy and personal-profile content migration beyond the completed
   preservation, partial-conversion and layout-copy stages, without fabricating provenance.
   Current-format report regeneration from explicitly pasted excerpts is complete;
   broader legacy conversion must preserve unsupported content and uncertainty.
3. Implement a recoverable encrypted-storage option with synthetic recovery tests;
   add transparent retention/deletion controls including history snapshots. Do not
   automatically migrate real vaults or store recovery secrets in the repo.
4. Add browser report translation and a vault-session history restore interface.
5. Expand bilingual model/evidence evaluations, importers and interoperability.
   Matching federation and public use stay behind release review.

Vaults remain **plaintext**; sync folders may copy them through the sync provider.
A schema verifies shape, not truth or absence of harmful meaning. Prompt-role
separation is not a proof against all prompt injection. Local HTTP protection is
not OS-user authentication. Public matching still lacks production account
recovery, verified eligibility and a complete abuse-response system.

### Morning review

No approval is needed to continue local implementation or synthetic testing.
Important decisions are held for a concrete later review:

- Public release or inviting external testers: review the local package, privacy
  limitations and proposed adult, consent-based pilot before publication/contact.
- Migrating real vaults to encryption: review backup, recovery and rollback with a
  synthetic demonstration before changing personal files.

No money spent, payment data used, paid model call made, message sent, public
release created or personal data imported. Existing uncommitted work is preserved;
no broad staging/reset or commit was performed. The `ai-slowmatch` continuation
task is paused: it does not run on a schedule. After the owner explicitly confirms
continuation in this chat, it may work through the authorized local scope until a
complete reviewable milestone or an important owner decision. Details: [request boundary](../../17_reviewed_ai_requests.md),
[artifact contracts](../../local_artifact_contracts.md),
[matching protocol](../../matchmaking_protocol_hardening.md).

## 中文版

完整当前格式画像/择偶标准重新生成通过 **1720 项测试验收**。用户选择已保存更正，粘贴
原始摘录，审核准确的本地请求，再分开确认生成、保存与启用。每条引文必须逐字出现在
对应摘录内，全部主张保持低置信度。完整双语 0.4 副本保留旧警示及 AI 重新生成/未经核实
说明；原件、卡片和当前选择不变，不自动发现或打开证据文件。
详见[完整重新生成及限制](../../27_full_report_regeneration.md)。

完整重新生成现在让模型同时提供每个叙述字段的英文和中文。应用将其复制为既有规范
报告及翻译映射，再运行全部原有校验，不补造翻译，也不修补无效回复。仍然只执行一次
经过复核的本地调用，旧准备请求必须重新审核。已保存的 0.4 副本及其他生成流程保留
既有契约。详见[成对双语生成](../../29_paired_report_generation.md)。

最终成对实现共执行三次真实合成请求。Qwen3.5 画像回复缺失证据，被拒绝（8.56 秒）。
本机已安装的 `gemma4:latest` 分别通过一份画像（15.70 秒）和一份择偶标准（3.39 秒），
包括逐来源精确引文、完整双语映射、单独保存/重读，以及保留原件和非空当前选择。
人工检查确认主张限于所述事件和偏好，未虚构候选人。翻译仍需复核：“asked”译成了
语气较强的“要求”，部分措辞生硬，英文照片归属也存在歧义。这是有限真实集成验收，
不是普遍语义认证。界面检查使用注入回复；真实调用运行的是核心验收流程，并非真实
界面点击。

十份修改前的副本可正常重读，154 个文件哈希保持不变。两份捕获的旧准备请求均在传输前
被拒绝。自有本地服务和运行进程已停止，11434 端口无监听。此前语法/本地化失败及
未证实的大型模型 CUDA 根因保留在[历史恢复记录](../../28_local_model_recovery.md)中，
新样例不会追溯性地认定这些失败输出有效。

此前的一条争议主张 AI 辅助修订仍支持准确请求复核、明确本地生成、双语措辞编辑及单独确认
另存副本。已保存引文保持原样，批注只作背景；AI 归属、低置信度推测及来源版本检查贯穿
保存和选择。此流程不重新生成整份报告，也不核实原始来源。
详见[AI 辅助修订](../../26_ai_assisted_claim_revision.md)。

此前的真实本地 `qwen3.6:latest` 单条主张画像样例通过了生成、校验、另存/重读及精确保留原件/当前
选择。首次回复的内容检查发现频率/强度延伸；收紧指令后，第二次请求耗时 **29.75 秒**，
明确指出单个事件不能支持行为模式推断。共执行两次合成请求。这是有限样例验收，不保证
普遍推理或翻译质量；该里程碑的择偶标准起草及界面传输测试使用模拟。

此前的小窗口里程碑通过 1193 项测试。全部 20 个页面在中英文下均保持指定的
940×700 或 1100×760 窗口尺寸。各页面独立滚动，键盘焦点显示下方控件，同意文字完整保留，
导出操作分行排列，状态栏长路径折行且不丢字符。普通导航保留页面对象、历史及后台任务；
页面原有重新加载行为和切换语言重建时的草稿限制仍然适用。
详见[窗口导航](../../25_desktop_window_navigation.md)。

明确的个人档案布局迁移仍可使用。历史根目录档案现在先按原文
预览并确认，再逐字节复制到 `profile/`。保留原件，目标非空或 JSON 不受支持时阻止复制。
取消或失败保留当前档案库和草稿。JSON 在独立只读页显示，避免误覆盖 Markdown；切换
档案库后，缺失配套文件也不会再从旧界面缓存带回。详见[迁移范围](../../24_profile_layout_migration.md)。

此前的旧报告部分转换仍可使用。两个查看器仅将原本已有完整证据、
不确定性及双语表述的旧主张复制到另行确认的报告中。不支持内容精确保留在关联存档；
没有完整主张时不能保存为空壳成功报告。保存不启用副本，须另行选择，且报告明确为部分
内容、未经核实。仅复核状态会停用报告参考，不回退旧报告。原件和卡片保持不变；转换
不读取原始证据、不调用模型。完整旧格式及个人档案内容迁移仍未完成。

手动画像与择偶标准交接现使用与应用内 AI 相同的生成结构，要求校验翻译映射并确定性生成
双语报告。已有请求文件需要重新生成；手动提示词本身不能强制执行隔离或写入检查。

桌面、浏览器便携程序及全新 wheel 已重建并通过脱离源码验收。新构建包含 167 个运行源码
哈希及 161 个逐字节匹配的 wheel 运行文件，最终独立产物检查记录见下文。完整旧格式
转换及个人档案内容迁移仍未完成。

### 可用的本地检查点

保留现有架构：PySide6 桌面、与界面独立的核心、可选本地浏览器应用及实验性匹配节点。
这是一次实质性的本地产品推进，不代表整个路线图完成或已批准公共匹配。

- 真实本地 **qwen3.5:latest** 已使用虚构成年笔记跑通：连接 → 生成 → 校验 → 保存重读 →
  指纹 → 成年登记 → 仅指纹登记。预热后耗时 **4.11 秒**。最初只返回思考内容的问题已通过
  本地输出控制修复。实际浏览器点击测试也生成、保存并显示了中文模型。稀少输入测试发现
  无依据延伸与旧 AI 证据复用；修复后的全新生成只使用原始笔记。最终界面验收保留未知字段、
  保存新指纹，并成功连接默认已安装模型，无需下载。这只是一个合成样例，不保证内容真实。
- 类型化 AI 请求只接受数据角色；导入内容及知识包不进入系统指令。每次外发均须审核可编辑
  披露内容、接收方与指令，取消不会发送。本地传输强制回环地址、禁用代理与重定向，并拒绝
  云端路由，包括旧版结构化提供方路径。
- 桌面和核心共享适配器。CLI 检测不调用模型，不再直接访问档案库或续接旧会话；无法证实
  隔离能力的 CLI 会拒绝运行。本轮未调用付费 API。
- 报告与卡片在保存或哈希之前须通过结构、证据及不确定性校验。无效输出不会覆盖旧文件。
  旧文档须明确纠正或重新生成，才可按新契约分享。视觉画像已展示证据、来源、置信度及覆盖缺口。
- 桌面的自我画像和择偶标准查看器现提供证据复核与持久更正批注。明确保存后会保留完整原始
  JSON 快照和独立批注；拒绝过期版本保存，刷新时保留草稿。批注不会自动应用于报告、导出内容
  或 AI 请求。原始证据和旧报告读取器均拒绝历史别名、硬链接和 Windows 目录联接。
  详见[纠错历史](../../18_report_review_history.md)。
- 已保存的更正现可用于预览撤回副本。保留主张的证据和译文保持对应；移除可能依赖争议主张的
  画像一致性分析或虚构候选人。明确确认后，精确来源与更正快照及校验后的报告作为完整目录保存。
  来源、译文或批注字节变化会使预览失效。重新生成原报告后仍可打开历史副本；原报告、卡片及
  AI 输入均不改变。详见[复核副本](../../19_reviewed_report_copies.md)。
- 明确选择报告现将复核副本或当前生成报告绑定到经过校验的来源版本，不改变原始写入路径。
  桌面查看器、浏览器的桌面报告回退及手动/实时访谈参考均使用该选择。过期或损坏时停止使用；
  损坏副本可以明确取消选择，损坏的选择记录则须单独恢复。报告变化后，旧访谈不能继续或保存；
  明确确认重新开始后，草稿及先前对话仍保留于当前窗口。详见[当前报告选择](../../20_active_report_selection.md)。
- **改写一条争议主张**允许在独立副本中明确加入用户自行提出的中英文表述。证据、主题及
  分组固定保留；移除相关一致性发现或虚构候选人，保留原有警示。保存不改变原件、卡片或
  当前选择。版本失效会保留草稿，刷新不能悄悄改为另一条主张。0.1 版本撤回副本和新的 0.2
  版本重述副本共用经过验证的历史及选择流程。详见[用户提出的重述](../../21_user_proposed_reinterpretation.md)。
- **复核旧版文件**将固定报告原件及全部未知字段保留到独立不可变存档中。主 JSON 结构与
  缺失或无效配套文件分别诊断。原文视图不执行 HTML 或链接，非 UTF-8 数据保留精确字节。
  预览绑定文件存在及缺失状态，拒绝过期来源，保存要求明确确认；重读时校验每个成员，
  存档始终从原始证据中排除。详见[旧版报告存档](../../22_legacy_report_archives.md)。
- **转换归档中的完整主张**提供复制/仅存档字段清单、完整双语部分报告，以及明确分开的
  保存和选择操作。原有警示保留，不补造缺失证据或译文。转换只供阅读，更正工具仍针对
  原报告。来源变化会停止使用，但转换仍可作为历史打开。只要选择记录完整，即使目标
  损坏，也可通过**仅复核旧文件**停用报告参考；恢复时须明确选择有效报告。
  详见[转换与限制](../../23_legacy_report_conversions.md)。
- 匹配强制同意与成年年龄，限制请求和信标大小，节点拒绝完整卡片，凭据通过 Authorization
  请求头传输。节点实例相互隔离，并发身份操作受保护。比较和演练另须确认双方同意该用途。
  这些均为声明，不代表身份、年龄或来源真实性已被核验。
- wheel 现包含桌面、浏览器资源和启动命令。干净环境中的 sdist → wheel 安装、Qt 启动及
  回环 HTTP 启动通过。Windows 打包已修复 ICU DLL 冲突与非 ASCII 控制台输出问题；最终
  桌面和浏览器 EXE 均通过脱离源码目录的独立启动检查，wheel 中 161 个运行文件与当前源码
  逐字节一致。独立桌面程序包含全部二十个必需的报告/档案/导航模块，包括完整重新生成契约、
  服务及界面；167 个运行源码哈希绑定在构建快照中。
  参阅[使用指南](../../../dist/START_HERE.md)及[构建证据](../../../dist/BUILD_SNAPSHOT.json)。

### 验证

本地恢复里程碑新增 31 项合成验收脚本测试、十项提示词范围及错误回复回归，以及八项
生成语法回归。较长的有效报告仍可完整解析、保存和重开，不发生截断；生成结构变化后，
旧准备请求不能复用确认。最终界面检查重新运行八组实际样式流程及两个父窗口视图，
主代理检查了两种语言的请求页面。八份修改前的 0.1–0.4 副本可正常重读，114 个文件
哈希全部不变。这些合成检查与上文九次真实模型调用及失败结果分开记录。

成对生成里程碑新增 131 项回复格式/转换检查、18 项独立消费者集成检查及四项旧格式/
旧请求拒绝检查。全部叙述路径、精确证据、语言要求及输入/输出上限均有覆盖；超限时
拒绝，不丢弃内容。十份 0.1–0.4 历史副本及两份旧复核请求经过独立验证。八组当前实际
样式界面流程及两个父窗口视图通过，两种语言的请求/预览图像已经检查。界面回复均为
注入数据，与上文三次真实本地模型请求分开记录。

最近一轮综合合成测试：**1720 项通过、3 项跳过**（233.11 秒）。源码编译、核心/测试/脚本静态检查及专项
桌面/打包静态检查均通过。三项真实符号链接测试因当前 Windows 账户缺少相应权限跳过；
真实目录联接、硬链接及模拟重解析路径测试通过。仍有一条上游 Starlette/httpx 弃用提示。
额外的全桌面静态扫描在五个无关文件中发现六处既有行长度问题；本轮修改的全部桌面文件
均通过专项检查。
Qt 对话框已测试
审核、编辑、取消；中文主页在临时主目录中渲染并进行了视觉检查。未读取或修改真实档案库。

先前批注里程碑覆盖四进程与 16 线程并发保存。撤回副本里程碑覆盖四个独立写入进程、
第五个新进程恢复、八次线程并发保存、精确译文重排、撤回全部主张、原件不变、过期或被改动的
输入、写入失败，以及原有限制说明不被丢弃。两种报告均通过中英文界面流程，且在 940×700
和 1100×760 下完成视觉检查。当前报告选择里程碑新增严格确认、拒绝并发或过期选择、有界
记录完整性、损坏副本恢复、一致的读取行为，以及模拟提供方调用前后的报告版本检查。
界面检查覆盖保留草稿、丢弃过期回复、明确重启访谈及读取先前对话；选择与访谈界面在上述
两种尺寸下通过中英文视觉检查。最后修正历史文字间距后，13 项相关访谈测试、编译、专项
静态检查及两种语言的历史视图再次通过。

重述里程碑覆盖精确保留引文、强制归属、严格同意、拒绝篡改及来源版本变化、写入失败、
四线程保存、四进程混合保存撤回与重述副本，以及新进程恢复。两份修改前保存的撤回副本均
独立重读成功，全部已保存字节哈希保持不变。并发读取修复后，三种历史通过 24 项确定性的
目录重命名与路径安全测试。两种报告在 940×700 和 1100×760 下通过中英文预览、保存、重读
及视觉检查。

旧版存档里程碑新增 52 项核心测试、16 项独立消费者测试、四个写入进程及新读取进程测试、
14 项界面测试、6 项手动交接共享结构回归及 8 项历史时序测试。四种历史共通过 32 项确定性
时序/路径检查。未知或坏格式内容、精确保留 BOM/CRLF、严格同意、文件存在状态变化、篡改、
存储上限、写入失败和原件/当前选择不变均已验证。两种报告均通过 940×700 和 1100×760
下的中英文视觉检查，四个视图另行独立复核。

部分转换里程碑增加 60 项核心、47 项选择、13 项界面、10 项证据排除测试，四写入进程/新
读取进程检查及 8 项历史时序检查。五种历史共通过 40 项时序/路径测试。两种报告均通过
两种尺寸下的中英文预览、保存、选择、停用及视觉检查，主代理独立查看三个视图。两种
报告在修改前保存的存档及 0.1 选择记录均重读成功，完整对象与每个字节哈希不变；新的
0.2 选择事件与旧记录共存，不改写历史。上述存档/转换迭代没有调用 AI；其模拟结果与
上方本轮单条主张本地样例、下方先前完整链路验收分开记录。

个人档案布局迁移通过 76 项核心检查，包括四个独立写入进程竞争、只发布一份完整目录及
新进程重读。专项界面/存储检查通过 38 项，档案查看/缓存检查通过 15 项，迁移目录证据
排除通过 6 项。覆盖 BOM/CRLF 保留、严格结构与确认、目标冲突、过期/篡改来源、暂存
身份/字节变化、发布失败、原子替换档案库指针和原件不变。实际应用样式下，中英文迁移
窗口适配 940×700 与 1100×760，独立 JSON 页适配 940×700，且 Markdown 保存操作禁用。

全局主窗口最小尺寸问题已修复。新增 8 项导航、11 项响应式控件及 6 项真实 MainWindow
测试；原有四项进程级后台任务生命周期回归也通过。全部 80 种页面/语言/尺寸组合保持
指定窗口大小。检查覆盖键盘焦点、普通返回导航保留草稿、完整且默认未勾选的同意文字、
导出五项必需确认、纯文本长路径折行及语言重建。主代理独立查看五张代表性整窗截图，
使用实际应用样式，并为离屏渲染注册已有 Windows 字体。尺寸为 Qt 逻辑像素；其他显示
缩放、原生平台和辅助技术组合仍未验证。

AI 辅助修订里程碑新增 38 项核心检查、一项四进程混合格式保存/新进程重读检查、52 项
请求服务检查、5 项独立消费者检查及 23 项界面检查。修改前捕获的四份 0.1/0.2 副本均能
重读，53 个文件哈希全部不变。两种尺寸下的八组实际样式中英流程通过请求复核、模拟
生成、预览/保存/重读及原件/当前选择不变检查；四张视图另行独立检查。复现到一次偶发
原生 Qt 中止后，将结果/错误回调改为窗口持有的槽，并从后台闭包中移除窗口对象。连续
窗口检查验证回调处于界面线程，删除前后台任务已收尾；既有破坏性后台生命周期回归也
通过。原始原生中止的唯一原因尚未确定。本轮仅使用合成数据。
全新 wheel 检查在禁用包下载的条件下使用包含 44 个 wheel 的已有缓存，再检查资源、Qt 启动、
回环 HTTP 及来源拒绝边界。

完整重新生成里程碑新增 59 项核心、93 项请求、5 项独立消费者及 39 项界面检查，另加十项
共享/单条主张请求策略回归。六份修改前的 0.1/0.2/0.3 副本均能重读，74 个文件哈希全部
不变。四进程可以同时提交四种副本版本，第五个新进程验证读取。两类报告均保留旧警示及
译文、逐来源检查精确引文，并继续排除在原始证据发现之外。八组实际样式中英流程及两个
父窗口入口视图均适配测试尺寸；主代理独立检查八张图片。最终复核发现共享适配器的
HTTP 400 结构降级重试，现已在两种经过审核的 AI 修订请求中明确关闭。测试覆盖严格布尔
校验、准确请求绑定及真实传输分支的一次调用失败；普通请求保留原有降级行为。合成界面
运行使用模拟模型。

最终修正后的桌面/浏览器独立程序及离线全新 wheel 均通过脱离源码验收。独立检查确认
167 个运行哈希、161 个精确 wheel 文件、全部二十一个必需嵌入模块和六项产物校验和。
九个关键嵌入模块的代码对象与当前源码重新编译结果完全一致，包含两种请求服务、共享
策略/适配器、报告生成结构及完整副本界面/核心。包内双语指南和 sdist README 均与源码一致。此验收
之后未改动运行源码；旧产物和已有未提交工作均予保留。

浏览器端真实本地链路通过结构验证。此前真实桌面「画像 → 访谈 → 择偶标准」链路已由本机
**qwen3.6:latest** 在 **74.03 秒**内通过严格结构、引文及完整本地化映射检查，三次请求，
没有重试。确定性渲染现从已校验的规范字段生成完整英文和简体中文报告。该合成样例的人工
审阅确认了有依据的陈述、明确的信息缺口，未发现虚构候选选择。翻译仍须审阅，其中一个
访谈用词欠妥。该耗时仅为一次本机运行，不是性能基准。Qwen3.5 和 Gemma4 的桌面输出
还出现了格式失败，均被安全拒绝。模型侧语法约束不是保证，
应用校验仍属必需。远端模型、Linux 原生界面、macOS、公共部署及外部用户可用性尚未验证。

### 本地运行

```powershell
.\.venv-rehab\Scripts\python.exe run_desktop.py
# 可选本地浏览器界面：
.\.venv-rehab\Scripts\python.exe run_local_app.py
```

选择 Ollama，并明确指定本机已经安装的聊天模型。可连接或过去成功的样例不代表完整
报告可靠，请阅读[当前模型限制](../../28_local_model_recovery.md)。连接前先启动本地 Ollama；
本轮检查用的临时服务已在检查后停止。本机无需下载模型或购买服务。独立 Windows 程序位于 `dist/`：主入口为
**AI-SlowMatch-Desktop.exe**，可选浏览器客户端为 **AI-SlowMatch.exe**。
参阅[打包说明](../../../packaging/README.md)。

复现检查：

```powershell
.\.venv-rehab\Scripts\python.exe -m compileall src
.\.venv-rehab\Scripts\python.exe -m pytest -q
.\.venv-rehab\Scripts\python.exe -m ruff check src tests scripts
# 主动运行真实测试，仅使用临时合成档案库：
.\.venv-rehab\Scripts\python.exe scripts/smoke_local_ai.py --model qwen3.5:latest
.\.venv-rehab\Scripts\python.exe scripts/smoke_desktop_ai.py --model qwen3.6:latest --timeout 600
.\.venv-rehab\Scripts\python.exe scripts/smoke_full_report_regeneration.py --kind self_portrait --model qwen3.5:latest --timeout 240
```

### 下一阶段自主工作

1. 在适用的全新桌面报告生成流程中复用较简单的双语格式，再运行有限范围的真实
   画像 → 访谈 → 择偶标准链路。保留虚构练习的同意/来源约束，以及经复核的单次调用
   边界。更广泛的语义/翻译评估和大型模型 CUDA 根因仍待完成。
2. 在已完成的原文保留、部分转换及布局复制之外，继续完整旧格式和个人档案内容迁移，不补造缺失的来源。
   从明确粘贴的摘录重新生成当前格式报告已完成；更广泛旧格式转换须保留不支持内容和不确定性。
3. 实现可恢复的加密存储选项并以合成数据测试恢复；增加包含历史快照的透明保留/删除控制。
   不自动迁移真实档案，不将恢复秘密写入仓库。
4. 增加浏览器报告翻译，以及按档案恢复会话历史的界面。
5. 扩展双语模型与证据评估、导入器及互操作。匹配联邦和公共使用保留发布审核。

档案库仍是**明文**，同步目录可能经同步提供方复制。Schema 只能验证结构，不能保证内容
真实或无有害含义；消息角色隔离不能证明免疫所有注入；本地 HTTP 保护不等于操作系统用户
身份认证。公共匹配仍缺少生产级账户恢复、资格核验和完整的滥用响应机制。

### 明早审阅

继续本地实现和合成测试无需审批。重要决定留待具体方案备妥后审阅：

- 公共发布或邀请外部试用者：先审阅本地安装包、隐私限制和成年人自愿试用方案，再发布或联系。
- 真实档案迁入加密存储：先以合成演示审阅备份、恢复与回滚方案，再修改个人文件。

未花钱、未使用支付信息、未调用付费模型、未发送消息、未公开发布，也未导入个人数据。
保留所有已有未提交改动，未整体暂存、重置或提交。`ai-slowmatch` 继续任务现已暂停，
不会按计划自动运行；仅在所有者在本聊天明确确认继续后，才会在已授权的本地范围内推进，
直到形成完整可审阅里程碑或需要重要人工决定。详见[请求边界](../../17_reviewed_ai_requests.md)、
[产物契约](../../local_artifact_contracts.md)及[匹配协议](../../matchmaking_protocol_hardening.md)。
