# Shared activity planning / 共同活动安排

## English

First distinguish a private draft from a jointly shared plan and keep romance/friendship intent
explicit. Use implemented tools shown by `schema`/`--help`; do not invent command names or
claim a feature exists because this reference describes it. Missing shared infrastructure
still permits an honest private draft labelled “pending the other person's confirmation.”

Current local sequence: `sharing-draft` → `sharing-read` → `sharing-approve` →
`sharing-export`, with `sharing-withdraw` for local withdrawal. Export reports approved,
not sent; local withdrawal does not revoke a copy already on Sites. Use the corresponding
authenticated remote operation and check its actual receipt. `planning-suggest` is the
deterministic shared-only builder: it accepts the current approved joint context plus two
or three checked public place objects. It reads no private store and makes no model/network
call. It does not verify source URLs itself; check them first. Its budget is a shared spending
ceiling, not a venue price. Render its controlled choices into natural language without adding
private details or claiming an unverified arrangement/accessibility requirement is satisfied.
Each place's `planning_area` must match both approved coarse areas; this is not geocoding.
Claiming checked opening hours, price or an event date requires the corresponding structured
`source_open_window`, `source_admission` or `source_event_at` value. Preserve unknowns when
sources do not establish these facts. The builder can reject known closure/time/budget conflicts,
but a caller-supplied digest alone does not authenticate B; the live Site validates its current
bilateral context before accepting a shared proposal.

The Site's `slowmatch_planning_create` creates a pending request the peer can see. It requires
an explicit instruction to invite this candidate, separately from merely asking for ideas.
`slowmatch_planning_preferences` shares only the caller's own approved fields;
`slowmatch_planning_context` returns both approved objects when available. Use
`slowmatch_planning_propose` only with the exact locally reviewed plan and current server
revision. `slowmatch_planning_confirm` confirms only this caller's selected option; both
people must choose the same option in the same current version. Use `slowmatch_planning_read`
or `slowmatch_planning_list` to resolve uncertain state, `slowmatch_planning_withdraw` to stop
remote shared access, and `slowmatch_planning_feedback` only for an approved selected choice.
`slowmatch_planning_feedback_withdraw` removes only this caller's feedback, leaving the plan
and the other person's contribution intact.

Build shared context exclusively from each person's separately approved planning fields:
coarse area, time windows, budget, interests, duration, environment and voluntarily stated
accommodation needs without sensitive reasons. Never load a private profile, risk report,
raw transcript, home address, full calendar or precise location into a shared planning flow.
Approval must bind participant, object version, purpose, audience, expiry and withdrawal state.
A cannot consent, edit boundaries or confirm attendance for B. Missing B input stays unknown.
Recheck access and consent before each use; pause/revocation stops later shared access/generation.

Prompt secrecy is not isolation. If the current conversation already contains private context,
do not export its generated plan as safe merely because the model was told not to disclose it.
Use a clean supported context with only approved objects and an output schema, or a restricted
deterministic flow reading those objects alone. If neither is available, keep help private and
state that shared generation is unavailable; never create a new chat without user authorization.
Shared feedback is composed from individually selected contributions, not two private reports.

Confirm the intended coarse area before searching. Optional host location hints can be absent
or approximate and do not prove GPS, identity or consent. Web search, map display, location,
recording and transcription are separate capabilities. Use available web/place tools to open
official venue/event pages; preserve the actual source URL and check time. If lookup is missing,
offer activity types or user-supplied places with unverified details, never invented venues.

Default to two or three comparable options. Each should include activity and place/link/address,
fit based only on shared interests, sequence and duration, budget basis, opening/reservation
facts with sources/check time, unknowns, a natural opener, independent arrival and exit, and a
weather/closure fallback. Do not assert seats, price, availability or route time without evidence.
For an early meeting favor public, low-pressure, easy-to-leave options. A short or online meeting,
postponing or not meeting is valid; no real-time tracking or home departure point is needed.

Keep each option a draft until the required participants confirm that exact plan version.
A substantive plan change invalidates prior confirmations. Both current confirmations are
needed for “both confirmed”; no response is neither agreement nor rejection. Show the
[Site reminder](site-reminder.md) in the first shared-planning flow.

A plan does not authorize invitations, reservations, tickets, payment, calendar writes or
location sharing. These require a separate explicit real-action instruction and supported
account/permission. Never infer that an API or third-party service is free or covered by a
ChatGPT subscription. Respect unavailable credentials/approvals and continue the private path.

