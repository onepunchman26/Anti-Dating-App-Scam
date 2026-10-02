# Personal-profile layout migration / 个人档案目录布局迁移

## English

The historical layout kept `profile.mpm.md` and `profile.json` directly in the vault
root. The current desktop expects them inside `profile/`. This feature explicitly
copies those fixed members into the current layout. It is not conversion of arbitrary
profile schemas, reconciliation of Markdown with JSON, or report regeneration.

Choose **Open Existing Vault Folder** and select the old vault. A literal preview
shows the original files, missing companions, compatibility diagnostics and whether
the destination is empty. Review and explicitly confirm before any copy. Canceling
does not change the active vault, saved vault pointer or current in-memory profile.
A remembered legacy vault also offers an explicit migration action. If flat and
current files coexist, current files remain primary and migration refuses to merge.

Only the fixed root files are read. At least one must exist; Markdown-only and
JSON-only profiles are supported. Each file is bounded at 2 MB and the pair at 4 MB.
Text must be UTF-8; a BOM and original line endings are preserved. A JSON companion
must be an object conforming to the current `personal_profile.schema.json` contract.
Malformed JSON, duplicate keys, non-finite values and unsupported fields block the
copy rather than being stripped or assigned defaults. Unsupported originals remain
untouched and reviewable as literal text. Schema checks do not prove factual accuracy
or consistency between companions. No missing companion, translation, metadata or
evidence is invented.

Preview binds the selected vault, each file's presence and exact bytes, and the
destination state. Changes require a fresh preview. Explicit confirmation is checked
again by the core service; UI controls alone are not the enforcement boundary.
The service stages only the present files, verifies them, then publishes the complete
directory under a shared process/thread lock. A verified empty destination directory
can be removed and replaced; any nonempty destination blocks migration. A failed
publication may leave a hidden staging directory for later inspection, but never
shows a partly copied pair as a successful migration. Existing source bytes are
never overwritten or deleted. The checks are not an operating-system sandbox
against a malicious concurrent process with access to the same files.
Migration metadata and pending directories are excluded from original evidence and
generated-reference discovery, including when selected directly as an input root.

Successful migration copies only this profile pair within the same vault. Imports,
reports, archives and cards are not read or relocated. It performs no AI request,
upload, encryption or source-truth verification. Original flat copies remain
plaintext alongside the migrated copies, so future retention/deletion controls must
cover both. Sync providers may retain additional copies. Unknown historical profile
contents still need a separate, reviewed content-migration workflow.

The profile viewer now uses separate Markdown and read-only JSON views. Looking at
JSON cannot replace the Markdown draft or save JSON into the Markdown file. An absent
Markdown profile displays a placeholder rather than saveable sample text. Saving
Markdown does not silently synchronize JSON. When another vault is loaded, absent
companions clear the prior vault's values, and returning home cannot revive them
from the legacy-screen cache.

Implementation lives in `services/profile_migration.py`; desktop code handles only
preview, confirmation and switching the selected vault. Tests use synthetic files,
including BOM/CRLF, strict confirmation, destination conflicts, stale/tampered
previews, unsafe paths, failed saves and concurrency. Current integrated results
are in [CURRENT_STATUS.md](../CURRENT_STATUS.md). This is not real-profile migration
or a new real-model validation run.

## 中文版

历史布局将 `profile.mpm.md` 与 `profile.json` 直接保存在档案库根目录；当前桌面应用
要求它们位于 `profile/` 内。本功能明确复制这两个固定成员到当前布局，不转换任意档案
结构，不核对 Markdown 与 JSON 是否一致，也不重新生成报告。

选择**打开现有档案库文件夹**并选中旧档案库。按字面显示的预览会列出原文件、缺失的配套
文件、兼容性诊断及目标目录是否为空。复核并明确确认后才复制。取消不会改变当前档案库、
已保存的档案库指针或内存中的档案。已记住的旧版档案库也提供明确迁移入口。扁平文件与
当前文件并存时，以当前文件为主，迁移拒绝合并。

仅读取根目录的固定文件，至少须存在一个；支持仅 Markdown 或仅 JSON 的档案。每个
文件上限 2 MB，合计上限 4 MB。文本须为 UTF-8，保留 BOM 及原始换行。JSON 配套文件
必须是符合当前 `personal_profile.schema.json` 契约的对象。坏格式 JSON、重复键、非有限
数值及不支持字段会阻止复制，不会被删除或自动填默认值。不支持的原件保持不变，仍可按
原文复核。结构检查不能证明事实真实或配套文件一致；不会补造缺失文件、翻译、元数据或证据。

预览绑定所选档案库、每个文件的存在状态和精确字节，以及目标状态。变化后须重新预览。
核心服务会再次检查明确确认，保护不只依赖界面按钮。服务仅暂存实际存在的文件，校验后
在共享进程/线程锁保护下提交完整目录。经过校验的空目标目录可以移除后替换，任何非空
目标均阻止迁移。发布失败可能留下隐藏暂存目录供后续检查，但不会将只复制一半的文件对
显示为迁移成功。原始字节不会覆盖或删除。这些检查不是对拥有相同文件访问权的恶意并发
进程的操作系统级隔离。
迁移元数据和暂存目录从原始证据及生成参考的发现中排除，即使直接选为输入根目录也不读取。

成功迁移只在同一档案库内复制这对个人档案文件，不读取或移动导入材料、报告、存档或
卡片，不调用 AI、不上传、不加密，也不核实来源真实性。旧扁平副本仍以明文保留，与
迁移副本并存；未来保留期/删除功能须同时涵盖。同步服务可能保留额外副本。未知历史档案
内容仍须独立、经过复核的内容迁移流程。

档案查看器现分开显示 Markdown 草稿与只读 JSON。查看 JSON 不会替换 Markdown 草稿，
也不能把 JSON 保存到 Markdown 文件。没有 Markdown 时显示输入提示，不填入可保存的
样例文字。保存 Markdown 不会悄悄同步 JSON。加载另一档案库时，缺失的配套文件会清除
上一档案库的对应值，返回主页也不会从旧版界面缓存中重新带回。

实现位于 `services/profile_migration.py`，桌面界面只负责预览、确认与切换所选档案库。
测试使用合成文件，覆盖 BOM/CRLF、严格确认、目标冲突、过期/篡改预览、不安全路径、
保存失败及并发。综合结果见 [CURRENT_STATUS.md](../CURRENT_STATUS.md)。这不代表实际
迁移了私人档案，也不代表新增真实模型验证。
