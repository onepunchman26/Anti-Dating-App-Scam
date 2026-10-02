# Adult introductions and peer comparisons / 成年人介绍与参与者比较

## English

October 2, 2026 · S6 · app Skill version 3. This extends the existing Python core,
PySide desktop and FastAPI rendezvous factory. It is a working local integration;
there is no deployed public peer network, verified-age service or email provider.

### Use the desktop

1. Connect ChatGPT using the existing account flow. On Home open **Introductions &
   invitations**. You can write an introduction independently of discovery.
2. **My introduction:** supply age and explicitly confirm 18+. Load permitted notes
   from the existing enabled **My approved notes** store. Select 1–8 confirmed facts.
   Hypotheses, questioned/rejected entries, sensitive flags and conservatively detected
   private/third-party topics are excluded. Notes older than 90 days need reconfirmation.
   This screen is an extra filter, not a guarantee of semantic anonymization.
3. Use the generic template or enter your own field headings separated by `;`, audience,
   tone and character limit. No third-party platform rules are claimed to be verified.
   Review the exact model request, generate, edit, regenerate or shorten. Every nonempty
   generated field must cite selected source text. Unsupported fields remain empty.
   Quotes prove source presence, not semantic truth: review the wording yourself.
4. **Approve edited introduction** saves only the approved local draft. Copy or export
   TXT/JSON separately. Exports contain approved field text, not memory IDs or evidence.
   Publishing on a node requires a separate review. Editing the draft or correcting
   source memory prevents reusing an outdated approval. Already exported or published
   copies cannot be automatically recalled; use **Withdraw public introduction**.
5. **Connection & profile:** start the local node, enter a pseudonym, then create a
   device identity or connect an existing one. Each chosen local folder has its own
   protected node credential. Create a second synthetic folder to test a second adult
   on the same computer; no fictional candidates are inserted automatically.
6. Review a limited matching profile: city/region, explicitly chosen search areas,
   adult age range, selected categories, hard requirements and ordered private priorities.
   Processing permission and per-field disclosure checkboxes are separate. The profile
   starts undiscoverable. Only disclosed attributes enter the model; hidden fields are
   used only for reciprocal eligibility gates and never appear in explanations.
7. **Discover:** refresh eligible candidates or organize mutually authorized comparisons.
   Empty pools stay empty. Adjust settings yourself if wanted; areas never expand
   automatically. A selected candidate can receive a targeted invitation or be blocked.
8. **Invitations & results:** create an invitation (1–168 hours), copy the link and share
   it yourself. The recipient pastes it at the same configured node and claims it after
   approving their own limited profile. Both inspect the claimant's account identifier
   through an already trusted channel and approve the displayed current versions.
   Pseudonyms and bearer credentials do not establish a verified real-world identity.
9. Both separately permit ChatGPT processing. The initiating viewer then reviews the
   exact request and chooses Compare. A private bilingual report distinguishes stated
   alignment, potential tensions, uncertain differences and unknowns, citing both sides.
   The other participant must request their own report; private ordering is never shared.
   Decline, revoke, block, withdraw processing, correct a profile or delete an account
   to invalidate affected permissions/results. Declining is never a personality signal.

### Data flow, identity and persistence

The private personal model remains in `.relationship-memory`; it is not duplicated
or exposed to the node. Approved public text is in `.dating-introduction/approved.json`.
These existing-style local files are unencrypted, explicitly disclosed in the UI.
The node receives only adult declarations and separately approved matching/public
snapshots. It has no route for reading chats, vault files or private psychological notes.

Desktop identities use non-guessable bearer credentials in per-folder, per-origin
Windows DPAPI files under `.peer-session`. Server-side authentication compares token
hashes. The coordinator stores one AES-GCM encrypted state row in SQLite, with its key
protected by current-user DPAPI. `BEGIN IMMEDIATE` serializes claims, consent, versions
and results across concurrent sessions. This protects storage at rest; it does not
protect against malware or another process running as the same Windows user. There
is no identity recovery, password reset or verified-age provider in this local phase.
Under-18 declarations and non-boolean consent values fail closed. Self-declaration
cannot prove age or defeat a dishonest adult-age claim.

Profile changes require an expected revision and explicit approval. A stale write
fails rather than overwriting newer choices. A comparison ticket binds its viewer,
both approved versions, cloud permissions, sources and disclosed priorities. The
coordinator checks it before result persistence and before every read. The desktop
clears reports on navigation/node changes and checks a visible report every 15 seconds;
failed refresh clears it. Revocation cannot erase screenshots, copied text or data
already processed by the cloud. An in-flight request may complete after Stop, although
late results are discarded and a revoked report cannot be saved or read.

