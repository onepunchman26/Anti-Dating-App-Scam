# Full report regeneration / 完整报告重新生成

## English

### What is regenerated

The reviewed-copy workflow can regenerate a complete current-format self-portrait
or relationship-criteria report from explicitly supplied excerpts. Select one to
ten saved corrections for the current original report and paste one to five original
excerpts. Each excerpt is limited to 12,000 characters; together they may contain
at most 24,000 characters. Confirm that these are original notes you are authorized
to provide. This declaration does not verify authorship or factual truth.

The app assigns source IDs `S001`, `S002`, and so on by excerpt order. It does not
discover files, open paths from evidence labels or copy an entire vault. The selected
corrections, including their prior claim and reason, are unverified assistant context;
they are not allowed evidence for the regenerated claims. Existing original reports
are retained, not used as new testimony. Pasting generated text as an alleged original
excerpt cannot be detected reliably; the owner must review the input.

Prepare and read the exact request, then explicitly approve one request to the
connected local Ollama model. Remote API and agent-CLI adapters are rejected for
this workflow. The reviewed request disables the adapter's optional schema fallback,
so even an HTTP 400 does not silently send another request. No automatic repair/retry
request is sent. Inspect the full bilingual
preview and explicitly confirm saving a separate copy. Activation requires a separate
choice in **Select active report**. Editing inputs or correction selection invalidates
the prepared request and generated preview. Canceling discards a pending reply and
waits for the worker; it cannot promise to interrupt a model already running.

### Evidence and uncertainty checks

For this workflow only, the model returns each narrative as an English/Chinese pair.
The application deterministically builds the existing canonical bundle and complete
localization map, then runs all existing validators. No translation is supplied or
repaired by the application. See [the paired format](29_paired_report_generation.md).
Every quotation must be an exact contiguous substring of the
specific excerpt named by its source ID. A quotation found only in another excerpt,
an unknown source label or a quotation spliced across excerpts is rejected. These
checks do not normalize whitespace or read a source path. Portrait coverage IDs must
match the supplied excerpt IDs. Fictional candidates and recorded choices are not
generated in this bounded workflow.

All regenerated claims and consistency findings receive low confidence. Existing
warnings and their translations are preserved alongside new warnings and an
application-owned notice that this is an AI-regenerated, unverified report based
only on the supplied excerpts. Warning-capacity overflow rejects saving instead of
silently dropping old warnings. Missing support may produce empty claim lists with
limitations; the app does not invent content to fill a report. Citation membership
and schema/language checks do not establish semantic support, translation fidelity,
identity, source authenticity or immunity to prompt injection.

The whole new report is regenerated; this differs from editing one existing claim.
Unchanged old claims are not implicitly carried into the new report. The prior full
report remains in the original location and in the copy's exact source snapshots.
The generated bundle is not edited freely in the preview; change original input and
review a new request if regeneration needs another attempt.

### Storage and compatibility

Version 0.4 reviewed copies use the existing writer lock, bounds and complete-directory
publication. A `regeneration.json` snapshot contains the selected correction IDs,
exact pasted excerpts, validated generated bundle, context/request checksums and
AI-regenerated origin. Source files, translations and selected correction bytes are
checked before/after generation and again at preview/save. The verifier reconstructs
the output from the saved inputs. Checksums detect changes, not authorship or proof
that a model actually ran.

Copies retain full original snapshots and selected annotations. All snapshots,
excerpts and reports remain **plaintext** and may be copied by an existing sync
folder provider. Saving does not replace originals, modify cards or change active
selection. Previous 0.1 withdrawal, 0.2 user-proposed and 0.3 AI-assisted copies remain
readable without rewriting them. A changed original source prevents active use of
a stale copy while verified saved history remains readable.

Selected regenerated reports remain assistant references in desktop, browser and
interview consumers. Full excerpt snapshots and correction text are not implicitly
sent as reference content, and the reviewed-copy directory remains excluded from
original-evidence discovery.

### Verification and scope limits

Synthetic tests exercise both report kinds, exact source attribution, strict consent,
local-only dispatch, malformed/oversized replies, stale data and requests, preserved
warnings and originals, history verification, consumers and desktop lifecycle.
Current test/package and any separately identified real local-model results are in
[CURRENT_STATUS.md](../CURRENT_STATUS.md). Mocked responses are not live-model proof.

The model-facing generation schema requests strings of at most 1,000 characters
to avoid a confirmed local grammar-compiler limit. Input excerpts are not truncated;
the original full artifact validators and historical copies keep their existing
bounds. There is no output repair or added retry. Earlier recovery failures remain in
[local recovery evidence](28_local_model_recovery.md); later bounded real-model
integration results use [the paired format](29_paired_report_generation.md).

