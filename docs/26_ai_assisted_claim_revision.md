# AI-assisted claim revision / AI 辅助主张修订

## English

### Workflow and scope

After saving a correction against a current-format original portrait or criteria
report, open **Create reviewed copy** and the AI-assisted interpretation action.
Choose one correction, prepare and read the exact request, then explicitly consent
to drafting with the connected local Ollama model. Review and edit the English and
Simplified Chinese wording, inspect the complete report preview, and separately
confirm saving. Saving never activates the copy; use **Select active report** for
that separate decision. Cancellation before generation makes no model call.

This workflow reconsiders one claim using only its already saved quotations. It
does not open source-label paths or read new original documents. The prior claim,
correction and reason are unverified context, separated from the closed quotation
set. Application-assigned quotation IDs provide structure without disclosing the
stored source-label paths. Neither an annotation nor an earlier AI claim becomes
new evidence. This is not full-report regeneration, lossless legacy conversion or
verification that a quotation supports the proposed interpretation.

This first implementation permits the existing local Ollama adapter only. External
API and agent-CLI adapters are rejected before drafting. The existing local adapter
enforces loopback transport and rejects cloud routing. Preparing the request makes
no provider call. The prepared request disables the adapter's HTTP 400 schema
fallback, so a failed call is not automatically repeated. Generation uses one explicit request with a strict two-field
bilingual JSON response; unexpected fields, malformed JSON, duplicate keys,
oversized output and missing language content are rejected. Presence checks do not
establish translation fidelity, semantic support or complete safety of free text.

### Review and preservation

Every revised claim retains the visible **AI-assisted interpretation (quote-limited,
unverified)** attribution, including after the user edits it. The application fixes
its type to speculation and confidence to low. Topic, report group, quotations and
source labels remain unchanged. Existing warnings remain; one explanation of this
limited operation is added. A full warning list causes rejection rather than
removal of old warnings. Dependent portrait findings/headlines/summaries or criteria
fictional candidates/choices are removed. Other claims have not been reanalyzed.

The request binds exact original report, translation, optional candidate file and
selected correction bytes. Checks run before and after the model call and again
at preview/save. Changed inputs invalidate the draft for that source version;
the interface retains wording for inspection. Stale replies cannot silently target
another correction. Backend failures expose a generic message, not private model
output. A running worker must settle before its dialog is destroyed. Result/error
handlers are dialog-owned Qt slots, so UI updates run on the UI thread. Cancellation
discards the reply and waits for the worker; it does not promise to interrupt an
already running model request.

The new version 0.3 copy shares the existing atomic reviewed-copy storage, bounds,
writer lock and separate active-selection mechanism. It preserves exact originals,
the selected annotation and the AI-assisted proposal. Earlier 0.1 withdrawal and
0.2 user-proposed copies remain readable without rewriting their files. Source
changes stop active use while verified saved history stays readable. Desktop,
browser and interview consumers retain attribution; selected copies remain
assistant references, excluded from original-input discovery.

Snapshots remain plaintext. Context/request digests are checksums, not proof that
a particular model ran or that its interpretation is true. The full outbound
request and raw model response are not added as new evidence files. This operation
does not change original writer paths, compatibility cards or the active selection.

### Verification and remaining work

Tests use synthetic vaults and mocked local transports. They cover strict consent,
request integrity, stale inputs/replies, local-only dispatch, malformed replies,
preserved uncertainty, both report types, mixed history formats and downstream
consumers. No mocked response is reported as real-model validation. Current gate
and package evidence are recorded in [CURRENT_STATUS.md](../CURRENT_STATUS.md).

An actual local `qwen3.6:latest` check used a newly created fictional portrait and
one stored quotation. The first output passed structural validation but overstated
frequency/intensity; manual inspection prompted stricter single-episode and
translation-uncertainty instructions. The second request took 29.75 seconds and
explicitly said the single event could not establish a pattern. Validation,
separate saving/reopening, exact original preservation and unchanged selection
passed. This is one synthetic portrait example with two requests, not a general
reasoning or translation guarantee; criteria generation was mocked. The temporary
local server was stopped after the check. No model download or paid call occurred.

Fresh source selection and validation, genuinely source-based regeneration,
full-report regeneration, broader legacy/profile content migration and wider
real-model acceptance remain future work.

## 中文版

### 流程与范围