Invitations have random 256-bit identifiers in URL fragments, not profiles/emails in
query strings. Each has one recipient, expiry and revocation. Creation has an idempotency
key; simultaneous claims admit one recipient. A forwarded targeted invite rejects the
wrong account. An untargeted invite needs the sender to confirm whoever claimed it;
possession alone grants no comparison. Reapproval is necessary after profile correction.
Public `/p/<id>` links display only separately approved text and its approved pseudonym.
Changing a matching pseudonym does not silently change the public introduction.

The `/invite#...` landing page explains installation and consent without automatic
downloads or fictional browser participation. An optional Windows `slowmatch:` handler
opens the installed EXE with a review field; it does not fetch, claim or consent. Pasted
links must match the configured node, supported path and token format. The HTTP client
rejects redirects and arbitrary fetch routes. Local host/origin checks reject browser
cross-origin requests and DNS rebinding. Request/response limits, plain-text error
codes, no-store responses, escaped public text and disabled access logs reduce leakage.
There is no analytics or email delivery. Source backups explicitly exclude the four
private storage directories; no automatic private-data backups are created.

### Ordering and automatic updates

First apply mutual adulthood, processing/discovery permission, blocks/declines, chosen
areas, adult age ranges and hard requirements. Users are ranked privately by their
chosen priority order, using only fields both disclose: categorical overlap precedes
an explicit difference, then missing information. This is lexicographic preference
ordering, not a psychological score. At least two comparable priorities are needed;
otherwise candidates stay unranked. Equal evidence yields equal positions. No numeric
compatibility percentage is exposed. At most 20 candidates are shown; a limited list
is identified. Differences are not inherently bad or evidence of danger.

Optional automatic discovery runs in the local FastAPI lifespan worker, checking every
30 seconds with a user-selected interval of at least 15 minutes. It processes at most
20 due accounts per tick, uses the same deterministic shortlist, and records only a
minimal unread-update flag when enabled. A repeated unchanged run creates no repeated
notice. Connect/refresh shows the notice; there are no OS push notifications. The app
and node must stay running. This is a verified local worker, not an always-on hosted
service. AI comparison remains a separately reviewed user action: no unattended model
calls, invites, contacts, appointments or publication occur.

### Deployment gap and verification

Default node: `http://127.0.0.1:8766`, started explicitly from the desktop, stopped on
app exit. Data: `%LOCALAPPDATA%/AI-SlowMatch/matching-node`. A conflicting port fails
visibly; it never silently joins another service. The new mode intentionally omits
the older in-memory `/matchmaking` routes. Earlier ADR-012/013 describe that legacy
experiment; they do not govern the new minimal approved-snapshot persistence.

For cross-device participation, the owner must first choose and authorize a managed
HTTPS origin, deployment target and operations/retention policy; then integrate a
verified adult-eligibility/identity and credential-recovery approach. The current
loopback boundary must be replaced with a configured public-origin security policy,
with quotas, abuse controls, encrypted key custody, operational backup/deletion tests
and a verified distribution/download page. No host, account, cost or provider was
chosen or provisioned. No email integration is needed for manual link sharing. These
are explicit external-service gaps, not background work silently scheduled to run.

Tests cover synthetic adult eligibility, selected/stale/missing notes, evidence errors,
reciprocal scope, empty pools, hidden fields, concurrency, repeated consent, forwarding,
expiry, withdrawal, correction, private caching, true loopback HTTP/DPAPI/worker startup,
Qt English/Chinese journeys and backup exclusions. Native Computer Use checked the
source desktop entry, tabs and Back without automating consent or age verification.
Five real GPT-5.6-Luna plan calls used synthetic data: first two returned unusable empty
introductions; after adding the checked adult-declaration context, English and Chinese
drafts were useful. A real bilingual comparison passed source checks and revocation.
No automatic retry occurred. See [initial receipt](evidence/2026-10-02-peer-plan.json),
[corrected drafts](evidence/2026-10-02-peer-introductions-final.json) and
[current release checks](../CURRENT_STATUS.md). Samples do not validate psychology.

