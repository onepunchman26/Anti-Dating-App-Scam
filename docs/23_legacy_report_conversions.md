# Partial legacy conversion / 旧报告部分转换

## English

This workflow creates a separate, explicitly **partial and unverified** report from
an exact-byte legacy archive. It does not complete migration of every historical
format or the personal profile. No model is called, no original evidence file is
opened, and missing evidence, confidence or translations are never supplied.

### What can be copied

Historical portrait `0.3` claims and the older criteria `0.1` stated/revealed
criteria are eligible only when each entry already supplies supported topic,
claim type, confidence, exact quoted evidence and nonempty English and Simplified
Chinese wording. Criteria evidence may be an existing quote array, or an existing
quote string with its source. Unknown shapes and incomplete entries stay archived.
The archive's quoted wording is retained, not independently verified against the
named source; a source label is never treated as permission to open that path.

At least one complete claim is required to save or select a conversion. The older
narrative-only portrait example has none and remains archive-only. An empty rendered
preview is not a successful conversion. Existing top-level caveats must all have
complete bilingual wording within the current limits, or saving is blocked. Those
caveats are preserved alongside an explicit warning about partial conversion.

Other narratives, coverage claims, findings, open questions, fictional candidates,
choices and unsupported fields remain exactly in the linked archive. A ledger
distinguishes copied entries, partially copied entries and archive-only material.
Large field sets or exceptionally long field names receive an explicit grouping
notice; the full bytes remain in the archive. Coverage describes only the conversion
operation and records no original sources read. Structure checks cannot establish
truth, accurate translation, source identity or actual quotation support.

### Review, save, then select

1. In either report viewer, choose **Review legacy files**, preview and explicitly
   save an archive. Open the conversion dialog from the saved archive.
2. Choose **Preview conversion**, review the copied/archive-only ledger, the original
   archive and both report languages. Ineligible previews explain why saving is blocked.
3. Confirm **Save separate copy**. This does not activate the report or change cards.
4. Open **Select active report**, choose the partial conversion, preview it and
   separately confirm use. Desktop readers, desktop browser fallback and report
   references then use that verified selection. References keep the assistant role.

Converted reports are read-only. Existing evidence corrections, withdrawal copies
and user-proposed rewrites still target the original current-format report; they
do not edit converted claims. Their labels explain this scope.

Conversion preview and saving bind the archive's integrity and every fixed original
member's exact bytes and presence. A change requires a new archive/preview. Saved
conversions can be reopened as history after the originals change, but activating
or using them requires the same original source version. Reopening also requires
the intact linked archive and verifies that the saved report can be deterministically
derived from it. Changes to any saved member or archive companion fail closed.

### Explicit review-only state

Choose **Legacy review only / disable active report references**, preview and confirm
to preserve the files while disabling report references. This works even when the
selected target or original report cannot be validated, provided the selection
journal is intact. Readers show the disabled state and stop; they do not silently
fall back to the old report. The original files remain viewable in legacy review.
To resume, explicitly select a valid conversion, or generate a valid current report
and explicitly select it. Regeneration alone does not clear review-only mode.
This controls report references, not all AI features or separate browser products.
A damaged selection journal still requires separate recovery.

### Storage and compatibility

`services/legacy_conversions.py` owns conversion, and `services/active_reports.py`
owns selection. Atomic, lock-protected directories under
`reports/converted_reports/<kind>/<id>/` hold the canonical report, deterministic
bilingual rendering, preview ledger and a manifest linked to the archive. Each
kind allows 100 conversions and 128 MB total; each conversion is at most 16 MB,
its preview 8 MB and its manifest 16 KB. Failed pending writes are not committed
history. Existing records and originals are never overwritten or purged.

Conversion and review-only selection use journal events `0.2`; original and reviewed
copy events keep their existing `0.1` representation. Mixed histories are verified
as one chain without rewriting earlier records. The last available journal slot
is reserved for returning to a valid original or disabling references.

Conversions, archives and their aliases are excluded from original evidence
discovery. Hardlinks, unsafe paths and Windows reparse points are rejected. These
histories remain plaintext and may be copied by a sync provider; future encryption,
export, retention and deletion must cover them together. Hashes detect inconsistent
content, not authorship or malicious replacement of an entire history.

Validation uses synthetic fixtures, strict confirmation/stale/tamper checks,
cross-process saves and reopening, consumer isolation and bilingual GUI flows.
See [current results](../CURRENT_STATUS.md). This is not new real-model acceptance.
Full legacy/profile migration, source-supported model regeneration and recoverable
encryption remain separate unfinished work.

## 中文版

