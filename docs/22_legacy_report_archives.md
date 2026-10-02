# Legacy report preservation / 旧版报告保留

## English

This is the preservation stage of migration. It does not convert an old report
into a current report, repair its evidence, or migrate the personal profile.
The desktop portrait and criteria viewers expose **Review legacy files** even
when the current report cannot be selected. Open it to inspect compatibility
diagnostics, original content and a complete archive preview. Explicit confirmation
saves a separate archive; saved archives can be reopened after the originals change.
Original HTML and Markdown are shown as literal text, with no links or resources
executed. Non-UTF-8 files retain their bytes but have no text preview. Original
language, BOM and line endings are preserved in storage; the widget's text view is
only a review aid. The app does not invent missing translations or evidence.

`services/legacy_reports.py` owns inspection, preview, saving and verification.
It reads only fixed filenames immediately under the selected vault's `reports/`:

| Report kind | Fixed files |
| --- | --- |
| Self-portrait | `self_portrait.json`, `self_portrait.md`, `self_portrait.detailed.md`, `self_portrait_localization.json`, `self_portrait.html` |
| Criteria | `mate_criteria.json`, `mate_criteria.md`, `mate_criteria_localization.json`, `ideal_partner_profiles.json` |

No directory-wide import or arbitrary snapshot path is accepted. Unknown fields,
unsupported historical scoring fields, invalid JSON and invalid UTF-8 remain in
the exact original snapshot; preserving them does not validate or endorse them.
The field ledger lists top-level JSON fields, with an explicit whole-document
fallback for malformed or unusually large objects. It never silently drops data.
Archives use a validated envelope around opaque source bytes. Source report
validation remains strict for active reports, export and AI consumers.

Historical portrait `0.3` uses narrative fields that differ from the current
evidence-first `0.2`. Both historical and current criteria may say `0.1` but have
different shapes. Inspection uses structure, not numerical version ordering;
current canonical JSON alone does not guarantee a usable localized report bundle.
Checks report missing or invalid companions separately. The personal profile's
separate `0.1` contract is outside this workflow.

Saving binds both the presence and absence of every fixed file, exact bytes and
the full preview. The user must preview again after any source change. One file
may contain at most 2 MB and the source bundle at most 10 MB; oversized input is
rejected without truncation. A staged directory is verified before atomic rename
into `reports/legacy_archives/<kind>/<id>/`. A shared thread/process lock protects
writers. Each kind allows at most 100 committed archives and 256 MB total; each
archive is bounded at 80 MB, including encoded previews. Failed pending saves
never appear as committed records. Older committed records are not deleted.

Every reopen verifies the full manifest, hashes, fixed-member set and derivation
of diagnostics/preview from the raw bytes. A changed companion prevents reading
even an otherwise intact member. Hashes detect inconsistency, not authorship or
truth, and are not signatures against someone able to replace an entire archive.
Unsafe paths, symbolic links, Windows reparse points/junctions and hardlinks are
rejected. Archives are excluded from original evidence discovery even when an
archive subtree is selected directly or an outer folder is renamed.

Saving does not replace originals, activate a report, alter cards or make an AI
request. A saved archive now offers a separate [partial conversion workflow](23_legacy_report_conversions.md)
with its own preview, confirmation and subsequent selection; archiving itself does
not perform those steps. There is no restore-to-original-path or deletion button.
Snapshots are plaintext and may be copied by a sync provider. Future
retention, deletion and recoverable encryption must include these snapshots.
Full legacy conversion and personal-profile migration remain unfinished.

Manual portrait/criteria handoffs now embed the same generated bundle schemas as
the connected desktop flow. They require complete localization, original user
quotations, validation before writes and deterministic bilingual rendering. A
prompt alone cannot enforce those checks, isolation or atomic saving. Existing
saved request files must be regenerated to receive the new contract; merely
opening the application does not rewrite them.

## 中文版

这是迁移中的原文保留阶段，不会将旧报告转换成当前有效报告，不会修补证据，也不会迁移
个人档案。桌面画像和择偶标准查看器提供**复核旧版文件**入口，即使当前报告无法选择也能
进入。可以查看兼容性诊断、原始内容和完整存档预览；明确确认后另存一份存档，原文件变化
后仍可重读。原始 HTML 和 Markdown 按字面文本展示，不执行链接或外部资源。非 UTF-8
文件保留全部字节，但不提供文本预览。保存时保留原始语言、BOM 和换行；界面文本仅辅助
复核。应用不会编造缺失的译文或证据。

检查、预览、保存和验证由 `services/legacy_reports.py` 负责，只读取所选档案库
`reports/` 目录下的固定文件：

| 报告类型 | 固定文件 |
| --- | --- |
| 自我画像 | `self_portrait.json`、`self_portrait.md`、`self_portrait.detailed.md`、`self_portrait_localization.json`、`self_portrait.html` |
| 择偶标准 | `mate_criteria.json`、`mate_criteria.md`、`mate_criteria_localization.json`、`ideal_partner_profiles.json` |

不接受整目录导入或任意快照路径。未知字段、不受支持的历史评分字段、无效 JSON 和无效
UTF-8 都保留在精确原始快照中；保留不代表认可或校验通过。字段清单列出 JSON 顶层字段；
无法解析或字段异常多时明确按整份文档展示，不会静默丢弃内容。存档以合规元数据封装原始
字节，当前报告、导出和 AI 消费者仍执行严格的来源报告校验。

历史画像 `0.3` 使用叙述字段，与当前强调证据的 `0.2` 不同；历史及当前择偶标准都可能
标记为 `0.1`，但结构不同。诊断依据结构，不按版本号数值排序。仅规范 JSON 合规，并不
保证整套双语报告可用；缺失或无效的配套文件会另行报告。个人档案另有独立的 `0.1` 契约，
不属于本流程。

保存绑定每个固定文件的存在或缺失状态、精确字节及完整预览。来源变化后必须重新预览。
每个文件上限为 2 MB，来源总量上限为 10 MB；超限会拒绝，不截断。临时目录校验完成后
以原子重命名方式提交到 `reports/legacy_archives/<kind>/<id>/`，共享线程和进程锁保护
并发写入。每种报告最多保留 100 份已提交存档、总量 256 MB；每份存档包含编码后的预览，
上限为 80 MB。失败的暂存记录不会显示为已提交存档，旧有已提交记录不会删除。

每次重读都核验完整清单、哈希、固定成员集合，以及原始字节对应的诊断和预览。任意配套
文件变化后，即便某一成员未损坏，也会拒绝读取。哈希检测不一致，不证明作者身份或内容
真实；能够替换整份存档的人仍可重算哈希，这不是数字签名。不安全路径、符号链接、Windows
重解析点或目录联接，以及硬链接都会被拒绝。即使直接选择存档子目录或重命名外层目录，
存档内容仍会从原始证据发现中排除。

保存不覆盖原件、不启用报告、不修改卡片，也不调用 AI。已保存存档现提供独立的
[部分转换流程](23_legacy_report_conversions.md)，另行预览、确认并随后选择；存档本身不会
执行这些操作。不提供恢复至原路径或删除按钮。快照是明文，可能被同步服务复制；后续
保留期、删除及可恢复加密功能必须涵盖这些快照。完整旧格式转换及个人档案迁移仍未完成。

手动画像和择偶标准交接现嵌入与应用内桌面流程相同、由程序生成的报告结构，要求完整翻译
映射、用户原始引文、写入前校验及确定性双语渲染。但提示词本身不能强制执行这些检查、
隔离或原子保存。已有交接请求文件需要重新生成才能获得新契约；仅打开应用不会改写它们。
