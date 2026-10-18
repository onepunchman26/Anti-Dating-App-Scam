# AI-SlowMatch Sites service / AI-SlowMatch Sites 服务

## English

For 0.8 controlled-test scope configuration, protocol checks and recovery, use the
[maintainer operations guide](../../docs/SITE_OPERATIONS.md). Ordinary users use the
root installation guide and never deploy their own copy of this service.

This is the authoritative Site/MCP source inside the original Python project. Source 0.8
extends the existing Sites Vinext/Cloudflare Worker and D1 service with independent romance
(`dating`) and friendship modes and minimal joint planning. It never hosts the private Python
store, AI inference, private risk reports, raw materials, audio or transcripts. Native Sites
request identity determines ownership; preview/test identity is simulated and cannot prove
real-account acceptance.

The [private pilot](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site) already exists.
[Current status](../../CURRENT_STATUS.md) records which version is actually deployed and the
remaining channel/independent-account blockers. Source implementation, deployment, plugin
connection and actual authenticated operations are separate claims.

The Python-generated `lib/shareable-profile.schema.json` must equal the source contract at
`src/anti_dating_scam/schemas/shareable_profile.schema.json`. Version 2 summaries include mode,
expiry (at most 365 days), independent summary/version, selected public fields and participation. Dating retains
partner/relationship criteria; friendship uses independent intent, shared interests/activity
styles, accepted interaction frequencies and boundaries. Mode-specific summaries do not
contain private biographies, source quotations, exact coordinates or contacts. The v1 contract
is retained separately for legacy handling; legacy participation cannot enable friendship.

The six summary tools are `slowmatch_read_my_summary`, `slowmatch_publish_summary`,
`slowmatch_set_discoverability`, `slowmatch_find_candidates`, `slowmatch_delete_my_summary`
and `slowmatch_channel_check`. All participant operations select a mode. Publication verifies
exact content digest and expected server revision. Digests do not verify honesty or human
consent. Candidate access checks active same-mode participation, reciprocal region/age/intent
and applicable friendship interests/styles/frequency. Unknowns do not pass hard conditions.
At most 12 candidates are returned from a bounded scan; there is no arbitrary identity lookup
or bulk export. Soft preference explanations are not personality/compatibility scores.

Ten additional tools support joint planning (16 remote tools in total):

| Tool suffix after `slowmatch_planning_` | Behavior |
|---|---|
| `create` | Requires an explicit instruction to invite this candidate; creates a pending on-Site request visible to the other participant on their next visit. It sends no external message and does not approve their preferences. |
| `list`, `read` | Return only the current account's participating spaces and allowed state. Pending preferences are not exposed to the other participant. |
| `preferences` | Publish only the caller's reviewed minimal fields with exact digest, expiry and version. Changing them invalidates the plan and both confirmations. |
| `context` | Produce a dedicated input from both currently approved preference objects alone. Missing, expired or withdrawn consent blocks shared generation. |
| `propose` | Share a reviewed bounded plan based on that exact joint context; still a proposal. |
| `confirm` | Confirm only the caller's chosen option in the exact current plan version. Both must confirm the same option. |
| `withdraw` | Stop further shared access and purge controlled planning content for both parties. |
| `feedback` | Share only the caller's selected again/undecided/not-now/no-again choice for the confirmed plan and expiry. No private report text. |
| `feedback_withdraw` | Remove only the caller's shared feedback; preserve the other person's choice and the plan. |

Shared fields are coarse area, time windows, budget, interests, duration, environment and
voluntary accommodation needs without sensitive reasons; plans add public place evidence,
check times, unknowns and versioned choices. This is the explicit narrow exception to the
old summary-only service. No home address, detailed calendar, private profile, risk reason,
raw material or audio enters this flow. Participants separately approve their own contribution,
purpose, recipient and expiry; maximum expiry is 30 days. A cannot authorize for B.

Local `sharing-draft/read/approve/export/withdraw` tools maintain independent approval
receipts; `planning-suggest` deterministically reads only supplied approved context and public
place evidence. The generator does not browse or call a model. ChatGPT must first check sources
through an available search tool; supplied source metadata is not itself proof of lookup.
Budget output is the shared spending ceiling, not a verified venue price. Local withdrawal
does not perform remote withdrawal; confirm the actual server receipt separately.
The canonical plan includes this budget basis and environment/accommodation requirements
with their unconfirmed status. `planning_area` must match both approved areas without claiming
geocoding. Checked hours, price or dated events need structured source facts; known closing,
budget or time-window conflicts are rejected. Caller-supplied local context does not authenticate
another user; the server checks the current bilateral context digest when receiving a plan.

