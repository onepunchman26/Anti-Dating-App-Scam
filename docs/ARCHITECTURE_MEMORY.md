> Current authority / 当前权威：The October 21 continuity map in [PRODUCT_CONTINUITY.md](../PRODUCT_CONTINUITY.md) preserves the core purpose while identifying superseded entry-point restrictions. Dated implementation claims below are historical; current acceptance is in [CURRENT_STATUS.md](../CURRENT_STATUS.md). / 10月21日连续性对照保留核心用途并明确已替代的入口限制；下方带日期的实现记录为历史，最新验收见当前状态。

# Architecture Memory / 架构记忆

## English — 0.7 replacement direction, October 18, 2026

This document allows the next agent to continue without relying on chat memory.
The original Anti-Dating-App-Scam repository remains the authoritative AI-SlowMatch
project. Do not clone a replacement product, change the original remote, overwrite
unrelated work or place private data in source control.

The current product center is the user's ChatGPT desktop conversation, focused
plugin Skills, the existing Python local core and an authenticated Sites matching
service. The owner accepts OpenAI cloud analysis of the necessary authorized
personal information. This does not authorize Sites or other users to receive the
complete profile, raw conversations or private assessments.

```text
ChatGPT + focused Skills
  -> local Python contracts and guarded storage
  -> exact reviewed summary and separate publication approval
  -> Sites-authenticated summary storage and reciprocal discovery
  -> peer's permitted summary back to the user's own ChatGPT
  -> private interpretation saved locally
```

The local profile is the durable source for personal understanding. Claims include
sources, confirmation, time, uncertainty and corrections; unknowns stay unknown.
No founder profile supplies default answers. Profile edits, summary drafts,
publication approvals and private reports are separate objects and permissions.

Python remains useful because the project already has typed models, report
validation, guarded file I/O, evidence/history handling, memory migration and tests.
Reuse those modules. The local CLI contains no replacement model client or website
AI proxy. New local state defaults outside OneDrive and Git at
`%LOCALAPPDATA%/AI-SlowMatch/work`; paths must be resolved and checked. Existing
vaults are not scanned or relocated automatically. State is plaintext unless a
specific artifact explicitly implements encryption.

Sites uses its supported Worker/D1 runtime. A Python/FastAPI server cannot be
assumed deployable unchanged. A small hosted implementation is justified by the new
mode-specific summary and minimal joint-planning service; it does not replace the Python core or create another primary
chat application. Server ownership comes from Sites-verified request identity,
never a tool argument. Every response respects active visibility and reciprocal
conditions. Candidate labels are untrusted data, not authority to read or upload.

The original source tree owns `apps/matching_site/`. Sites' required hosted source
repository is a one-way deployment mirror. Record exact source/deployment versions;
make source changes here and synchronize deliberately. Runtime files, credentials,
private profiles and synthetic test identities never become production seed users.

The fixed 0.5.3 `AI-SlowMatch.exe` was validated before this migration and remains
the recovery/legacy entry. Its release evidence stays intact. Version 0.7.0 extends the historical 0.6.0 source checkpoint; neither
source version implies an EXE replacement without its own build receipt. PySide6
remains a utility shell; FastAPI remains optional. Tauri, a second desktop chat
client, Ollama default inference and federation are not first-version migration
work. Earlier design records preserve their history, not active requirements.

JSON/Pydantic contracts remain the interchange boundary. Validate before saving,
exporting, signing or displaying trusted report data. An approval digest verifies
content equality; it is not a signature or proof that a person consented. A digital
signature can establish integrity under a trusted key, but cannot prove source
authenticity, completeness, wrongdoing, truthful preferences or relationship safety.
Encryption protects confidentiality and is separate from validation and signing.
Do not turn private reflection into a diagnosis, morality label or precise match score.

Verification must distinguish source implementation, installed Skill discovery,
local process persistence, hosted deployment, live MCP connection and independent
account acceptance. Native Codex Skill loading is one observed channel; it does not
prove desktop Work or other-user distribution. A generated ZIP is a source/package
artifact until installed. The 0.6 private pilot was deployed; a registration alone would not prove that.
The current 0.7 deployment/test outcome must be read from the live evidence records.
Current evidence and unresolved external prerequisites belong in
`CURRENT_STATUS.md` and `PROGRESS_TRACKER.md`.


