# Distribution help / 分发帮助

## English

AI-SlowMatch is published from the existing
[onepunchman26/Anti-Dating-App-Scam](https://github.com/onepunchman26/Anti-Dating-App-Scam)
repository. [v0.8.0](https://github.com/onepunchman26/Anti-Dating-App-Scam/releases/tag/v0.8.0)
is a controlled Windows x64 preview, not a stable release, public plugin listing or proof of
independent-account access. Check the actual Release/assets and
[validation record](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/docs/DISTRIBUTION_VALIDATION.md) before stating availability. No project-wide
open-source license has been assigned by this migration; preserved third-party licenses
apply to their respective components. See [credits](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/docs/39_open_source_credits.md).

### Commands: normal user installation

Start with [the short guide](../INSTALL_WITH_CHATGPT.md), download the Release's named
Windows archive and integrity information, verify them, and extract the whole archive.
Do not run a binary from a lookalike repository. From the extracted package folder:

```powershell
.\SlowMatch-Work.exe install --package .
.\SlowMatch-Work.exe register-plugin
.\SlowMatch-Work.exe doctor
```

When the Release supplies the expected SHA-256 of `work-release.json`, pass that exact
value to `install --expected-manifest-sha256 <value>`; do not invent one. The installer
verifies its allowlisted component manifest and runtime before activation. Keep `_internal`
and other listed runtime files alongside the EXE. It installs into
`%LOCALAPPDATA%/AI-SlowMatch/portable/releases/`; private data is separately stored in
`%LOCALAPPDATA%/AI-SlowMatch/accounts/<opaque-slot>/work`. The old developer `work` store
is not silently migrated. Do not put private data in source, OneDrive or plugin caches.

This portable package includes its Python/Pydantic runtime. It intentionally excludes Vosk
and speech models because the available Vosk native wheel's bundled notices could not be
audited for this release. Private selected text/WAV import and user-supplied/corrected
transcripts remain available; automatic transcription is unavailable in the portable preview.
The source project's optional Vosk path is separate. Do not download models during setup.

`register-plugin` uses the installed release's local marketplace and the supported native
`codex plugin marketplace add <installed-release> --json`, then
`codex plugin add slowmatch@slowmatch-local --json`. It preserves unrelated settings.
This primary path does not clone Git or compile code. The current automatic registration
requires the supported `codex` installer to be available to this desktop environment;
absence returns `supported_plugin_installer_unavailable`. Installing the EXE alone does
not install that platform capability. Do not solve this by installing arbitrary developer
tools, editing all of `config.toml`, or granting broader permissions.

The manifest declares the official packaged setup entry
`extensions.com.openai.onboardingSkill: "./skills/setup/SKILL.md"`; select setup when the
client offers it. Its declared path is not proof that the client invoked it.
[OpenAI packaging documentation](https://developers.openai.com/plugins/build/plugins)
describes this contract and local marketplace commands.

### Account connection and first use

Use the one maintained [service](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site).
The owner completes their own supported desktop login/connection and local-access prompts.
Do not request passwords or reuse maintainer credentials. The bundled `.app.json` identifies
an existing registered Site app; that identifier does not grant an outside account access.
Each account's installation, connection and entitlement must be checked separately.

The pilot can use one maintainer-configured default controlled test scope for all accounts
that the platform already permits to access it. This avoids per-tester runtime configuration;
it does not grant platform access. Individual expiring memberships are an optional advanced
override. Testers never edit server configuration or supply maintainer credentials. Check
the actual `data_scope` response; absent/expired enrollment does not fall back to production.

The setup Skill calls `slowmatch_channel_check` with
`{"write":false,"client_protocol":"1.0"}` using the current user's authenticated connection.
Require `authenticated:true`, service `AI-SlowMatch`, supported protocol and
`data_scope.access:"enabled"`. Use the returned `account_fingerprint` and `data_scope.id`
only to bind the owner's chosen local slot. Never include fingerprints in public diagnostics.

```text
SlowMatch-Work.exe slot-create --account-key <current-fingerprint> --scope <current-scope> --confirmed
SlowMatch-Work.exe doctor --slot <returned-slot> --account-key <current-fingerprint> --scope <current-scope>
```

These placeholders come from actual current responses and the owner's selection; they are
not account IDs the assistant may invent. The runtime also binds the OS owner and pinned
service origin. A fingerprint is an ownership assertion, not a login or security token.
Call health afresh in a new session or after account changes before local access. Same-Windows-user
slots prevent accidental mixing, not hostile access by that OS user; independent-account
acceptance uses separate devices/OS users and independently signed-in clients.

Ordinary operations use the installed plugin's `scripts/work.ps1`, with explicit `--slot`,
`--account-key`, `--scope`, then the operation and JSON input. It never silently falls back
to the developer source runtime. The first flag `--developer-source` is retained only for
explicitly requested development; it is not an installation or account-isolation workaround.
Pass private JSON by stdin or an explicitly authorized local file, not interpolated shell text.

For `--input-json -`, the launcher must receive **process standard input**. A PowerShell
object pipeline directly into a `.ps1` script is not forwarded to its native child. Launch
the script with the already-permitted PowerShell executable's `-NoProfile -File` arguments
and write the JSON to that process's stdin; close stdin after the payload. Alternatively,
use the documented EXE command below, or `--input-json` with an explicitly authorized private
local file. Do not change execution policy. An empty-input `operation_failed` is not a reason
to reinstall or repair source. Keep private JSON and account bindings out of copied diagnostics.

For a minimal synthetic local check, send `{}` via stdin to
`SlowMatch-Work.exe run --slot <slot> --account-key <current-fingerprint> --scope <current-scope> local-probe --input-json -`.
The same operation works through the plugin launcher. It writes/reads/deletes a synthetic
marker in a separate probe folder, without touching the private profile. It returns
`local_read_write:passed_synthetic_only`, `native_caller:not_independently_verified` and
`remote_authentication:not_checked`; only actual observed invocation establishes the caller.

### What each check proves

| Layer | Evidence and limits |
|---|---|
| Program | `doctor` checks manifest/runtime and, when supplied, local slot binding. Its `native_chatgpt`, `remote_authenticated_identity`, `two_independent_accounts` remain `not_checked`. It makes no model call. |
| Desktop | Actually invoke the installed setup/daily Skill, the smallest synthetic local probe and authenticated health through ChatGPT. Reading source, running a terminal and opening the website are separate evidence. A missing native tool/permission is `BLOCKED`, not pass. |
| Product | Follow [CONTROLLED_TEST.md](../CONTROLLED_TEST.md) from two independent authorized accounts in the same server-enforced test scope. Mock identities, same-account tabs and forged headers do not qualify. |

Use `PASS`, `FAIL`, `BLOCKED`, `NOT_CHECKED` in human summaries; retain the program's precise
machine status underneath. Do not publish personal data, contact anyone or create plans as
an installation check. Controlled synthetic publishing needs the separate test authorization.
The native setup probe and the independent-account flow remain pending unless their actual
evidence is recorded. Successful terminal registration is not a fresh ChatGPT conversation test.

### A short result to copy for help

Share only version/channel, the named check states, a stable error code and the required next
step. Exclude full local paths, fingerprints, slot IDs, raw tool responses, credentials and
private content. Example: `0.8.0 controlled-preview; package=PASS; native=NOT_CHECKED;
remote=BLOCKED; code=connection_unavailable`. Do not append a profile, transcript or database.

| Result | Targeted next step |
|---|---|
| Release/page unavailable | Wait for the exact preview release; do not build source or choose a moving branch. |
| `release_checksum_mismatch` / integrity error | Stop using that package; obtain the same trusted release again and verify its published integrity information. |
| `repair_required` | Use that verified release's `repair --package .`; rerun the failed check once. |
| `supported_plugin_installer_unavailable` | Platform installer is unavailable in this environment; report the prerequisite and use an eligible desktop. The EXE cannot create that entitlement. |
| Plugin unavailable / connection denied | Check the current account's actual plugin/workspace access. Maintainer-private registration is not transferable. |
| `owner_binding_mismatch` | Stop before any profile read; verify current login/scope and explicitly select its own slot. Do not edit owner metadata. |
| Scope expired / not configured | Maintainer checks the once-configured shared test scope or optional membership override; the tester does not edit configuration. Never fall back to production. |
| Local execution unsupported | Use an eligible local desktop environment. Do not upload the full profile to make web-only chat work. |

Retry only the specific failed step after new evidence. No automatic developer-agent loops,
full-source audits or unbounded reinstalls. Ordinary conversation does not rerun setup.

### Update, repair, rollback and uninstall

Updates are a separate maintenance action. Obtain one newer verified release, run its
`install --package .`, then `register-plugin` and the relevant checks. Identical intact content
returns `already_installed`; it does not create another owner slot. Repair uses
`repair --package .` and keeps account data separate. The supported data schema is checked;
this preview does not perform a private-data migration or promise arbitrary downgrades.
Downgrade is rejected. Activation follows package validation; a recorded previous release
pointer is recovery evidence, not a user-facing universal rollback command.

If future migration requires backup, place it in a protected nonsynced data location with
the same privacy boundary, not Git or the install package. Restore only a compatible format
through a documented recovery procedure. Never reset a profile to make an update pass.

Uninstall has separate effects: remove AI-SlowMatch through the supported desktop plugin
removal flow (or `codex plugin remove slowmatch@slowmatch-local --json` when available), and
run the packaged `SlowMatch-Work.exe uninstall` for the local runtime. Read its result for
deactivation/removal and any retained running files. Private account data and unrelated
configuration remain preserved. This does not withdraw Site summaries or erase accounts.
Deleting local private data or withdrawing remote shared objects is a separate explicit
action with its own verified result. No automatic contact, invitations, reservations,
payments, microphone recording or calendar writes are part of installation/maintenance.

### Other official distribution channels and remaining gates

- **Pinned GitHub source, optional administrator/developer route:**
  `codex plugin marketplace add onepunchman26/Anti-Dating-App-Scam --ref v0.8.0 --json`,
  followed by `codex plugin add slowmatch@slowmatch-local --json`. Verify the tag resolves
  to the Release's source commit. This installs plugin sources only; it does not replace
  the prebuilt component install. Ordinary users use the bundled local marketplace above.
- **Install link:** `codex://plugins/install/slowmatch?marketplace=slowmatch-local` opens an
  already-known marketplace. It accepts no version or GitHub URL parameter and does not
  register the repository. Missing marketplace opens Plugins. See the
  [official deep-link reference](https://learn.chatgpt.com/docs/reference/commands).
- **Workspace import:** an authorized workspace admin can import the exact repository,
  leaving Path empty and selecting the release tag or full commit. Access policies remain
  workspace-admin decisions; import is not outside-account distribution.
  [Official GitHub workspace import](https://learn.chatgpt.com/docs/enterprise/plugin-management).
- **Public directory:** local programs require desktop execution. Public local-MCP
  submissions require approved organizations; skills-only desktop execution has its own
  declared flag and submission path. This package uses that flag but has not gained a
  catalog listing. [Desktop submission rules](https://developers.openai.com/plugins/deploy/desktop-only).
- **Package differences:** the ordinary public ZIP path excludes `.app.json`/`apps`; remote
  MCP uses the platform's “With MCP” submission. Do not upload this manual-distribution
  package unchanged and claim eligibility. [Submission errors](https://developers.openai.com/plugins/deploy/submission-errors).

The service maintainer deploys once from `apps/matching_site/` using its
[existing maintenance guide](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/apps/matching_site/README.md); original repository source
flows one way into the hosted mirror. Ordinary users do not provision Sites/databases/domains.
Maintainers control authorized test membership, supported service/client versions and
schema-compatible recovery. Keep credentials out of repositories, releases and diagnostics.

Installation scripts report `model_calls:0` for their own deterministic work; that is not
a zero-token claim for ChatGPT guidance. Use the
[validation/cost record](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/docs/DISTRIBUTION_VALIDATION.md) and its sanitized measurements for
elapsed time, tool calls and text volume. Text length is not token count. Daily work uses
`profile-index`, topic reads, compact/selected schemas and incremental changes; server
prefiltering limits candidate scope. Long private explanations are on demand, and historical
reports are not silently reused after corrections, revocations or relationship events.

## 中文版

AI-SlowMatch 慢慢相识继续从原仓库
[onepunchman26/Anti-Dating-App-Scam](https://github.com/onepunchman26/Anti-Dating-App-Scam)
发布。[v0.8.0](https://github.com/onepunchman26/Anti-Dating-App-Scam/releases/tag/v0.8.0)
是 Windows x64 受控预览，不是稳定版、公共目录上架或独立账号访问证明。说明可用性前核对真实
Release／产物和[验证记录](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/docs/DISTRIBUTION_VALIDATION.md)。本迁移没有替项目决定新的整体开源许可；
保留的第三方许可适用于相应组件，见[署名](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/docs/39_open_source_credits.md)。

### 命令：普通用户安装

从[短安装页](../INSTALL_WITH_CHATGPT.md)进入，下载 Release 指定的 Windows 包和完整性资料，
核对后完整解压。不运行近似名称仓库中的程序。在解压后的包目录执行：

```powershell
.\SlowMatch-Work.exe install --package .
.\SlowMatch-Work.exe register-plugin
.\SlowMatch-Work.exe doctor
```

Release 提供 `work-release.json` 的预期 SHA-256 时，把真实值传给
`install --expected-manifest-sha256 <value>`，不自行编造。安装程序在激活前核对允许清单中的
组件与运行环境；保留 EXE 旁的 `_internal` 和其他列出文件。组件进入
`%LOCALAPPDATA%/AI-SlowMatch/portable/releases/`，私人资料另放
`%LOCALAPPDATA%/AI-SlowMatch/accounts/<opaque-slot>/work`。旧开发 `work` 库不自动迁移。
私人数据不进入源码、OneDrive 或插件缓存。

便携包自带 Python/Pydantic 运行组件。本次无法核清现有 Vosk 原生 wheel 随附材料的署名，因此
主动排除 Vosk 和语音模型。仍可选择导入私人文本／WAV、使用本人提供或纠正的转写；便携预览不提供
自动转写。源码项目的可选 Vosk 路径独立保留，设置不自动下载模型。

`register-plugin` 使用已安装发布目录的本机 marketplace，调用受支持的
`codex plugin marketplace add <installed-release> --json`，再执行
`codex plugin add slowmatch@slowmatch-local --json`，保留其他设置。主流程不克隆 Git 或编译。
目前自动登记要求桌面环境可调用受支持的 `codex` 安装器；缺失会返回
`supported_plugin_installer_unavailable`。仅装 EXE 不会增加该平台能力。不能以安装随意的开发工具、
整体覆盖 `config.toml` 或放宽权限解决。

插件清单声明官方设置入口 `extensions.com.openai.onboardingSkill: "./skills/setup/SKILL.md"`。
客户端提供设置时选择运行；字段存在不证明客户端实际调用过。
[OpenAI 插件打包文档](https://developers.openai.com/plugins/build/plugins)说明该字段和本机目录命令。

### 账号连接与首次使用

连接统一维护的[服务](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)。本人完成桌面登录、
连接和本机访问提示；不索要密码、不借维护者凭据。随包 `.app.json` 指向已有 Site app 登记，
此标识不授予外部账号访问权。每个账号的安装、连接、资格都须分别核对。

试点可由维护者一次配置默认受控测试范围，让平台已经允许访问的账号进入同一范围，免去逐测试者
补运行配置；这不授予平台访问权。按账号限期登记属于可选高级覆盖。测试者不编辑服务配置、不提供
维护者凭据。以真实 `data_scope` 回复为准；无登记／过期不回退正式范围。

设置 Skill 通过当前用户的认证连接调用 `slowmatch_channel_check`，参数为
`{"write":false,"client_protocol":"1.0"}`。要求 `authenticated:true`、服务为 `AI-SlowMatch`、
协议受支持、`data_scope.access:"enabled"`。返回的 `account_fingerprint` 和 `data_scope.id`
只用于绑定本人选择的本机槽位；指纹不进入公开诊断。

```text
SlowMatch-Work.exe slot-create --account-key <current-fingerprint> --scope <current-scope> --confirmed
SlowMatch-Work.exe doctor --slot <returned-slot> --account-key <current-fingerprint> --scope <current-scope>
```

占位内容必须来自实际当前回复和本人选择，不是助手可编造的账号 ID。组件还绑定系统用户和固定服务源。
指纹只是归属声明，不是登录或安全令牌。新会话或切换账号后，本机访问前重新核对健康工具。
同一 Windows 用户的分槽防误混，不抵御该系统用户的恶意读取；独立账号验收使用不同设备／系统用户
及独立登录客户端。

日常操作使用已安装插件 `scripts/work.ps1`，明确传 `--slot`、`--account-key`、`--scope`，
再传操作与 JSON。它不默默回退到开发源码；首参数 `--developer-source` 只供明确要求的开发流程，
不能绕过安装或账号隔离。私密 JSON 走标准输入或本人授权的本机文件，不拼入命令文本。

使用 `--input-json -` 时，启动器必须收到**进程标准输入**。PowerShell 对象管道直接传入 `.ps1`
不会自动转交其内部原生程序。应通过已获准的 PowerShell 程序，以 `-NoProfile -File` 启动脚本，
把 JSON 写入该进程的标准输入并关闭输入；也可使用下方 EXE 命令，或通过 `--input-json` 指定本人
授权的私密本机文件。不更改执行策略；空输入导致的 `operation_failed` 不需要重装或修源码。
复制诊断时不附上私密 JSON 或账号绑定值。

最小合成本机检查把 `{}` 经标准输入交给
`SlowMatch-Work.exe run --slot <slot> --account-key <current-fingerprint> --scope <current-scope> local-probe --input-json -`，
插件启动器也支持此操作。它在独立探针目录写／读／删除合成标记，不接触私人档案。返回
`local_read_write:passed_synthetic_only`、`native_caller:not_independently_verified`、
`remote_authentication:not_checked`；谁实际调用须用真实观察证明。

### 每层检查证明什么

| 层次 | 证据及限制 |
|---|---|
| 程序 | `doctor` 验证清单、运行组件及提供时的本机槽位绑定。`native_chatgpt`、`remote_authenticated_identity`、`two_independent_accounts` 仍为 `not_checked`；程序不调用模型。 |
| 桌面 | 在 ChatGPT 中真实调用已安装设置／日常 Skill、最小合成本机探针和认证健康工具。读源码、终端执行、打开网站是不同证据。缺真实工具／权限记 `BLOCKED`，不是通过。 |
| 产品 | 两个独立获准账号按 [CONTROLLED_TEST.md](../CONTROLLED_TEST.md)，进入同一服务端强制测试范围。mock、同账号多标签或伪造认证头不算。 |

人类摘要用 `PASS`、`FAIL`、`BLOCKED`、`NOT_CHECKED`，同时保留程序准确机器状态。安装检查
不发布个人资料、不联系别人、不创建计划；合成发布属于单独获准的受控测试。没有实际证据时，本机设置
探针和独立账号流程仍待验。终端登记成功不等于新 ChatGPT 会话验证成功。

### 可复制的简短求助结果

只分享版本／渠道、各检查状态、稳定错误码及下一步；排除完整本机路径、指纹、槽位 ID、原始工具回复、
凭据和私人内容。例如：`0.8.0 controlled-preview; package=PASS; native=NOT_CHECKED;
remote=BLOCKED; code=connection_unavailable`。不附档案、转写或数据库。

| 结果 | 对应下一步 |
|---|---|
| 发布／页面不存在 | 等待指定预览发布，不构建源码或改用变化分支。 |
| `release_checksum_mismatch`／完整性错误 | 停用该包，从同一可信发布重新获取并核对公布的完整性资料。 |
| `repair_required` | 用已核实发布运行 `repair --package .`，仅重查失败项一次。 |
| `supported_plugin_installer_unavailable` | 当前缺平台安装器，准确说明前提并使用合资格桌面；EXE 不会创造此权限。 |
| 插件不可用／连接拒绝 | 核对本人实际插件／工作区访问权，维护者私有登记不可转借。 |
| `owner_binding_mismatch` | 读档案前停止，核实当前登录／范围并明确选择其本人槽位，不改归属元数据。 |
| 范围过期／未配置 | 维护者检查一次配置的共享测试范围或可选成员覆盖；测试者不改配置，不回退正式范围。 |
| 不支持本机执行 | 使用合资格的本机桌面，不为让网页能用而上传完整档案。 |

只有新证据时才重试已定位步骤。不自动进入开发 agent 循环、全库审查或无限重装。日常聊天不重跑设置。

### 更新、修复、回退和卸载

更新是独立维护动作：获取一个新的已核实发布，运行其 `install --package .`，再
`register-plugin` 和相关检查。完整的相同内容返回 `already_installed`，不新建另一槽位。
修复使用 `repair --package .`，账号资料独立保留。程序检查支持的数据格式；本预览不迁移私人数据，
不承诺任意降级，降级被拒绝。包验证后才激活；已有 previous 指针是恢复证据，不是面向用户的通用回退命令。

未来需要迁移备份时放在相同隐私边界的受保护非同步数据位置，不放 Git 或安装包。仅按明确恢复流程
恢复兼容格式，不能为通过更新而重置档案。

卸载分两步：用桌面支持的插件移除流程卸载 AI-SlowMatch（有 CLI 时可
`codex plugin remove slowmatch@slowmatch-local --json`），再运行包内 `SlowMatch-Work.exe uninstall`。
读取实际返回的停用／移除结果及仍被占用保留的文件。私人账号资料与无关配置默认保留；这不撤回 Sites
摘要或删除账号。删除私人本机资料、撤回远程共享对象是独立明确操作，各自验证结果。安装／维护不会
自动联系、邀请、预订、付款、录音或写日历。

### 其他官方分发通道与尚未通过的条件

- **固定 GitHub 源码，可选管理员／开发路线：**
  `codex plugin marketplace add onepunchman26/Anti-Dating-App-Scam --ref v0.8.0 --json`，
  再 `codex plugin add slowmatch@slowmatch-local --json`。核对标签对应 Release 的源码提交。
  这只装插件源文件，不代替预编译组件；普通用户走上面的随包本机目录。
- **安装链接：** `codex://plugins/install/slowmatch?marketplace=slowmatch-local` 仅打开已知目录；
  不支持版本或 GitHub URL 参数，不登记仓库；目录缺失时转到 Plugins。
  见[官方深链接说明](https://learn.chatgpt.com/docs/reference/commands)。
- **工作区导入：** 获准管理员可导入准确仓库，Path 留空并选择发布标签或完整提交。访问策略由
  工作区管理员决定，导入不等于工作区外分发。
  [官方 GitHub 工作区导入](https://learn.chatgpt.com/docs/enterprise/plugin-management)。
- **公共目录：** 调用本机程序需要桌面执行；公共本地 MCP 提交限获准组织。仅 Skill 的桌面需求
  有独立字段与提交流程。本包声明了字段，不代表已上架。
  [桌面插件提交规则](https://developers.openai.com/plugins/deploy/desktop-only)。
- **包形式有别：** 普通公共 ZIP 排除 `.app.json`／`apps`；远程 MCP 走平台 “With MCP” 提交。
  不能把当前手动分发包原样上传就声称具备资格。
  [提交错误说明](https://developers.openai.com/plugins/deploy/submission-errors)。

维护者从 `apps/matching_site/` 按[现有维护说明](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/apps/matching_site/README.md)统一部署一次，
原仓库单向同步到托管镜像；普通用户不部署 Sites、数据库或域名。维护者管理获准测试成员、服务／客户端
兼容版本和数据格式兼容恢复。凭据不进仓库、发布包和诊断。

安装脚本的 `model_calls:0` 仅描述自身确定性工作，不代表 ChatGPT 引导零 token。耗时、工具次数、
文本量见[验证／成本记录](https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/docs/DISTRIBUTION_VALIDATION.md)及脱敏测量；文本长度不等于 token 数。
日常用 `profile-index`、主题读取、精简／单项结构及增量变更；服务器先筛选少量候选。详细私人解释
按需生成，纠正、撤回或关系事件后不默默复用旧报告为当前结论。
