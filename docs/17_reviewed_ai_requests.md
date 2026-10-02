# Reviewed AI requests / 经审核的 AI 请求

## English

The shared `ai/privacy.py` contract separates application instructions from user
and assistant messages. Only those two data roles are accepted. Imported vault
content, optional knowledge packs and counterpart cards are data, never system
instructions. This separation reduces authority confusion; it does not prove a
model is immune to prompt injection.

Local Ollama requests require a loopback origin. The transport disables inherited
proxies and redirects. It does not fall back to a remote provider. External HTTP
and CLI providers require an explicit reviewed disclosure tied to the recipient,
model, trusted instructions and exact approved messages. The desktop dialog and
browser dialog show these instructions and editable messages before sending.
Cancelling sends nothing. External output is still untrusted.

The shared service never adds hidden vault content to an approved external
summary. It does not claim automatic anonymization: the user must remove private
identifiers and select only what they intend to disclose. Keys remain in process
memory or the environment. CLI calls use a temporary directory, disabled tools,
disabled configuration discovery and no resumed session. Unsupported CLI
isolation fails closed. No AI calls occur in CLI availability checks.

The advanced manual handoff is outside the connected-provider controls. Its
bilingual prompt now explicitly permits only an independently isolated local
model and tells cloud-backed agents to stop before reading the vault. Onboarding
directs external AI users to the reviewed workflow. A prompt is not a sandbox and
cannot prove the behavior of a separately operated tool.

Local structured synthesis supplies a JSON schema to Ollama and validates the
result again before storage. Reports require bounded fields, evidence and
uncertainty. Schema validity does not establish evidence truth or semantic safety.
Original files remain intact if validation fails. Legacy artifacts may be read,
but must satisfy the current contract before saving or sharing again.

`ChatRequest.allow_schema_fallback` is a strict Boolean with the existing default
of `true`. It controls the local adapter's HTTP 400 retry in JSON syntax mode.
The explicitly reviewed single-claim and full-report regeneration workflows set it
to `false` and bind that policy in the request checksum: failures send no automatic
retry or repair request. Other generation workflows keep their existing behavior.

Connected desktop reports now use canonical structured findings and a complete
`localized_text` map instead of model-authored Markdown. Every required narrative
field has exactly one JSON-pointer entry containing its exact canonical source
text and English/Simplified Chinese versions. Validation rejects missing,
duplicate, extra or stale mappings and preserves the source-language text.
English-letter and Chinese-character checks establish only minimal language
presence. Optional free-form headlines and summaries cannot introduce a second
channel for unsupported claims in new connected report bundles.

The application renders both languages from those validated fields with fixed
headings, claim-type and confidence explanations. The concise portrait summarizes
recorded claims and caveats; its detailed companion includes original quotations,
coverage, questions and clarification findings. Criteria sections and fictional
scenarios appear only when the corresponding canonical lists contain entries.
Narrative text, source labels and quotations are escaped so imported Markdown,
HTML, URLs and newlines cannot create their own links, images or report structure.
Original evidence wording and source labels remain visible; only the renderer
owns formatting and line breaks.

Canonical JSON schemas remain unchanged. Translations are saved separately in
`self_portrait_localization.json` or `mate_criteria_localization.json`, not added
to the canonical facts. The visual portrait rechecks the mapping against its
canonical report before using it. An invalid companion is rejected; an older
report without one explicitly identifies its missing translation rather than
silently presenting English as Chinese. Canonical extraction and localization
share the same reviewed provider request; rendering makes no additional AI call.
These checks do not prove that an inference follows from its quotation, that a
source label identifies the correct origin, or that a translation preserves the
meaning. Users still need to review the claims and translations against the
original material.

The runtime/model may ignore the requested output format; the application never
relies on native grammar enforcement alone. Desktop report bundles also check
that evidence quotations occur in the supplied user messages. Prior AI portraits
remain assistant-role references, and mixed generated transcripts are excluded
from automatic evidence imports. User-only interview answers are stored
separately. Exact quotation checks establish text presence, not source authorship
or truth. A single local correction attempt is allowed; external correction
requires a new review instead of automatically sending another request.

The browser also separates original user evidence from prior generated content.
Known AI cards, reports, localization companions, application settings and mixed
interview transcripts are excluded from automatic evidence imports, including
when the configured folder is the vault root. The user-only interview companion
remains eligible. During an ongoing conversation or refinement, prior AI cards
and reports may be included only as explicitly unverified assistant-role
references. Fresh refinement with no conversation history omits those references;
fresh analysis reads only the selected original material. Old AI output alone
does not satisfy the requirement for original user data. This prevents known
generated assertions from being automatically recycled as owner testimony; it
does not authenticate authorship or detect every generated passage a user may
have placed inside an imported file.