Pausing/deleting a mode closes its shared planning without disabling the other mode. Expiry
is checked on access; it is not a background deletion scheduler. Summary deletion retains a
minimal replay-prevention tombstone; closed planning retains minimal status/version/participant
metadata while removing controlled preferences/plan/feedback content. Responses use no-store.
Platform backups and previously saved copies cannot be recalled. Local private histories have
separate lifecycle rules. Planning does not send invitations externally, reserve, pay, write
calendars, record or track location. Those are separate user-authorized actions.

The owner-approved bilingual [warning](../../plugins/slowmatch/skills/slowmatch/references/site-reminder.md)
belongs in homepage explanation, joining, candidate detail and the first planning flow. Its
presence in this README does not replace rendered-page acceptance. Keep implementation terms
out of the daily user path. Never expose private data even in hidden markup or browser state.

Development: `node scripts/run-framework.mjs dev --hostname 127.0.0.1`. Run the relevant
`node --test tests/*.test.mjs`, TypeScript check and Sites build helper after behavior changes.
Generate migrations with `node node_modules/drizzle-kit/bin.cjs generate`; never rewrite a
previously deployed migration. Wrangler applies local migrations; Sites applies production
migrations during publication.

Publishing: root `scripts/sites_source_snapshot.py` creates an allowlisted one-way mirror
under LocalAppData outside private-data directories. The supported Sites source workflow owns
only that mirror's hosting repository, never the original remote. `source-map.json` records
hashes and authority. Validate/build the same source, synchronize deliberately, and do not edit
the mirror independently. On this Windows host the npm JS entrypoint and Git Bash packaging
path were needed; use forward-slash absolute paths and `TAR_OPTIONS=--force-local` when required
by the helper. Supply credentials through supported hidden stdin, never files or arguments.

Thanks to Sites bundle `1.0.2-remix-a.1` and its Vinext starter. Actual copied MIT build and CSS
notices remain under `build/` and `vendor/`; the root credits distinguish bundled source from
method/documentation references. Existing notices remain applicable.

## 中文版

0.8 受控测试范围、协议检查及恢复见[维护者操作指引](../../docs/SITE_OPERATIONS.md)。
普通用户使用根目录安装入口，不自行部署本服务。

本目录是原 Python 项目内的 Site／MCP 权威源码。0.8 源码在现有 Sites Vinext／Cloudflare Worker
和 D1 上增加独立恋爱（`dating`）／朋友模式及最小共同安排，不托管私人 Python 存储、AI 推理、私人
风险报告、原始材料、音频或转写。所有权来自原生 Sites 请求身份；预览／测试身份是模拟的，不算真实
账号验收。

[私密试运行站点](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)已经存在；
[当前状态](../../CURRENT_STATUS.md)记录实际部署版本及通道／独立账号缺口。源码实现、部署、插件
连接和真实认证操作是独立状态。

Python 生成的 `lib/shareable-profile.schema.json` 必须与源文件
`src/anti_dating_scam/schemas/shareable_profile.schema.json` 一致。第二版摘要包含模式、最多三百六十五天的到期、
独立摘要／版本、选定公开字段及参与。恋爱保留择偶／关系条件；朋友采用独立交友意图、共同兴趣／
活动方式、接受频率和边界。摘要不含私人经历正文、来源引文、精确坐标或联系方式。第一版结构单独
保留供旧版处理，旧参与不能自动启用朋友模式。

六个摘要工具为 `slowmatch_read_my_summary`、`slowmatch_publish_summary`、
`slowmatch_set_discoverability`、`slowmatch_find_candidates`、`slowmatch_delete_my_summary`
及 `slowmatch_channel_check`。参与者操作均选择模式，发布校验准确内容哈希及预期服务版本；哈希
不核验诚实或本人同意。候选检查同模式有效参与、双向地区／年龄／意图和适用朋友兴趣／方式／频率，
未知不满足硬条件。有限扫描最多返回十二位，没有任意身份查询或批量导出。软偏好解释不是人格／兼容分。

