---
name: slowmatch-setup
description: Set up or repair the released AI-SlowMatch Windows component and plugin, verify current account binding, and report layered readiness. Use for first installation, account changes or a diagnosed setup failure; ordinary relationship help uses slowmatch.
---

# AI-SlowMatch setup / 慢慢相识设置

## English

For local webpage setup, first use [the Codex setup guide](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/SETUP_WITH_CODEX.md): verified bootstrap `-Launch`, then the permanent daily launcher. This route reuses official AI authorization and explicitly selected account storage. The native plugin/remote binding steps below are optional for that separate route; local chat does not require Site access.

Install the existing product with bounded deterministic steps. The authority is
`onepunchman26/Anti-Dating-App-Scam`; use its pinned `v0.8.6` controlled preview and
[short installation guide](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/INSTALL_WITH_CHATGPT.md).
If the release is unavailable, report that gate. No source reconstruction, full-repository
audit, development agents, model/API calls inside scripts or automatic updates during chat.
Do not deploy a separate service for this user or change their model/subscription settings.

1. Check Windows x64, permitted local execution and plugin installation. The release includes
   `SlowMatch-Work.exe` plus dependencies; ordinary setup needs no Python/Git/Node installation.
   Use the release's `install`, `register-plugin` and `doctor` commands in the short guide/help.
   Keep the exact package together, verify its listed version/integrity, and preserve other
   plugins/settings. No permanent execution-policy changes. Missing local execution is blocked.
2. Let the owner complete the client's own login/connection/permission UI. The maintained
   service origin is `https://slowmatch-private-pilot.fizzydeer7.chatgpt.site`. Its bundled
   registered-app mapping does not grant access to another account. Do not ask for passwords,
   tokens or a maintainer's login. Do not claim a public catalog listing.
3. On each new session or account change, actually call connected `slowmatch_channel_check`
   with `{"write":false,"client_protocol":"1.0"}`. Require `authenticated:true`, expected
   `service_name:"AI-SlowMatch"`, supported protocol, and `data_scope.access:"enabled"`.
   Bind `account_fingerprint` and `data_scope.id` to the explicitly selected local slot.
   The fingerprint is not a credential and must not enter public diagnostics. Never invent it,
   derive it from a display name, reuse a remembered account, or trust tool arguments as identity.
4. Use the installed runtime's `slot-create` only for this verified account/scope with the
   owner's confirmation. A slot belongs to that account, scope and pinned service. Pass its ID,
   current fingerprint and scope to every [local business call](../../scripts/work.ps1).
   Do not load an existing slot before checking binding. Separate slots under one Windows user
   prevent accidental mixing; use separate OS users/devices for a stronger boundary. Never
   import a legacy vault automatically. If identity/scope cannot be verified, conversation can
   continue but bound local persistence is blocked; do not bypass it with developer mode.
5. For the minimal local check, invoke the launcher with current binding, `local-probe`
   and `--input-json -`, sending `{}`. It writes/reads/deletes a synthetic marker in a separate
   probe folder without touching the profile. Its `native_caller:not_independently_verified`
   cannot certify who invoked it; observe actual ChatGPT invocation separately.
   Report three independent rows: deterministic installation/connection; actual loaded Skill,
   synthetic local write/read and authenticated remote invocation; independent A/B flow.
   Use `PASS`, `FAIL`, `BLOCKED`, `NOT_CHECKED`. `doctor` cannot prove client invocation.
   Run only the smallest synthetic client probe explicitly authorized for setup; never publish
   profiles, contact people or create a meeting as an installation check. A/B tests require
   separate authorized accounts and a server-enforced controlled scope.

Stop initialization once the necessary checks pass; route to the [daily Skill](../slowmatch/SKILL.md).
For failure, read only the matching section of
[distribution help](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/docs/DISTRIBUTION_HELP.md).
Retry a diagnosed step only after new evidence; otherwise give the exact remaining condition.
Report short sanitized status, not full paths, private contents or tokens. Fixed scripts do not
use a model, but this guidance and real ChatGPT checks may consume usage. On an explicitly
requested loading probe, return `SLOWMATCH_SETUP_LOADED` only after reading this installed Skill;
that marker proves instruction loading alone.

