# User-proposed reinterpretation / 用户提出的重述

## English

### What the workflow does

After saving a correction against the current original report, open **Create
reviewed copy**, then **Rewrite one disputed claim**. Choose one correction and
read its original claim, quotations and source labels. Enter the proposed wording
in English and Simplified Chinese, inspect the complete bilingual preview, and
explicitly confirm saving a separate copy.

The result identifies the edited claim as a **user-proposed interpretation
(unverified)**. Its type is always **speculation** and its confidence always **low**.
The application preserves that claim's original topic, group, quotation text and
source labels. It does not verify that those quotations support the new wording,
that their source is authentic, or that the translations agree. Source labels are
displayed as text; they are never followed as file paths. This action calls no AI.

The saved correction is context for the review, not replacement evidence. The
editor starts with blank proposal fields; it does not automatically copy a note
into a report. A separate, explicit proposal is required. The operation edits one
claim per copy and still starts from the original report when another copy is
active. It does not merge edits from several copies or edit a selected copy in place.

### Review, preservation and uncertainty

The preview includes the original and proposed claim and the full bilingual
report. Editing a proposal or changing its selected correction invalidates both
preview and confirmation. A failed or stale save preserves the draft. Refreshing
does not authorize applying the wording to a different claim or source version.
Cancellation makes no new copy. Saving does not overwrite the original report,
correction note, compatibility card or current selection.

Other claims keep their wording and translations. All portrait consistency
findings, headlines and summaries are removed because they may depend on the
changed claim. A criteria copy instead removes all fictional candidates and their
recorded choices. Existing warnings remain, and a bilingual explanation of this
limited edit is added. A report whose warning list cannot fit that explanation is
rejected instead of dropping an existing warning. Remaining content has not been
reanalyzed and can still need correction.

Saved copies can be reopened in **Saved copies**. To use one, separately preview
and confirm it through **Select active report**. That choice follows the existing
version checks and interview protections described in
[active report selection](20_active_report_selection.md). Even after selection,
the copy remains an unverified assistant reference; it does not become original
user testimony. External disclosure still requires its own review.

### Storage and compatibility

`ReportRevisionService.preview_replacement` accepts a strict `ReplacementProposal`
containing one correction ID and separately bounded `text_en` and `text_zh` fields.
Both fields need their own language-content checks before attribution labels are
added. These checks establish format, not translation quality. The replacement
uses the attributed Chinese wording as its canonical source and an explicit
English mapping; the existing language-neutral artifact contract remains intact.

The preview binds exact source report, localization, candidate-file and selected
correction bytes, together with the complete proposal and derived outputs.
`save_replacement` requires strict boolean consent and regenerates and compares
the complete preview before committing. It reuses the reviewed-copy service's
bounded reads, link rejection, writer lock, staging directory and atomic directory
rename. Original report paths are never redirected.
History readers tolerate a valid staging name disappearing during that rename by
checking the parent again. Missing committed records, missing locks and unsafe
paths still fail closed; the exception does not hide a damaged history.

New reinterpretation copies use a version 0.2 manifest and a separate `proposal.json`
snapshot. Existing version 0.1 withdrawal copies retain their original format and
verification behavior. Both kinds share the existing bounded copy history. The
verifier reconstructs the result from its saved inputs, rather than trusting a
stored Markdown file or an integrity hash alone.

Snapshots, corrections and proposals are **plaintext**. Checksums can detect
inconsistent data; they do not protect against an operating-system account able
to rewrite the vault. The existing generated-history exclusions cover both copy
kinds. They cannot identify every arbitrarily copied or renamed piece of text.

### Verification and remaining work

Synthetic tests cover both report kinds, explicit consent, exact citations,
mandatory attribution and uncertainty, stale and tampered previews, invalid
language content, failed writes, history verification and selection consumers.
Older withdrawal copies are also checked for compatibility. GUI verification
covers edit/cancel/save, preserved drafts and both languages. Current integrated
test counts and package evidence are in [CURRENT_STATUS.md](../CURRENT_STATUS.md).
No mocked test is described as real-model validation.

Evidence-supported model regeneration, adding or replacing original evidence,
multi-copy edit merging and lossless legacy migration remain separate work.

## 中文版

