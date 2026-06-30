# Progress Tracker / 进度追踪表

**Agent-maintained — do not hand-edit casually.** Any agent session that starts, blocks, or finishes a task listed in `PLAN_FOR_ONEPUCHMAN.md` should update this file's status in both languages, same edit. / **本文件由 AI 代理自动维护，请勿随意手动修改。** 任何代理在开始、卡住或完成 `PLAN_FOR_ONEPUCHMAN.md` 中列出的任务时，都应在同一次修改中同步更新中英文状态。

Status legend / 状态图例: ⬜ Not started / 未开始 · 🟦 In progress / 进行中 · ✅ Done / 已完成 · ⛔ Blocked / 受阻

Last updated / 最近更新: 2026-06-30

---

## Phase 1 — MVP polish / 第一阶段：完善现有 MVP

- ✅ Working desktop MVP (engine + PySide6 GUI + tests) / 可运行的桌面 MVP（引擎 + PySide6 界面 + 测试）
- ✅ Tighten scam-risk taxonomy & trust-ladder edge cases using synthetic test set / 用合成测试集打磨诈骗风险分类与信任阶梯的边界情况 — trust-ladder engine now reuses the scam-risk analyzer's `RISK_RULES` taxonomy instead of a separate hardcoded list; added regression tests for isolation pressure, guilt/fear pressure, emergency story, and naturally-phrased investment scams. / 信任阶梯引擎现在复用诈骗风险分析器的 `RISK_RULES` 分类体系，不再使用独立的硬编码列表；新增了针对孤立施压、愧疚/恐惧施压、紧急情况话术、自然语句投资诈骗的回归测试。
- ✅ Fix rough edges in desktop onboarding flow / 修复桌面端引导流程中的细节问题 — fixed a data-loss bug where navigating Home after loading/creating a profile could silently wipe it due to a stale legacy-state dict; `AppState.sync_from_legacy_dict` now only overwrites fields when the legacy dict actually carries a new value. / 修复了一个数据丢失问题：加载或创建档案后点击「主页」可能因旧版状态字典过期而被静默清空；`AppState.sync_from_legacy_dict` 现在只在旧版字典确实带有新值时才覆盖对应字段。

## Phase 2 — Real provider hookup / 第二阶段：接入真实 AI 提供方

- ⬜ Wire one real cloud LLM provider behind existing interface / 在现有接口后接入一个真实的云端 LLM 提供方
- ✅ Add Ollama (local) provider adapter — recommended default / 添加 Ollama（本地）提供方适配器 —— 推荐默认选项 — implemented `OllamaClient` (stdlib HTTP, no new dependency) plus thin adapters for both the `LLMClient` and `AIProvider` interfaces; registry now returns a real adapter for "Ollama" instead of a placeholder; tests use an injected fake transport, no real network/Ollama install required. / 实现了 `OllamaClient`（仅用标准库 HTTP，无需新依赖），并为 `LLMClient` 与 `AIProvider`两套接口都提供了适配器；provider 注册表现在为 "Ollama" 返回真实适配器而非占位实现；测试使用注入的模拟传输层，无需真实网络或安装 Ollama。
- ⬜ User-facing local-vs-API toggle with privacy explanation / 面向用户的「本地 / API」切换开关，并附隐私说明

## Phase 3 — New scope: data import / 第三阶段：新增功能 —— 数据导入

Import = user uploads their own official platform export file. No scraping, no login automation. / 导入方式均为用户自行上传官方导出文件，绝不抓取、绝不自动登录。

- ⬜ Importer interface shared by all sources / 所有来源共用的统一导入接口
- ⬜ Instagram / Facebook official export import / Instagram / Facebook 官方导出导入
- ⬜ Google Takeout (YouTube) import / Google Takeout（YouTube）导入
- ⬜ X (Twitter) archive import / X（推特）数据存档导入
- ⬜ TikTok official export import / TikTok 官方导出导入
- ⬜ WhatsApp per-chat export import / WhatsApp 单聊导出导入
- ⬜ WeChat Moments/Favorites/account-info import (chat history not yet possible — no official export exists) / 微信朋友圈·收藏·账号信息导入（聊天记录暂不支持——目前没有官方导出渠道）
- ⛔ Douyin / Xiaohongshu (RedNote) / Bilibili import — blocked, no confirmed official export found; paste-text fallback only / 抖音·小红书·哔哩哔哩导入 —— 受阻，未找到可靠的官方导出渠道，暂仅支持手动粘贴文本

