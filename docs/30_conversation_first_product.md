> English: This dated record preserves the earlier audit/design. The implemented October 2 correction and current evidence are in [standards correction](32_standards_correction.md) and [current status](../CURRENT_STATUS.md).
>
> 中文版：本文保留早期审计／设计。10 月 2 日已实施整改及当前依据见[规范整改](32_standards_correction.md)和[当前状态](../CURRENT_STATUS.md)。

# Conversation-first product direction / 以对话为先的产品方向

## English

### Purpose and present scope

The first useful product is a private relationship conversation with a perceptive, grounded AI coach. It helps a person understand how they actually relate to others, notice needs and boundaries, and make calmer decisions without turning people into a catalogue of jobs, income, appearance, or defensive checklists. “Relationship coach” describes a way of asking and reflecting; it does not mean therapy, a personality diagnosis, a surrogate partner, or an authority over the user's choices.

The current local checkpoint focuses on the user's own conversation and a provisional self/relationship reflection. Risk awareness remains available in separate advanced tools; it is separate from whether two people might enjoy building a relationship. Unknown information is **unknown**, not evidence that someone is dangerous. No population search, introduction service, public profile, feed, swipe, score, rank, or predicted soulmate belongs in this release. Any later, slow introduction or comparison would require both adults' explicit, revocable participation and a separate design and privacy review; it has not been implemented.

### One simple path

1. Home offers **AI Chat**. Inside it, **Start** begins a fresh conversation and **End** remains available, including while a request is pending; there is no duration or “dating market” setup step. Before each remote request, the user reviews the proposed disclosure and may cancel. The user can skip a question, change topic, correct the AI in the conversation, or end at any moment.
2. The AI asks one relevant question at a time, adapting to the user's answers. It explores concrete experiences: pace of closeness, care and communication, needs, boundaries, how disagreement is handled, repair after hurt, and what the user can offer another person. It can ask for an example when an answer is abstract. It must not force intimate disclosure, infer a stable trait from one answer, or treat a desired partner as a list of assets.
3. **End** immediately stops this session and discards any late reply. It does not request or save a portrait. Only a separate **Create my reflection** action asks the AI for a short, private, provisional report; the user reviews it and separately confirms **Save this reflection**. Saved sessions are read from **Saved reflections** in their own local history folder, without changing existing reports or the active report choice. This checkpoint does **not** yet offer in-place editing, deleting saved sessions, or updating a claim across sessions. Those remain design goals, with visible correction history required before implementation.
4. The future coaching experience should suggest a few practical next steps, such as a question to ask a real person, a boundary to state, or a pace to try. The user chooses whether to act. Clear safety concerns deserve proportionate advice; the system does not promise a safe relationship or an inevitable match. These coaching outcomes still need real-model and user review.

### Model and connection boundaries

The implemented reflection cites exact spans from the user's typed statements in this session, marks claims as low confidence, and states what remains unknown. AI questions are conversation context, never evidence. A fuller model should eventually distinguish the user's own words, examples and source references, AI interpretations, needs, boundaries, conflict and repair habits, pace, and user corrections. Those additional editable fields are design gaps, not completed features. This path does not scan the user's vault, local ChatGPT history, another person's messages, or third-party platforms.

