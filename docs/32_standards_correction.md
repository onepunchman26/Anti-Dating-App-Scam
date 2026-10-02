# Implemented correction / 已实施整改

## English

The approved product stays in the existing Python engine and PySide6 interface.
`ReflectionChatService` owns sessions, source binding, validation and history;
`RelationshipMemory` owns approved annotations; exchange/comparison services own
consent and schema-valid encrypted summaries. GUI screens only coordinate these services.

The ChatGPT adapter keeps its legacy string-returning interface and adds a typed
result with requested model, reported model, response ID and token usage. Missing
or different reported IDs are explicitly distinguishable; aliases are not relabelled
as upgrades. Model preferences are separate non-secret files scoped to an app
registration; no authorization tokens or billing consent are stored there. The server's
October 2 catalog includes GPT-6-Astra, GPT-5.6-Sol/Terra/Luna and GPT-5.5, not GPT-6.1.
Another app's model list is not evidence of availability to this registration.

Inference uses the official OAuth-authorized Responses endpoint, `store:false`,
streaming, exact reviewed disclosure and no automatic retries. Completed output items
are accumulated by identity and index; a terminal `response.completed` is still
required. Empty terminal output is accepted only with completed text items that match
the streamed deltas. Partial, changed, failed or incomplete output is rejected.
This fixes a real observed stream shape; it does not turn partial text into a success.
[Official model/inference guide](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference).

The consumer has a total deadline and independent stop event. Two bounded daemon
readers at most handle blocking sockets; each owns its connection and an eight-event
queue. Windows socket shutdown is attempted, but UI cancellation never waits for it.
If old connections still occupy both slots, a new request fails clearly without retry.
End invalidates service requests and UI callbacks; a later response cannot overwrite
another session or its controls. Safe error categories contain no provider body.

The coaching contract is a useful bilingual reply plus an optional single follow-up.
Quoted suggested wording may contain a question. Recent AI replies retain links to
the adjacent user source IDs and are context only. Portraits still cite exact original
current-session statements, retain low confidence and distinguish preferences from behavior.

### Evolving personal model (0.3.0)

The authoritative bilingual [conversational Skill v2](../src/anti_dating_scam/skills/relationship-reflection/SKILL.md)
is loaded with `importlib.resources`, injected into actual chat requests and packaged
with the EXE. Editing an installed personal skill cannot change it. Protocol schemas
and deterministic access checks remain in the core. There is no separate database.

`personal_model.py` validates proposals, exact source quotes, existing targets and
qualitative uncertainty. Self-reports/preferences/events remain unverified reports;
interpretations/patterns/open questions are tentative hypotheses with alternatives.
The model can propose at most three candidates per accepted reply. A pattern requires
multiple supporting accounts; semantic quality still needs model judgment and review.
Malformed updates are discarded with an explicit unavailable status while a valid
conversational reply survives. Missing/invalid chat content is not fabricated.

The existing `.relationship-memory/state.json` accepts legacy v1 files and writes v2
only on explicit changes. It holds at most 20 entries (250 characters each), their
context/basis/uncertainty, up to three exact quotes, origin, review state, dates and
dependency IDs. No raw conversation or audio is silently copied into this model.
Rejected stored hypotheses remain visible but are excluded from recall; rejecting a
new candidate keeps only a content-free operation receipt. Approving a candidate
explicitly covers its quoted evidence. Closing the review makes no change.

Recall uses local English-word/Chinese-bigram overlap, at most four relevant notes.
Opening orientation uses at most two recent preferences/goals/boundaries. This bounded
method may miss paraphrases; it is not semantic vector search. Only retrieved notes
and their provenance enter the exact outgoing review. No private archive is discovered
or imported, and memory never becomes evidence for a new standalone portrait.

Opt-in and session-only mode are enforced by the service, not just the prompt. The
store is isolated by canonical selected folder. Revision checks, a cross-process lock,
atomic replacement and operation receipts prevent lost updates or retry duplicates.
An old approval cannot resurrect a deleted entry; identical text in a new session
also does not create a second entry. Changed text still requires a new review.

Correction, question, rejection or deletion removes dependent interpretations
transitively. AI hypotheses conservatively depend on all retrieved notes, even if the
model omits a dependency. A store revision invalidates pending responses, candidate
batches and prior assistant context. Earlier current-session user turns become
ineligible evidence for new proposals. They remain visible conversation context until
the session is replaced; deleting a model entry does not erase that conversation.
There is no hidden retrieval index, memory importer or automatic private backup.
History is bounded to 100 ID/action records and 200 content-free operation receipts;
removed text is not retained in an undo log.

