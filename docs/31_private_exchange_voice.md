# Private relationship reflections, exchange and voice / 私密相处画像、交换与语音

## English

This document preserves the September 30 design and observations. Current 0.3.0
implementation, memory and live-test evidence are in [the architecture update](32_standards_correction.md)
and [current handoff](../CURRENT_STATUS.md); they supersede historical verification gaps below.

### Product intent

AI-SlowMatch helps a person understand how they relate to others, discuss an
appropriate relationship at their own pace, and notice concrete risks. The AI
acts as a relationship companion: it asks thoughtful questions, remembers the
user's explicitly supplied answers within the app, reflects uncertainty, and
helps prepare a respectful next conversation. The person decides what to share,
whom to meet and whether to continue. Public personality scores, ranked people,
automatic judgments of character and swiping through a catalogue are outside
this product design.

The intended loop is **Connect ChatGPT → Start a conversation → Answer or skip
questions → End whenever desired → Review a tentative self-reflection → Choose
what to share → Privately discuss another person's chosen reflection → Decide
together whether to continue**. Starting and ending are immediate user actions.
There is no required market, timed interview or prompt configuration before
chatting. Later comparisons should produce discussion points, boundaries,
unknowns and possible tensions; they should support a human decision instead of
claiming that two people will be compatible.

### ChatGPT connection and model choice

The actual app observation on 30 September 2026 showed a signed-in state with the
extra-credit confirmation still unchecked. This establishes that the observed
screen considered the account connected. It does **not** establish that a model
request completed, that its answers were suitable, or that credits were disabled
on the server. The earlier lack of a visible next step should not be described
as proven OAuth failure.

The updated connection screen distinguishes account connection, permission to
use the ChatGPT plan, loading the account's model list, and readiness to begin
AI Chat. The success badge confirms the account stage. Model discovery uses the
signed-in account's actual catalog and does not run sample inference. The user
can see available choices before confirming the extra-credit setting, choose a
model, and then explicitly enable chat. Connecting an account alone does not
activate a backend or send an interview to a model.

The suggested default comes only from models actually returned to this account.
A name containing mini, nano, small or luna is a heuristic for a lighter model;
catalog ordering provides the fallback among general choices. Actual speed,
allowance consumption and support for portrait structured output remain
unverified. The picker must keep the other account choices available. An empty
catalog or catalog error keeps the account-success state visible and prevents
the app from claiming it is ready to chat.