The main connection screen offers **ChatGPT** only. The local code implements the official **Continue with ChatGPT** browser sign-in with PKCE, a separate plan-usage permission, model discovery, and a provider adapter. [OpenAI's quickstart](https://developers.openai.com/siwc/quickstart) and [open-source desktop example](https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt) describe eligible Plus/Pro use and distinguish account sign-in from permission to use plan allowance. Neither permission grants access to earlier ChatGPT conversations. The code has been exercised with synthetic fakes, **not a real account or model**, so entitlement, live response quality and real authorization remain unverified. The user must check plan eligibility and disable extra-credit use for this app in ChatGPT settings before enabling it in the app; the app cannot programmatically guarantee zero credit use. The local ChatGPT desktop app is not a data source or login shortcut. No paid API call, purchase, card use, or silent fallback is authorized for development.

### What evidence can and cannot support

[Pronk and Denissen's three online-dating studies](https://research.tilburguniversity.edu/en/publications/a-rejection-mind-set-choice-overload-in-online-dating/) found increasing rejection across successive options in their study settings. This motivates testing a slower interface; it does not establish that every dating app objectifies people or that AI will improve relationships. A [43-dataset study of existing couples](https://pmc.ncbi.nlm.nih.gov/articles/PMC7431040/) found present relationship experience more informative for current quality than standalone traits, while change over time was largely unpredictable; it cannot validate matching strangers. A [four-week randomized chatbot study](https://arxiv.org/abs/2503.17473v2) found no significant effects from assigned conversation modes, while heavier voluntary use was associated with worse psychosocial outcomes. That association is not proof of causation, but it supports an easy stop and success measures other than time spent chatting. The [FTC's romance-scam guidance](https://consumer.ftc.gov/consumer-alerts/2025/02/looking-love-watch-out-scammers) supports a clear warning against sending money or gifts to an online-only romantic contact. The product flow above is a design hypothesis, not an established clinical or matching result.

Future evaluation should ask whether users understand the tentative reflection, can contest it in conversation and eventually edit or delete saved results, feel free to stop, retain control over disclosure, and can distinguish a concrete risk signal from missing information. The app does not collect these metrics today. Do not optimize for chat hours, swipes, or disclosures. Public testers, publication, and moving real private vaults to encrypted storage remain separate owner review decisions.

## 中文版

### 目标与当前范围

第一版有用的产品，是一段私密的亲密关系对话：由敏锐、务实的 AI 恋爱军师陪用户梳理自己如何与人相处、有哪些需要和边界，并更从容地作决定。它希望减轻把彼此当作职业、收入、外貌或防御性条件清单来筛选的负担。“恋爱军师”指提问和反思的方式，不是心理治疗、人格诊断、替代伴侣，也不替用户作主。

目前本地阶段只聚焦与用户本人对话，形成暂定的自我与相处反思。风险工具另列于高级功能，与“两人是否适合尝试建立关系”分开；资料未知就是**未知**，不能直接判为危险。此阶段不做人口搜索、引荐服务、公开档案、信息流、滑动筛选、评分、排名或“命定伴侣”预测。以后若考虑慢速介绍或比较，须经双方成年人明确且可撤回的同意，并另行审查设计和隐私边界；目前尚未实现。

### 一条简单路径

1. 首页提供 **AI 聊天**入口；进入后点击**开始**建立新会话，**结束**始终可用，包括请求仍在处理时。无需预选聊天时长或填写“交友市场”条件。每次远程请求前，用户可查看拟发送内容并取消；也可以跳过问题、换话题、在对话中纠正 AI，或随时结束。
2. AI 根据回答一次提出一个相关问题，询问具体经历：亲近的节奏、关心与沟通方式、需要与边界、分歧如何处理、受伤后如何修复，以及自己能为另一人提供什么。回答过于抽象时，可以温和地请用户举例。不能强迫披露私密经历、凭一次回答给人定性，或把未来伴侣变成资源清单。
3. 点击**结束**会立即停止本次会话并丢弃迟到回复，不会自动请求或保存画像。只有用户另点**生成我的相处画像**，AI 才生成简短、私密、暂定的报告；用户阅读后再单独确认**保存这份画像**。已保存会话可在**已保存画像**中从独立本地历史目录读取，不改变已有报告或当前报告选择。本阶段**还不能**在原地编辑、删除已保存会话，或跨会话更新某条判断；这些仍是设计目标，实现前需有可见的更正历史。
4. 未来的军师体验应提出少量可执行的下一步，例如可以问真实对象的问题、可以表达的边界，或可以尝试的相处节奏。做不做由用户决定。遇到明确安全风险应给出相称提醒，但不能保证一段关系安全或断言谁是“命中注定”。这类指导效果仍待真实模型和用户复核。

### 模型和连接边界

已实现的暂定画像只从本次会话中用户亲自输入的原话引用连续片段，将主张标为低置信度，并写清未知事项。AI 提问只是对话背景，不能当证据。更完整的模型今后还应分别记录用户原话、例子和来源、AI 解释、需要与边界、冲突及修复习惯、节奏和用户更正；这些可编辑字段仍是设计缺口，并非已交付功能。此路径不会扫描用户的档案库、本地 ChatGPT 既有聊天、他人消息或第三方平台。

主连接界面只提供 **ChatGPT**。本地代码已实现官方 **Continue with ChatGPT** 浏览器登录及 PKCE、单独的套餐使用授权、模型发现和服务适配器。[OpenAI 官方入门文档](https://developers.openai.com/siwc/quickstart)与[开源桌面应用示例](https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt)说明了符合条件的 Plus/Pro 套餐用法，也明确区分账号登录与套餐额度授权；两种授权均不开放以往的 ChatGPT 对话。代码已用合成假对象测试，**没有用真实账号或模型验证**，因此真实授权、套餐资格和模型表现仍未知。用户启用前需自行核对套餐资格，并在 ChatGPT 设置中关闭此应用的额外积分使用；本应用无法通过程序保证绝不消耗积分。本地 ChatGPT 桌面应用既不是数据来源，也不是登录捷径。开发期间不得调用付费 API、购买服务、使用银行卡或暗中切换连接方式。

### 证据的适用范围

[Pronk 与 Denissen 的三项线上约会研究](https://research.tilburguniversity.edu/en/publications/a-rejection-mind-set-choice-overload-in-online-dating/)在其研究情境中观察到，连续看到更多选项时拒绝倾向上升。这给“放慢界面节奏”提供了研究动机，却不能证明所有交友应用都会物化人，更不能证明 AI 一定改善关系。[针对既有伴侣的 43 组数据研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC7431040/)发现，当下的关系体验比个人静态特征更能解释当前关系质量，但之后的变化大多难以预测；它不能证明陌生人匹配算法有效。[一项为期四周的随机聊天机器人研究](https://arxiv.org/abs/2503.17473v2)没有发现分配到不同对话方式带来显著差异；自发使用更多的人与较差的心理社会结果有关。相关不等于因果，但提醒我们应让用户容易停止，也不能拿聊天时长当成功指标。[美国 FTC 的恋爱诈骗提示](https://consumer.ftc.gov/consumer-alerts/2025/02/looking-love-watch-out-scammers)支持明确提醒：不要给只在网上接触的恋爱对象汇款或送礼。以上产品路径是待验证的设计假设，不是已证实的临床或配对结果。

今后评估应看用户能否理解暂定反思、能否在对话中提出异议并最终编辑或删除已保存结果、是否能自在地停止、是否掌握披露控制权，以及能否区分具体风险信号与信息缺口。应用目前没有采集这些指标。不要优化聊天时长、滑动次数或披露量。公开试用、发布以及把真实私人档案迁入加密存储，仍须由项目所有者另行审阅决定。
