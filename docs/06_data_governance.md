# Data Governance

## English — current destination boundaries, October 17, 2026

The owner's October 17 requirements supersede conflicting local-only and GUI-only
assumptions in the historical sections below. OpenAI analysis, local persistence
and Sites publication are separate operations with separate data scopes. Accepting
cloud analysis does not grant the matching website, other participants or the public
access to the complete private profile.

| Destination | Allowed data and authority |
|---|---|
| User's local state | Full profile claims, sources, corrections, uncertainty, revision history, drafts, approvals and private assessments. Read only material required for the current authorized task. |
| User's ChatGPT session / OpenAI | Task-relevant personal information the user has chosen to analyze, under the applicable service settings. Do not scrape prior ChatGPT history, borrow another application's credentials or treat login as unrestricted local-file access. |
| Sites matching service | Separately approved summary plus necessary authenticated ownership, visibility, version and matching state. Never raw chats, detailed history, private claims/reports, original source quotations, secrets or full-profile embeddings. |
| Other participants | Only the fields allowed by current visibility and reciprocal eligibility. No private report, internal user identity, credentials, arbitrary database row or bulk identity export. |
| Public product page / source / package | Product explanation, code and synthetic examples only. No real profiles, private state, credentials or private test output. |

The local contracts are in `models/work_profile.py`; the guarded service and JSON
CLI are in `services/work_profile.py` and `work_cli.py`, all below
`src/anti_dating_scam/`. `PrivateProfile`, `ShareableProfileDraft`,
`PublishedProfile` and `PrivateMatchAssessment` are distinct schema-versioned
objects. An important claim records whether it is self-report, observation,
inference or unknown, its confirmation status and update time. Preserve alternative
explanations and contradictions; a correction must not be overwritten by stale work.

The first summary contract is intentionally narrow: alias, adult age band, chosen
city/areas, relationship goal, accepted goals and age bands, selected value,
life-direction, communication and interest tokens, soft preferences, participant
visibility, discoverability and summary identifiers/versions. No free-form private
biography or exact coordinates are required. Approved labels still reveal selected
information; allowlisting is not a claim of anonymity or proof that all text is safe.

Generate and validate the summary locally before any network operation. Preview the
exact content, destination, audience and version; record the user's separate
publication approval. Upload reads the independent approved summary artifact, never
the private profile followed by server-side filtering. Refuse content changed after
approval, unexpected fields, excess sizes, arbitrary destinations and private nested
objects. A digest binds exact bytes but is not a signature or evidence of human
identity. An approved local receipt is distinct from a successful remote write.

Use Sites-verified request identity for every owned query/write. Ignore or reject
client `user_id` fields. Account A cannot select account B as the owner by changing
arguments. Candidate access must recheck authentication, current participation,
visibility and both sides' hard conditions. Bound queries and responses; do not
implement identity enumeration or bulk export. Treat all returned labels, links and
attachments as untrusted data, never instructions to run tools or read local files.
No tool may upload a private assessment or contact a candidate automatically.

New local state defaults to `%LOCALAPPDATA%/AI-SlowMatch/work`. The resolved path
must remain outside OneDrive, Git, plugin packages, builds and website assets, even
when a packaged Windows host redirects AppData. `profile/`, `drafts/`,
`publications/`, `assessments/` and `outbound/` are separate. The state is plaintext;
do not claim that file separation or a content hash encrypts it. No new cloud sync
or broad backup destination is implied. Protect backups as private state and never
store real backup data in source or deployment folders.

Legacy import must explicitly select and validate an existing supported source,
copy only the required fields and retain original bytes. Unsupported, malformed or
conflicting input must fail without silently discarding fields or deleting the
source. No real legacy archive has been imported during this migration. Synthetic
tests do not authorize later bulk archive reading.