### 此流程的作用

先针对当前原始报告保存一条更正，再打开**生成复核副本**，选择**改写一条争议主张**。
选择一条更正，阅读原始主张、引文及来源标识，然后分别输入英文与简体中文的新措辞，
检查完整双语预览，明确确认后另存副本。

结果将改写后的主张标为**用户提出的解释（未经核验）**，类型固定为**猜测**，置信度固定为
**低**。应用保留该主张的原主题、分组、引文文字及来源标识。它不验证这些引文能否支持新
措辞、来源是否真实，也不验证两种语言是否准确对应。来源标识仅作为文字展示，不会被当成
文件路径打开。此操作不调用 AI。

已保存的更正仅为复核提供背景，不构成替代证据。编辑器的新措辞输入框初始为空，不会将
批注自动复制进报告，必须另行明确提出重述。每份副本只改写一条主张，即使当前启用了其他
副本，仍从原始报告开始；不会合并多份副本的修改，也不会直接编辑当前选择的副本。

### 复核、保留与不确定性

预览展示原始与新主张，以及完整双语报告。编辑措辞或更换所选更正后，预览及确认均失效。
保存失败或版本过期会保留草稿。刷新不代表同意将措辞应用到不同主张或不同来源版本。
取消不会生成新副本。保存不会覆盖原报告、更正批注、兼容性卡片或当前选择。

其他主张保持原措辞及译文。画像副本会移除全部一致性发现、标题及摘要，因为它们可能依赖
已改写的主张；择偶标准副本则移除所有虚构候选人及其中记录的选择。保留原有警示，并加入
双语说明，解释此次有限改写。警示列表已满、无法容纳该说明时拒绝保存，不丢弃已有警示。
其余内容未经重新分析，仍可能需要更正。

可以在**已保存副本**中重新打开结果。如需启用，须另行通过**选择当前报告**预览并确认，
遵循[当前报告选择](20_active_report_selection.md)所述的版本检查与访谈保护。即使启用后，
副本仍是未经核验的助手参考，不会成为原始用户证言。对外披露仍须单独审核。

### 存储与兼容性

`ReportRevisionService.preview_replacement` 接受严格的 `ReplacementProposal`，其中包含一条
更正 ID 和分别限制长度的 `text_en`、`text_zh` 字段。添加来源归属标签前，两字段须分别通过
语言内容检查。这些检查只保证格式，不保证翻译质量。改写使用带归属标签的中文作为规范
来源，并提供明确的英文映射；既有的语言无关产物契约保持不变。

预览绑定精确的原报告、双语映射、候选人文件及所选更正字节，同时绑定完整提议和派生输出。
`save_replacement` 要求严格的布尔确认，提交前重新生成并比较完整预览。它复用复核副本服务
的有界读取、链接拒绝、写入锁、暂存目录及原子目录重命名，不重定向原始报告路径。
历史读取遇到符合格式的暂存名称在重命名期间消失时，会重新校验父目录。已提交记录缺失、
写入锁缺失及不安全路径仍会停止读取，这项例外不会掩盖历史损坏。

新的重述副本使用 0.2 版本清单及独立的 `proposal.json` 快照。已有 0.1 版本撤回副本保留
原始格式与校验行为。两类副本共用已有的有界历史。验证器会根据保存的输入重建结果，
不会仅信任存储的 Markdown 或完整性哈希。

快照、更正及提议均为**明文**。校验和可以发现数据不一致，但无法抵御能重写档案库的操作
系统账户。既有生成历史排除机制覆盖两类副本，无法识别任意复制或重命名后的全部文字。

### 验证与剩余工作

合成测试覆盖两种报告、明确同意、精确保留引文、强制归属与不确定性、过期或被改动的预览、
无效语言内容、写入失败、历史校验及选择后的读取。旧撤回副本也需通过兼容性检查。界面
验证覆盖编辑、取消、保存、草稿保留及两种语言。最新综合测试数量与程序包证据见
[CURRENT_STATUS.md](../CURRENT_STATUS.md)，不会将模拟测试称作真实模型验证。

有证据支持的模型重新生成、添加或替换原始证据、多副本修改合并，以及无损旧格式迁移，
仍是独立的未完成任务。