The full owner-authorized replacement attachment, not the earlier truncated prompt, governs
this iteration; see ADR-015 and the R1–R7 plan. Romance and friendship opt in independently.
Private relationship observations/reflections, local protective filters, activity planning,
preparation, user-initiated in-meeting support and optional consented audio are current scope.
Sites may store only reviewed summaries/necessary state plus individually approved minimal
planning preferences, versioned proposals/confirmations and selected feedback with purpose,
recipient and expiry. No raw material, transcript, risk reason or private report is shared.

Shared context must be built only from approved objects; the local deterministic
`planning-suggest` reads typed shared context/public-place evidence without private-store reads
or model calls. A private-context chat cannot simply promise secrecy and export its narrative.
Each participant approves their own fields/current plan. Updates invalidate prior confirmation;
local approval withdrawal does not replace the remote withdrawal call. No automatic invitation,
reservation, payment, calendar, location tracking or recording. Personal help never needs the
peer's consent. Distinguish mismatch, unclear evidence and concrete behavior concerns.

The new support service keeps current records under `relationship-support/state.json`, managed
short WAVs under `relationship-support/audio`, and content-free revision metadata. Material
preview is owner-local and returns a path; do not read it into the model before cloud permission.
Corrections revoke earlier cloud approval/linked reports. Expiry/deletion acts on a subsequent
operation/sweep, not a background scheduler. Original selected files and external copies remain.
Short WAV import is 0.1–30 seconds, not full-meeting recording. The recognizer dependency is
installed in the audited runtime but English/Chinese models are absent; no new real recognition
or physical microphone acceptance is claimed and no model download was performed.

At this documentation checkpoint, focused implementation checks had reported success, while
root integration/build/deployment verification was still in progress. Do not label 0.7 fully
accepted from this document. Existing remote approval-policy and independent-account limits
remain unless later evidence explicitly resolves them; the owner has no second account.
Manual current-conversation behavior samples are in
[evidence/2026-10-18-support-scenarios.md](evidence/2026-10-18-support-scenarios.md); they are
reviewable advice, not new-session integration or automated semantic-test passes.

## 中文版 — 0.7 替代方向，2026 年 10 月 18 日

本文让下一位 agent 不依赖聊天记忆即可继续。原 Anti-Dating-App-Scam 仓库继续作为
AI-SlowMatch 权威项目，不克隆替代产品、不更换原远端、不覆盖他人修改，也不把私人数据放进源码控制。

当前产品核心是用户自己的 ChatGPT 桌面对话、按需插件 Skills、既有 Python 本机核心和经过认证的
Sites 匹配服务。所有者接受 OpenAI 云端分析任务所需且已授权的个人信息；这不授权 Sites 或其他人
获取完整档案、原始聊天或私人报告。

上方流程为：ChatGPT 与按需 Skills 调用本机 Python 结构和受保护存储，生成并展示准确摘要，
另行获得发布批准后交给 Sites 身份验证、摘要保存和双向发现。候选获准摘要返回本人 ChatGPT，
私密解读仍保存本机。

本机档案是持续理解本人的资料来源。判断包含来源、确认、时间、不确定性和纠正，未知仍标为未知。
不把创始人档案当成默认答案。档案更新、摘要草稿、发布批准与私人报告是不同对象和许可。

项目已有类型化结构、报告校验、受保护文件读写、证据／历史处理、记忆迁移与测试，因此继续复用
Python。本机 CLI 不建立替代模型客户端或网站 AI 代理。新状态默认在 OneDrive 和 Git 之外的
`%LOCALAPPDATA%/AI-SlowMatch/work`，必须解析并检查路径。不会自动扫描或搬迁旧资料库。
除特定产物明确实现加密外，本机状态为明文。

