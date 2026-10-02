# Paired-language full report generation / 成对双语完整报告生成

## English

### Why the generation format changes

Recent local models returned complete-report replies that failed the required
translation mapping. They sometimes copied a quotation or source ID into a
canonical-text field, omitted a mapping, or repeated a path. Those replies were
rejected without replacing an original or changing the selected report. The
[local recovery record](28_local_model_recovery.md) distinguishes those failures
from CUDA startup and output-grammar compilation failures.

Full-report regeneration now asks the model to place each narrative's English
and Simplified Chinese wording together. For example, a claim's narrative is:

```json
{
  "en": "One note expresses a preference for morning conversations.",
  "zh": "一份笔记表达了对早晨交流的偏好。"
}
```

This is a fictional formatting example, not an assessment of a person. The model
does not also produce translation paths or repeat the English sentence as a
translation-source field. The application derives those mechanical fields from
the validated location of each pair. Both languages remain model output and need
review; deriving a mapping does not translate, correct or endorse the content.

This change applies only to **Regenerate a full report from original excerpts**
for current-format self-portraits and relationship criteria. Other report
generation, manual handoffs, one-claim revision and historical storage formats
retain their existing contracts.

### What the application validates and derives

The paired reply is a separate, strict generation format. Unknown fields,
missing language members, invalid types, blank text and unexpected report shapes
are rejected. A mixed reply containing the old `localized_text` mapping is also
rejected; the application does not try a second parser or another model request.

Every narrative item keeps its own pair: claims, questions, limitations, portrait
coverage and consistency-finding narratives, and the separate criteria/profile
limitations. Array order remains intact. Evidence quotations, source identifiers,
schema versions and enumerated labels keep their original typed fields; they do
not become translatable pairs. Fictional candidate lists remain empty because
this workflow contains no candidate exercise or choices.

After strict validation, the application uses each pair's English text as the
canonical narrative and constructs its exact path, source, English and Chinese
mapping. It does not infer missing sentences, merge limitations, shorten input
excerpts or silently discard unknown material. The result then passes the same
complete report, localization and per-source quotation validation as before.
The model-facing grammar still requests bounded strings; an accepted paired
reply must also satisfy the full application contract.

Each evidence quotation must be an exact contiguous substring of its particular
explicit excerpt, identified in submitted order as `S001`, `S002`, and so on.
Combining two excerpts or attributing one excerpt's words to another ID fails.
Quotation membership does not establish source authenticity, factual truth,
semantic support or translation accuracy. Language-character checks likewise
cannot establish whether a translation preserves meaning or strength.

All resulting claims and findings remain low confidence. Existing report
warnings and their translations survive along with the application-owned
AI-regenerated/unverified notice. A limit overflow rejects the copy instead of
dropping a warning to make it fit. Unsupported claims may remain absent; missing
information must not become an invented personality trait, requirement or ban.

### Request review, saving and activation

1. Select saved corrections and explicitly provide the original excerpts. Their
   existing quantity and size bounds remain. Corrections are unverified context;
   they do not become evidence or authorize reading source files.
2. Prepare and read the complete local request. It includes the paired output
   schema, instructions and exact submitted data. A request reviewed under the
   older generation format cannot reuse its approval after this change.
3. Explicitly approve one local Ollama call. Changes to the request, selected
   notes or bound report invalidate it. There is no automatic retry, output-format
   fallback, cloud routing or model download in this workflow.
4. Read both rendered languages after validation. Check interpretation, scope,
   frequency, intensity and uncertainty against the excerpts. A wish must not
   silently become a requirement, and one episode must not become a stable trait.
5. Confirm saving a separate copy only after reviewing the preview. Original
   reports and the current selection remain unchanged. Activating the new copy
   requires a separate deliberate selection.

The stored copy still uses version **0.4** and the existing canonical report plus
`localized_text` contract. Existing viewers, browser references, immutable history
and active-report consumers receive the same format. The proposal snapshot keeps
the validated canonical bundle, excerpts and request/context digests; a digest
binds recorded values but does not prove execution or provenance. This format
change does not migrate old copies or rewrite their files.

Saved excerpts and old source snapshots remain plaintext within the explicitly
saved copy. They do not become automatically discoverable original evidence.
Only the selected generated report can become an attributed, unverified reference
for a later workflow; its unquoted excerpt contents and correction notes are not
silently supplied as new user evidence. See the existing
[full-regeneration boundaries](27_full_report_regeneration.md) and
[report-selection rules](20_active_report_selection.md).

### Verification scope

Independent integration checks inject synthetic replies through the normal local
adapter, then exercise preparation, validation, separate saving, fresh reopening,
deliberate activation and existing desktop/browser consumers. They check that all
supplied narrative pairs survive, old warnings remain, and original bytes and a
previous nonempty report selection are preserved until explicit activation.
Malformed pairs, unexpected fields, language failures and incorrect quotation
sources must fail after one injected call without saving a generated copy.

These are offline structural and workflow checks, not actual-model validation or
proof of good relationship advice. Real local model acceptance is reported
separately in the current status and progress tracker after an explicitly chosen
synthetic run. Public-release readiness, paid/remote models, arbitrary historical
content migration and broad semantic or translation reliability are outside this
format change.

