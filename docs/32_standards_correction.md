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

Memory starts empty and disabled. Only an explicit Add/Correct action writes a note;
20 entries of 250 characters maximum, each with source, approval time, kind, unverified
status and superseded ID for corrections. Revisions and a cross-process lock prevent
lost updates; atomic files preserve the previous complete state on interruption.
Pause/revoke excludes all notes from future requests. Delete purges the app's stored
entry without retaining its old text in an undo log; it cannot erase past disclosures,
exports, saved conversations or copies outside this store. Export never overwrites a
file. Notes are unencrypted and appear in the exact outgoing review, never as portrait
evidence. Correcting a note does not rewrite old reports.

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

记忆默认空白并关闭。只有明确新增／纠正才写入，每条最多 250 字、共 20 条，记录来源、
批准时间、类型、未经核实状态，以及纠正时所替代的编号。版本号与跨进程锁防止覆盖其他更新，
原子写入在中断时保留上一完整状态。暂停／撤销后不再向后续请求提供记忆。删除移除本应用
存储的条目，不在撤销日志保留旧文字；不能抹除此前披露、导出、保存的对话或存储之外的副本。
导出不覆盖文件。记忆未加密，发送前完整展示，绝不作为画像证据。纠正记忆不会重写旧报告。

已备份并快进更新 goutoujunshi skill 至 `6db7354a4002dc7c448a9c87ffdad8132570c9d3`
（MIT）。仅将审阅过的核心、证据边界、沟通修复及经同意记忆原则融入应用自己的策略。
不加载问卷、分数、性别校准、自动记忆脚本或 ChatLab 导入。旧可选网页军师也改用固定策略，
不读取随安装更新而变化的 skill 内容。MIT 许可随程序打包，并在“关于”中展示。
审阅的 Pi `0.99.2`，提交 `8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d`，仅用于借鉴接口，
未新增 Node 运行环境。

固定 EXE 的检查及恢复见[打包说明](../packaging/README.md)。所有者文档按职责整理，完整旧版
保存在 `history/`。真实模型和实体麦克风验收始终与确定性测试分开记录。