另有十个共同安排工具（远程共十六个）：

| `slowmatch_planning_` 后缀 | 行为 |
|---|---|
| `create` | 明确要求邀请该候选后，才建立对方下次访问可见的本站待处理请求；不发外部消息，不替对方批准偏好。 |
| `list`、`read` | 只返回当前账号参与的空间及获准状态，待定偏好不向对方披露。 |
| `preferences` | 仅发布本人审阅的最小字段，绑定准确哈希、到期及版本；更新使计划及双方确认失效。 |
| `context` | 仅从双方当前批准的偏好构建独立输入；许可缺失、过期或撤回时拒绝共同生成。 |
| `propose` | 分享根据准确共同上下文审阅的有界计划，仍是提议。 |
| `confirm` | 只确认本人在当前准确版本所选方案；双方必须确认同一项。 |
| `withdraw` | 停止双方后续共享访问并清除受控安排正文。 |
| `feedback` | 仅分享本人针对已确认计划及到期所选再见／未定／暂不／不再见，无私人报告正文。 |
| `feedback_withdraw` | 仅撤回本人的共享反馈，保留对方选择及计划。 |

共享字段是大致地区、时间窗口、预算、兴趣、时长、环境及不含敏感原因的自愿便利需求；计划增加公开
地点证据、核对时间、未知和版本化选择。这是对旧“仅摘要”服务的明确狭窄例外，不允许家庭地址、完整
日历、私人档案、风险原因、原始材料或音频。各人单独批准本人贡献、用途、接收者和到期，最长期限三十天；
A 不能代 B 授权。

本机 `sharing-draft/read/approve/export/withdraw` 维护独立批准记录，`planning-suggest` 只读取
所供获准上下文和公开地点证据，确定性生成。它不浏览或调用模型，ChatGPT 须先用可用检索工具核对来源；
所填来源元数据本身不证明实际检索。预算输出是双方消费上限，不是核实场所价格。本机撤回不执行远程
撤回，另行核对真实服务端回执。
标准计划包含预算依据及环境／便利要求和未确认状态。`planning_area` 须符合双方批准区域，不声称地理
编码；核实营业、价格或活动日期须有结构化来源事实，已知关门／预算／时间窗口冲突会被拒绝。本机所填
上下文不能验证另一用户身份，服务端收到计划时核验当前双方上下文哈希。

暂停／删除某模式会关闭其安排，不关闭另一模式。到期在访问时检查，不是后台删除计划任务。摘要删除
保留最小防重放记录；关闭安排保留最小状态／版本／参与者元数据，清除受控偏好／计划／反馈正文。响应
不缓存，平台备份及他人此前保存的副本无法收回；本机私人历史另有生命周期。规划不外发邀请、不预订、
付款、写日历、录音或跟踪位置，这些需要独立授权动作。

所有者批准的双语[提醒](../../plugins/slowmatch/skills/slowmatch/references/site-reminder.md)用于首页
相关解释、加入、候选详情和首次安排。出现在本 README 中不能替代真实页面验收。日常用户路径不塞入
实现术语，隐藏页面标记或浏览器状态也不能存私密内容。

开发使用 `node scripts/run-framework.mjs dev --hostname 127.0.0.1`。行为改变后执行相关
`node --test tests/*.test.mjs`、TypeScript 检查及 Sites 构建。用
`node node_modules/drizzle-kit/bin.cjs generate` 生成迁移，不改写已部署迁移。Wrangler 应用本地
迁移，Sites 发布流程应用生产迁移。

根目录 `scripts/sites_source_snapshot.py` 在 LocalAppData 非私人数据目录创建允许列表单向镜像。
受支持 Sites 源码流程只管理镜像托管仓库，不改原远端；`source-map.json` 记录哈希及权威。检查／构建
同一源码再明确同步，不独立编辑镜像。本机 Windows 曾需 npm JS 入口及 Git Bash 打包路径，工具需要时
使用正斜杠绝对路径及 `TAR_OPTIONS=--force-local`。凭据只经受支持隐藏 stdin，不写文件或命令参数。

感谢 Sites bundle `1.0.2-remix-a.1` 和 Vinext 模板。实际复制的 MIT 构建与 CSS 声明保留于 `build/`
和 `vendor/`，根目录致谢区分打包源码和方法／文档参考；原声明继续适用。