### Actual local examples and manual review

On 2026-09-28, three explicitly chosen synthetic requests used already installed
local models. Each made one actual request, with the exact prepared request checked
and schema fallback disabled. These runs used the core smoke flow, not live GUI
clicks. No automatic retry or additional model correction was performed.

| Model and report | Result | Whole-run time |
| --- | --- | --- |
| qwen3.5:latest, self-portrait | Reply rejected: claim text was a plain string with a sibling Chinese field, and claim evidence was missing; no copy saved | 8.56 s |
| gemma4:latest, self-portrait | Paired reply, exact source quotations, complete localization, separate save and fresh reopening passed | 15.70 s |
| gemma4:latest, relationship criteria | Paired reply, exact source quotations, complete localization, separate save and fresh reopening passed | 3.39 s |

All three preserved original bytes and the existing nonempty selection record.
These durations describe individual local runs, including setup and validation;
they are not performance benchmarks. The normal CLI keeps metadata only and marks
semantic review as not performed. For these particular runs, an additional
temporary recording transport retained only the synthetic replies for separate
manual review. This did not add a model call or repair a reply.

Independent comparison against the fictional input found the portrait's two
claims limited to one tired pause and one request to speak the next morning.
It explicitly denied a recurring pattern and invented no contradiction. However,
the Chinese wording changed “asked” to the stronger “要求”, and “该个人” is stilted.
The first claim's `pattern` topic is a category even though its narrative denies
a stable pattern; the coverage summary mentions only the first excerpt. These
are review limitations, not grounds to infer a personality trait.

The criteria example kept the stated wishes as wants/preferences, left revealed
criteria and fictional candidates empty, and put the lack of past choices in a
caveat. Its English “their photos” has an ambiguous referent; the Chinese “我的照片”
matches the input. “征得同意” makes the original request to ask before sharing more
explicit, and “理想人设” is an awkward label for ideal profiles. The original model
wording was not silently edited to remove these issues.

This is limited acceptance of the two local integration paths with identified
wording caveats. It does not certify flawless translation, semantic support for
every future report, broad model reliability or public-release readiness. Review
both languages before using any generated interpretation; the failed qwen3.5
sample shows that grammar-guided generation still needs full application validation.

## 中文版

### 为什么调整生成格式

近期本地模型返回的完整报告回复未能通过必需的翻译映射校验。有些回复把引文或来源编号
复制进应填写规范原文的字段，有些遗漏映射或重复路径。这些回复均被拒绝，没有替换原件，
也没有改变当前报告选择。[本地恢复记录](28_local_model_recovery.md) 将这些问题与
CUDA 启动故障、输出语法编译故障分别记录。

完整报告重新生成现在要求模型将每段叙述的英文和简体中文放在一起。例如，一条主张的
叙述部分使用以下形式：

```json
{
  "en": "One note expresses a preference for morning conversations.",
  "zh": "一份笔记表达了对早晨交流的偏好。"
}
```

这只是虚构的格式示例，不是对任何人的判断。模型不再同时编写翻译路径，也不再把同一句
英文重复填入翻译来源字段。应用根据通过校验的每个语言对所在位置，生成这些机械性字段。
两种语言仍由模型提供，都需要复核；生成映射不等于翻译、修正或认可其中内容。

本次改动只适用于当前格式的自我画像和择偶标准中的**根据原始摘录重新生成完整报告**。
其他报告生成、手动交接、单条主张修订及历史存储格式继续使用原有契约。

### 应用校验什么、生成什么

成对回复是独立且严格的生成格式。未知字段、缺少一种语言、类型错误、空白文字及非预期
报告结构都会被拒绝。混入旧 `localized_text` 映射的回复也会被拒绝；应用不会尝试另一套
解析方式，也不会再次请求模型。

每个叙述项目都保留独立的语言对，包括主张、问题、局限性、画像覆盖范围与一致性发现，
以及择偶标准和虚构档案部分各自的局限性。数组顺序保持不变。证据引文、来源编号、结构
版本和枚举标签保留原有的带类型字段，不变成待翻译的语言对。由于本流程没有候选人练习
或选择，虚构候选人列表仍必须为空。

严格校验之后，应用使用语言对中的英文作为规范叙述，并生成对应的准确路径、原文、英文
及中文映射。它不推断缺失句子、不合并局限性、不缩短输入摘录，也不静默丢弃未知内容。
随后结果仍须通过原有的完整报告、本地化及逐来源引文校验。提供给模型的生成语法继续
限制字符串长度；被接受的成对回复也必须满足完整应用契约。

每条证据引文都必须精确且连续地出现在其指定的明确摘录中。来源按提交顺序编号为
`S001`、`S002` 等。拼接两份摘录，或把一份摘录中的话标成另一来源，都会失败。
引文存在性不能证明来源真实、事实属实、语义支持或翻译准确。语言字符检查同样不能证明
译文保留了原意和表述强度。