OpenAI controls eligibility, app limits and credit use. The app cannot enforce
an included-plan-only billing policy through a documented inference parameter.
The user must inspect [ChatGPT Usage settings](https://chatgpt.com/settings/usage),
disable extra credits for this app, and explicitly confirm that action before
activation. Discovery and local UI tests do not provide that confirmation. See
the official [model and inference contract](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
and [usage guidance](https://developers.openai.com/siwc/ui-ux-guidelines).

### A selected reflection for a private exchange

The exchange core prepares a summary from one explicitly selected, separately
saved reflection. It includes at most five tentative statements about values,
needs, communication or boundaries, plus open questions, unknowns and caveats.
Both language versions travel together. The packet marks its origin as an AI
interpretation of self-report, keeps confidence low, and states that authorship
and relationship claims are unverified.

The selected packet excludes chat transcripts, original quotations, account
credentials and saved history. Narrative text can still reveal personal
information, so the sender must review the exact export preview. Export requires
explicit confirmation and a password or passphrase of 12–256 characters. The
current core encrypts the file using AES-GCM with a fixed scrypt configuration,
refuses to replace an existing file, and checks that the prepared reflection
has not changed. There is no email sending, recipient search or automatic upload
in this service.

The recipient explicitly selects the file and confirms opening it with the
password. Import decrypts a bounded packet in memory and validates its schema;
it does not extract an archive or overwrite a local portrait. Encryption
protects file contents but does not verify the sender, make claims true,
anonymize the text or grant permission to forward it. Sharing permission is
limited to the chosen recipient's private comparison. Any wider sharing needs
another explicit decision by the sender.

The comparison core accepts two distinct, explicitly supplied packets and
requires separate permission for each. It prepares one exact request for review
before an external provider is called. A common-ground or tension point must
quote both selected summaries; other points must cite an exact supplied field.
These quotations establish only what the shared AI interpretation said, not
observed behavior or facts about a person. The report keeps low confidence and
separate unknowns, possible tensions, behavior hypotheses and questions. It does
not produce scores or a final dating verdict. Stop invalidates pending work;
there is no automatic retry. An explicitly chosen offline question guide is
labelled as a static guide and is not an AI result or silent fallback.

The exchange screen is now connected to Home and AI Chat. Real Qt checks cover
selected synthetic reflections, encrypted file export and import, permissions,
review, stop and navigation. Both languages and two window sizes have been
visually reviewed with synthetic data. These checks do not test a real couple's
relationship or deliver email. The build and real-model evidence are recorded in
[current status](../CURRENT_STATUS.md), separately from mock transport tests.

Each comparison source ID now identifies one bilingual summary field. A quote
must occur exactly within either supplied language version; combining languages,
translation and paraphrase are rejected. Common ground, tensions and risk points
may cite only interpretation fields, not missing information, questions or caveats.
For a session containing one short statement (up to 350 characters), the new
portrait request permits at most one claim. A narrow bilingual guard rejects
observed preference-to-action inflation, such as asserting that someone establishes
a boundary merely because they prefer a pause. The app rejects invalid output
rather than rewriting it. These conservative checks do not verify all meanings
or translation accuracy; human reading remains necessary.

### Optional voice input

Voice should be another way to fill the user's editable message box. The intended
interaction is **choose to record → stop recording → transcribe locally → edit
the text → choose Send**. Recording or transcription must not automatically send
an answer to ChatGPT. Typed chat remains available when the microphone, offline
recognizer or language model is unavailable.

The voice core accepts at most 30 seconds of supplied audio, normalizes supported
capture formats, and transcribes in memory with an explicitly installed offline
Vosk English or Chinese model. It does not write raw audio into the vault or pass
audio to an AI provider. Installing a model is a separate action; fixed official
download locations, archive checksums, bounded extraction and link checks guard
that installation. A successful download does not itself show that transcription
is accurate.

The real English recognizer transcribed synthetic English speech successfully.
Both pinned official models were downloaded, verified and loaded. Real Qt tests
exercise recording lifecycle signals and draft-only delivery with injected audio;
they do not establish actual microphone capture. Read-only device enumeration
found zero microphone inputs on this computer. Physical microphone recording and
Chinese transcription quality remain owner checks. Synthetic audio cannot prove
recognition accuracy for an actual user's voice or room.

### Evidence and boundaries

The final frozen-source gate passed 2116 tests with nine Windows link-permission
skips; compilation, full lint and portable Desktop package checks passed. This
does not establish real AI acceptance. Actual synthetic-data Gemma and Qwen 3.5
runs produced rejected comparisons or portraits; the larger installed Qwen 3.6
failed CUDA startup. No semantically acceptable full real-model comparison has
been accepted. Actual ChatGPT inference awaits the owner's confirmation that
extra credits are disabled. The task-owned local server was stopped after testing;
hourly automation remains paused. The detailed receipts and owner actions are in
[current status](../CURRENT_STATUS.md) and [owner review](../OWNER_REVIEW.md).

The ChatGPT core has synthetic OAuth, signature, refresh, callback, safe error
and stream tests, including an actual local loopback listener with synthetic
authorization. It has not used those tests to establish real model quality.
The updated model picker and badge are tested with the real Qt widgets and
synthetic services. The exchange and voice cores have explicit consent and data
boundaries, with their latest separate results in the current handoff. Public
deployment, automatic contact and
real-person matching are not completed by this local milestone.

For the wider product direction, see [conversation-first product design](30_conversation_first_product.md).

## 中文版

本文保留 9 月 30 日的设计和观察。当前 0.3.0 的实现、记忆和真实测试依据以
[架构更新](32_standards_correction.md)和[当前交接](../CURRENT_STATUS.md)为准，
下文历史验证缺口不代表今天仍然存在。

### 产品意图

AI-SlowMatch 帮助用户理解自己的相处方式，按自己的节奏讨论适合的关系，并留意具体风险。
AI 扮演懂得相处的陪伴型军师：提出有意义的问题，在应用内结合用户明确提供的回答，保留
不确定性，帮助准备下一次尊重彼此的交流。用户自己决定分享什么、见谁、是否继续。公开的
人格评分、对人的排名、自动判定人品，以及在商品目录般的人选中不断左右挑选，不属于此
产品的设计方向。

预期闭环是**连接 ChatGPT → 开始聊天 → 回答或跳过问题 → 随时结束 → 审阅暂定的
自我相处画像 → 选择愿意分享的内容 → 私下讨论对方自选的画像 → 双方决定是否继续**。
开始与结束都由用户直接操作，聊天前不必选择市场、填写限时访谈或配置提示词。后续比较
应提供可讨论的问题、边界、未知信息和可能的摩擦点，支持人的决定，不应声称两个人一定
相合。

### ChatGPT 连接与模型选择

2026 年 9 月 30 日实际观察到的应用界面已经显示登录成功，但额外积分确认尚未勾选。
这只能说明当时的界面已将账号识别为已连接，不能证明模型请求成功、回答适合此产品，或
服务器上的额外积分已关闭。此前缺少清楚的下一步提示，不应被表述为已经证实的 OAuth
登录失败。

更新后的连接页面区分账号连接、ChatGPT 套餐使用权限、账号模型列表加载，以及进入 AI
聊天的准备状态。成功标记确认账号这一阶段。模型发现读取此账号真实返回的模型目录，
不运行示例推理。用户在确认额外积分之前就能看到模型列表，选择模型，再明确启用聊天。
单纯连接账号不会自动激活后端，也不会将访谈内容发送给模型。

推荐默认模型只从此账号实际返回的模型中选择。名称中出现 mini、nano、small 或 luna
只是模型可能较轻量的启发式线索；没有此类线索时，按账号返回顺序在通用模型中选择。
实际速度、额度消耗和自我画像结构化输出的兼容性仍未验证。模型选择框须保留账号提供的
其他选项。目录为空或读取失败时，账号连接成功的状态仍应可见，但应用不得显示已经可以
聊天。

套餐资格、应用额度与积分使用由 OpenAI 管理。现有公开推理参数无法让本应用强制只使用
套餐内额度。用户须进入 [ChatGPT 用量设置](https://chatgpt.com/settings/usage)，关闭此
应用的额外积分，然后明确确认这一操作，才能激活聊天。模型发现与本地界面测试不能代替
此确认。相关依据见官方[模型与推理契约](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
和[用量界面指引](https://developers.openai.com/siwc/ui-ux-guidelines)。

### 用于私密交换的自选画像

交换核心从用户明确选择、已经单独保存的一份相处画像准备摘要。摘要最多包含五条关于
价值观、需要、沟通或边界的暂定陈述，以及待讨论问题、未知信息与局限。两种语言版本
一起传递。资料包明确说明其来源是 AI 对自述的解读，保持低置信度，并声明作者身份与
关系结论未经核实。

自选资料包不包含聊天原始记录、原文引证、账号凭据或已保存的历史。但叙述文字仍可能
透露个人信息，因此发送者必须审阅完整导出预览。导出要求明确确认，并使用 12–256 个
字符的密码或口令。当前核心使用 AES-GCM 和固定的 scrypt 参数加密文件，拒绝替换已有
文件，并检查准备后的画像是否发生变化。该服务没有邮件发送、接收者搜索或自动上传。

接收者明确选择文件，确认用密码打开。导入在内存中解密有大小限制的资料包，并验证结构；
不会解压任意压缩包，也不会覆盖本地画像。加密保护文件内容，但不会核实发送者、让结论
成为事实、自动匿名化文字或授权转发。分享许可仅限所选接收者进行私下比较；扩大分享
范围须由发送者另行明确决定。

比较核心接收两份不同、明确提供的资料包，并分别要求双方许可。调用外部提供方前，先准备
一次完整请求供用户审阅。共同点或差异点须同时引用双方自选摘要；其他讨论点也须逐字引用
指定资料字段。这些引文只能证明共享的 AI 解读说过什么，不能证明实际行为或一个人的事实。
报告保持低置信度，分别列出未知、可能的差异、待澄清的行为假设及问题，不输出分数或最终
约会判决。停止会使待处理任务失效，不自动重试。用户另行选择的离线提问提纲明确标为静态
提纲，不冒充 AI 结果，也不是暗中切换的后备服务。

交换界面已连入首页与 AI 聊天。真实 Qt 检查覆盖自选合成画像、加密文件导出与导入、
许可、审阅、停止与导航；中英文及两种窗口尺寸都已用合成资料进行视觉检查。这些检查
不涉及真实情侣的关系结果，也不发送邮件。构建与真实模型证据单独记录在
[当前状态](../CURRENT_STATUS.md)，与模拟传输测试区分。

比较的每个来源编号现在代表一个双语摘要字段。引文必须逐字出现在所提供的任一语言
版本中；拼接两种语言、翻译引文或改写引文都会被拒绝。共同点、差异与风险点只能引用
解读字段，不能引用缺失信息、问题或局限。一段最多 350 字符的单条输入，在新画像请求中
最多产生一条解读。有限的双语检查会拒绝已发现的“偏好变成实际行动”膨胀，例如仅凭
喜欢暂停就断言用户已经设立边界。无效输出会被拒绝，不会被自动改写。这些保守检查
无法核验所有含义与翻译准确性，仍须人工阅读。

### 可选语音输入

语音应作为填写可编辑消息框的另一种方式。预期交互是**选择录音 → 停止录音 → 本机
转写 → 编辑文字 → 自己选择发送**。录音或转写不能自动把回答发送给 ChatGPT。麦克风、
离线识别器或语言模型不可用时，用户仍然可以打字聊天。

语音核心接收最多 30 秒明确提供的音频，转换支持的录音格式，再使用用户明确安装的
Vosk 英文或中文离线模型，在内存中转写。它不会将原始音频写进资料库，也不会将音频
交给 AI 提供方。安装模型是独立动作；固定的官方下载位置、压缩包校验值、有界解压和
链接检查用于保护安装过程。下载成功本身不代表转写准确。

真实英语识别器已成功转写合成英语语音。两个固定版本的官方模型都已下载、校验并加载。
真实 Qt 测试使用注入音频，验证录音生命周期信号与仅交付草稿的逻辑，不能证明实体麦克风
录音。只读设备枚举在这台电脑上发现零个麦克风输入，因此实体录音与中文转写质量仍须
所有者检查。合成音频不能证明对真实用户声音或房间的识别准确性。

### 证据与边界

最终冻结源码验收为 2116 项测试通过、9 项因 Windows 链接权限跳过；编译、全范围静态
检查与便携桌面程序核验通过。这不能证明真实 AI 验收。Gemma 与 Qwen 3.5 的实际合成
数据运行产生了被拒绝的比较或画像；已安装的较大 Qwen 3.6 遇到 CUDA 启动错误。
尚未接纳语义可接受的完整真实模型比较。真实 ChatGPT 推理等待所有者确认已关闭额外
积分。本轮自启的本地服务器已在测试后停止，小时自动任务继续暂停。详细依据与所有者
操作见[当前状态](../CURRENT_STATUS.md)及[所有者审阅](../OWNER_REVIEW.md)。

ChatGPT 核心具有合成 OAuth、签名、刷新、本机回调、安全错误与事件流测试，其中包含
实际本机回调监听器与合成授权。这些测试不能证明真实模型质量。更新后的模型选择框与
成功标记使用真实 Qt 控件、合成服务进行测试。交换与语音核心明确限制了同意和数据范围，
最新独立结果见当前交接。本地里程碑不等于完成公开部署、
自动联系他人或真实人员匹配。

更完整的产品方向见[以聊天为起点的产品设计](30_conversation_first_product.md)。
