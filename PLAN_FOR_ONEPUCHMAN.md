# AI-SlowMatch — Plan (onepuchman's reading copy) / 计划（观澜击水 专用阅读版）

Bilingual by design — English first, Chinese (中文) below. Everything else in `docs/` (27+ files) stays English-only, agent-facing reference; this file plus `PROGRESS_TRACKER.md` are the two files you actually need to read. Live status/checklist now lives in `PROGRESS_TRACKER.md`, also bilingual, auto-updated by agents as work happens.

---

# ENGLISH

## What the project actually is

Not a dating app. It's a local-first desktop tool that helps someone slow down and check their own risk while talking to a stranger they met online: it analyzes pasted conversations for scam-pattern signals, tracks relationship pacing through a "trust ladder" (stranger → low-pressure chat → verified → safe-to-meet), builds a private profile document, and exports a signed risk report. Everything runs on the user's machine; nothing is uploaded automatically.

Current state: this is real, not just docs. ~2,400 lines of working Python (engine, PySide6 desktop GUI, FastAPI routes, report signing, browser-export helper), 19 test files, all wired into a working desktop MVP you can run today (`python run_desktop.py`).

## Does a mature competitor already exist?

Close, but not the same product.

| Product | What it does | Gap vs. yours |
|---|---|---|
| **Social Catfish** (~$27/mo) | Reverse image/identity search + AI "chat checker" that scans pasted messages for fraud signals | Cloud-based, paid, focused on *investigating the other person*, not on pacing your own behavior or keeping data local |
| **Bitdefender Scamio** (free) | General-purpose AI chatbot: paste any message/link/image, get a scam verdict | Generic scam detector, not dating-specific, no relationship pacing, no profile/journal, no local-only guarantee |
| **Bark / Aura** | Parental/gaming monitoring — scans kids' or gamers' chats for predators | Wrong audience, surveillance model (monitoring someone *else's* chats), not self-directed |
| Dating platforms (Tinder, Bumble, Hinge) | ID verification, in-app AI moderation | Only covers in-app chat; useless once a scammer moves you to WhatsApp/WeChat/Telegram, which is where most scam money actually moves |

No existing product combines: local-first/no-cloud privacy, a pacing model (trust ladder) instead of a one-shot verdict, a personal reflection profile, and a deliberately non-accusatory/non-scoring stance. That's your whitespace.

## Matching pivot — soulmate-finding, not swiping (clarified scope)

You asked to shift focus toward actually helping people find a soulmate, weighted toward deep compatibility (values, life goals, emotional/communication style) over superficial factors (wealth, status, interests, hobbies) — while still allowing a few necessary basic filters (location, age, income, and now also education, marital/relationship history, and health/lifestyle basics).

Clarified model, and it matters: this is **not** a centralized matching platform. There's no database of users, no discovery feed, no algorithm that searches a population and suggests candidates. People still find each other entirely on their own, the same way they always have. What gets added is a **decentralized, peer-to-peer compatibility comparison**: each person builds a private "Deep Compatibility Profile" on their own device, and — only when both people explicitly agree — they exchange a redacted, shareable summary of it directly with each other (a file, a QR code — no server involved) and run a local, on-device comparison. The output is a non-scoring reflection (where you align, where you differ, discussion prompts) — never a percentage match or ranking, which keeps this consistent with the project's existing "no public personality score" rule.

Why this shape and not a real matching pool: established compatibility algorithms (eHarmony, OkCupid) are centralized, proprietary, and well-documented to skew toward superficial similarity over actually-predictive compatibility, with no independent science backing their match quality. Decentralized/blockchain dating apps exist but are early-stage and focused on identity/reputation, not this specific "compare two already-connected people, locally, privately" use case. Nobody is doing the thing you're describing — that's good news for differentiation, and it also avoids the much harder, much riskier problem of needing a critical mass of users on a platform (which is what "full matching platform" would require, and which would conflict with the project's local-first identity and safety stance). Full technical plan: `docs/11_compatibility_matching_plan.md`.

Anti-scam/trust-ladder work stays the core of the product, per your direction — this is a second pillar added alongside it, sharing the same local-first, non-scoring, consent-gated philosophy, not a replacement for it.

## Target market — and why Chinese-speaking users belong in it from day one

English and Mandarin Chinese are, combined, the two largest first+second-language populations in the world — building bilingually from the start is the single highest-leverage market decision available here, not a later localization task.

Romance-scam demand evidence in English-speaking markets: FTC reports **$1.16B** lost to romance scams in the first 9 months of 2025 alone (up 22% YoY in complaint volume), median loss ~$2,200, older adults nearly twice as likely to report six-figure losses.

Demand evidence in Chinese-speaking markets is arguably even stronger: so-called "pig-butchering" scams (杀猪盘 — a term that originated in Chinese-language scam communities before spreading globally) have moved an estimated **$75B+** globally since 2020, with major scam-operation infrastructure historically tied to Chinese-speaking criminal networks operating out of Southeast Asia. Chinese courts alone show hundreds of documented 杀猪盘 prosecutions. This isn't an adjacent market — it's arguably the origin market for the exact scam pattern this tool is built to catch, which makes Chinese-language support a credibility issue, not just a reach issue.

## Is it feasible?

**Technically:** yes, low risk for the existing scope. It's a Python desktop app with a deterministic + optional-LLM engine — no novel ML research required, no infra to scale (local-first), working MVP already passes tests. The new scope items below (import, frontend, self-portrait) are each independently feasible — see the breakdown.

**As a business:** local-first + privacy-first is a genuine differentiator but also a monetization constraint. Realistic paths: free/open-source with optional paid features (cloud provider, advanced reports), or a niche play aimed at the over-50 demographic (English-speaking markets) and at Chinese-speaking communities directly affected by 杀猪盘-style scams — both audiences respond to "calm, non-accusatory, private" positioning better than a flashy app.

## New scope you asked to add — summary (full technical plan in `docs/10_data_import_and_frontend_plan.md`)

**1. Import your own social media / chat history / AI chat history.** Feasible *only* via each platform's own official "download your data" export — not scraping, not login automation (this is a hard line from the project's own privacy rules, and also the only legally safe approach). Official export exists and is V1-ready for: Instagram/Facebook, YouTube/Google Takeout, X (Twitter), TikTok, and WhatsApp (per-chat, with size limits). WeChat only officially exports Moments/Favorites/account info — not full chat history, since WeChat doesn't store chat history server-side. Douyin, Xiaohongshu (RedNote), and Bilibili have **no confirmed official self-export** as of this research — these stay on a manual paste-in fallback (same mechanism the app already uses for pasted conversations) until/unless that changes. I'm not going to wire up scrapers for these even though they exist online — that would break this project's own no-scraping rule and likely each platform's terms of service.

**2. Better-looking frontend.** PySide6 is the honest bottleneck you're feeling. Two-step fix: short-term, swap the visual layer to a Python-embedded webview (PyWebView) running a modern HTML/Tailwind UI — keeps 100% of your existing engine untouched, fastest visible improvement. Long-term — and this matches what your own roadmap docs already proposed — migrate to Tauri (a Rust-based shell rendering a real React/Svelte frontend, ~8MB installers, fast startup) with the Python engine running as a local sidecar. Don't skip straight to Tauri; prove the new screens cheaply first.

**3. Local AI agent vs. API for a self-portrait / personality model.** Your codebase already has a provider-abstraction layer built for exactly this choice — it just needs a local provider added. Recommended default: **Ollama** (a local LLM runtime) — the self-portrait gets generated entirely on-device, nothing about your imported social/chat/dating history ever leaves your machine, which matters a lot once all that data lives in one place. Cloud API stays available as an explicit opt-in for people who want stronger model quality and accept sending redacted data off-device. Output is framed the same way the rest of this project already insists on: a private, editable reflection document — not a score, not a diagnosis.

## Roadmap (live checklist now in `PROGRESS_TRACKER.md`)

1. Polish the existing MVP (taxonomy, trust-ladder edge cases, GUI rough edges).
2. Real provider hookup — add the Ollama local provider first, real cloud API second.
3. Build the V1-ready importers (Instagram/FB, Google Takeout, X, TikTok, WhatsApp) using the existing ChatGPT-import pattern as the template; WeChat partial import next.
4. Extend the profile schema with Tier 1 basic filters + Tier 2 deep-compatibility dimensions, then build the Shareable Compatibility Card export/import and the local comparator (`docs/11_compatibility_matching_plan.md`).
5. PyWebView+Tailwind UI pass; add Import Center, Self-Portrait, and Compatibility Comparison screens.
6. Closed pilot with 5–10 consenting users (in pairs, since the compatibility feature needs two people per test) — include both English- and Chinese-speaking testers given the market case above.
7. Decide distribution model (open-source vs. small paid version) based on pilot feedback.
8. Only then revisit Tauri migration, FastAPI server hardening, signed-keypair reports — these stay in `docs/08_roadmap.md` as later-phase material.

## Housekeeping

27+ markdown files in `docs/` for the current code size is a heavy ratio — keep them (agents use them for context), but you personally only need this file + `PROGRESS_TRACKER.md` + `README.md`. New technical depth from this round of planning lives in `docs/10_data_import_and_frontend_plan.md`, agent-facing, not required reading for you.

On "add to skill as rule" — I can't create or edit a reusable Claude skill from inside this session (that requires Settings → Capabilities on your end). What I did instead: added the bilingual-documentation requirement directly into this project's own `AGENTS.md`, so any future agent session working in this repo will follow it automatically, which gets you the same practical outcome.

---

# 中文版

## 这个项目到底是什么

这不是一个交友 App。它是一个本地优先的桌面工具，帮助用户在和网上认识的陌生人聊天时放慢节奏、检查自身风险：分析粘贴进来的对话，识别诈骗模式信号；通过「信任阶梯」（陌生人 → 低压力聊天 → 身份核实 → 可安全见面）跟踪关系推进节奏；生成私密的个人档案文档；导出带签名的风险报告。所有处理都在用户自己的设备上完成，不会自动上传任何数据。

目前状态：这不只是文档堆砌，是真实可运行的项目。已有约 2400 行可运行的 Python 代码（核心引擎、PySide6 桌面界面、FastAPI 路由、报告签名、浏览器导出辅助工具），19 个测试文件，全部接入到一个今天就能运行的桌面 MVP 中（运行命令：`python run_desktop.py`）。

## 市面上是否已有成熟的同类产品？

接近，但不完全相同。

| 产品 | 它能做什么 | 与你的项目的差距 |
|---|---|---|
| **Social Catfish**（约 27 美元/月） | 反向图片/身份搜索 + AI「聊天检测器」，扫描粘贴的消息找诈骗信号 | 云端、付费、关注点是「调查对方」，而非帮你管理自己的节奏，也不保证数据留在本地 |
| **Bitdefender Scamio**（免费） | 通用 AI 聊天机器人：粘贴任意消息/链接/图片，给出诈骗判断 | 通用诈骗检测器，不针对交友场景，没有关系节奏管理、没有个人档案/日记功能，也不保证纯本地 |
| **Bark / Aura** | 家长监控/游戏监控——扫描孩子或玩家的聊天记录找猎食者 | 受众完全不同（监控「别人」的聊天，不是自我管理），监控模式而非自主使用模式 |
| 交友平台（Tinder、Bumble、Hinge） | 身份验证、App 内 AI 审核 | 只覆盖 App 内聊天；一旦诈骗者把你转移到 WhatsApp / 微信 / Telegram，这些防护就失效了，而诈骗资金恰恰主要在这些场景流失 |

目前没有任何产品同时具备：本地优先/无云端隐私、节奏管理模型（信任阶梯）而非一次性判断、私密反思档案、刻意保持的「非指控性、不打分」立场。这正是你的市场空白点。

## 匹配方向的调整——找灵魂伴侣，而不是「刷脸式」匹配（范围已明确）

你要求把项目重心转向真正帮人找到灵魂伴侣，更看重深层兼容性（价值观、人生目标、情感与沟通方式），而不是表面因素（财富、地位、兴趣、爱好）——同时保留几项必要的基础筛选条件（地点、年龄、收入，现在再加上教育程度、婚姻/恋爱历史，以及健康与生活方式基础信息）。

明确后的模式很关键：这**不是**一个中心化的匹配平台。没有用户数据库，没有「发现」信息流，没有算法在用户池里搜索并推荐候选人。人们依然完全靠自己去认识对方，方式和以前一样。新增的是一种**去中心化、点对点的兼容性比对**：每个人在自己的设备上建立私密的「深层兼容性档案」——只有当双方都明确同意时，才会把经过脱敏处理的、可分享的摘要直接交换给对方（文件、二维码——不经过任何服务器），然后在本地完成比对。输出结果是一份不打分的反思报告（哪些地方契合、哪些地方不同、可以讨论的话题）——绝不是百分比匹配度或排名，这与本项目「不做公开人格评分」的原则保持一致。

为什么是这种形态而不是真正的匹配池：成熟的兼容性算法（如 eHarmony、OkCupid）都是中心化、专有的，且已被充分证明更倾向于「表面相似度」而非真正具有预测力的兼容性，也没有独立科学研究能证实它们的匹配效果。去中心化/区块链交友 App 也存在，但仍处于早期阶段，关注点是身份/信誉，并不是你描述的这种「让两个已经互相认识的人，在本地、私密地做比对」的具体场景。目前没有人在做你描述的这件事——这对差异化是好消息，同时也避免了「真正的匹配平台」所需要的更难、更高风险的问题：需要在平台上积累足够多的用户（这正是「完整匹配平台」方案所要求的，也与本项目本地优先的定位和安全立场相冲突）。完整技术方案见 `docs/11_compatibility_matching_plan.md`。

按你的要求，反诈骗/信任阶梯功能依然是产品的核心——这是在其之上新增的第二支柱，沿用同样的本地优先、不打分、需双方同意的理念，而不是取代它。

## 目标市场——以及为什么中文用户从第一天起就该是核心受众

英语和中文（普通话）合计是全球第一语言加第二语言人数最多的两个语言群体——从一开始就做中英双语，是目前能做出的杠杆最高的市场决策，而不是「以后再本地化」的次要任务。

英语市场的诈骗需求证据：美国联邦贸易委员会（FTC）数据显示，仅 2025 年前 9 个月，浪漫诈骗造成的损失就达 **11.6 亿美元**（投诉量同比增长 22%），中位损失约 2218 美元，老年人报告六位数损失的可能性几乎是年轻人的两倍。

中文市场的需求证据可能更强：所谓「杀猪盘」诈骗（这一说法最早就源自中文网络诈骗圈，后才扩散到全球）自 2020 年以来已在全球转移了约 **750 亿美元以上**的资金，主要诈骗园区基础设施历史上与活跃在东南亚的中文犯罪网络密切相关。仅中国法院系统就有数百份涉及「杀猪盘」的判决文书。这不是一个「附带」市场——可以说，这正是这类诈骗模式的「发源地市场」，因此支持中文不只是为了扩大用户覆盖面，更关乎产品的可信度。

## 这个项目是否可行？

**技术上：** 对现有范围而言，可行且风险低。这是一个 Python 桌面应用，核心是「确定性规则 + 可选 LLM」引擎——不需要原创的机器学习研究，无需扩容基础设施（本地优先），现有 MVP 已经能跑通测试。下面列出的新增功能（数据导入、前端、自我画像）每一项都各自可行——具体拆解见下文。

**作为一个产品/生意：** 本地优先 + 隐私优先是真正的差异化优势，但也限制了变现方式。比较现实的路径：开源 + 可选付费功能（云端模型、高级报告），或者聚焦细分人群——英语市场的 50 岁以上群体，以及直接受「杀猪盘」类诈骗影响的中文社群——这两类人群都更认可「冷静、不指控、私密」的定位，而不是花哨的 App 风格。

## 你要求新增的范围——摘要（完整技术方案见 `docs/10_data_import_and_frontend_plan.md`，仅英文，供 AI 代理使用）

**1. 导入自己的社交媒体 / 聊天记录 / AI 对话历史。** 唯一可行且合规的方式是通过各平台**官方的「下载我的数据」导出功能**——绝不抓取、绝不自动登录（这是本项目隐私规则的硬性底线，也是唯一合法安全的做法）。已确认有官方导出且第一版可直接支持的平台：Instagram/Facebook、YouTube/Google Takeout、X（推特）、TikTok，以及 WhatsApp（按单个聊天导出，有数量上限）。微信目前官方导出仅覆盖朋友圈、收藏、账号信息——**不包含完整聊天记录**，因为微信聊天记录本身不存储在服务器端。抖音、小红书、哔哩哔哩截至本次调研**没有找到可靠的官方个人数据导出渠道**——这些平台暂时只能走「手动粘贴文本」这条路（也就是 App 现有的对话分析功能本来就支持的方式），除非未来情况有变。即便网上能找到第三方抓取工具，我也不会接入——那会违反本项目自己的「禁止抓取」规则，也很可能违反各平台的服务条款。

**2. 更好看的前端界面。** PySide6 确实是你感觉到的瓶颈，这个判断没错。建议分两步走：短期方案——把界面层换成基于 Python 内嵌网页视图（PyWebView）的现代化 HTML/Tailwind 界面，现有引擎代码 100% 不需要改动，是见效最快的视觉升级方式。长期方案——这与你自己的路线图文档中早就提到的方向一致——迁移到 Tauri（基于 Rust 的外壳，渲染真正的 React/Svelte 前端，安装包约 8MB，启动速度快），Python 引擎作为本地「side car」子进程运行。不要直接跳到 Tauri 那一步；先用低成本的方式把新界面（导入中心、自我画像）验证清楚再迁移。

**3. 用本地 AI 还是 API 来生成自我画像/性格模型。** 你的代码库里已经有专门为这种选择设计的「服务商抽象层」，只需要新增一个本地服务商适配器即可。推荐默认方案：**Ollama**（本地大语言模型运行环境）——自我画像完全在用户设备本地生成，导入的社交/聊天/交友历史数据永远不会离开用户的电脑——一旦这些数据都汇聚到一起，这一点格外重要。云端 API 作为「需要用户主动选择」的可选项保留，给那些希望模型效果更强、并接受将脱敏数据发送到设备外的用户使用。输出形式延续本项目一贯的原则：是一份私密、可编辑的反思文档，不是打分，也不是诊断结论。

## 路线图（实时进度清单见 `PROGRESS_TRACKER.md`）

1. 打磨现有 MVP（诈骗分类细节、信任阶梯边界情况、界面流程中的细节问题）。
2. 接入真实的 AI 服务商——先加本地 Ollama 服务商，再加真实云端 API。
3. 按照现有 ChatGPT 导入功能的模式，构建第一版可用的导入器（Instagram/Facebook、Google Takeout、X、TikTok、WhatsApp）；接下来做微信的部分导入功能。
4. 扩展个人档案结构，加入第一层基础筛选条件和第二层深层兼容性维度，然后构建「可分享兼容性卡片」的导出/导入功能与本地比对引擎（详见 `docs/11_compatibility_matching_plan.md`）。
5. 完成 PyWebView + Tailwind 的界面升级；新增「导入中心」「自我画像」「兼容性比对」三个界面。
6. 进行 5–10 人（按对计算，因为兼容性功能需要两人配对测试）的小范围封闭试点——鉴于上面的市场分析，应同时包含中文和英文测试用户。
7. 根据试点反馈，决定发布方式（开源 vs. 小型付费版本）。
8. 在此之后才重新评估 Tauri 迁移、FastAPI 服务端加固、密钥对签名报告等——这些继续留在 `docs/08_roadmap.md` 中作为更后期的内容。

## 日常维护提示

以目前的代码量来说，`docs/` 文件夹下 27 个以上的 Markdown 文件确实偏多——继续保留它们（AI 代理需要用作上下文），但你个人只需要阅读这份文件 + `PROGRESS_TRACKER.md` + `README.md` 就够了。这次新增的技术细节都放在 `docs/10_data_import_and_frontend_plan.md` 中，那份文档是给 AI 代理看的，你不需要读。

关于「把这条规则加进 skill」——我在当前会话里无法创建或修改可复用的 Claude 技能（这需要你自己在 设置 → 功能 中操作）。我换了一种方式达到同样效果：把「双语文档」这条要求直接写进了本项目自己的 `AGENTS.md` 文件中，这样以后任何在这个项目里工作的 AI 代理都会自动遵守这条规则。