Pause/revoke excludes notes from future requests. Export is explicit and cannot
replace an existing file. Local notes and separately saved chat/portrait files are
unencrypted. Model deletion cannot erase earlier cloud disclosures, independently
saved reports/transcripts, exports, OS/OneDrive backups or files a person restores
outside the app. Manage those copies separately; the app never auto-restores them.
Development backup/publishing excludes all private stores and recordings.

### Voice and failure handling

Existing local Vosk transcription still produces an editable draft; sending remains
manual. Raw audio stays ephemeral. Voice input sets a short-response mode in the
cloud request. Optional **Read latest reply** uses Qt's installed offline OS voice;
Stop, a new Send, Voice input, End and leaving the page stop it immediately. Missing
language/audio devices or engine failure preserves text and shows a fallback message.
Qt's mock engine and online/paid voices are not product fallbacks. Windows packaging
includes the QtTextToSpeech module and SAPI plugin; macOS packaging is not verified.

A failed request keeps the user's turn and offers an explicit reviewed retry; there
is no automatic remote retry or silent model replacement. A reply arriving after
End, a memory revision or a new session is discarded. Synthetic regression coverage
includes competing updates, cross-user rejection, exact-quote checks, cascaded
changes, malformed candidates, opt-out, retries and speech interruption.

The new live evidence is [the synthetic cloud receipt](evidence/2026-10-02-evolving-model.json).
It records successes and the unclassified failed follow-up honestly. Actual English
Vosk recognition of generated synthetic speech passed. The test machine reports no
microphone, one output device, and English/Spanish SAPI locales only. This does not
verify physical capture, spoken Chinese or audible playback quality.

The installed goutoujunshi skill was backed up and fast-forwarded to
`6db7354a4002dc7c448a9c87ffdad8132570c9d3` (MIT). Only reviewed principles from its
core, evidence-boundary, communication/repair and consent-aware memory guidance inform
the app-owned policy. No questionnaires, scores, gender calibration, automatic memory
scripts or ChatLab imports are loaded. The legacy optional web coach also uses the
pinned app policy rather than reading mutable installed skill text. MIT notices are
bundled and visible in About. Pi's reviewed `0.99.2` source at
`8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d` informed interfaces only; no Node runtime was added.

The fixed EXE's release gates and recovery are described in [packaging](../packaging/README.md).
Owner docs are now separated by role; superseded full documents live under `history/`.
Real model and physical microphone acceptance remain distinct from deterministic tests.

## 中文版

批准后的产品继续使用现有 Python 引擎和 PySide6 界面。`ReflectionChatService` 管理会话、
来源绑定、校验及历史；`RelationshipMemory` 管理已批准备注；交换／比较服务负责同意和
满足结构约束的加密摘要。界面只负责协调服务。

ChatGPT 适配器保留原有字符串接口，同时提供包含请求模型、返回模型、回复编号及用量的
类型化结果。缺失或不一致的返回标识可以明确区分，不把别名改称“升级”。模型偏好另存于
按应用注册隔离的非敏感文件，不包含授权令牌或费用确认。10 月 2 日的服务器目录实际包含
GPT-6-Astra、GPT-5.6-Sol／Terra／Luna 和 GPT-5.5，不包含 GPT-6.1。另一应用的列表不能
证明本注册具有相同模型权限。

推理使用官方 OAuth 授权的 Responses 端点，设置 `store:false`、流式返回、精确披露审核，
不自动重试。按标识与位置收集完成的输出条目，仍必须收到最后的 `response.completed`。
末尾正文为空时，只接受已完成且与增量文本一致的文本条目，拒绝部分、变化、失败或未完成
输出。这修复了真实观察到的返回格式，并没有把部分文本当成成功。
[官方模型及推理指南](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)。

接收方有总截止时间和独立停止信号，最多两个后台线程各自处理一个连接及最多八事件队列。
会尝试关闭 Windows 套接字，但取消界面不等待其完成。两个旧连接均未退出时，新请求明确
失败，不自动重试。结束会同时使服务请求与界面回调失效，迟到结果不能覆盖另一会话或按钮
状态。安全错误分类不包含提供方原始正文。

军师输出为有效双语回应，加最多一个可选追问；建议发送的话术内部可以带问号。近期 AI
回复关联前后用户来源编号，只作为背景。画像仍只引用当前会话用户的准确原话，保持低置信度，
区分偏好与真实行为。

### 持续个人模型（0.3.0）

唯一权威的双语[对话 Skill v2](../src/anti_dating_scam/skills/relationship-reflection/SKILL.md)
由 `importlib.resources` 加载，真正注入聊天请求并随 EXE 打包。修改外部个人 skill 不会改变它。
协议结构及确定性访问检查仍由核心负责，没有第二套数据库。

