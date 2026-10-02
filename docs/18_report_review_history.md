# Evidence review and correction history / 证据检查与纠错历史

## English

### Scope

The desktop self-portrait and mate-criteria viewers provide a local evidence-review
dialog. It shows each canonical claim, its observation/inference/speculation type,
model confidence, quoted evidence, source labels and report caveats. Source labels
are displayed as text; they are not instructions to open a file or URL. The dialog
does not fetch original files or call an AI provider. Quotation presence in an AI
request is not verification of authorship, source identity or truth.

The user can save a correction and its reason against one selected claim. This is
a **user-authored annotation**, not a verified replacement fact. It does not change
the original report, translations, exported card or fingerprint, and is not
automatically included in later AI input. The report viewers identify saved notes
separately. A subsequent explicit workflow can now withdraw selected disputed
claims into a separate [reviewed copy](19_reviewed_report_copies.md). Replacing
claims with new facts, regeneration and active-report changes remain future work.

### Core service and persistence

`services/report_review.py` owns report inspection and persistence independently
of PySide6. Only `self_portrait` and `mate_criteria` are supported. It reads the
corresponding fixed JSON filenames under the selected vault's `reports/`, validates
the canonical artifact contract, and exposes only existing claim paths. Old or
malformed reports are preserved and require explicit correction/regeneration;
opening the dialog does not migrate them.

Saving requires explicit confirmation and the digest of the report that was
reviewed. A stale digest is rejected so the user can refresh and compare the new
report. Each saved annotation is tied to that exact report version and includes
the original claim, proposed correction, reason and timestamp. Immutable records
and exact-source snapshots live under `reports/review_history/<kind>/`. A snapshot
preserves the complete original JSON bytes, including their formatting. History
for another report version remains identifiable rather than being attached to
a similarly numbered claim in a newer report.

Reads and writes have size and type limits. Fixed report kinds and claim paths,
containment checks and rejection of linked/reparse paths prevent ordinary path
substitution. Corrupt snapshots or records fail closed. Integrity hashes detect
inconsistent stored data; they do not authenticate the operating-system user or
defend against someone who can rewrite the entire vault. Concurrent processes
with access to the same operating-system account are not a security sandbox.

### Evidence and retention boundaries

`services/evidence_paths.py` centralizes automatic evidence-path checks for the
browser context collector, desktop collector and manual handoff manifest.
Generated reports, review history and reviewed copies remain excluded when selected directly as
an import root or reached through a linked alias. Known mixed AI interview
transcripts are excluded; separately saved user-only answers remain eligible.
Deliberate prior-report references use a separate fixed-filename allowlist and
bounded reader, with the same link/history rejection. They retain the unverified
assistant role and cannot become new owner evidence.
These checks identify application-managed outputs, not arbitrary copied or
renamed AI text. Users still choose and review the material they provide.

Saving a correction retains a plaintext report snapshot and plaintext annotation
in the chosen vault. Opening or canceling the dialog does not create history.
Regenerating a report does not delete its saved correction history. A synced vault
can be copied by its sync provider. There is no hidden upload or model call.
Encrypted storage, recovery, retention/deletion controls and lossless legacy
migration are separate remaining tasks; this feature does not encrypt the vault.

### Verification

Use synthetic fixtures for persistence/restart, stale reports, invalid claim paths,
corruption, consent types, file bounds, path substitution, and no-rewrite checks.
UI checks exercise save, cancel, refresh and plaintext rendering in both languages.
These are local deterministic tests, not additional live-model acceptance.

The integrated milestone passed 529 tests, with two Windows symlink-privilege
skips and one upstream deprecation warning. Actual junction and hardlink tests
passed. Four independent processes and 16 threads saved complete unique records.
Compilation, lint and both-language visual checks passed; no real vault was used.

## 中文版

### 范围

桌面的自我画像和择偶标准查看器提供本地证据检查对话框，展示规范报告中的每条主张、
观察/推断/猜测类型、模型置信度、证据引文、来源标签及报告限制。来源标签仅作为文字显示，
不会被解释为打开文件或网址的指令。对话框不抓取原始文件，也不调用 AI 提供方。
引文出现在 AI 请求中，并不代表其作者、来源身份或内容真实性已经核验。

用户可以针对选中的主张保存纠正内容与理由。这是**用户填写的批注**，不是已核验的替代事实。
它不会修改原始报告、翻译、导出卡片或指纹，也不会自动进入后续 AI 输入。报告查看器会将
已保存的批注单独标明。后续增加的明确流程现可撤回选中的争议主张，生成独立的
[复核副本](19_reviewed_report_copies.md)。用新事实替换主张、重新生成及变更当前报告仍待实现。

### 核心服务与持久保存

`services/report_review.py` 负责独立于 PySide6 的检查和保存行为，只支持 `self_portrait`
和 `mate_criteria` 两种报告。它读取所选档案库 `reports/` 下对应的固定 JSON 文件名，
验证规范报告契约，只提供实际存在的主张路径。旧版或格式损坏的报告会保留，须明确纠正或
重新生成；打开对话框不会自动迁移它们。

保存需要明确确认，并携带已审阅报告的摘要指纹。过期指纹会被拒绝，用户须刷新并对照新报告。
每条批注绑定该确切报告版本，记录原始主张、建议纠正、理由和时间。不可变记录及原始快照
位于 `reports/review_history/<kind>/`。快照保留完整原始 JSON 字节，包括排版。
其他报告版本的历史会被明确区分，不会附到新报告中碰巧具有相同编号的主张上。

读写有大小和类型限制。固定报告类型与主张路径、目录约束，以及拒绝链接和重解析路径，
可防止常见的路径替换。快照或记录损坏时会拒绝处理。完整性哈希能发现存储数据不一致，
但不能认证操作系统用户，也不能防御可以重写整个档案库的人。对同一操作系统账户下的
并发进程而言，这些措施不是安全沙箱。

### 证据与保留边界

`services/evidence_paths.py` 统一浏览器上下文、桌面材料收集和手动交接清单的自动证据路径检查。
直接将生成报告、纠错历史或复核副本选为导入根目录，或者通过链接别名访问，也不会使其成为原始证据。
已知混合 AI 访谈记录会被排除；另存的纯用户回答仍可使用。这些检查只能识别应用管理的产物，
不能识别任意复制或重命名后的 AI 文字。用户仍需选择、审阅自己提供的材料。

有意使用的旧报告参考另有固定文件名允许清单和有界读取器，同样拒绝链接和纠错历史。
这些材料保留为未经核验的助手角色参考，不能成为新的用户证据。

保存纠正会在所选档案库内保留明文报告快照和明文批注。仅打开或取消对话框不会创建历史。
重新生成报告不会删除已保存的纠错历史。同步目录中的档案库可能被同步提供方复制。
这里没有隐藏上传或模型调用。加密、恢复、保留/删除控制以及无损旧格式迁移仍是独立的待办
任务；本功能不会加密档案库。

### 验证

使用合成材料测试持久保存与重启、过期报告、无效主张路径、损坏数据、同意类型、文件大小、
路径替换及原文不被改写。界面测试覆盖中英文的保存、取消、刷新及纯文本显示。
这些属于本地确定性测试，不是新增的真实模型验收。

本轮综合验收为 529 项通过，两项因 Windows 符号链接权限跳过，另有一条上游弃用提示。
真实目录联接和硬链接测试通过，四个独立进程及 16 个线程均保存了完整且唯一的记录。
编译、静态检查及双语视觉检查通过，未使用真实档案库。
