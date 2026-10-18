# Site maintenance / 网站维护

## English

This is the maintainer procedure for the existing 0.8 service. Ordinary users follow
[installation](../INSTALL_WITH_CHATGPT.md); they do not build, provision hosting, configure
the server or obtain maintainer credentials.

### Source and current deployment

- Authority: [onepunchman26/Anti-Dating-App-Scam](https://github.com/onepunchman26/Anti-Dating-App-Scam),
  specifically `apps/matching_site/`. Preserve the original Git remote and unrelated work.
- The Sites hosting repository is a one-way deployment mirror. Run the root
  `scripts/sites_source_snapshot.py` to copy allowlisted source and its matching build into
  `%LOCALAPPDATA%/AI-SlowMatch/site-build/source`. Its `source-map.json` records file hashes
  and authority. Never edit the mirror independently or copy a private data directory into it.
- Keep project ID `appgprj_6ad4306f79e88191bbbd502f495ec501` from
  `apps/matching_site/.openai/hosting.json`. Reuse the
  [existing private pilot](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site);
  its MCP endpoint is the same origin plus `/mcp`. Do not create a replacement Site.
- Saved version **6**, hosting source `93b02ea3f06043485f7320e0ad1f9842aff0a195`,
  deployment `appgdep_6ad45d83f3f48191979dd23de3877cf1`, environment revision **1**:
  deployment succeeded at `2026-10-18T05:47:57.989536+00:00`. A signed-in browser service
  check returned service `0.8.0`, protocol `1.0`, controlled-test access enabled and database
  read passed. This does not establish native MCP/Skill/local-tool execution or account B.
  [Current status](../CURRENT_STATUS.md) and [distribution validation](DISTRIBUTION_VALIDATION.md)
  record later evidence; a subsequent documentation edit is not automatically deployed.

### Check, mirror and publish

1. Inspect branch/status and applicable rules. Use native Sites `get_site` to verify this
   project and its current audience; keep the existing owner-private audience. Open only the
   hosting mirror through the installed Sites `site-workflow.mjs` helper, using a fresh
   `create_source_repository_write_credential` result for this same Site. Keep the complete
   opening result for the packaging step. Do not change the original repository's remote.
2. Change the authoritative source. If dependency inputs changed or dependencies are absent,
   use the installed Sites `install-dependencies.mjs` helper once. From `apps/matching_site/`,
   run the relevant checks below. There is no `npm test` script in this version.

   ```powershell
   node --test tests/*.test.mjs
   node node_modules/typescript/bin/tsc --noEmit
   npm run lint
   ```

   Build this same checkout with `node <installed-sites-plugin-root>/scripts/build-site.mjs`.
   The package's `npm run build` invokes its framework build; the supported Sites helper
   also performs the platform packaging preparation. If PowerShell blocks the npm wrapper,
   invoke the installed npm JavaScript entrypoint with Node instead of changing execution
   policy. Python core changes additionally require the repository's compileall/pytest checks.
3. Inspect the build and schema changes, then run `python scripts/sites_source_snapshot.py`
   from the original repository root. It checks the three Python/Site JSON contracts and
   refreshes only the allowlisted mirror. Rebuild before snapshotting after any source change;
   do not package an old `dist` with newer source.
4. From that mirror, launch
   `node <installed-sites-plugin-root>/scripts/site-workflow.mjs --project-id appgprj_6ad4306f79e88191bbbd502f495ec501`
   with a supported hidden-stdin terminal (`exec_command` with `tty:true`, then `write_stdin`).
   After its ready prompt, send one newline-terminated
   JSON object containing `credential`, the complete previous `source` result, `commands`
   and absolute `archivePath`. Use `commands: []` only when all relevant checks/builds already
   passed with unchanged inputs. Otherwise supply remaining commands as ordered argument arrays.
   Credentials stay in session memory and hidden stdin: never command arguments, files or output.
5. On this Windows host, the source helper needed Git Bash tools first in its process `PATH`
   and `TAR_OPTIONS=--force-local`. Use an absolute archive path with forward slashes. Example
   process-local preparation, after verifying these installed tool locations:

   ```powershell
   $env:PATH = "C:\Program Files\Git\bin;C:\Program Files\Git\usr\bin;" + $env:PATH
   $env:TAR_OPTIONS = '--force-local'
   $siteArchive = (Join-Path $env:LOCALAPPDATA 'AI-SlowMatch/site-build/site-0.8.0.tar.gz').Replace('\','/')
   ```

   Do not persist these settings globally. Keep the archive unchanged until saving succeeds.
   The helper owns mirror commit/push and returns the exact verified `project_id`, `commit_sha`
   and `archive`. Pass those returned values directly to the native save/deploy operation.
6. For confirmed owner-private access use `save_version_and_deploy_private`, or
   `save_site_version` followed by `deploy_private_site_version` when necessary. Preserve
   saved version/deployment IDs and resume an existing operation after an uncertain result.
   Pass the returned opaque saved-version ID, not the displayed number `5`, to deployment.
   Poll `get_deployment_status` only while pending/building/publishing. A terminal success
   confirms deployment; a pushed commit, saved archive or successful local build does not.
   Record sanitized version, commit, environment revision, terminal state and check results.

### One-time controlled-test configuration

The maintainer configures one default scope through native Sites
`update_environment_variables`, preserving all unrelated keys. This is a server configuration
operation, not a browser setting or tool argument. Use the exact structure below, replacing the
expiry placeholder with the authorized future UTC timestamp; do not submit the placeholder:

```json
{
  "project_id": "appgprj_6ad4306f79e88191bbbd502f495ec501",
  "set_values": [{
    "key": "SLOWMATCH_DEFAULT_TEST_SCOPE",
    "value": "{\"scope\":\"pilot-202610\",\"expires_at\":\"<future UTC timestamp>\"}",
    "is_secret": true
  }]
}
```

Omit `remove` to preserve other variables. Keep values in Sites runtime configuration, never
source, `.openai/hosting.json`, client bundles or release packages. Deploy a saved version after
changing configuration to apply its new environment revision. The version-5 default pilot
expires at `2026-11-17T05:30:00Z`; this is a recorded limit, not a perpetual default to copy.
Scope names are 3–40 lowercase letters/digits/hyphens, begin with a letter, and cannot be
`production`. The value has exactly `scope` and `expires_at`.

Every account already authorized by the platform automatically enters the same configured
scope. B needs no per-person code or server configuration. This does not grant private-site
access, send an invitation or broaden the audience. Preserve owner-private access; any later
viewer-access change is a separate explicit action. Until a real second account has normal
platform access, the independent-account test remains blocked.

Optional advanced `SLOWMATCH_TEST_SCOPES` overrides use exactly
`{"version":1,"memberships":{"<caller fingerprint>":{"scope":"pilot-other","expires_at":"<future UTC timestamp>"}}}`.
Use only a fingerprint from that account's actual authenticated health result; do not publish
the mapping or invent identities. The default avoids requiring this per-tester administration.
Once a caller is enrolled, missing or expired configuration blocks access instead of silently
switching to production. Renew the intended scope through the same supported configuration
flow when authorized. Restore its access before an authorized participant cleanup; do not
erase the enrollment ledger to force fallback. Historical production rows remain unchanged.

### Verify connection and compatibility

Through the current account's native connected tool, call `slowmatch_channel_check` with
`{"write":false,"client_protocol":"1.0"}`. The same operation is available to an authenticated
same-origin browser through `POST /api/matching`:

```json
{"name":"slowmatch_channel_check","arguments":{"write":false,"client_protocol":"1.0"}}
```

Require `authenticated:true`, the expected service/protocol version, `database_schema:"passed"`
and `data_scope:{kind:"controlled_test",id:"test:<configured-name>",access:"enabled"}` before
controlled synthetic publication. Check both accounts independently. `write:false` does not
write the channel marker; first access can establish the maintainer-authorized enrollment
record. `write:true` separately tests only a fixed synthetic marker, never a profile.

`account_fingerprint` is a caller-only stable ownership pseudonym, not authentication or a
credential. Use it only for the user's local account binding; omit it, slot IDs, private paths,
raw responses and credentials from public diagnostics. Health reports `client_skill` and
`client_local_tools` as `not_checked`; only actual native invocation can verify those layers.
Browser success cannot resolve an MCP approval rejection. Never forge identity headers or
reuse a maintainer token to simulate account B.

Protocol `1.0` is supported. A declared incompatible `client_protocol` fails before database
operations: the HTTP API returns **426** with `client_upgrade_required`; MCP `tools/call`
returns `isError:true` with that code. Update to a compatible verified client. Omitting the
optional field preserves older-client compatibility; do not strip a declared mismatch to force
a write. `controlled_test_scope_expired` / `controlled_test_scope_not_configured` require a
maintainer configuration check, not a production fallback.

### Migrations and recovery

Generate new migrations with `npm run db:generate`; review SQL and Drizzle metadata together.
Applied SQL, snapshots and journal entries are immutable. Version 0.8 adds
`0005_wandering_zarda.sql`: scope columns/index and an enrollment table, with constant defaults;
it has no user-data backfill, seed, delete or update. Local D1 migrations/tests are separate
from hosted D1. The Sites publication flow applies hosted migrations before the Worker;
a failed Worker deployment may still have applied its migration. Resolve the actual state
through supported platform evidence before retrying or repairing, without dumping user rows.

Prefer a forward fix or a previously verified **scope-aware** saved version. Do not reverse DDL,
drop tables, restore a test database over production, reset Git or copy private backups into
source/packages. The additive schema preserves 0.7 production rows. New test rows use server-only
`active=2`; the old 0.7 `active=1` candidate query excludes them, as verified locally. This limited
rollback safeguard does not make 0.7 scope-aware: downgrading loses current enrollment/protocol
controls and is not the normal recovery procedure. Keep the database schema and protected data
in place; no private-data migration or backup is required for this schema-only update. Any later
explicit private backup belongs in protected nonsynced storage, with a separately verified
restore procedure. Keep [controlled-test evidence](../CONTROLLED_TEST.md) distinct from live
account acceptance and do not publish synthetic profiles as a maintenance check.

## 中文版

这是现有 0.8 服务的维护者操作说明。普通用户按[安装说明](../INSTALL_WITH_CHATGPT.md)操作，
不构建源码、不配置托管或服务器，也不获取维护者凭据。

### 源码与当前部署

- 权威是原仓库 [onepunchman26/Anti-Dating-App-Scam](https://github.com/onepunchman26/Anti-Dating-App-Scam)
  内的 `apps/matching_site/`，保留原 Git 远端和无关工作。
- Sites 托管仓库只是单向部署镜像。根目录 `scripts/sites_source_snapshot.py` 将允许列表源码和
  对应构建复制到 `%LOCALAPPDATA%/AI-SlowMatch/site-build/source`，由 `source-map.json` 记录
  文件哈希和权威。不要独立编辑镜像，也不要向其复制私人数据目录。
- 保留 `apps/matching_site/.openai/hosting.json` 中的项目 ID
  `appgprj_6ad4306f79e88191bbbd502f495ec501`，复用
  [现有私密试运行站](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)，MCP 地址为同源 `/mcp`。
  不另建替代站点。
- 已保存版本 **6**，托管源码提交 `93b02ea3f06043485f7320e0ad1f9842aff0a195`，部署
  `appgdep_6ad45d83f3f48191979dd23de3877cf1`，环境修订 **1**，于
  `2026-10-18T05:47:57.989536+00:00` 部署成功。真实登录浏览器的服务检查返回服务 `0.8.0`、
  协议 `1.0`、受控测试访问有效及数据库读取通过。这不证明原生 MCP／Skill／本机工具执行或账号 B。
  后续证据见[当前状态](../CURRENT_STATUS.md)与[分发验证](DISTRIBUTION_VALIDATION.md)；
  后来的文档编辑不会自动部署。

### 检查、镜像与发布

1. 检查分支、工作区和适用规范。通过原生 Sites `get_site` 核实同一项目与受众，保留现有所有者私有
   访问。使用同站新返回的 `create_source_repository_write_credential` 凭据，通过已安装 Sites 的
   `site-workflow.mjs` 只打开托管镜像，保留完整打开结果供打包使用，不改原仓库远端。
2. 修改权威源码。依赖缺失或其输入变化时，运行一次已安装 Sites 的 `install-dependencies.mjs`。
   在 `apps/matching_site/` 执行相关检查；本版本没有 `npm test` 脚本：

   ```powershell
   node --test tests/*.test.mjs
   node node_modules/typescript/bin/tsc --noEmit
   npm run lint
   ```

   对同一检出目录执行 `node <已安装-sites-插件根目录>/scripts/build-site.mjs`。包内
   `npm run build` 调用框架构建；受支持 Sites helper 还执行平台打包准备。若 PowerShell 阻止 npm
   包装脚本，用 Node 调用已安装 npm 的 JavaScript 入口，不修改执行策略。Python 核心变化另须
   完成仓库规定的 compileall／pytest。
3. 核对构建和结构变更，再从原仓库根目录运行 `python scripts/sites_source_snapshot.py`。
   它核验三份 Python／Site JSON 契约并刷新允许列表镜像。源码变化后先重新构建再生成快照，
   不把旧 `dist` 和新源码一起打包。
4. 在镜像目录启动
   `node <已安装-sites-插件根目录>/scripts/site-workflow.mjs --project-id appgprj_6ad4306f79e88191bbbd502f495ec501`，
   使用受支持的隐藏 stdin 终端（`exec_command` 设置 `tty:true`，再用 `write_stdin`）。
   出现就绪提示后，输入一个以换行结尾的 JSON，包含 `credential`、
   之前完整 `source` 结果、`commands` 和绝对 `archivePath`。仅在相关检查／构建均已通过且输入
   未变时使用 `commands: []`，否则以有序参数数组提供剩余命令。凭据只留会话内存并经隐藏 stdin
   传入，不放命令参数、文件或输出。
5. 此 Windows 主机的源代码 helper 需要在其进程 `PATH` 前加入 Git Bash 工具，并设置
   `TAR_OPTIONS=--force-local`。归档使用正斜杠绝对路径。确认安装位置后可使用以下进程级准备：

   ```powershell
   $env:PATH = "C:\Program Files\Git\bin;C:\Program Files\Git\usr\bin;" + $env:PATH
   $env:TAR_OPTIONS = '--force-local'
   $siteArchive = (Join-Path $env:LOCALAPPDATA 'AI-SlowMatch/site-build/site-0.8.0.tar.gz').Replace('\','/')
   ```

   不持久修改全局配置，保存成功前不改归档。helper 管理镜像提交／推送，返回准确核验过的
   `project_id`、`commit_sha` 和 `archive`，将返回值直接传给原生保存／部署工具。
6. 已确认所有者私有站使用 `save_version_and_deploy_private`，必要时使用 `save_site_version`
   后接 `deploy_private_site_version`。保留保存版本和部署 ID，结果不确定时继续原操作。
   部署传入工具返回的完整保存版本 ID，不传显示编号 `5`。
   仅在 pending／building／publishing 时调用 `get_deployment_status`；成功终态才证明部署。
   已推送提交、已保存归档或本地构建成功均不能替代。记录脱敏版本、提交、环境修订、终态及检查结果。

### 一次配置受控测试范围

维护者通过原生 Sites `update_environment_variables` 配置默认范围，保留所有其他键。这是服务端
运行配置，不是浏览器设置或工具参数。结构如下；将到期占位符替换为授权的未来 UTC 时间，不提交占位符：

```json
{
  "project_id": "appgprj_6ad4306f79e88191bbbd502f495ec501",
  "set_values": [{
    "key": "SLOWMATCH_DEFAULT_TEST_SCOPE",
    "value": "{\"scope\":\"pilot-202610\",\"expires_at\":\"<future UTC timestamp>\"}",
    "is_secret": true
  }]
}
```

省略 `remove` 以保留其他变量。值仅存 Sites 运行配置，不放源码、`.openai/hosting.json`、客户端包
或发布包。修改后部署已保存版本，才能应用新环境修订。版本 5 的默认试运行到期是
`2026-11-17T05:30:00Z`；这是已记录期限，不是永远复制的默认值。范围名为 3–40 个小写字母／数字／
连字符，以字母开头，不能是 `production`。值恰好包含 `scope` 与 `expires_at`。

所有已获平台访问许可的账号会自动进入同一个配置范围，B 不需要逐人改代码或配置服务器。这不会授予
私有站访问、发送邀请或扩大受众。保留所有者私有状态；以后改变访问者权限属于单独明确动作。在真实
第二账号获得正常平台访问之前，独立账号测试仍然受阻。

可选高级覆盖 `SLOWMATCH_TEST_SCOPES` 的准确结构为
`{"version":1,"memberships":{"<caller fingerprint>":{"scope":"pilot-other","expires_at":"<future UTC timestamp>"}}}`。
只使用该账号真实认证健康检查返回的指纹，不发布映射、不虚构身份；默认范围可避免逐人维护。
一旦加入测试范围，配置缺失或过期会阻止访问，不会静默切回正式范围。获授权后通过同一配置流程续期
目标范围；参与者执行已授权清理前先恢复其正常访问，不通过删除加入记录强制回退。历史正式记录保持原样。

### 核验连接与兼容性

通过当前账号原生连接工具调用 `slowmatch_channel_check`，参数为
`{"write":false,"client_protocol":"1.0"}`。已认证同源浏览器也可向 `POST /api/matching` 发送：

```json
{"name":"slowmatch_channel_check","arguments":{"write":false,"client_protocol":"1.0"}}
```

受控合成发布前要求 `authenticated:true`、预期服务／协议版本、`database_schema:"passed"`，以及
`data_scope:{kind:"controlled_test",id:"test:<配置名称>",access:"enabled"}`，分别核验两个账号。
`write:false` 不写通道标记；首次访问可能建立维护者已授权的范围加入记录。`write:true` 单独测试
固定合成标记，不发布档案。

`account_fingerprint` 是只返回本人的稳定所有权代号，不是身份认证或凭据。只用于本人本机账号绑定，
公开诊断去掉指纹、slot ID、私密路径、原始响应和凭据。健康结果的 `client_skill`、`client_local_tools`
为 `not_checked`，只有真实原生调用能核验这些层。浏览器成功不能解除 MCP 审批拒绝；不伪造身份头，
不复用维护者令牌模拟账号 B。

支持协议 `1.0`。声明不兼容 `client_protocol` 会在数据库操作前失败：HTTP API 返回 **426** 和
`client_upgrade_required`；MCP `tools/call` 返回 `isError:true` 及该代码。升级到核验过的兼容客户端。
可选字段省略是为旧客户端兼容，不应删掉已声明的不兼容版本来强行写入。
`controlled_test_scope_expired`／`controlled_test_scope_not_configured` 应由维护者检查配置，
不能回退正式范围。

### 数据库迁移与恢复

使用 `npm run db:generate` 生成新迁移，一起审阅 SQL 和 Drizzle 元数据。已应用 SQL、快照和 journal
记录不可改写。0.8 新增 `0005_wandering_zarda.sql`：范围列／索引和加入记录表，采用常量默认值，
没有用户数据回填、种子、删除或更新。本地 D1 迁移／测试与托管 D1 分开；Sites 发布在上传 Worker 前
应用托管迁移，所以 Worker 部署失败时迁移仍可能已应用。重试或修复前用受支持平台证据核实状态，
不导出用户数据行。

优先向前修复或部署此前已核验且**支持范围隔离**的保存版本。不反向执行 DDL、不删表、不用测试数据库
覆盖正式库、不 reset Git，也不把私人备份复制进源码／包。追加结构保留 0.7 正式记录。新测试记录使用
服务端 `active=2`，旧 0.7 的 `active=1` 候选查询会排除它们，本地已验证。但这项有限回退保护不会让
0.7 获得范围隔离：降级会失去当前加入／协议控制，因此不是常规恢复方案。保留数据库结构和受保护数据；
本次纯结构更新不需要私人数据迁移或备份。日后若明确需要私人备份，应放受保护、不同步的位置，单独
核验恢复流程。区分[受控测试证据](../CONTROLLED_TEST.md)与真实账号验收，不为维护检查自动发布合成档案。