先针对当前格式的原始画像或择偶标准报告保存更正，再打开**生成复核副本**中的 AI 辅助
解释操作。选择一条更正，准备并阅读准确请求内容，然后明确同意由已连接的本地 Ollama
模型起草。复核并编辑英文与简体中文措辞，查看完整报告预览，再单独确认保存。保存不会
启用副本；如需使用，另行通过**选择当前报告**确认。生成前取消不会调用模型。

此流程仅使用该主张已经保存的引文重新考虑一条解释，不沿来源标签读取路径，也不读取
新的原始文档。旧主张、更正和理由均为未经核实的背景，与固定引文集合分开。由应用分配
的引文编号提供结构，不向模型披露已保存的来源路径标签。批注和旧 AI 主张不会变成新
证据。本功能不等于完整报告重新生成、无损旧格式转换，也不证明引文支持新解释。

第一版只允许现有本地 Ollama 适配器，起草前拒绝外部 API 与代理命令行适配器。既有本地
适配器强制回环传输并拒绝云端路由。准备请求不调用提供方，并关闭适配器在 HTTP 400 后的
结构降级重试，因此失败后不自动重复调用。生成使用一次明确请求，要求
返回严格的双字段双语 JSON。额外字段、坏格式 JSON、重复键、过大输出及语言内容缺失
均拒绝。语言存在性检查不能证明翻译准确、语义支持成立或自由文本完全安全。

### 复核与保留

修订后的主张始终显示 **AI 辅助解释（仅依据已有引文，未经核实）**，即使用户编辑措辞
也保留此归属。应用固定将其标为推测、低置信度；主题、报告分组、引文及来源标签保持
不变。保留原有警示，并增加本次有限操作的说明；原警示列表已满时拒绝保存，不删除
旧警示。移除可能依赖原结论的画像一致性分析/标题/摘要，或择偶标准的虚构候选人及其
选择。其他主张没有重新分析。

请求绑定原报告、翻译、可选候选文件和所选更正的精确字节。调用模型之前、返回之后及
预览/保存时均检查。输入发生变化后，该草稿不能直接用于新的来源版本；界面保留措辞
供查看。过期回复不能悄悄改为针对另一条更正。提供方失败仅显示通用错误，不暴露模型
返回的私密内容；运行中的后台任务必须完成收尾，才可销毁其窗口。结果/错误处理使用
窗口持有的 Qt 槽，使界面更新在界面线程上执行。取消会丢弃回复并等待任务结束，不承诺
中断已经运行的模型请求。

新的 0.3 版本副本共用既有完整目录提交、大小限制、写入锁及独立当前选择机制，保留
精确原件、所选批注和 AI 辅助提议。此前的 0.1 撤回副本和 0.2 用户提议副本仍可读取，
不改写其文件。来源变化会停止当前使用，经过校验的历史副本仍可阅读。桌面、浏览器和
访谈消费者保留归属标记；所选副本仍作为助手参考，不进入原始输入发现。

快照仍为明文。上下文/请求摘要只是校验和，不证明某个模型实际运行过或解释属实。完整
外发请求和原始模型回复不会新增为证据文件。此操作不改变原始写入路径、兼容性卡片或
当前选择。

### 验证与后续工作

测试使用合成档案库和模拟本地传输，覆盖严格同意、请求完整性、过期输入/回复、仅本地
调用、无效回复、不确定性保留、两类报告、混合历史格式及下游消费者。模拟回复不会被
称为真实模型验证。最新验收与打包证据见 [CURRENT_STATUS.md](../CURRENT_STATUS.md)。

实际本地 `qwen3.6:latest` 验证使用新建的虚构画像及一条已保存引文。第一次输出通过
结构校验，但夸大了频率/强度；内容检查后收紧了单一事件及双语不确定性一致性的指令。
第二次请求耗时 29.75 秒，明确说明单个事件不能证明行为模式。校验、另存/重读、精确保留
原件及当前选择不变均通过。这是一个合成画像样例、共两次请求，不保证普遍推理或翻译
质量；择偶标准生成仅通过模拟验证。检查后已停止临时本地服务，未下载模型或调用付费服务。

新原始来源的选择和校验、基于原始来源的重新生成、完整报告重新生成、更广泛旧格式/
档案内容迁移，以及更广泛真实模型验收，仍属后续工作。