Withdrawal must remove a profile from current matching/display and controlled
caches. Deletion cannot revoke another participant's saved copy or promise removal
from provider/platform backups whose retention the app does not control. Local
private reports and local history have their own lifecycle; withdrawing from Sites
does not silently erase them. Document the actual retained state, not absolute erasure.
The service clears the summary and digest on deletion while retaining an ownership
tombstone, public ID, server revision, last summary version and update timestamp.
A revoked summary version cannot be republished even after reloading server state;
rejoining requires review and approval of a newer summary version. Account query-limit
counters and a fixed synthetic channel marker may remain; neither contains private text.

Tests and receipts use synthetic data. Inspect the actual approved upload, stored
remote object and returned fields; use synthetic private markers to test exclusion.
Handle network, expired-session, failed-write and version-conflict errors explicitly.
Retries must not duplicate publication or overwrite newer revisions. Authentication
tests with injected headers are local logic tests, not real two-account acceptance.
Current deployment, connection and acceptance evidence belongs in the status tracker.

## 中文版 — 当前目的地边界，2026 年 10 月 17 日

所有者 10 月 17 日要求替代下方历史记录中冲突的“仅本机”和“仅 GUI”假设。OpenAI 分析、
本机保存和 Sites 发布是独立操作，使用不同资料范围。接受云端分析，不代表允许匹配网站、
其他参与者或公众获取完整私人档案。

| 目的地 | 允许资料与授权范围 |
|---|---|
| 本人本机状态 | 完整档案判断、来源、纠正、不确定性、修订历史、草稿、批准和私人分析；只读当前获准任务所需材料。 |
| 本人 ChatGPT 会话／OpenAI | 按适用服务设置处理本人选择用于任务的个人信息。不抓取既有 ChatGPT 历史，不借用其他应用凭据，不把登录当成无限本机文件访问权。 |
| Sites 匹配服务 | 独立批准的摘要和必要认证所有权、可见性、版本与匹配状态。禁止原始聊天、详细经历、私密判断／报告、来源引文、秘密或完整档案向量。 |
| 其他参与者 | 仅展示当前可见范围与双方条件允许的字段，不返回私人报告、内部用户身份、凭据、任意数据库完整行或身份批量导出。 |
| 公开介绍页／源码／插件包 | 仅产品说明、代码与合成示例，不含真实档案、私人状态、凭据或私人测试输出。 |

本机结构在 `src/anti_dating_scam/models/work_profile.py`，受保护服务和 JSON CLI 分别在同目录下
的 `services/work_profile.py` 与 `work_cli.py`。`PrivateProfile`、`ShareableProfileDraft`、
`PublishedProfile` 和 `PrivateMatchAssessment` 是分开的版本化结构。重要判断记录自述、观察、
推断或未知、本人确认状态和更新时间。保留其他解释及矛盾，旧任务不得覆盖新纠正。

首版摘要刻意收窄为：化名、成年年龄段、自选城市／区域、关系目标、接受的目标与年龄段、选定价值观／
人生方向／沟通／兴趣选项、软偏好、参与者可见范围、发现状态和摘要编号／版本。不要求自由撰写私人
经历或精确坐标。获准标签仍会披露选定信息；字段白名单不等于匿名，也不证明所有文字都安全。

任何网络操作前，先在本机生成并校验摘要。展示准确内容、目的地、受众与版本，记录本人独立发布批准。
上传只读取独立获准摘要产物，不能先传完整档案再在服务端过滤。拒绝批准后被修改的内容、额外字段、超限
大小、任意目标和夹带私人对象。哈希绑定准确字节，不是签名或身份同意证明；本机批准记录不同于远程写入成功。

每次查询或写入都使用 Sites 验证的身份，忽略或拒绝客户端 `user_id`。A 不能通过参数把 B 设为所有者。
候选访问重新核验登录、当前参与状态、可见范围和双方硬条件，限制查询与返回量，不提供身份枚举或批量导出。
所有候选标签、链接及附件都当作不可信数据，不能成为执行工具或读取本机文件的指令。不提供私人报告上传
或自动联系候选的工具。