## 中文版

先区分私人草案与双方共享计划，明确朋友／恋爱意图。工具以 `schema`／`--help` 实际列出的操作为准，
不虚构命令，不因本参考描述了流程就声称能力已存在。共享基础设施缺失时，仍可提供明确标为“待对方确认”
的私人草案。

当前本机顺序为 `sharing-draft` → `sharing-read` → `sharing-approve` → `sharing-export`，
`sharing-withdraw` 撤回本机许可。导出只表示已批准而未发送，本机撤回不撤销已在 Sites 的副本；须调用
对应认证远程操作并核对真实回执。`planning-suggest` 是确定性、仅共享输入的构建器，接收当前获准共同
上下文及两到三个已核对公开地点对象，不读私人存储，不调用模型或网络。它不自行核实来源 URL，须先
核实；预算是共同消费上限，不是场所价格。把受控选项表达为自然语言时不加入私人信息，不宣称未核实的
环境／便利要求已满足。
每个地点的 `planning_area` 必须符合双方批准大致区域，这不是地理编码。声称已核实营业时间、价格或
活动日期时，须有对应结构化 `source_open_window`、`source_admission` 或 `source_event_at`；来源
不能证明时保持未知。构建器可拒绝已知关门／时间／预算冲突，但调用方自填哈希不验证 B 身份；真实网站
接受共同提案前还会检查当前双方上下文。

网站 `slowmatch_planning_create` 会创建对方可见的待处理请求，必须明确要求邀请该候选，不能从“给我
些想法”推断。`slowmatch_planning_preferences` 只分享调用者自己的获准字段；双方可用时
`slowmatch_planning_context` 返回两个批准对象。`slowmatch_planning_propose` 只传本机准确审阅计划
和当前服务版本；`slowmatch_planning_confirm` 只确认本人选项，双方须在同一当前版本选同一项。
状态不确定时用 `slowmatch_planning_read`／`slowmatch_planning_list` 核对，
`slowmatch_planning_withdraw` 停止远程共享访问；`slowmatch_planning_feedback` 只提交获准选定意愿。
`slowmatch_planning_feedback_withdraw` 只撤回本人反馈，保留计划和对方贡献。

共同上下文只从各自单独批准的安排字段构建：大致地区、时间窗口、预算、兴趣、时长、环境偏好及自愿提供
的必要便利需求，不包括敏感原因。不得加载私人档案、风险报告、原始转写、家庭住址、完整日历或精确位置。
批准绑定参与者、对象版本、用途、受众、到期和撤回状态。A 不能代 B 同意、修改边界或确认出席，缺少 B
信息时保持未知。每次使用前重新检查访问与授权；暂停／撤回后停止后续共享读取和生成。

提示词保密不等于上下文隔离。当前对话已有私人内容时，不能仅凭“不要泄露”就导出其中生成的计划。使用
只含获准对象和输出结构的干净受支持上下文，或只读取这些对象的受限确定性流程。两者都不可用时保留私人
建议，并说明共享生成不可用；未获用户授权不新建聊天。共同反馈由各自选定贡献组合，不合并两份私人报告。

检索前确认目标大致地区。宿主位置提示可能缺失或不准确，不代表 GPS、身份或同意。网页检索、地图展示、
定位、录音和转写是不同能力。用实际可用的网页／地点工具打开官方场所／活动页面，保留真实来源链接和
核对时间。缺少检索时给活动类型或用户所供地点，并标注未核实，不编造场所。

默认给两到三个可比较方案：活动、地点／链接／地址、仅基于共同兴趣的理由、步骤和时长、预算依据、营业／
预约事实与来源和核对时间、未知、自然开场、各自到达与离开方式、天气／关门备选。没有证据不承诺空位、
价格、可预订或路线时长。早期见面优先公共、轻松、容易离开的地点；短时、线上、延期或不见面都有效，
不需要实时跟踪或家庭出发点。

所需参与者确认准确版本前，方案始终是草案。实质修改后原确认失效；只有双方对当前版本都确认才称“双方
已确认”，无回应既不是同意也不是拒绝。首次共同安排显示[网站提醒](site-reminder.md)。

生成计划不授权邀请、订位、购票、付款、写入日历或共享位置；这些需要单独明确的实际动作指令和受支持
账号／权限。不假定 API 或第三方服务免费或包含在 ChatGPT 订阅中。凭据／审批缺失时遵守限制，继续私人路径。
