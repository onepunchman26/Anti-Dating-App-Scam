# Reviewed report copies / 复核报告副本

## English

### What this action means

The desktop review workflow can create a separate report copy by withdrawing
claims that the user has disputed in saved correction notes. The user selects
notes for the current report version, previews the resulting bilingual report,
and explicitly confirms saving. This workflow makes no AI call and does not
invent replacement conclusions.

The original canonical report, translations, correction history, compatibility
card and current AI context remain unchanged. The saved copy is not automatically
made active or shared. A separate [explicit report selection](20_active_report_selection.md)
can now choose it for desktop viewing and interview reference. A separate
[user-proposed reinterpretation](21_user_proposed_reinterpretation.md) edits one
claim with unchanged quotations and mandatory attribution/uncertainty; that does
not establish factual support. Model-assisted supported regeneration and legacy
migration remain separate work. Saved copies reopen through the review interface.

### Transformation rules

Only saved correction IDs belonging to the exact current report digest can be
selected. Duplicate IDs are rejected; multiple distinct notes about one claim
withdraw that claim once. The service removes the selected structured claims and
keeps the surviving claims' text, evidence, type and confidence intact. Existing
translation entries are remapped by their original field paths, not by matching
similar text. No translation is invented.

A portrait copy also clears consistency findings and optional free-form headline
and summary fields, which could depend on withdrawn claims. A criteria copy clears
fictional candidate profiles and recorded candidate choices for the same reason.
The preview explains these changes. Fixed English and Simplified Chinese caveats
state that no replacement facts were established and that other report content
was not reanalyzed. Source coverage is a record of the supplied material, not proof
that every remaining conclusion is correct.

The revised canonical artifacts and complete localization map must pass existing
contracts before deterministic Markdown is rendered. Removing every claim is
valid if the required coverage and uncertainty fields remain. Unsupported legacy
formats, incomplete translations or a size-limit failure stop the operation;
existing files and warnings are not silently removed or truncated to make it fit.

### Preview, consent and persistence

`services/report_revisions.py` owns the transformation and storage independently
of the GUI. Previewing is read-only. Saving requires a strict affirmative
confirmation and revalidates the exact preview, current canonical bytes,
translation companion, relevant candidate artifact and selected correction
records. A changed report or translation requires another preview. Editing a
selection invalidates the UI's previous preview and confirmation.

Each committed copy lives under `reports/reviewed_copies/<kind>/<id>/`. It includes
the exact original source snapshots, selected correction records, revised
schema-valid artifacts, bilingual rendered reports and an integrity manifest.
Both the original report version and the new revision's creation time remain
identifiable. A complete staged directory is committed as one unit; failed or
interrupted writes do not replace the original files or expose a partial copy.

Saved-copy listing and reopening use fixed kinds and IDs, enforce path and size
limits and verify the stored manifest and report contents. The UI does not open
arbitrary paths supplied by report text. Linked/reparse paths and hardlinks are
rejected. Integrity checks detect inconsistent stored data; they do not prove
authorship, truth or protection against an operating-system account that can
rewrite the whole vault.

### Privacy and limitations

Copies and their original snapshots are plaintext in the selected vault. They
persist after report regeneration, and a sync provider can copy a synced vault.
The confirmation explains this retention. There is no hidden upload, model call,
automatic import into evidence or automatic change to a card fingerprint.

`reviewed_copies` is a reserved generated-output directory even when directly
selected as an import root, reached through aliases, or moved below a renamed
outer folder. Prior-report reference readers also exclude it. These checks do
not identify arbitrary copied bytes after all provenance filenames are removed.

Validation uses synthetic data for selection, translation reindexing, stale or
tampered previews, consent, corruption, concurrent saves, failures, restart and
GUI behavior. These tests are deterministic checks, not live-model validation.

The integrated gate passed **629 tests**, with two Windows symlink-privilege skips
and one upstream deprecation warning. Four simultaneous writer processes committed
four unique copies; a fifth fresh process reopened all four. Eight threaded saves,
staging input changes, disk failures, tampered output and preservation of originals
passed. Compilation, lint and EN/ZH portrait/criteria GUI checks passed. Portable
package evidence is maintained separately in `../CURRENT_STATUS.md`.

## 中文版