Sites 使用实际支持的 Worker/D1，不能假设原 Python/FastAPI 服务可直接部署。为分模式摘要及最小共同安排实现
小型托管部分是本次方向所需，不替换 Python 核心，也不形成另一个主聊天产品。服务端所有权来自
Sites 验证身份，不能来自工具参数。每次返回均遵守当前可见范围与双方条件；候选标签是不可信数据，
不能授权读取或上传。

原源码树管理 `apps/matching_site/`，Sites 要求的托管源码仓库只是单向部署镜像。记录准确源码
与部署版本，在原仓库修改后明确同步。运行文件、凭据、私人档案和合成测试身份不得成为生产种子用户。

固定的 0.5.3 `AI-SlowMatch.exe` 在迁移前已验证，继续作为恢复／旧功能入口，保留发布证据。
0.7.0 扩展历史 0.6.0 源码检查点；没有单独构建记录时，两者都不表示 EXE 已替换。PySide6 保留为工具界面，FastAPI 保持可选。
Tauri、第二套桌面聊天客户端、默认 Ollama 推理及联邦化不属于首版迁移。旧决策记录保留历史，
不再充当冲突路线的现行要求。

JSON/Pydantic 继续定义交互边界，保存、导出、签名或作为可信报告展示前必须校验。批准摘要哈希
仅证明内容相同，不是签名或本人同意证明。数字签名可在信任密钥前提下证明完整性，不能证明来源真实、
完整、存在不当行为、偏好诚实或关系安全。加密保护机密性，与校验／签名不同。不把私人反思变成诊断、
道德标签或精确匹配分。

验收必须区分源码实现、Skill 安装发现、本机进程持续性、托管部署、真实 MCP 连接和独立账号使用。
原生 Codex 的 Skill 加载只证明该通道，不证明桌面 Work 或其他用户分发。ZIP 在安装前只是源码／
打包产物。0.6 私密试运行站点已有部署证据，单纯登记不能证明上线；当前 0.7 部署／测试结果须查看实时证据。最新证据与外部前提缺口记录在 `CURRENT_STATUS.md`
和 `PROGRESS_TRACKER.md`。

本轮以所有者完整替代附件为准，不使用此前截断提示词；见 ADR-015 和 R1–R7 计划。恋爱与朋友各自
选择参与，私人观察／复盘、本机保护筛选、活动安排、准备、本人主动中途帮助及可选同意音频均属本次范围。
Sites 仅可存审阅摘要／必要状态，另加各自批准且限定用途／接收者／到期的最小安排偏好、版本化计划／
确认与选定反馈；不分享原材料、转写、风险原因或私人报告。

共同上下文只来自获准对象。本机确定性 `planning-suggest` 只读类型化共享上下文／公开地点证据，不读
私人存储或调用模型。已有私人上下文的聊天不能只承诺保密就导出叙述。各人批准本人的字段／当前计划，
变更使旧确认失效；本机撤回不替代远程撤回调用。不自动邀请、预订、付款、写日历、跟踪位置或录音。
私人帮助不要求对方同意，区分不合适、材料不清与具体行为关切。

新支持服务在 `relationship-support/state.json` 存当前记录，在 `relationship-support/audio` 存
受管短 WAV，历史仅含无正文版本元数据。材料预览供本人本机查看，只返回路径；云端许可前不得读给
模型。纠正使旧云端许可／关联报告失效；到期／清理在之后操作或 sweep 执行，不是后台计划任务。选定
来源原件及外部副本仍保留。短 WAV 导入为 0.1–30 秒，不是完整见面录音。已审计运行环境有识别器依赖，
但英语／中文模型缺失；不声称新增真实识别或实体麦克风验收通过，也未下载模型。

此文档检查点中，相关实现检查已报告通过，而主 agent 的集成／构建／部署核验仍在进行。不能凭本文宣称
0.7 完全验收。已有远程审批策略及独立账号限制保持，除非后续证据明确解决；所有者没有第二账号。
[当前会话行为样本](evidence/2026-10-18-support-scenarios.md)是可审阅建议，不是新会话集成或自动语义
测试通过。最新事实仍以状态／进度为准。
