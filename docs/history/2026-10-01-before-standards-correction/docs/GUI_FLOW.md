# Historical snapshot / 历史快照

English: Superseded on October 2, 2026; current scope is in the root plan.

中文版：2026 年 10 月 2 日起被替代；当前范围以根目录计划为准。

# GUI Flow

## Current conversation-first flow — English

The main desktop route is simple and user-controlled:

```text
Welcome → Safety & Consent → choose/create local folder → Home
Home → Connect ChatGPT → browser sign-in and separate plan permission → Home
Home → AI Chat → Start → one optional AI question at a time
                 → answer / skip / change topic → Send → next question
                 → End at any time (late reply discarded)
                 → optionally Create my reflection → review → separately Save
Home → My reflections → AI Chat → Saved reflections (read earlier saved sessions)
Home → More tools → older import, portrait, risk, report and provider tools
```

A new or empty local folder can proceed to Home without importing files or building an older profile. **Start** makes the first question request only after an AI connection is active. Each remote question and reflection request has its own visible disclosure review; canceling sends nothing. There is no fixed duration, dating-market form, automatic data import, automatic portrait at End, automatic retry, or public matching. The new portrait uses only words typed by the user in this session; earlier AI questions are context, not evidence. It marks claims as low confidence and states unknowns. **Save this reflection** needs its own confirmation and creates ordinary, unencrypted files under `reports/reflection_history/<session_id>/`; **Saved reflections** reads these separate copies. Existing reports and their active choice are unchanged. In-place editing, deleting a saved session, and cross-session claim updates are design work still to come.

The main connection screen shows ChatGPT only. Local code implements official browser sign-in with PKCE, separate plan-use permission, model discovery and an AI adapter, but tests have used synthetic fakes, not a real account or model. The user checks plan eligibility and disables extra-credit use for this app in ChatGPT settings; the app cannot verify that switch. Earlier manual/local provider and import/report features remain reachable under **More tools**. Switching interface language keeps the current in-memory conversation and unsent draft. **Back** ends a running conversation before returning Home, while keeping its transcript and draft available in this app session for reflection; continuing requires starting a new session.

## 当前“先聊天”流程 — 中文版

桌面主流程由用户掌控，步骤保持简单：

```text
欢迎 → 安全与同意 → 选择/创建本地文件夹 → 首页
首页 → 连接 ChatGPT → 浏览器登录、单独授权套餐使用 → 首页
首页 → AI 聊天 → 开始 → AI 每次提出一个可跳过的问题
               → 回答 / 跳过 / 换话题 → 发送 → 下一问
               → 随时结束（丢弃迟到回复）
               → 可选“生成我的相处画像” → 阅读 → 再单独确认保存
首页 → 我的相处画像 → AI 聊天 → 已保存画像（读取先前会话）
首页 → 更多工具 → 原有导入、画像、风险、报告和服务连接工具
```

新建或选中的空文件夹也能直接进入首页，不必先导入资料或生成旧版档案。只有 AI 已连接，点击**开始**才请求第一问。每次远程提问或生成画像前，都有可见的发送内容复核；取消后不会发送。主流程没有固定时长、“交友市场”表单、自动导入资料、结束后自动生成画像、自动重试或公开匹配。新画像只引用用户在本次会话亲自输入的原话；先前 AI 提问只是背景，不是证据。画像把主张标为低置信度，并说明未知事项。**保存这份画像**需另行确认，在 `reports/reflection_history/<session_id>/` 写入普通、未加密的独立文件；**已保存画像**可读取这些副本。已有报告和当前报告选择不会改变。原地编辑、删除已保存会话、跨会话更新判断仍待设计和实现。

主连接页只显示 ChatGPT。本地代码已实现官方浏览器登录及 PKCE、单独套餐授权、模型发现与 AI 适配器，但测试仅使用合成假对象，没有真实账号或模型验证。用户需自行确认套餐资格，并在 ChatGPT 设置中关闭此应用的额外积分使用；应用无法核验该开关。旧版手动/本地连接和导入、报告功能仍在**更多工具**中。切换界面语言会保留内存中的对话和未发送草稿。点击**返回**会先结束正在进行的会话，再回到首页；本次应用运行期间仍可查看原对话与草稿并用于生成画像，但继续聊天需要开始新会话。

---

## Historical Agent Mode route (advanced)

The material below records the earlier Agent Mode route. Its entry points now live under **More tools**; it is not the main conversation-first workflow above.

The earlier desktop GUI used **Agent Mode**: the
desktop app did not analyze data itself. It prepared a vault (the *rules* + the
*data-saving standard*) and handed it to a desktop agent (Claude Code / Cowork),
which reviewed the designated inputs and wrote the result back into the vault.

The earlier **primary** task was self-understanding: the user added their *own* chat history
and notes, and the agent reflected back a theory-grounded portrait of *them*.
Analyzing a conversation with someone else (scam/risk) was a secondary tool.

```text
Welcome
  -> Consent
  -> Vault (detect / create / open)
  -> Home hub
        -> Understand Yourself      (your own data -> self-portrait; primary)
        -> Add Data                 (your chat history + notes -> the vault)
        -> View My Self-Portrait     (rendered reports/self_portrait.md)
        -> Analyze a Conversation    (someone else; scam/risk; secondary)
        -> Settings
        -> Offline Tools             (rule-based tools, advanced/offline path)
```

## Startup Flow

1. Welcome introduces AI-SlowMatch as a local relationship trust and anti-scam assistant.
2. Safety & Consent appears before any import or analysis.
3. Local Profile Detection checks the active vault (`<vault>/profile/profile.mpm.md`
   and `profile.json`). A folder counts as a vault by its structure, so a freshly
   created but empty vault is recognized rather than treated as "nothing here".
4. From the vault screen every path leads to the **Home hub**: continue an existing
   profile, build one in this vault, create a new vault, or open an existing vault
   (tolerant of selecting the parent folder).
5. Home is a minimal hub with one clear next step.

## Home hub actions

- **Understand Yourself** — the primary action. Writes `SELF_PORTRAIT_REQUEST.md`
  into the vault and shows a copyable prompt. The agent reads the user's own data
  and synthesizes the self-portrait.
- **Add Data** — collect the user's own chat history / notes into `imports/`.
- **View My Self-Portrait** — **Open Visual Report** renders a polished, offline HTML
  page (`reports/self_portrait.html`, generated from `self_portrait.json`) that opens in
  the browser: hero, animated Big Five trait bars, value cards, growth-edge cards, and an
  EN/中文 toggle, styled like a personality-test result page. The in-app Markdown of
  `self_portrait.md` remains as a lightweight fallback.
- **Analyze a Conversation** — secondary scam/risk tool for a chat with someone
  else (rule-based screen).
- **Settings** — provider settings (API Mode placeholder).
- **Offline Tools** — the earlier rule-based screens (conversation risk analysis,
  trust ladder, generate/view local profile, report export/verify, assisted browser
  export). Kept as an advanced/offline path; Agent Mode is recommended.

## Agent Mode contract

See `AGENT_ANALYSIS_HANDOFF.md`. In short: the app's only job in Agent Mode is to
state the rules and define exactly which files are input (`profile/`, `imports/`)
and which files the agent must write. For self-understanding that's a simple
`reports/self_portrait.md` (for the user), a `reports/self_portrait.detailed.md`
(for the agent to follow later), and a `reports/self_portrait.json` companion. All
synthesis is left to the agent.