### 此操作的含义

桌面复核流程可以根据已保存的更正批注，撤回用户提出异议的主张，并生成独立的报告副本。
用户选择当前报告版本的批注，预览得到的双语报告，再明确确认保存。此流程不调用 AI，
也不创造替代性结论。

原始规范报告、译文、更正历史、兼容性卡片和当前 AI 上下文都保持原样。保存的副本不会
自动启用或分享。另行进行[明确报告选择](20_active_report_selection.md)，现可将其用于桌面
查看与访谈参考。另行进行[用户提出的重述](21_user_proposed_reinterpretation.md)，可以在保留
引文、强制归属与不确定性标记的条件下改写一条主张，这不证明事实支持。模型辅助的有依据
重新生成及旧格式迁移仍是独立任务。用户可通过复核界面重新打开已保存的副本。

### 转换规则

只能选择属于当前报告确切摘要指纹的已保存批注 ID。重复 ID 会被拒绝；同一主张下选择
多条不同批注，只撤回该主张一次。服务移除选中的结构化主张，保留其余主张的文字、证据、
类型和置信度。已有译文按照原始字段路径重新映射，不依赖相似文字匹配，也不编造新译文。

画像副本还会清除一致性推断，以及可选的自由格式标题和总结，因为它们可能依赖被撤回的
主张。择偶标准副本则清除虚构候选画像及记录的候选选择，理由相同。预览会说明这些变化。
固定的英文和简体中文限制说明会强调：没有建立替代事实，其余报告内容也没有重新分析。
资料覆盖描述的是提交过的材料，不证明所有保留结论都正确。

修订后的规范产物和完整双语映射必须通过已有契约，才能确定性渲染 Markdown。撤回全部
主张也可以有效，但必需的资料覆盖和不确定性字段必须保留。不支持的旧格式、不完整的翻译
或大小限制失败都会停止操作；不会为了凑合通过校验而静默删除、截断原文件或原有限制说明。

### 预览、同意与保存

`services/report_revisions.py` 独立于界面负责转换和存储。预览只读。保存要求严格的明确确认，
并重新验证确切预览、当前规范报告字节、翻译伴随文件、相关候选产物及选中的纠错记录。
报告或译文变化后须重新预览；修改选择会使界面中的旧预览和确认失效。

每个已保存的副本位于 `reports/reviewed_copies/<kind>/<id>/`，包含精确的原始来源快照、
选中的纠错记录、修订后通过结构校验的产物、双语渲染报告及完整性清单。原报告版本与新副本
的创建时间均可区分。完整的暂存目录会作为整体提交；写入失败或中断不会替换原文件，
也不会将不完整副本作为已完成结果显示。

副本列举和重新打开使用固定类型与 ID，限制路径和大小，并验证已保存清单及报告内容。
界面不会打开报告文字指定的任意路径。链接、重解析路径和硬链接会被拒绝。完整性检查
可以发现存储数据不一致，但不能证明作者身份、内容真实，也不能防御能够重写整个档案库
的操作系统账户。

### 隐私与限制

副本和其中的原始快照以明文保存在所选档案库内，重新生成报告后仍会保留。同步提供方可能
复制同步目录中的档案。确认文案会说明这种保留行为。这里没有隐藏上传、模型调用、自动
导入证据或自动修改卡片指纹。

`reviewed_copies` 是保留的生成产物目录：直接选它作为导入根目录、经由别名访问，或移动到
已改名的外层目录下，也会被排除。旧报告参考读取器同样排除它。不过，删除全部来源文件名
之后任意复制的字节，不能仅靠这些检查识别。

合成数据验证覆盖选择、译文重排、过期或被改动的预览、同意、损坏、并发保存、失败、重启
及界面行为。这些属于确定性检查，不是实际模型验证。

完整验收为 **629 项通过**，两项受 Windows 符号链接权限限制跳过，另有一条上游弃用提示。
四个同时写入的进程保存了四份不同副本，第五个新进程成功重新打开全部副本。八次线程并发
保存、暂存期间输入变化、磁盘失败、产物被改动及原件保留均通过验证。编译、静态检查及
中英文画像/择偶标准界面检查通过。便携程序验收证据另行维护于 `../CURRENT_STATUS.md`。