## Phase 4 — New scope: Deep Compatibility Profile & decentralized exchange / 第四阶段：新增功能 —— 深层兼容性档案与去中心化交换

Decentralized, peer-to-peer only — no central user pool, no discovery feed, no algorithmic matchmaking. Two people who are already in contact, comparing locally. / 去中心化、点对点——没有中心化用户池、没有发现信息流、没有算法撮合。仅供两位已经互相认识的人在本地进行比对。

- ⬜ Extend profile schema: Tier 1 basic filters (location, age, income, education, marital/relationship history, health & lifestyle) / 扩展档案结构：第一层基础筛选条件（地点、年龄、收入、教育程度、婚恋历史、健康与生活方式）
- ⬜ Extend profile schema: Tier 2 deep-compatibility dimensions (values, life goals, attachment style, communication/conflict style, deal-breakers) / 扩展档案结构：第二层深层兼容性维度（价值观、人生目标、依恋风格、沟通/冲突处理方式、不可妥协事项）
- ⬜ Shareable Compatibility Card export (redacted, signed, file/QR) / 「可分享兼容性卡片」导出功能（脱敏、签名、支持文件/二维码）
- ⬜ Shareable Compatibility Card import + consent gate / 「可分享兼容性卡片」导入功能 + 双方同意确认
- ⬜ Local compatibility comparator (deterministic core, non-scoring output) / 本地兼容性比对引擎（规则驱动核心，不输出分数）
- ⬜ LLM-assisted discussion-prompt narrative layer (local Ollama default) / AI 辅助生成讨论话题的叙述层（默认使用本地 Ollama）

## Phase 5 — New scope: better-looking frontend / 第五阶段：新增功能 —— 更美观的前端界面

- ⬜ Step A: PyWebView + Tailwind UI pass over existing screens / 第一步：用 PyWebView + Tailwind 重做现有界面
- ⬜ New "Import Center" screen / 新增「导入中心」界面
- ⬜ New "Self-Portrait" screen / 新增「自我画像」界面
- ⬜ New "Compatibility Comparison" screen / 新增「兼容性比对」界面
- ⬜ Step B (later): Tauri + Python sidecar migration / 第二步（后续）：迁移到 Tauri + Python 子进程架构

## Phase 6 — New scope: self-portrait / personality model / 第六阶段：新增功能 —— 自我画像 / 性格模型

- ⬜ Local-first generation via Ollama provider / 通过 Ollama 实现本地优先生成
- ⬜ Opt-in cloud API path with explicit consent + redaction / 可选的云端 API 路径，需明确同意并支持信息脱敏
- ⬜ Output framed as private editable reflection doc, not a fixed score/diagnosis / 输出形式为私密、可编辑的反思文档，而非固定评分或诊断结论

## Phase 7 — Pilot & distribution decision / 第七阶段：试点与发布方式决策

- ⬜ Closed pilot with 5–10 consenting users in pairs (EN + CN speakers) / 5–10 名同意参与的中英文用户配对小范围试点
- ⬜ Decide: open-source release vs. small paid version / 决策：开源发布 vs. 小型付费版本

---

## Bilingual documentation rule / 双语文档规则

- ⬜ Confirm `README.md` has a Chinese counterpart or section / 确认 `README.md` 已补充中文对应内容
- ✅ `AGENTS.md` updated with bilingual rule for human-facing docs / `AGENTS.md` 已加入面向用户文档的双语规则
- ✅ `AGENTS.md` updated with no-real-name rule (use onepuchman / 观澜击水) / `AGENTS.md` 已加入禁止使用真实姓名的规则（统一使用 onepuchman / 观澜击水）
- ✅ `PLAN_FOR_ONEPUCHMAN.md` rewritten bilingually, incl. matching pivot / `PLAN_FOR_ONEPUCHMAN.md` 已改写为中英双语，并纳入匹配方向调整
- ✅ `docs/00_project_vision.md` reconciled with new matching feature / `docs/00_project_vision.md` 已与新增匹配功能做一致性说明
- ✅ Full desktop GUI (PySide6) made bilingual (EN + Simplified Chinese) — all screens, widget pages, window title, and CLI dependency message now use `bi()` helper / 全部桌面端 GUI（PySide6）已实现中英双语——所有界面屏幕、功能页面 widget、窗口标题及命令行依赖提示均改用 `bi()` 辅助函数输出双语文本
