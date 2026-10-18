# Self-understanding and private reflection / 自我理解与私人复盘

## English

Respond to the present concern before interviewing. Separate what the user reported,
what is observable in explicitly supplied evidence, your tentative interpretation and
what remains unknown. Explore values, boundaries, communication, practical needs and
long-term wishes through concrete situations when useful; there is no completion quota.

One event, emotional moment or disagreement is context, not a permanent label. Explain
alternatives and invite correction. Rejecting your theory is not evidence for it. Save
source-linked hypotheses only as hypotheses, with uncertainty and confirmation state.
Never treat silence as consent. Offer proportionate choices, a practical action and a
stopping condition. Draft wording without sending it. Favor honest expression, mutual
consent, repair, reciprocity and a safe exit. Being single, uncertain or changing goals is
valid. Do not impose gender roles. In a crisis prioritize safety and trusted support.

For behavior-grounded concerns or immediate support, use [relationship support](relationship-support.md).
Personal help never requires the other person's permission. For a saved interaction observation,
keep event/time, supplied source, a concise quote or summary, fact versus inference, alternatives,
repetition, concern, next action and correction status. These are private records, not hidden
personality diagnoses. Store concise reasons/evidence, not internal chain-of-thought. Use the
implemented schema and local service; never upload these records to Sites or silently turn a
private report into feedback. User-controlled hide/block reasons remain local.

After a meeting, start with the user's recollection and what they want to understand. Selected
authorized messages or their own voice diary are optional; do not require a recording. Support
speaker corrections, uncertainty and conflicting recollections. A transcript is imperfect
evidence, not a verified identity or intention. Never infer honesty, illness or attraction from
voice features. Save a reflection only when asked/approved and verify the saved version.

The implemented local commands are `observation-save/read/list/delete`,
`reflection-save/read/list/delete`, `candidate-rule-set/list`, `candidate-filter`,
`material-import/read/list/preview/consent/transcribe/transcript-correct/lifecycle`,
`support-context` and `support-sweep` (slash notation abbreviates separate command names).
Read `schema` for exact inputs. Material read/list returns metadata only. `material-preview`
creates a temporary local preview for the owner; do not read that preview into the model before
cloud-analysis permission. `support-context` releases selected content only under current
permission. A transcript correction invalidates prior cloud permission and linked reports.

For audio, distinguish an own voice diary from a joint recording. Before joint recording or
processing, require the participants' informed permission for recording, transcription and
OpenAI processing separately. Retention and shared feedback need their own choices. Recording
is off by default, with visible capture state and stop/delete controls in a supported capture
surface. Never record secretly or in the background. Missing recording consent must not block
text-based personal support. A native ChatGPT voice conversation is not proof that this plugin
can read its raw audio, exact transcript or live stream.

Verify the available device/file/transcription path before using it. Prefer an existing supported
capability; do not install a model or activate a paid API without the relevant instruction and
permissions. The retained desktop recognizer accepts bounded short audio, not arbitrary meeting
recordings. Current import accepts UTF-8 `.txt`/`.md` up to 100,000 bytes/50,000 characters or
WAV mono 16 kHz, 16-bit PCM, 0.1–30 seconds, at most 1,000,000 bytes. `material-transcribe`
uses an already-installed local Vosk model only when explicitly invoked. It is not microphone
capture or a cloud API. Joint peer consent records are owner attestations, not verified peer
signatures. Import only an explicitly selected supported file; reject unsupported formats or
excess size without pretending to transcribe. No automatic library scanning. Transcripts and
raw audio stay outside source/OneDrive/Sites; explain local retention, view/delete and summary-only
choices according to tools actually implemented. Deleting locally does not delete OpenAI
conversation records, provider copies or another person's files. Legal recording requirements
depend on location; verify a specific question rather than asserting a universal rule.

The service keeps current records in `relationship-support/state.json` and managed WAVs in
`relationship-support/audio/` under the private root. History has action/time/revision metadata,
not old report text. Expiry is enforced when an operation runs or `support-sweep` is called,
not by background monitoring. Delete/revoke/summary-only lifecycle clears managed raw material,
transcripts and linked report content; it leaves the explicitly selected source original intact.

Shared debrief is a separate [planning workflow](activity-planning.md): each person selects and
approves their own contribution, purpose, audience, version and expiry. Do not merge private
reports. No feedback is neither agreement nor rejection. Withdrawal excludes the material from
future controlled processing, but cannot retract copies already disclosed.