Comparison and rehearsal require separate confirmation that both people agreed
to that purpose. Sender disclosure approval alone does not imply counterpart
consent. Both cards are schema-validated before model processing.

The browser's disclosure response is local HTTP 409 with a preview; it makes no
provider call. The retry carries the edited messages, strict boolean consent,
recipient and instruction hash. Actual outbound adapters revalidate a typed,
fingerprinted request. This is consent in a local user interface, not remote
identity authentication or proof that another person consented.

The local browser backend and vault selection are isolated per application.
Each request captures its provider and file destinations. The browser refuses
vault switching during a pending request/review and rejects stale responses;
another tab cannot make a running job save into the newly selected vault.
Switching clears the active model, drafts, AI and matching context while retaining
the old tab session under its vault identity in session storage. A history-restore
interface is not yet implemented. These protections do not authenticate other
processes running as the same operating-system user.

Desktop evidence review now stores explicit user corrections separately from
canonical reports, with original report snapshots and version-bound history.
Review notes are never automatically included in AI requests. The shared evidence
collector excludes generated history and reviewed copies even when selected
directly as an input root, and rejects linked file aliases. See
[review history](18_report_review_history.md) and [reviewed copies](19_reviewed_report_copies.md).
Withdrawing claims into a separately confirmed copy makes no AI call and leaves
the active report unchanged. A separate [confirmed selection](20_active_report_selection.md)
can choose the report used for viewing and subsequent interview reference. It remains
assistant context; stale selections stop requests and require a new interview.
Explicit single-claim interpretation and full current-format regeneration from pasted
excerpts are available; see [full regeneration](27_full_report_regeneration.md).
Remaining work: broader legacy migration, recoverable encryption, broader model
evaluations and release review. Public matching remains experimental.

