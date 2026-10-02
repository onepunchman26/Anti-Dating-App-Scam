# Validated local artifacts / 本地产物验证契约

## English

`reports/local_artifacts.py` provides shared Pydantic contracts for the browser and
desktop: self-model, compatibility card, social self-portrait, desktop self-portrait,
mate criteria, fictional interview candidates, and relationship plan. Callers must
validate generated JSON before writing any associated Markdown/JSON, hashing,
signing, or exporting it. `artifact_schema_prompt()` supplies matching instructions
to the provider-neutral generation request; `validate_local_artifact()` rejects
unknown fields, wrong types, missing required content and oversized/nonfinite JSON.
Its exceptions do not echo the submitted payload.

Self-models and cards require nonblank evidence and uncertainty notes. Portrait
claims require at least one quote/source, observation/inference/speculation, and
word-only low/medium/high confidence. Consistency tensions require two pieces of
evidence, a clarifying question and an alternative benign explanation. Thin data
may produce no claims, with explicit coverage gaps and caveats. Criteria use the
same claim structure. Fictional candidates must be explicitly fictional adults;
reported user choices require interview evidence. Plans require a bounded list of
stages, cautions, and explicit uncertainty. Unrecognized scoring/diagnosis fields
are rejected rather than silently ignored.

Existing incomplete files are not silently rewritten. Existing viewers may still
read historical files; saving/exporting under the new contract requires review,
correction or regeneration. Validation preserves supplied fields, so fingerprint
inputs do not silently acquire defaults. Newly generated desktop portraits use the
evidence-first 0.2 contract, with optional bilingual headline/summary; historical
visualization files remain readable by the older tolerant renderer.

Structural validation does not establish that a quote is faithful, a source is
real, consent exists, prose is safe, or advice is correct. Those limits must remain
visible. This module has no network or filesystem side effects and performs no
automatic data migration. Synthetic negative tests cover unsupported scoring fields,
missing evidence/uncertainty, fabricated unsupported choices, malformed confidence,
underage fictional candidates, size limits and private error messages.

The separate [legacy archive workflow](22_legacy_report_archives.md) preserves raw
historical bytes in a validated archive envelope; it does not make unsupported
report content valid under these contracts. Compatibility diagnostics distinguish
primary structure from missing or invalid companions. Manual portrait and criteria
request builders now embed the shared connected-AI bundle schema, requiring exact
localization and validation before deterministic bilingual rendering. Those prompts
are instructions, not an enforced sandbox or atomic-write guarantee.

## 中文版

`reports/local_artifacts.py` 为浏览器端和桌面端提供共享 Pydantic 契约，涵盖自我模型、
兼容性卡片、社交自我画像、桌面自我画像、择偶标准、访谈虚构候选人和关系行动计划。
调用方必须先验证生成的 JSON，再写入相关 Markdown/JSON、计算指纹、签名或导出。
`artifact_schema_prompt()` 为与提供方无关的生成请求提供对应结构要求；
`validate_local_artifact()` 拒绝未知字段、错误类型、必需内容缺失，以及过大或包含
非有限数字的 JSON。异常信息不会回显提交的内容。

自我模型和卡片必须包含非空的证据说明与不确定性说明。画像中的每项论断至少需要一条
引文及来源，并区分观察、推断或猜测，以低、中、高文字描述置信度。一致性张力需要两条
证据、澄清问题和另一种善意解释。资料不足时允许不输出论断，但必须明确覆盖范围、缺口
和局限。择偶标准使用同样的论断结构。虚构候选人必须明确标记为虚构且成年；声称用户
作出的选择必须有访谈证据。行动计划需要数量受限的阶段、注意事项及明确的不确定性。
不支持的评分或诊断字段会被拒绝，而非静默忽略。

系统不会静默改写已有不完整文件。现有查看器仍可读取历史文件，但按新契约保存或导出
需要先审核、修正或重新生成。验证保留原先提供的字段，不会因自动添加默认值而改变指纹。
新生成的桌面画像采用强调证据的 0.2 契约，可附中英文标题和摘要；旧版宽容渲染器仍可
读取历史可视化文件。

结构验证不能证明引文准确、来源真实、已经取得同意、正文安全或建议正确；这些局限必须
保留说明。本模块不联网、不读写文件，也不自动迁移数据。合成反例测试覆盖不支持的评分
字段、证据或不确定性缺失、缺乏证据的虚构选择、无效置信度、未成年虚构候选人、体积限制
及不泄露原文的错误信息。

独立的[旧版存档流程](22_legacy_report_archives.md)以合规存档元数据保留原始历史字节，
不会使不受支持的报告内容通过本契约。兼容性诊断区分主结构及缺失或无效的配套文件。
手动画像及择偶标准请求现嵌入应用内 AI 共用的报告结构，要求精确翻译映射，并在确定性
双语渲染前完成校验。这些提示词是指令，不是强制隔离机制或原子写入保证。