This is regeneration of a current-format report from explicitly pasted excerpts.
Arbitrary old-format migration, automatic file selection, verification of original
source authenticity, encrypted storage and broad model-quality acceptance remain
separate work.

## 中文版

### 重新生成的范围

复核副本流程可以从明确提供的摘录重新生成完整的当前格式自我画像或择偶标准报告。
针对当前原始报告选择一至十条已保存更正，粘贴一至五份原始摘录。每份最多 12,000 字符，
合计最多 24,000 字符。须确认这些是你有权提供的原始笔记；此声明不核实作者身份或事实
真实性。

应用按摘录顺序分配 `S001`、`S002` 等来源编号，不发现文件、不沿证据标签打开路径，
也不复制整库。所选更正（含旧主张和理由）作为未经核实的助手背景，不能作为重新生成
主张的证据。旧报告保留，但不会当成新证言。若将生成文本粘贴并声称是原始摘录，应用
无法可靠识别，输入仍需由用户复核。

准备并阅读准确请求后，明确批准向已连接的本地 Ollama 模型发送一次请求。此流程拒绝
远程 API 和代理命令行适配器。已复核的请求关闭适配器的可选结构降级，因此即使收到
HTTP 400 也不会静默再发一次请求；不自动补发修复或重试请求。查看完整双语预览，明确确认
后另存副本；启用还须通过**选择当前报告**另行决定。编辑输入或更正选择会使请求和生成
预览失效。取消会丢弃待返回的回复并等待后台任务结束，不保证中断已在运行的模型。

### 证据与不确定性检查

仅在此流程中，模型将每个叙述字段作为中英对提供，应用按确定规则建立既有规范报告和完整
翻译映射，再执行全部原有校验。应用不补充或修补翻译，详见[成对格式](29_paired_report_generation.md)。
每条引文必须精确、连续地出现在其来源
编号对应的那份摘录内。只在另一份摘录出现的引文、未知来源标签，或跨摘录拼接的引文
均拒绝。这些检查不归一化空白、不读取来源路径；画像覆盖的来源编号必须与已提供的
摘录编号一致。此有限流程不生成虚构候选人或其中的选择记录。

重新生成的主张和一致性发现一律使用低置信度。保留已有警示及其翻译，并加入新警示和
应用固定说明，明确这是仅依据已提供摘录、由 AI 重新生成且未经核实的报告。警示容量
不足时拒绝保存，不静默丢弃旧警示。证据不足时可以出现附有限制说明的空主张列表；
应用不会为了填满报告编造内容。引文存在性、结构和语言检查不证明语义支持、翻译准确、
身份或来源真实，也不保证免疫提示注入。

此次重新生成整份新报告，与改写一条既有主张不同；不会自动沿用未改动的旧主张。完整
旧报告仍保留在原路径和副本的精确来源快照中。预览不能自由改写生成结构；需要再次
生成时，应修改原始输入并复核新的请求。

### 存储与兼容

0.4 版本副本使用既有写入锁、大小限制和完整目录提交。`regeneration.json` 快照包含
所选更正编号、精确粘贴的摘录、已校验生成结构、上下文/请求校验和及 AI 重新生成归属。
生成前后及预览/保存时检查源文件、翻译和所选更正的精确字节。读取时从保存的输入重建
结果；校验和用于检测变化，不证明作者或模型实际运行。

副本保留完整原件快照和所选批注。全部快照、摘录及报告仍为**明文**，已有同步目录的
提供方可能会复制它们。保存不替换原件、不改动卡片或当前选择。此前 0.1 撤回、0.2 用户
提议及 0.3 AI 辅助副本仍可读取，不改写其文件。原始来源变化后，过期副本不能继续启用，
经过校验的历史副本仍可阅读。

所选重新生成报告在桌面、浏览器和访谈中仍为助手参考。完整摘录快照和更正文字不会被
自动发送为参考内容；复核副本目录仍从原始证据发现中排除。

### 验证与范围限制

合成测试覆盖两类报告、精确来源归属、严格同意、仅本地调用、无效/过大回复、过期数据
和请求、警示及原件保留、历史校验、消费者和桌面生命周期。最新测试/打包结果及另行
标明的真实本地模型结果见 [CURRENT_STATUS.md](../CURRENT_STATUS.md)；模拟回复不等于
真实模型验证。

为避开已确认的本地语法编译限制，发送给模型的生成结构要求字符串不超过 1,000 字符。
输入摘录不被截断，原有完整产物校验及历史副本保留既有范围。不修补输出，也不增加重试。
此前失败样例保留在[本地恢复证据](28_local_model_recovery.md)中；后续有限范围的真实模型
集成结果使用[成对格式](29_paired_report_generation.md)。

此功能针对明确粘贴的摘录，重新生成当前格式报告。任意旧格式迁移、自动文件选择、
原始来源真实性核实、加密存储及广泛模型质量验收仍为独立的后续工作。