新本机状态默认存入 `%LOCALAPPDATA%/AI-SlowMatch/work`。即使 Windows 打包宿主重定向 AppData，
最终解析路径仍须在 OneDrive、Git、插件包、构建和网站资源之外。`profile/`、`drafts/`、
`publications/`、`assessments/` 和 `outbound/` 分开保存。状态为明文，目录隔离或哈希并不加密文件。
不暗含新增云同步或广泛备份目标。备份按私人状态保护，不能进入源码或部署目录。

旧资料导入必须明确选择并校验受支持来源，只复制必要字段，保留原始字节。遇到不支持、损坏或冲突输入
应失败，不能暗中丢字段或删除源文件。本次迁移未导入真实旧档案，合成测试不授权以后批量扫描资料库。

撤回应从当前匹配、展示与受控缓存中移除相应资料。删除不能追回他人已保存的副本，也不能承诺移除应用
无法控制保留期的平台／提供方备份。本机私人报告与历史有独立生命周期，退出 Sites 不会暗中删除它们。
如实说明实际保留状态，不承诺绝对抹除。
删除时服务清空摘要正文与摘要哈希，保留归属墓碑、公开标识、服务版本、最近摘要版本与更新时间。
即使重新读取服务状态，也不能重发已撤回的旧摘要版本；再次加入需要审阅并批准更高版本。
账号查询限额计数与固定合成通道标记可能保留，两者均不包含私人正文。

测试和证据使用合成资料，检查真实获准请求、远程保存对象与返回字段，可用合成私人标记验证排除边界。
明确处理网络、登录过期、写入失败与版本冲突，重试不能重复发布或覆盖更新版本。注入身份头的测试只证明
本地逻辑，不算双真实账号验收。当前部署、连接与验收结果记录在状态追踪中。

---

## Historical desktop governance records / 历史桌面资料治理记录

The sections below preserve earlier implementation boundaries and limitations.
They do not override the October 17 destination policy or assert the new plugin's
status. In particular, old provider-test and no-database statements are historical.
/ 下方保留早期实现边界与局限，不覆盖 10 月 17 日目的地政策，也不代表新插件状态。
其中旧提供方验收和“无数据库”等表述均为历史记录。

## Private attachment and microphone boundary — English (2026-09-30)

Voice capture begins only after Start recording. At most 30 seconds of audio remain in memory, are normalized and recognized by a user-installed offline Vosk model, and are discarded after transcription or cancel. No audio is saved or sent to AI. The editable words enter the same reviewed text-chat boundary as typed words. Official English/Chinese model downloads occur only after an explicit click and are stored outside the vault. A permission or absent-device failure must remain visible; the app cannot assert that a physical microphone worked.

The encrypted `.slowmatch` attachment contains only a selected reflection's tentative bilingual narratives, open questions, unknowns and caveats. It excludes original quotations, transcript, history, credentials and the local session identifier. Narrative text is not automatically anonymous. A fixed bounded scrypt derivation and AES-256-GCM protect confidentiality and integrity; neither authenticates the sender nor verifies their claims. Export checks the reviewed source version and refuses existing destinations. Import validates a bounded file and decrypts in memory without archive extraction or persistent imported profiles. Private-comparison permission does not grant permission to forward.

Comparison needs explicit permission for each person. A remote request discloses both unverified summaries and its exact instructions/schema; no source vault is opened by the comparison service. Shared-summary quotes are not proof of actual behavior. Results contain low-confidence possibilities and unknowns, with no scores or final matching verdict. Stopping discards late results. The user attaches and sends email outside the app. This feature does not encrypt the ordinary saved chat history or its backups. The account observation and model-list request were user-authorized diagnostics, not access to existing ChatGPT chats or a real inference validation.

## 私密附件与麦克风边界 — 中文版（2026-09-30）

只有点击“开始录音”才开始采集。最长 30 秒音频留在内存中，转换格式后由用户安装的离线 Vosk 模型识别，转写或取消后丢弃。不保存音频，也不将音频发送给 AI。可编辑文字与打字回答进入同一文本审阅流程。官方英语及中文模型只有明确点击后才下载，存放在资料库外。权限失败或没有设备必须明确显示，应用不能据此声称实体麦克风已成功使用。

