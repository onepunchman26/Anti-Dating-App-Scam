# Data Governance

## Private attachment and microphone boundary — English (2026-09-30)

Voice capture begins only after Start recording. At most 30 seconds of audio remain in memory, are normalized and recognized by a user-installed offline Vosk model, and are discarded after transcription or cancel. No audio is saved or sent to AI. The editable words enter the same reviewed text-chat boundary as typed words. Official English/Chinese model downloads occur only after an explicit click and are stored outside the vault. A permission or absent-device failure must remain visible; the app cannot assert that a physical microphone worked.

The encrypted `.slowmatch` attachment contains only a selected reflection's tentative bilingual narratives, open questions, unknowns and caveats. It excludes original quotations, transcript, history, credentials and the local session identifier. Narrative text is not automatically anonymous. A fixed bounded scrypt derivation and AES-256-GCM protect confidentiality and integrity; neither authenticates the sender nor verifies their claims. Export checks the reviewed source version and refuses existing destinations. Import validates a bounded file and decrypts in memory without archive extraction or persistent imported profiles. Private-comparison permission does not grant permission to forward.

Comparison needs explicit permission for each person. A remote request discloses both unverified summaries and its exact instructions/schema; no source vault is opened by the comparison service. Shared-summary quotes are not proof of actual behavior. Results contain low-confidence possibilities and unknowns, with no scores or final matching verdict. Stopping discards late results. The user attaches and sends email outside the app. This feature does not encrypt the ordinary saved chat history or its backups. The account observation and model-list request were user-authorized diagnostics, not access to existing ChatGPT chats or a real inference validation.

## 私密附件与麦克风边界 — 中文版（2026-09-30）

只有点击“开始录音”才开始采集。最长 30 秒音频留在内存中，转换格式后由用户安装的离线 Vosk 模型识别，转写或取消后丢弃。不保存音频，也不将音频发送给 AI。可编辑文字与打字回答进入同一文本审阅流程。官方英语及中文模型只有明确点击后才下载，存放在资料库外。权限失败或没有设备必须明确显示，应用不能据此声称实体麦克风已成功使用。

`.slowmatch` 加密附件仅包含所选画像的暂定双语解释、开放问题、未知及限制，不包含原始引文、对话、历史、凭据或本地会话标识。文字并不会自动匿名。固定且有界的 scrypt 密钥派生及 AES-256-GCM 保护机密性与完整性，但不证明发送者身份或结论真实性。导出核验经审阅的源版本，并拒绝已有目标文件。导入验证有界文件，仅在内存解密，不解压存档或持久保存导入档案。私下比对许可不等于转发许可。

比对需要分别确认两个人的许可。远程请求会披露双方未经核实的摘要及准确指令、结构要求，比对服务不打开源资料库。共享摘要中的引文不是实际行为证据。输出保留低置信度可能性及未知，不打分，也不作最终匹配判决。停止后丢弃迟到结果。用户在应用外自行附加并发送邮件。本功能不会加密普通聊天历史或其备份。账号观察及模型列表请求属于用户授权的诊断，并非读取既有 ChatGPT 聊天或验证真实推理。

The earlier conversation checkpoint follows / 下方保留此前聊天里程碑。

## Current conversation boundary — English

The new AI Chat starts with a user-selected local folder, including an empty one; it does not require importing a file or building an older profile. The conversation lives in memory until the user explicitly chooses to save a reflection. Only original text typed by this user in the current chat can become portrait evidence. A remote request includes those typed statements and at most two earlier AI questions as non-evidence context. Every remote question or portrait request requires a fresh disclosure review; canceling it sends nothing. The flow does not read existing ChatGPT conversations, silently scan the vault, ingest another person's messages, or scrape a platform. **End** invalidates pending responses and does not trigger a portrait or save; it cannot retract a request that was already sent to an online service.

After End, a separate **Create my reflection** action may produce a provisional report with low-confidence claims, exact quotations tied to this session's typed source IDs, and explicit unknowns. A second **Save this reflection** confirmation creates an independent plaintext copy at `reports/reflection_history/<session_id>/` with the report, bilingual text, transcript, and file-digest manifest. **Saved reflections** reads these files. It does not replace older report files, activate a report, or treat AI questions as user evidence. There is currently no in-place editing, saved-session deletion control, automatic retention limit, or cross-session claim update. Future controls must cover these new history files and user backups as well as older histories. Until encryption and deletion controls are complete, users should avoid entering sensitive real material they do not want stored in ordinary files.

The visible ChatGPT connection uses local code for official browser sign-in, PKCE, separate plan-use permission, model discovery and provider requests; all present verification is synthetic. Real account authorization, model quality and plan eligibility have not been verified. The app does not borrow the local ChatGPT app's credentials or chats. The user must review eligibility and disable extra-credit use for this app in ChatGPT settings before activation; the app cannot inspect that setting or guarantee zero credit use. Do not use paid APIs, buy credits, enter card details or perform live account tests as part of the autonomous development run. Public testers and moving real private vaults into encrypted storage remain owner-review decisions.

## 当前对话资料边界 — 中文版

新的 AI 聊天先由用户选择本地文件夹，空文件夹也可以直接进入；不要求导入文件或建立旧版档案。对话先留在内存中，只有用户明确选择保存画像才写入独立历史文件。画像证据只能来自用户在本次聊天亲自输入的原文。远程请求会包含这些原话，并最多附上两条先前 AI 问题作为**非证据背景**。每次远程提问或生成画像都要重新查看拟发送内容；取消则不发送。此流程不会读取已有 ChatGPT 对话、暗中扫描档案库、导入他人消息或抓取平台内容。点击**结束**会使待处理回复失效，且不会自动生成或保存画像；已经发到在线服务的请求无法追回。

结束后，用户另点**生成我的相处画像**才可能得到暂定报告：主张均为低置信度，引文需与本次输入的来源编号精确对应，并明确写出未知事项。再单独确认**保存这份画像**后，应用才会在 `reports/reflection_history/<session_id>/` 建立普通明文副本，保存报告、双语文本、对话和文件摘要清单。**已保存画像**可以读取这些文件。它不会覆盖旧报告、激活某份报告，或把 AI 提问当成用户证据。目前没有原地编辑、已保存会话删除、自动保存期限或跨会话更新主张的功能。未来删除控制需覆盖这份新历史及用户备份，也要涵盖旧版历史。在加密和删除功能完善前，不宜输入不希望以普通文件保留的真实敏感材料。

可见的 ChatGPT 连接已写入官方浏览器登录、PKCE、单独套餐使用授权、模型发现与服务请求的本地代码；目前验证全是合成测试。真实账号授权、模型质量和套餐资格尚未验证。应用不会借用本地 ChatGPT 客户端的凭据或聊天记录。启用前，用户须自行核对资格，并在 ChatGPT 设置中关闭此应用的额外积分使用；应用无法读取该开关，也无法保证绝不消耗积分。自主开发运行不得调用付费 API、购买积分、输入银行卡信息或开展真实账号测试。公开招募试用者及把真实私人档案迁入加密存储，仍须由所有者另行审阅。

---

## Earlier vault and report records (advanced tools)

The current prototype has no database. This is intentional. Early work should stabilize safety behavior before retaining sensitive relationship data.

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
