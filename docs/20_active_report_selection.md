# Active report selection / 当前报告选择

## English

### Explicit choice and scope

Saving a reviewed withdrawal copy does not activate it. **Select active report**
offers the current generated report and saved copies. Preview the full
bilingual content, confirm the choice, then select **Use this report**. Returning
to the generated report uses the same review and confirmation process. Original
report files and immutable copies are never overwritten by a selection.

The selection applies to desktop portrait/criteria readers, including their
detail actions, and to the portrait reference supplied to subsequent desktop
interviews. The browser's desktop-report fallback and manual interview handoff
also honor the selection. The browser's separately generated social portrait,
compatibility cards and their fingerprints remain separate artifacts; this action
does not revise them. Selecting a report performs no AI call or upload and does
not approve future external disclosure.

Evidence review and withdrawal creation still operate on the **original source
report**, which the UI labels explicitly. They do not edit the selected copy.
[Explicit user-proposed reinterpretation](21_user_proposed_reinterpretation.md)
adds another kind of separately saved copy that this selector can use. Model-assisted
supported regeneration and annotations against a revised copy remain future work.
A reviewed report remains an unverified interpretation;
selection does not make it owner testimony or establish factual accuracy.

[Partial legacy conversions](23_legacy_report_conversions.md) are another explicitly
selected target. The selector also offers **Legacy review only / disable active
report references** with its own preview and confirmation. This disables references
even when a target is invalid, without deleting files or falling back to the original.
An intact selection journal is still required. Choose a valid conversion or generate
and explicitly choose a current report to resume; regeneration alone does not resume.
Original/reviewed-copy events retain version `0.1`; conversion/review-only events
use `0.2`, with earlier bytes preserved in one verified chain. Converted copies
remain read-only and do not become new evidence or correction targets.

### Core state and version checks

`services/active_reports.py` owns selection independently of the GUI. It returns
a validated in-memory bundle of canonical fields, source-bound translations and
deterministically rendered Markdown. Consumers do not redirect original writer
paths or open a path supplied by a journal entry.

Each selection is a small, append-only event committed as a complete directory
under `reports/active_selections/<kind>/`. The journal records a sequence, previous
version digest, target identity, source/target digests, UTC time and integrity
checksum. It retains selection metadata, not another full report snapshot. Copy
snapshots remain in the existing reviewed-copy store. Both stores are plaintext.
Linked/reparse paths and hardlinks are rejected; reads, entries and history size
are bounded. Hashes detect inconsistent data, not a malicious operating-system
account able to rewrite the vault.

Preview and confirmation bind the preceding selection version, the exact current
canonical/translation/candidate files, and all verified copy contents. A copy
from an older generated bundle cannot be activated. A concurrent selection or
changed source requires a fresh preview. Both a selected copy and an explicitly
selected generated report are version-bound: regenerating or editing the source
requires a deliberate new choice. Saving never automatically activates a copy.

Without a selection journal, existing default/legacy behavior remains available.
Once a choice exists, stale or damaged content fails closed: viewers clear their
content and reference consumers stop. There is no silent fallback to the original.
A damaged selected copy can be deselected by previewing a valid generated report.
A damaged journal requires separate recovery; this milestone does not repair,
delete or replace that history automatically. The bounded journal reserves its
last available selection slot for returning to the generated report or disabling references.

### Interview continuity

An interview binds its report reference and vault identity when it starts. Sending
another turn or saving criteria checks that binding again. A selection change or
invalid report blocks continuation before discarding a draft. Requests check the
reference after disclosure review and before provider dispatch; stale replies are
discarded. Criteria generation checks again after model validation and before
writing reports, so a response to an earlier selection cannot silently become the
new criteria report when that change is detected. The existing criteria files are
still written sequentially; this check is not a filesystem transaction isolating
the entire save from concurrent operating-system processes.

Starting a new interview requires explicit confirmation when a conversation
already exists. The prior conversation remains readable under **Earlier interviews**
in that window, and the unsent draft stays intact. This temporary history is not
sent with the new interview and is not a persistent backup; copy desired text
before closing the application. Chat and archived text are displayed inertly.

Automatic evidence discovery excludes selection journals, correction history and
reviewed copies, including directly selected roots. Deliberate selected references
remain assistant-role material. These filename/path controls do not identify every
arbitrarily copied or renamed piece of generated text.

### Verification boundary

Use synthetic fixtures for strict confirmation, stale previews, journal chains,
corrupt-target recovery, write failures, concurrent choices, viewer consistency,
reference roles and interview draft/history preservation. Model stubs test race
handling without contacting a provider. Integrated results and package evidence
are recorded in `../CURRENT_STATUS.md`; synthetic tests are not live-model acceptance.

## 中文版

### 明确选择及适用范围