`.slowmatch` 加密附件仅包含所选画像的暂定双语解释、开放问题、未知及限制，不包含原始引文、对话、历史、凭据或本地会话标识。文字并不会自动匿名。固定且有界的 scrypt 密钥派生及 AES-256-GCM 保护机密性与完整性，但不证明发送者身份或结论真实性。导出核验经审阅的源版本，并拒绝已有目标文件。导入验证有界文件，仅在内存解密，不解压存档或持久保存导入档案。私下比对许可不等于转发许可。

比对需要分别确认两个人的许可。远程请求会披露双方未经核实的摘要及准确指令、结构要求，比对服务不打开源资料库。共享摘要中的引文不是实际行为证据。输出保留低置信度可能性及未知，不打分，也不作最终匹配判决。停止后丢弃迟到结果。用户在应用外自行附加并发送邮件。本功能不会加密普通聊天历史或其备份。账号观察及模型列表请求属于用户授权的诊断，并非读取既有 ChatGPT 聊天或验证真实推理。

The earlier conversation checkpoint follows / 下方保留此前聊天里程碑。

## Historical conversation checkpoint — English

The new AI Chat starts with a user-selected local folder, including an empty one; it does not require importing a file or building an older profile. The conversation lives in memory until the user explicitly chooses to save a reflection. Only original text typed by this user in the current chat can become portrait evidence. A remote request includes those typed statements and at most two earlier AI questions as non-evidence context. Every remote question or portrait request requires a fresh disclosure review; canceling it sends nothing. The flow does not read existing ChatGPT conversations, silently scan the vault, ingest another person's messages, or scrape a platform. **End** invalidates pending responses and does not trigger a portrait or save; it cannot retract a request that was already sent to an online service.

After End, a separate **Create my reflection** action may produce a provisional report with low-confidence claims, exact quotations tied to this session's typed source IDs, and explicit unknowns. A second **Save this reflection** confirmation creates an independent plaintext copy at `reports/reflection_history/<session_id>/` with the report, bilingual text, transcript, and file-digest manifest. **Saved reflections** reads these files. It does not replace older report files, activate a report, or treat AI questions as user evidence. There is currently no in-place editing, saved-session deletion control, automatic retention limit, or cross-session claim update. Future controls must cover these new history files and user backups as well as older histories. Until encryption and deletion controls are complete, users should avoid entering sensitive real material they do not want stored in ordinary files.

The visible ChatGPT connection uses local code for official browser sign-in, PKCE, separate plan-use permission, model discovery and provider requests; all present verification is synthetic. Real account authorization, model quality and plan eligibility have not been verified. The app does not borrow the local ChatGPT app's credentials or chats. The user must review eligibility and disable extra-credit use for this app in ChatGPT settings before activation; the app cannot inspect that setting or guarantee zero credit use. Do not use paid APIs, buy credits, enter card details or perform live account tests as part of the autonomous development run. Public testers and moving real private vaults into encrypted storage remain owner-review decisions.

## 历史对话资料里程碑 — 中文版

新的 AI 聊天先由用户选择本地文件夹，空文件夹也可以直接进入；不要求导入文件或建立旧版档案。对话先留在内存中，只有用户明确选择保存画像才写入独立历史文件。画像证据只能来自用户在本次聊天亲自输入的原文。远程请求会包含这些原话，并最多附上两条先前 AI 问题作为**非证据背景**。每次远程提问或生成画像都要重新查看拟发送内容；取消则不发送。此流程不会读取已有 ChatGPT 对话、暗中扫描档案库、导入他人消息或抓取平台内容。点击**结束**会使待处理回复失效，且不会自动生成或保存画像；已经发到在线服务的请求无法追回。

结束后，用户另点**生成我的相处画像**才可能得到暂定报告：主张均为低置信度，引文需与本次输入的来源编号精确对应，并明确写出未知事项。再单独确认**保存这份画像**后，应用才会在 `reports/reflection_history/<session_id>/` 建立普通明文副本，保存报告、双语文本、对话和文件摘要清单。**已保存画像**可以读取这些文件。它不会覆盖旧报告、激活某份报告，或把 AI 提问当成用户证据。目前没有原地编辑、已保存会话删除、自动保存期限或跨会话更新主张的功能。未来删除控制需覆盖这份新历史及用户备份，也要涵盖旧版历史。在加密和删除功能完善前，不宜输入不希望以普通文件保留的真实敏感材料。