Implementation references inspected October 2: [FastAPI bearer-token interface](https://fastapi.tiangolo.com/tutorial/security/first-steps/),
[Python SQLite transactions](https://docs.python.org/3/library/sqlite3.html),
[Windows application launching](https://learn.microsoft.com/en-us/windows/win32/shell/launch),
and [ChatGPT model discovery/inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference).
These support implementation choices, not a claim of legal or identity compliance.

## 中文版

2026 年 10 月 2 日 · S6 · 应用 Skill 版本 3。沿用 Python 核心、PySide 桌面和 FastAPI
会合节点工厂，已实现本机整合；尚无公开参与者网络、年龄核验服务或邮件供应商。

### 桌面操作

1. 按原有流程连接 ChatGPT，在主页进入**介绍与邀请**。生成介绍不要求启用发现。
2. **我的介绍：**填写年龄并明确确认年满 18 岁，从已启用的**我批准的记忆**载入条目，
   选择 1–8 条已确认事实。排除 AI 假设、被质疑／拒绝条目、敏感标记及保守识别出的私人／
   第三方话题。超过 90 天的记忆须重新确认。这是额外筛选，不保证语义层面完全脱敏。
3. 使用通用模板，或以 `;` 分隔输入自己的栏目，选择受众、语气和字数。没有冒认已核实的
   第三方平台规范。审核精确模型请求后生成、编辑、重新生成或缩短。每个非空生成栏目必须
   引用选中原文，没有依据的栏目留空。引用只能证明来源存在，不能证明语义正确，仍须审稿。
4. **批准编辑后的介绍**只保存本机批准稿，随后可单独复制或导出 TXT／JSON。导出仅包含
   批准文字，不包含记忆编号或证据。向节点发布须另行审阅；编辑草稿或纠正来源后不能复用
   旧批准。已导出／已发布副本无法自动召回，已发布内容请用**撤下公开介绍**处理。
5. **连接与匹配资料：**启动本机节点，填写化名并建立身份，或连接已存身份。每个本地资料
   文件夹有独立受保护凭据。可用第二个合成资料文件夹，在同一电脑测试另一位成年人；
   应用不会自动插入虚构候选。
6. 审阅有限匹配资料：城市／地区、明确选择的寻找地区、成年年龄范围、类别选择、硬要求
   和私密优先级。处理许可与各字段展示许可分开，初始不参与发现。只有已披露属性发送给
   模型；隐藏字段仅用于双方资格筛选，不进入解释。
7. **发现：**刷新合资格候选，或整理双方已授权的比较。空池保持为空，可自行调整设置，
   应用不自动扩大地区。可为选定候选创建指定接收人邀请，或屏蔽此人。
8. **邀请与结果：**创建有效期 1–168 小时的邀请，自行复制分享。接收人配置相同节点，批准
   自己的有限资料后粘贴并认领邀请。双方通过已有可信渠道核对认领者账号标识，并批准展示
   的当前版本。化名和访问令牌并不能核实真实身份。
9. 双方分别允许 ChatGPT 处理，发起比较的人再审核精确请求并点击比较。私密双语报告区分
   自述契合、可能矛盾、影响未知的差异和缺失信息，引用双方资料。另一方须自行请求自己的
   报告，不会收到你的私密排序。婉拒、撤销、屏蔽、撤回处理许可、纠正资料或删除账号会使
   相关许可／结果失效。婉拒绝不被当作人格信号。

### 数据流、身份与存储

私人模型仍在 `.relationship-memory`，没有复制到第二套私人数据库或向节点开放。
批准介绍保存在 `.dating-introduction/approved.json`。这些延续原有方式的本机文件未加密，
界面明确说明。节点仅接收成年声明和另行批准的匹配／公开快照，没有读取聊天、资料库
文件或私人心理记忆的接口。

桌面身份使用不可预测的访问令牌，按文件夹和节点隔离，以 Windows DPAPI 保护后保存在
`.peer-session`。服务端比较令牌哈希。协调库用 AES-GCM 加密整行 SQLite 状态，密钥由
当前用户 DPAPI 保护；`BEGIN IMMEDIATE` 事务串行处理并发认领、同意、版本和结果。
这保护静态存储，不能防御同一 Windows 用户权限下的恶意程序。当前没有身份恢复、重置
密码或年龄核验供应商。未满 18 岁的声明及非布尔同意会被拒绝；自行声明不能证明真实年龄，
也不能阻止谎报成年。

资料更新须提交预期版本并明确批准，过时写入失败，不覆盖较新选择。比较凭据绑定查看者、
双方批准版本、云端同意、来源及已披露优先级，保存和每次读取均复核。桌面在离开页面或
切换节点时清空报告，对可见报告每 15 秒复核，失败也清空。撤销不能删除截图、复制文字
或已被云端处理的数据。停止后在途请求仍可能完成，但迟到结果不显示，撤销后不能保存
或读取报告。

邀请使用 URL 片段中的 256 位随机标识，不在查询参数携带画像／邮箱。每份限一位接收人，
支持到期和撤销，创建有幂等标识，并发认领只接纳一人。指定接收人的邀请拒绝错误账号；
未指定的邀请要求发起人核对实际认领者，持有链接本身不授予比较权限。资料纠正后须重新
批准。公开 `/p/<id>` 链接仅展示另行批准的文字和化名，修改匹配化名不会暗中更改公开介绍。

`/invite#...` 落地页解释安装和同意，不自动下载，也不虚构纯网页参与功能。可选 Windows
`slowmatch:` 处理器仅打开已安装 EXE 的审核输入框，不请求、认领或批准。粘贴链接必须
符合当前节点、支持的路径与令牌格式。客户端拒绝重定向及任意抓取路径；本机来源／主机
检查拒绝跨来源浏览器请求和 DNS 重绑定。请求／响应限额、安全错误码、禁止缓存、公开
文字转义及关闭访问日志减少泄漏。没有分析埋点或邮件发送；源码备份明确排除四个私人
存储目录，不自动建立私人数据备份。

### 排序与自动更新

先检查双方成年、处理／发现许可、屏蔽／婉拒、选定地区、成年年龄范围及硬条件。随后
按本人选定优先级，使用双方都披露的字段作私密排序：类别重合优先于明确差异，再是缺失。
这是逐项优先级排序，不是心理分数。至少两个可比维度才排序，否则保持未排序；依据相同
则名次相同，不展示契合百分比。最多显示 20 位，达到上限会说明。差异本身不代表不好或危险。

可选自动发现在本机 FastAPI 生命周期工作进程运行，每 30 秒检查，以用户选择的至少 15
分钟间隔执行；每次最多处理 20 个到期账号，复用相同确定性候选逻辑。开启提示后只记录
最小未读更新标记，不变的重复执行不重复提醒；连接／刷新时显示，没有系统推送。应用和
节点须持续运行，这是经验证的本机工作进程，不是全天托管服务。AI 比较仍是单独审核的
用户操作，不自动调用模型、邀请、联系、约会安排或发布。

### 部署缺口与验证

默认节点 `http://127.0.0.1:8766`，从桌面明确启动，退出应用时停止。数据在
`%LOCALAPPDATA%/AI-SlowMatch/matching-node`。端口冲突会明确失败，不暗中连接别的服务。
新模式刻意不加载原有内存 `/matchmaking` 接口；旧 ADR-012/013 描述历史实验，不约束
新增的最小批准快照持久化。

跨设备参与需要所有者先选择并授权受管理 HTTPS 地址、部署目标和运营／保留策略，再整合
成年资格／身份核验与凭据恢复。当前本机来源限制须替换为明确配置的公共来源策略，并
补充配额、滥用控制、加密密钥管理、运营备份／删除测试及核实后的下载页。没有选择、购买
或配置托管商、账号、成本或供应商；手动分享链接不需要邮件整合。这些是明确外部服务缺口，
没有暗中安排后续自动任务。

测试涵盖合成成年资格、选定／陈旧／缺失记忆、引用错误、双向范围、空池、隐藏字段、并发、
重复同意、转发、到期、撤回、纠正、私密缓存、真实本机 HTTP／DPAPI／工作进程启动、
Qt 中英文完整流程和备份排除。Computer Use 检查源码桌面入口、标签及返回，没有自动操作
成年声明或同意。使用合成数据共调用真实 GPT-5.6-Luna 套餐五次：前两次介绍空白，不可用；
补入应用已检查的成年声明后，中英文介绍可用。真实双语比较通过引用及撤销检查，无自动
重试。见[初次记录](evidence/2026-10-02-peer-plan.json)、[修正介绍](evidence/2026-10-02-peer-introductions-final.json)
及[当前发布检查](../CURRENT_STATUS.md)。样本不验证心理学效度。

10 月 2 日检查的实现依据：[FastAPI 令牌接口](https://fastapi.tiangolo.com/tutorial/security/first-steps/)、
[Python SQLite 事务](https://docs.python.org/3/library/sqlite3.html)、
[Windows 启动应用](https://learn.microsoft.com/en-us/windows/win32/shell/launch)、
[ChatGPT 模型发现与推理](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)。
这些支持技术选择，不构成法律或身份合规的声明。