`personal_model.py` 校验候选、准确引文、现有目标及定性不确定性。自述／偏好／事件都是
未经独立核实的报告；解释／模式／开放问题是带其他可能的暂定假设。每次有效回复最多提出
三条候选；模式须有多次报告支持，但语义质量仍需模型判断及人工审核。无效候选会被丢弃，
明确显示评估不可用，同时保留有效的聊天回复；不会捏造缺失或不合格的聊天内容。

现有 `.relationship-memory/state.json` 兼容 v1，仅在明确变更时写入 v2。最多 20 条，
每条正文 250 字，保存情境／依据／未知、最多三处原话、来源类别、审核状态、日期及依赖编号。
不会把整段对话或音频暗中复制进模型。拒绝已存假设后仍可查看，但不再召回；拒绝新候选
只留无正文的操作记录。批准候选也明确涵盖其中引文，关闭审核不产生更新。

召回采用本地英文词／中文双字重叠，最多四条相关记忆；开场最多两条近期偏好／目标／边界。
这种有限方法可能漏掉同义表达，不是语义向量检索。仅检索结果及其来源进入发送审核，
不发现或导入私人档案；记忆也不会成为另行生成画像的新证据。

主动启用及仅本次会话由服务执行，不只靠提示词。按实际选定文件夹隔离存储，使用版本检查、
跨进程锁、原子替换及操作凭据防止覆盖和重试重复。旧批准不能复活已删条目，跨新会话的
相同文字也不会生成第二条；改变措辞仍需重新审核。

纠正、质疑、拒绝或删除会逐级移除依赖解释。即使模型漏写依赖，AI 假设也保守地依赖全部
已检索记忆。存储版本变化使在途回复、候选批次及旧 AI 背景失效；当前会话的更早用户轮次
不能再为新候选提供证据，但直到替换会话之前，它们仍是可见对话背景。删除模型条目不是
删除该对话。没有隐藏检索索引、记忆导入或自动私人备份。历史最多 100 条编号／动作及
200 条无正文操作记录，不在撤销日志保留已删文字。

暂停／撤销后不向未来请求提供记忆。导出须明确操作且不覆盖文件。本地记忆及另行保存的
聊天／画像文件未加密。删除模型无法抹除此前云端披露、独立保存的报告／转录、导出、系统／
OneDrive 备份，或人从应用之外恢复的文件；这些副本须分别管理，应用不自动恢复它们。
开发备份和源码发布排除全部私人存储与录音。

### 语音与失败处理

现有本地 Vosk 转写仍先形成可编辑草稿，手动发送，原始音频临时存在。语音输入会在云端
请求启用简短回应模式。可选的**朗读最新回复**使用 Qt 已安装的离线系统声音；停止、新发送、
语音输入、结束和离开页面均立即停止。缺少对应语言／音频设备或引擎失败时保留文字并提示。
不以 Qt 模拟引擎或联网／付费声音替代。Windows 包核验 QtTextToSpeech 和 SAPI 插件；
macOS 打包未验证。

失败请求保留用户轮次，提供需重新审核的手动重试；不自动联网重试，也不暗换模型。
结束、记忆变更或新会话之后抵达的回复会被丢弃。合成回归覆盖并发、跨用户拒绝、准确引文、
联动变更、不合格候选、退出、重试及停止朗读。

新增真实依据见[云端合成样本记录](evidence/2026-10-02-evolving-model.json)，如实记录成功
及一次未归因的后续失败。真实英文 Vosk 已识别生成的合成语音。测试机器没有麦克风、
有一个输出设备，SAPI 仅装英语／西语；这不能证明实体采集、中文口述或可听朗读质量。

已备份并快进更新 goutoujunshi skill 至 `6db7354a4002dc7c448a9c87ffdad8132570c9d3`
（MIT）。仅将审阅过的核心、证据边界、沟通修复及经同意记忆原则融入应用自己的策略。
不加载问卷、分数、性别校准、自动记忆脚本或 ChatLab 导入。旧可选网页军师也改用固定策略，
不读取随安装更新而变化的 skill 内容。MIT 许可随程序打包，并在“关于”中展示。
审阅的 Pi `0.99.2`，提交 `8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d`，仅用于借鉴接口，
未新增 Node 运行环境。

固定 EXE 的检查及恢复见[打包说明](../packaging/README.md)。所有者文档按职责整理，完整旧版
保存在 `history/`。真实模型和实体麦克风验收始终与确定性测试分开记录。