保存撤回后的复核副本不会将其启用。**选择当前报告**提供当前生成的报告及已保存
副本。请先预览完整双语内容，确认选择，再点击**使用这份报告**。返回生成报告也经过相同的
预览与确认流程。选择操作不会覆盖原始报告文件或不可变的复核副本。

选择适用于桌面的画像与择偶标准查看器及详细内容操作，也适用于后续桌面访谈使用的画像
参考。浏览器在回退使用桌面报告时，以及手动访谈交接，也会遵循该选择。浏览器单独生成的
社会画像、兼容性卡片及其指纹仍是不同产物，此操作不会修订它们。选择报告不调用 AI、不上传
数据，也不代表批准以后向外部提供方披露内容。

证据复核与撤回副本创建仍针对**原始来源报告**，界面会明确标注；它们不会编辑所选副本。
[明确提出用户重述](21_user_proposed_reinterpretation.md)增加了另一种可通过本选择器启用的
独立副本。模型辅助的有依据重新生成，以及针对修订副本添加批注，仍属于后续工作。复核报告仍是未经
核验的解释；选择它不会使其成为用户证言，也不能证明事实准确。

[旧报告部分转换](23_legacy_report_conversions.md)也可作为明确选择的目标。选择器还提供
**仅复核旧文件 / 停用当前报告参考**，要求独立预览与确认；即使目标无效也可停用参考，
不删除文件，也不回退至原报告，但仍要求选择记录完整。恢复时须选择有效转换，或生成并
明确选择符合当前格式的报告；单独重新生成不会恢复使用。原报告/复核副本事件保留 `0.1`，
转换/仅复核事件使用 `0.2`，早先字节不变，并作为同一记录链校验。转换副本仍只供阅读，
不会成为新证据或更正目标。

### 核心状态与版本检查

`services/active_reports.py` 独立于界面负责选择行为，返回经过校验的内存报告包，包含规范
字段、与来源绑定的译文及确定性渲染的 Markdown。使用方不会重定向原始写入路径，也不会
打开选择记录指定的任意文件路径。

每次选择作为一个小型、仅追加的事件，以完整目录保存于 `reports/active_selections/<kind>/`。
记录包含序号、前一版本摘要、目标身份、来源与目标摘要、UTC 时间和完整性校验和。它保留
选择元数据，不另存一份完整报告快照；报告快照仍位于已有复核副本存储中。两类存储均为明文。
链接、重解析路径和硬链接会被拒绝，读取、记录数及历史大小均受限制。哈希可以发现数据不一致，
但无法抵御能够重写整个档案库的恶意操作系统账户。

预览与确认绑定前一选择版本、当前规范报告/译文/候选人文件的精确字节，以及副本中全部经过
验证的内容。属于更早生成报告包的副本不能启用。并发选择或来源变化后须重新预览。所选副本
和明确选择的生成报告均绑定版本：重新生成或编辑来源后，须再次明确选择。保存副本不会自动启用。

没有选择记录时，保留既有默认与旧格式读取行为。一旦明确选择，过期或损坏的内容会停止使用：
查看器清空内容，参考读取停止，不会悄悄退回原报告。所选副本损坏时，可以通过预览有效的生成
报告来取消选择该副本。选择记录本身损坏则需要单独恢复；本里程碑不会自动修复、删除或替换
这段历史。有界记录会保留最后一个可用选择名额，用于返回生成报告或停用参考。

### 访谈连续性

访谈开始时绑定报告参考与档案库身份，发送下一轮或保存择偶标准前会再次检查。选择变化或
报告无效会阻止继续，并保留草稿。请求在披露审核后及实际调用提供方前检查参考版本，过期
回复会被丢弃。择偶标准生成在模型输出校验后、写入报告前再次检查，避免旧版本请求的回复
在检测到版本变化时被静默保存为新的择偶标准。现有择偶标准文件仍逐个写入；此检查不构成
能够将整次保存与其他操作系统进程完全隔离的文件系统事务。

已有对话时，开始新访谈需要明确确认。先前对话仍可在该窗口的**先前访谈**中查看，未发送
草稿也会保留。这些临时历史不会随新访谈发送，也不是持久备份；关闭应用前请复制需要保留
的内容。聊天及历史文字不会被解析为可执行内容、链接或图片。

自动证据发现会排除选择记录、纠错历史及复核副本，即使直接将它们选为根目录。有意使用的
所选报告仍作为助手角色参考。这些文件名与路径控制无法识别任意复制或重命名后的全部生成文字。

### 验证范围

使用合成材料验证严格确认、过期预览、记录链、损坏目标恢复、写入失败、并发选择、查看器
一致性、参考角色，以及访谈草稿与历史保留。模拟模型用于验证时序变化，不联系提供方。
综合结果及程序包证据记录于 `../CURRENT_STATUS.md`；合成测试不等于真实模型验收。
