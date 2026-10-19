# Friends/groups migration evidence / 好友群组迁移证据

## English

The original repository remains authoritative. Work continues on `codex/friends-groups`
from rollback `9e0876cfa4b2d90921f59413c268fac414461e80`, with the existing remote intact.
Unrelated `.vscode/` and `paper/` were not read, modified or staged. The latest complete
turn in **整合Skills与界面** was retrieved. Its linked new Markdown attachment body was
not exposed and was not found at the supplied Desktop locations; its unseen fourteen
attachment clauses are not represented as reviewed. The complete conversation's ID,
friends, acquaintance, private groups and shared-activity requirements were implemented.

| Module | Evidence and decision | Acceptance |
|---|---|---|
| Auth, scopes and SQL storage | Reused validated platform identity and server-controlled isolation; additive migration 0006 | Cross-scope lookup and nonmember reads rejected |
| Discovery and pair planning | Existing functionality retained; friends need no discovery summary | Three synthetic accounts used zero discovery records |
| Social identity | New stable per-scope ID, opt-in exact lookup, mutual requests and block/remove | Browser ID/request/accept flow; ID survives nickname change |
| Small circles | New revision-guarded group aggregate, at most eight accepted/pending members, explicit activity roster | Three browser members individually accepted; ninth invite rejected |
| Shared conditions | Reused typed Python preferences with explicit travel limits, exclusions, optional values/communication and separate AI/romance consent | All-member intersection, denial, no overlap, withdrawal, races and expiry checked |
| Local shared AI | Reused official adapter and refactored pure deterministic planner; no private vault/session read | Source and browser each completed a real synthetic OpenAI request; two options and validated discussion returned |
| Web UI | Same component tree and language system; separate friends/group view | English/Chinese, actual 360/1280/1440 widths without horizontal overflow; draft/consent preserved across language switch |
| Distribution | Same original repository, prebuilt helper and maintained service | See current release receipt; no second/third real account inferred |

Local browser evidence used three fixed synthetic identities on loopback ports
5174–5176 against real Miniflare D1 and the production service functions. The QA proxy
is excluded from the one-way Site mirror and Windows package. A temporary paired
helper on port 8911 used only synthetic inputs and its isolated LocalAppData QA directory.
No real private vault was scanned. The flow reached **Everyone chose the same option**
after three separate confirmations. Language changes left the QA API-call count at 99,
kept the unsubmitted area draft and approval, and initiated no model call.

Automated Site suite: **37 passed**. Final focused Python planning/companion suite:
**62 passed**. Compile, TypeScript and production build passed. Full Python: **2,571 passed,
11 skipped**; final capability checks 22; bootstrap 41 passed / 1 skipped. The 150-file
0.8.2 package from clean source `e22ffd2` passed 29 actual EXE calls and one real synthetic
three-person AI generation. Its public GitHub download and repeated cached installation
both passed, including official plugin registration and zero setup model calls. Site
version10 deployed from hosting source `a9d7eb5`; authenticated native read-only health
checked the new database structure. The new social tool still needs a refreshed native
chat invocation. [Sanitized receipt](evidence/2026-10-18-friends-groups.json).

Important limits: public venue links are supplied and marked unverified; map/place
search and route-duration checks are not automated. Every participant must check route,
price, opening hours and required conditions before confirming. An expired/withdrawn
context cannot authorize a later result, but already transmitted copies cannot be recalled.
Shared consent is rechecked on proposal; a local request already sent to OpenAI cannot
be unsent. Group expiry is at most 30 days. Member changes end current activities;
removing/blocking closes common groups. These conservative preview semantics are visible.

The Site remains owner-private. Independent B and C are unavailable, so real three-account
invitation, installation, identity isolation and hosted lifecycle are **NOT EXERCISED**.
Fresh account authorization, distribution eligibility/license and hosted HTTPS-to-loopback
browser acceptance remain separate gates. Local synthetic and current-owner AI successes
do not resolve them. No access was widened, message sent, reservation made or payment made.