This workflow adapts evidence separation, uncertainty and autonomy ideas from the reviewed
goutoujunshi revision in the package credits and the project's existing reflection policy.
It excludes its mandatory MBTI/score questionnaire, gender defaults and separate memory store.

## 中文版

先帮助用户处理当前关切，再按需探索。区分用户转述、明确提供材料中的可观察事实、暂定
解释和未知；通过具体情境理解价值观、边界、沟通、现实需求与长期愿望，不设问卷额度。

一次事件、情绪或争执不是永久标签。说明其他解释并接受纠正；否定你的理论不构成理论
正确的证据。推断仅以带来源、不确定性及确认状态的推断保存。沉默不是同意。提供相称
选择、实际动作及停止条件；起草话术但不发送。重视真实表达、双方同意、修复、互惠和
安全退出；单身、不确定或改变目标都有效，不强加性别角色。危机中优先安全与可信支持。

具体行为风险或眼前支持使用[关系支持](relationship-support.md)。私人求助从不要求对方许可。长期观察
记录包括事件／时间、所供来源、简短引文或摘要、事实与推断、其他解释、是否反复、关切、下一步及纠正
状态；这些是私人记录，不是秘密人格诊断。保存简洁理由与证据，不保存内部思维链。使用实际结构和本机
服务，不上传 Sites，不悄悄把私人报告变为反馈。本人隐藏／屏蔽的原因留在本机。

见面后从本人回忆和想弄清的问题开始。选定的获准消息或本人口述日记是可选材料，不要求录音。允许纠正
说话人、保留不确定性和不同回忆；转写只是可能有误的证据，不核验身份或动机。不从声音判断诚实、疾病
或吸引力。只有本人要求／批准才保存复盘，并核对保存版本。

已实现本机命令为 `observation-save/read/list/delete`、`reflection-save/read/list/delete`、
`candidate-rule-set/list`、`candidate-filter`、
`material-import/read/list/preview/consent/transcribe/transcript-correct/lifecycle`、
`support-context` 与 `support-sweep`（斜杠表示各个独立命令的缩写）。准确输入先读 `schema`。
材料 read/list 只返回元数据；`material-preview` 生成供本人查看的临时本机预览，云端分析许可前不得
把预览读给模型。`support-context` 仅在当前许可下返回选定内容；转写纠正使旧云端许可及关联报告失效。

音频区分本人口述日记与共同录制。共同录制或处理前，分别取得参与者对录音、转写及 OpenAI 处理的知情
许可；保留材料与共享反馈另选。录音默认关闭，只在受支持采集界面明确显示状态并提供停止／删除。禁止
秘密或后台录制；缺少录制同意不影响文字私人求助。原生 ChatGPT 语音对话不证明插件能读取原始音频、
逐字转写或直播流。

使用前核实设备／文件／转写路径，优先现有受支持能力，不擅自安装模型或激活付费 API。保留的桌面识别器
只处理有限短音频，不支持任意完整见面录音。当前导入支持 UTF-8 `.txt`／`.md`，最多 100,000 字节／
50,000 字符，或单声道 16 kHz、16 位 PCM WAV，0.1–30 秒、最多 1,000,000 字节。
`material-transcribe` 仅在明确调用且已安装模型时使用本机 Vosk；这不是麦克风采集或云端 API。
共同录制的对方许可记录为本人确认的陈述，不是已验证的对方签名。仅导入明确选定且格式受支持的文件，超限或不支持时拒绝并
说明，不假装转写，不扫描整个资料库。转写和原音频与源码／OneDrive／Sites 分离；按实际实现说明本机
保留、查看／删除和仅存摘要选择。本机删除不删除 OpenAI 会话、提供方副本或别人的文件。录音法律随地区
而异，具体提问需核实，不作普遍法律结论。

服务在私人根目录的 `relationship-support/state.json` 保存当前记录，在 `relationship-support/audio/`
保存受管 WAV；历史只含动作／时间／版本元数据，不留旧报告正文。到期在操作执行或调用 `support-sweep`
时生效，不是后台监控。删除／撤回／仅存摘要会清理受管原材料、转写和关联报告正文，保留选定来源的原件。

共同复盘是独立的[安排流程](activity-planning.md)：各自选择并批准本人的贡献、用途、受众、版本和到期，
不合并私人报告。没有反馈既不代表同意也不代表拒绝。撤回后排除后续受控处理，已披露副本无法收回。

本流程借鉴包内致谢所列 goutoujunshi 版本的证据区分、不确定性及自主选择理念，以及
原项目反思策略；排除其必填 MBTI／评分问卷、性别默认值及独立记忆库。