可见的 ChatGPT 连接已写入官方浏览器登录、PKCE、单独套餐使用授权、模型发现与服务请求的本地代码；目前验证全是合成测试。真实账号授权、模型质量和套餐资格尚未验证。应用不会借用本地 ChatGPT 客户端的凭据或聊天记录。启用前，用户须自行核对资格，并在 ChatGPT 设置中关闭此应用的额外积分使用；应用无法读取该开关，也无法保证绝不消耗积分。自主开发运行不得调用付费 API、购买积分、输入银行卡信息或开展真实账号测试。公开招募试用者及把真实私人档案迁入加密存储，仍须由所有者另行审阅。

---

## Earlier vault and report records (advanced tools)

At this early checkpoint the prototype had no database. That historical choice
prioritized safety behavior before retaining sensitive relationship data; the
October 17 architecture explicitly adds summary-only Sites storage.

The local desktop/browser prototype now uses ordinary plaintext vault files.
Explicitly saved report corrections retain a full original JSON snapshot and a
separate user annotation under `reports/review_history/`. Opening a review does
not persist anything. Regeneration does not erase older correction history.
This is a prototype retention mechanism, not encrypted production storage.
See `18_report_review_history.md` for the consent and evidence boundaries.

Explicit legacy-report archives additionally retain exact source bytes, including
unsupported fields and malformed files, under `reports/legacy_archives/`. These
are inert plaintext preservation records, not converted current reports or user
evidence. Opening inspection does not save an archive; preview and confirmation
are required. No original file is removed or replaced. See
`22_legacy_report_archives.md` for bounded fixed-member storage and verification.

Separately confirmed partial conversions retain a canonical report, localized
renderings and a field ledger under `reports/converted_reports/`. They depend on
the intact archive, copy only structurally complete claims and remain unverified.
They are excluded from original evidence discovery, including direct subfolder
selection and renamed ancestors. Explicit activation supplies an assistant-role
reference, never user testimony. An explicit review-only selection disables those
references without deleting originals or histories. See `23_legacy_report_conversions.md`.

## Data Minimization

Explicit personal-profile layout migration copies only the fixed flat root files
into `profile/` after preview and confirmation, retaining original bytes and the
flat originals. It does not read imports or reports. Unsupported JSON blocks the
copy without dropping unknown fields. Metadata and pending copies are excluded from
evidence discovery. Future retention/deletion must cover both source and copied
profiles plus any failed pending directories. See `24_profile_layout_migration.md`.

Collect only the text required for a user-requested analysis. Do not collect device contacts, hidden profile data, private social media data, or location history.

## Deletion

Future storage must support deletion of local records. Deletion should include submitted text, journal entries, generated outputs, and metadata where feasible.

Future vault deletion/export controls must include review-history snapshots and
annotations as well as current reports. They must explain that sync providers or
user backups may retain independent copies. There is no automatic history purge.

Those future controls must also cover reviewed copies, active-selection journals
and legacy archives and conversions, including snapshots and any failed pending directories.

## Export

Users should be able to export their own records in a readable format before deleting or migrating them.

## Local-First Retention Direction

The prototype already stores these records locally. Future design must make retention, deletion, backup and migration understandable and controllable.

## Encryption Future Option

Persistent plaintext storage already exists in this prototype. Encryption at rest, key management, backup recovery and migration need explicit design before production use.

## Audit Logs

Future audit logs should track user-controlled actions such as creation, export, deletion, and model-provider calls. Audit logs should not become surveillance logs.

## Model-Output Retention Policy

Model outputs should have retention limits. Users should be able to delete outputs and see whether a provider call was made.

## No Real User Data In Repo

Tests, examples, fixtures, screenshots, and docs must use synthetic data only.