本流程从精确字节旧版存档生成独立报告，明确标记为**部分内容、未经核实**。这不代表所有
历史格式或个人档案已完成迁移。流程不调用模型，不打开原始证据文件，也不补造缺失的
证据、置信度或翻译。

### 可以复制哪些内容

历史画像 `0.3` 的主张，以及旧版择偶标准 `0.1` 的口头/实际标准，仅在每条原本就提供
受支持的主题、主张类型、置信度、精确证据引文，以及非空完整中英文表述时才可转换。
择偶标准可以使用已有引文数组，或已有的引文字符串及来源。未知结构和不完整条目保留在
存档中。存档内的引文按原样保留，不会独立核对命名来源；来源标签不会被当成打开该路径
的许可。

保存或选用转换至少需要一条完整主张。旧版纯叙述画像样例没有完整主张，仍只能存档。
空的报告预览不算转换成功。原报告顶层所有警示必须具备完整双语表述且符合当前数量限制，
否则拒绝保存；已有警示与明确说明部分转换限制的新警示共同保留。

其他叙述、覆盖声明、一致性发现、开放问题、虚构候选人、选择及不支持字段，全都精确保留
在关联存档中。字段清单区分已复制、部分复制及仅存档内容。字段过多或名称异常长时明确
说明合并展示，完整字节仍在存档中。覆盖说明仅描述转换操作，并记录未读取原始来源。
结构检查不能证明事实、翻译准确性、来源身份或引文实际支持关系。

### 复核、保存，再另行选择

1. 在任一报告查看器中选择**复核旧版文件**，预览并明确保存存档，再从已保存存档打开转换窗口。
2. 选择**预览转换**，复核复制与仅存档字段清单、原始存档及两种语言的报告。不合格预览会说明无法保存的原因。
3. 确认**保存独立副本**；这不会启用报告或改变卡片。
4. 打开**选择当前报告**，选择部分转换副本，预览后另行确认使用。桌面读取器、浏览器的桌面报告回退及报告参考随之使用经过校验的选择；参考保留助手角色。

转换报告只供阅读。已有证据更正、撤回副本及用户重述仍针对符合当前格式的原始报告，
不会编辑转换主张；界面标签明确说明此范围。

转换预览与保存绑定存档完整性、每个固定原始成员的精确字节及存在状态。变化后需要新的
存档与预览。原件变化后仍可作为历史重读已保存转换，但启用或使用时要求原始来源版本
一致。重读还要求关联存档完整，并校验保存报告确实能从存档确定性推导。任何保存成员或
存档配套文件变化，都会停止读取。

### 明确的仅复核状态

选择**仅复核旧文件 / 停用当前报告参考**，预览并确认后保留文件、停用报告参考。只要
选择记录完整，即使所选目标或原报告无法校验也可停用。读取器显示停用状态并停止使用，
不会悄悄退回旧报告；原文件仍可通过旧版复核查看。恢复时须明确选择有效转换，或生成
符合当前格式的有效报告后明确选择。单独重新生成不会解除仅复核状态。
此状态控制报告参考，不会关闭全部 AI 功能或独立浏览器产物。选择记录本身损坏仍须单独恢复。

### 存储与兼容性

`services/legacy_conversions.py` 负责转换，`services/active_reports.py` 负责选择。
`reports/converted_reports/<kind>/<id>/` 下使用锁保护和原子提交保存规范报告、确定性
双语渲染、预览清单及关联存档的校验清单。每种报告最多 100 份转换、总量 128 MB；每份
上限 16 MB，预览上限 8 MB，校验清单上限 16 KB。失败的暂存写入不属于已提交历史，
已有记录和原件不会覆盖或自动清除。

转换与仅复核选择使用 `0.2` 事件；原报告与复核副本选择保留既有 `0.1` 表示。混合历史
作为一条完整链校验，不改写早先记录。最后一个可用选择名额保留给返回有效原报告或停用参考。

转换、存档及其别名均从原始证据发现中排除。硬链接、不安全路径和 Windows 重解析点会
被拒绝。这些历史仍为明文，可能被同步服务复制；未来加密、导出、保留期和删除须共同
覆盖。哈希检测内容不一致，不证明作者身份，也不能阻止整段历史被恶意替换。

验证使用合成样例，覆盖严格确认、过期与篡改拒绝、跨进程保存与重读、使用方隔离及双语
界面流程。结果见[当前状态](../CURRENT_STATUS.md)，不代表新增真实模型验收。完整旧格式
及个人档案迁移、有来源依据的模型重新生成、可恢复加密，仍是独立的未完成工作。