References: [Ollama structured output](https://docs.ollama.com/capabilities/structured-outputs)
and [thinking controls](https://docs.ollama.com/capabilities/thinking).

## 中文版

共享的 `ai/privacy.py` 契约将应用指令与用户、助手消息分开，只允许这两种数据角色。
导入的档案内容、可选知识包及对方卡片始终属于数据，不进入系统指令。
这种分离可减少权限混淆，但不能证明模型免疫提示词注入。

本地 Ollama 请求必须使用回环地址；传输层禁用继承的代理和重定向，不会回退至远端提供方。
外部 HTTP 与 CLI 提供方要求明确审核披露内容，并绑定接收方、模型、可信指令及最终确认的消息。
桌面与浏览器均在发送前展示指令和可编辑消息；取消不会发送数据。远端输出仍不可信。

共享服务不会向已审核的外发摘要偷偷添加档案内容。系统不声称能自动彻底匿名化：用户须删除
私密标识，只选择自己愿意披露的内容。密钥只驻留于进程内存或环境变量。CLI 调用使用临时目录，
禁用工具、配置发现及会话续接；无法证实有等效隔离的 CLI 会拒绝执行。CLI 可用性检查不调用模型。

高级手动交接不受已连接提供方的控制层约束。其双语提示词现明确限定为已独立隔离的本地模型，
并要求使用云端的代理在读取档案前停止。引导文案将外部 AI 用户导向披露审核流程。
提示词不是沙箱，无法证明另行操作的工具会如何处理数据。

本地结构化生成会将 JSON Schema 提供给 Ollama，并在保存前再次校验结果。报告要求字段有界、
包含证据和不确定性。结构正确不能证明证据真实或语义安全。校验失败不覆盖原有文件。
旧格式文件仍可阅读，但再次保存或分享前必须满足当前契约。

`ChatRequest.allow_schema_fallback` 是严格布尔值，保留既有默认值 `true`，控制本地适配器
是否在 HTTP 400 后以 JSON 语法模式重试。明确复核的单条主张和完整报告重新生成流程
将其设为 `false`，请求校验和也绑定该策略：失败后不自动补发重试或修复请求。其他生成
流程保留原有行为。

已连接 AI 的桌面报告现在使用规范化的结构化结论和完整的 `localized_text` 双语对照，
不再直接保存模型自由撰写的 Markdown 正文。每个必须翻译的叙述字段都必须且只能对应一个
JSON 指针条目，包含与规范字段完全一致的原文，以及英文和简体中文版本。校验会拒绝缺失、
重复、多余或过期的对照，并保留源语言文字。英文字母与汉字检查只能确认最低限度的语言字符
存在，不能证明语言质量。新生成的报告包也不允许通过可选的自由标题或摘要另行加入无证据主张。

应用根据这些经过校验的字段生成两种语言的正文，并统一提供标题、主张类型和置信度说明。
画像简版概括已记录的主张和限制；详细版包含原始引文、材料覆盖范围、问题及待澄清记录。
择偶标准章节和虚构情境仅在对应的规范列表存在条目时出现。叙述、来源标注和引文都会经过
转义处理，导入内容中的 Markdown、HTML、网址和换行不能自行变成链接、图片或报告结构。
证据原文及来源标注仍然可见，排版和换行仅由渲染器决定。

规范 JSON 的结构契约保持不变。译文另存于 `self_portrait_localization.json` 或
`mate_criteria_localization.json`，不会作为新事实加入规范数据。可视化画像使用译文前，会
再次将其与规范报告逐项核对。无效的译文文件会被拒绝；缺少译文的旧报告会明确提示，不会
悄悄把英文当作中文展示。规范信息提取与双语对照由同一次经过审核的提供方请求完成，渲染
本身不会追加 AI 调用。这些检查不能证明推断确实由引文支持、来源标注确实指向正确出处，
也不能证明翻译准确保留原意。用户仍须对照原始材料审核主张与译文。

运行时或模型可能忽略所请求的输出格式；应用不单独依赖模型侧语法约束。桌面报告包还会检查
证据引文是否出现在本次输入的用户消息中。既有 AI 画像保留为助手角色参考，包含生成内容的
混合访谈记录不会自动作为证据导入；纯用户访谈回答另行保存。精确引文检查只能确认文本存在，
不能证明来源作者或内容真实。本地允许一次纠错重试；外部纠错须重新审核，不会自动再次发送。

浏览器同样区分原始用户证据与既有生成内容。已知的 AI 卡片、报告、双语对照文件、应用设置
以及混合访谈记录不会自动作为证据导入，即使所配置的文件夹是整个档案库根目录也一样。
仅含用户回答的访谈伴随文件仍可作为输入。在进行中的对话或完善过程中，既有 AI 卡片和报告
只能以明确标注“未经核实”的助手角色参考材料出现。没有对话历史的重新完善会排除这些参考；
重新分析也只读取所选择的原始材料。仅有旧 AI 输出不能满足存在原始用户数据的要求。这样可
防止已知的生成结论被自动循环引用为用户证言，但不能验证作者身份，也不能识别用户放进导入
文件中的每一段生成文字。

比较与演练要求另行确认双方都同意该用途。发送方同意披露，不代表对方同意被分析。
两张卡片均须通过结构校验，才可交给模型处理。

浏览器通过本地 HTTP 409 获取披露预览，此时不会调用提供方。再次请求携带编辑后的消息、
严格布尔同意值、接收方和指令哈希；实际提供方适配器还会重新验证类型化、带指纹的请求。
这是本地界面的同意流程，不是远程身份认证，也不能证明另一人确实同意。

本地浏览器后端与档案选择已按应用实例隔离；每个请求固定其提供方与文件目的地。浏览器在
请求或审核尚未完成时拒绝切换档案，并拒绝过期响应；其他标签页也不能让进行中的任务改写
新档案库。切换会清空当前模型、草稿、AI 和匹配上下文，同时按旧档案标识在标签页会话存储中
保留此前的会话。尚未实现历史恢复界面。这些保护不等于对同一操作系统用户下其他进程进行认证。

桌面证据复核现将用户明确保存的更正与规范报告分开，保留原始报告快照和绑定版本的历史。
复核批注不会自动进入 AI 请求。共享证据收集器会排除直接选为输入根目录的生成历史与复核副本，
并拒绝链接文件别名。详见[纠错历史](18_report_review_history.md)和[复核副本](19_reviewed_report_copies.md)。
撤回主张并明确确认独立副本不调用 AI，也不改变当前报告。另行[确认选择](20_active_report_selection.md)
现可决定查看及后续访谈参考使用的报告；它仍属于助手参考。选择过期时停止请求，并要求开始
新访谈。现已提供明确的单条主张解释，以及从粘贴摘录重新生成完整当前格式报告，详见
[完整重新生成](27_full_report_regeneration.md)。剩余工作包括更广泛的旧格式迁移、可恢复加密、更广泛的模型评估及
发布审核。公共匹配仍属于实验。

参考：[Ollama 结构化输出](https://docs.ollama.com/capabilities/structured-outputs)及
[思考控制](https://docs.ollama.com/capabilities/thinking)。