## 中文版

原仓库继续作为源码权威。在 `codex/friends-groups` 分支从回退点
`9e0876cfa4b2d90921f59413c268fac414461e80` 继续，远端不变。无关 `.vscode/`、`paper/`
未读取、修改或提交。已读取“整合Skills与界面”的最新完整轮次；其中新 Markdown 附件正文未由
工具提供，在所给桌面位置也未找到，所以不声称读过附件中未展示的14条细则。已实施完整对话中的
ID、好友、熟人、私人群组与共同活动要求。

| 模块 | 证据与复用决定 | 验收 |
|---|---|---|
| 认证、范围和存储 | 复用平台验证身份及服务端隔离，新增0006迁移 | 拒绝跨范围查找和非成员读取 |
| 发现与双人计划 | 保留已有功能，好友无需先发布发现摘要 | 三个合成账号使用零条发现记录 |
| 社交身份 | 新增稳定范围内ID、完整ID可选查找、双向申请及屏蔽／删除 | 浏览器查找申请接受；改昵称不改ID |
| 小群组 | 新增带版本检查的群组状态，已加入及待邀请最多8人，独立活动名单 | 三人分别接受；拒绝第9个邀请 |
| 共同条件 | 复用Python类型模型，增加路程限制、排除兴趣、选填价值观／沟通、独立AI／恋爱授权 | 检查全员交集、拒绝、无交集、撤回、并发和到期 |
| 本机共同AI | 复用官方适配器与纯确定性规划器，不读私人档案／会话 | 源码和浏览器各完成一次真实合成OpenAI请求，返回两选项及结构有效讨论 |
| 网站界面 | 同一组件树和语言系统，独立好友群组入口 | 中英文及实际360／1280／1440宽度无横向溢出，切语言保留草稿和批准 |
| 分发 | 同一原仓库、预构建助手及维护者统一服务 | 以当前发布证据为准，不推定第二／第三真实账号已通过 |

本机浏览器证据使用5174–5176三个端口的固定合成身份，连接真实 Miniflare D1 和正式服务函数。
测试代理不进入网站单向镜像或Windows包。8911临时配对助手只处理合成输入，使用隔离的LocalAppData
测试目录，没有扫描真实档案。三个成员分别确认后，页面显示“全员已确认同一方案”。切换语言时
测试API调用数保持99，未提交区域草稿和批准状态保留，没有触发模型请求。

网站自动化套件 **37项通过**，最终Python规划／助手针对性套件 **62项通过**，编译、TypeScript
及正式构建通过。完整Python **2,571通过、11跳过**，最终能力检查22项，安装器41通过／1跳过。
来自干净源码 `e22ffd2` 的0.8.2包含150个清单文件，通过29项实际EXE调用及一次真实合成三人AI
生成。GitHub公开下载及缓存重复安装均通过，包括官方插件登记，设置时模型调用为零。
网站第10版由托管源码 `a9d7eb5` 部署，认证原生只读检查确认新数据库结构。新社交工具仍需新原生
会话调用验收。[脱敏记录](evidence/2026-10-18-friends-groups.json)。

实际限制：公共场所链接由人提供且标记未核实；地图／地点搜索与路程计算尚未自动化。每个人确认前
须自行核对路线、费用、营业时间和必要条件。过期／撤回上下文不能批准后续结果，但无法收回已传出
的副本。发布前再次检查共享同意；已发往OpenAI的请求无法撤回传输。群组最长30天，成员变化结束
当前活动，删除／屏蔽关闭共同群组。这些预览版保守规则已在界面明确显示。

网站仍仅限所有者访问。独立B、C账号不可用，真实三账号邀请、安装、身份隔离及线上生命周期均
**尚未实测**。新账号授权、分发资格／许可及HTTPS网站到本机助手仍是独立限制。
本机合成测试和当前所有者AI成功不替代这些验收。没有扩大访问、向外发消息、预订或付款。