所有生成主张和一致性发现仍固定为低置信度。既有报告警示及译文会与应用自行加入的
AI 重新生成／未经核实说明一同保留。超过限制会拒绝副本，不会为适应上限而删除警示。
没有支持的主张可以为空；信息缺失不能被补写成虚构的人格特质、硬性要求或禁令。

### 请求复核、保存与启用

1. 选择已保存的更正，并明确提供原始摘录。原有数量和大小限制继续生效。更正属于未经
   核实的背景，不会变成证据，也不授权读取来源文件。
2. 准备并阅读完整本地请求，其中包含成对输出结构、指令及准确提交的数据。
   按旧生成格式复核的请求，在格式改变后不能沿用原有批准。
3. 明确同意一次本地 Ollama 调用。请求、所选批注或绑定报告发生变化后，请求会失效。
   本流程不会自动重试、回退输出格式、转向云端或下载模型。
4. 校验通过后，阅读两种语言的渲染结果。对照摘录检查解释、范围、频率、强度及
   不确定性。愿望不能静默变成要求，单次经历也不能变成稳定特质。
5. 复核预览之后，另行确认保存独立副本。原报告和当前选择保持不变。
   启用新副本仍需单独明确选择。

保存副本继续使用 **0.4** 版本，以及原有的规范报告加 `localized_text` 契约。
已有查看器、浏览器参考、不可变历史及当前报告消费者收到的格式相同。
提议快照保存通过校验的规范报告、摘录和请求／背景摘要；摘要绑定记录的值，但不能证明
模型实际执行或内容来源。此次格式修改不会迁移旧副本，也不会改写其文件。

保存的摘录及旧来源快照仍以明文保存在用户明确保存的副本中，不会自动成为可发现的
原始证据。只有被选择的生成报告才能作为有明确归属、未经核实的参考进入后续流程；
其中未引用的摘录内容及更正批注不会被静默当成新的用户证据。详见原有的
[完整重新生成边界](27_full_report_regeneration.md) 与
[报告选择规则](20_active_report_selection.md)。

### 验证范围

独立集成检查通过正常本地适配器注入合成回复，依次检查准备、校验、单独保存、全新重读、
主动启用及已有桌面／浏览器消费者。检查确认所有提供的叙述语言对均保留，旧警示仍在，
原件字节和之前非空的报告选择在明确启用前不变。格式错误、未知字段、语言问题及错误
引文来源必须在一次模拟调用后失败，不保存生成副本。

这些是离线结构和流程检查，不是真实模型验证，也不证明恋爱建议质量。
真实本地模型验收仅在明确选择的合成运行后，另行记录于当前状态与进度表。
公共发布条件、付费／远程模型、任意历史内容迁移，以及广泛的语义或翻译可靠性，均不属于
此次格式改动的范围。

### 真实本地样例与人工复核

2026-09-28，三次明确选择的合成请求使用了本机已经安装的模型。每次都只实际请求一次，
检查了准确准备的请求，并禁用了结构回退。这些运行使用核心检查流程，不是实时点击 GUI
的测试。没有自动重试，也没有增加模型纠错调用。

| 模型与报告 | 结果 | 整次运行耗时 |
| --- | --- | --- |
| qwen3.5:latest，自我画像 | 回复被拒绝：主张文字是普通字符串，中文另放在同级字段，且缺少主张证据；没有保存副本 | 8.56 秒 |
| gemma4:latest，自我画像 | 成对回复、准确来源引文、完整本地化、单独保存及全新重读通过 | 15.70 秒 |
| gemma4:latest，择偶标准 | 成对回复、准确来源引文、完整本地化、单独保存及全新重读通过 | 3.39 秒 |

三次运行均保留了原件字节及原有非空选择记录。这些耗时描述单次本地运行，包含准备和
校验，不是性能基准。正常 CLI 只保存元数据，并将语义复核标记为未进行。
对这几次特定运行，额外的临时记录传输只保留合成回复，供另行人工复核；这没有增加
模型调用，也没有修补回复。

独立对照虚构输入后，画像的两条主张仅描述了一次疲倦时的停顿，以及一次希望次日早晨
再谈的请求。它明确否认存在反复模式，没有虚构矛盾。不过，中文把“asked”译为更强的
“要求”，“该个人”也不够自然。第一条主张的 `pattern` 是主题分类，但其叙述明确否认
稳定模式；覆盖摘要只提到了第一份摘录。这些是需要复核的局限，不能据此推断人格特质。

择偶标准样例把陈述的愿望保留为期待／偏好，行为揭示标准及虚构候选人为空，并把缺少
过去选择放入警示。其英文“their photos”指代不够明确，中文“我的照片”则与输入一致。
“征得同意”比原文“分享前先询问”的说法更明确，“理想人设”作为理想档案的名称也不够
恰当。没有通过静默修改模型原文来消除这些问题。

这构成两条本地集成路径的有限验收，并明确保留上述措辞局限。它不认证翻译毫无问题、
今后每份报告都有充分语义支持、模型普遍可靠或已经满足公共发布条件。使用生成解释前
仍须复核两种语言；qwen3.5 的失败样例表明，即使使用生成语法约束，完整应用校验仍不可缺少。