## 中文版

本机网页设置优先使用[Codex设置指引](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/SETUP_WITH_CODEX.md)：核对安装脚本并用 `-Launch` 启动，以后使用固定日常入口。此路线复用官方AI授权及明确选择的账号存储；下列原生插件／远程绑定步骤只适用于另一条可选路线，本机聊天不以网站访问为前提。

按有限、确定性的步骤安装现成产品。权威仓库为 `onepunchman26/Anti-Dating-App-Scam`，使用固定
`v0.8.6` 受控预览和[简短安装页](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/INSTALL_WITH_CHATGPT.md)。
发布不可取得就报告受阻条件。不重建源码、不全库审计、不启开发 agent、不在固定脚本内请求模型/API，
不在日常聊天时自动升级。不为每位用户另建服务，不改变其模型／订阅设置。

1. 检查 Windows x64、本机执行和插件安装许可。发布包带 `SlowMatch-Work.exe` 及依赖，普通安装
   不需另装 Python/Git/Node。按短指引／帮助运行 `install`、`register-plugin`、`doctor`。
   保留整包，核对版本与完整性，保留其他插件／设置；不永久修改执行策略。缺本机执行能力就记受阻。
2. 由本人完成客户端登录、连接和权限界面。统一服务源是
   `https://slowmatch-private-pilot.fizzydeer7.chatgpt.site`；随包的已有 app 映射不授予其他账号访问权。
   不索要密码、令牌或维护者登录，不声称已上架公共目录。
3. 每次新会话或切换账号，实际调用已连接的 `slowmatch_channel_check`，参数
   `{"write":false,"client_protocol":"1.0"}`。要求 `authenticated:true`、服务名
   `"AI-SlowMatch"`、受支持协议和 `data_scope.access:"enabled"`。用回复的
   `account_fingerprint`、`data_scope.id` 绑定本人明确选择的本机槽位。指纹不是凭据，不能进入公开
   诊断；不虚构、不从显示名推导、不沿用记住的账号、不相信工具入参自报身份。
4. 仅为该已核实账号／范围、经本人确认使用已安装组件的 `slot-create`。槽位绑定账号、范围和固定
   服务。每次[本机业务调用](../../scripts/work.ps1)都传槽位 ID、当前指纹和范围。核对前不加载旧槽位。
   同一 Windows 用户的分槽防误混，不构成抵御该系统用户的安全边界；更强隔离用不同系统用户／设备。
   不自动导入旧库。身份／范围无法核实时仍可聊天，但账号绑定保存受阻，不用开发模式绕过。
5. 最小本机检查：用当前绑定调用启动器，操作 `local-probe`、`--input-json -`，输入 `{}`。
   它在独立探针目录写／读／删除合成标记，不碰私人档案。返回的
   `native_caller:not_independently_verified` 不能证明由谁调用，须另行观察真实 ChatGPT 调用。
   分别报告三层：确定性程序／连接；真正加载 Skill、合成本机写读与认证远程调用；独立 A/B 流程。
   使用 `PASS`、`FAIL`、`BLOCKED`、`NOT_CHECKED`。`doctor` 不证明客户端调用成功。
   只运行设置范围内明确授权的最小合成探针，安装检查不发布、不联系别人、不安排见面。
   A/B 测试需要独立获准账号及服务端强制隔离范围。

必要检查通过即结束初始化，进入[日常 Skill](../slowmatch/SKILL.md)。失败时仅读
[分发帮助](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/docs/DISTRIBUTION_HELP.md)
相关一段；只有新证据时才重试，否则说明具体剩余条件。仅报告简短脱敏状态，不展示完整本机路径、
私密内容或令牌。固定程序不调用模型，但引导与真实 ChatGPT 检查仍可能耗用额度。
明确要求加载探针时，只有读到本已安装 Skill 后才返回 `SLOWMATCH_SETUP_LOADED`；它只证明指令加载。
