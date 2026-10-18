# AI-SlowMatch Sites service / AI-SlowMatch Sites 服务

## English

This directory is the authoritative website/MCP source inside the original Python project.
It uses the supported Sites Vinext/Cloudflare Workers starter and D1. It never hosts the
private Python profile store, AI inference or private assessments. Native Sites dispatch
provides account identity; local preview identity is simulated and is not a real-account test.

The private pilot is https://slowmatch-private-pilot.fizzydeer7.chatgpt.site . Current acceptance
and blockers are recorded in the repository's CURRENT_STATUS.md. Deployment, native tool
connection and successful authenticated operations are separate claims.

The Python-generated contract in `lib/shareable-profile.schema.json` is copied from
`src/anti_dating_scam/schemas/shareable_profile.schema.json`; keep them identical. Public fields
are alias, adult age band, coarse city/accepted regions, relationship goal/accepted goals and
age bands, controlled vocabulary values/life directions/communication/interests/preferences,
summary identity/version, participant audience and discovery preference. No biography,
source quotations, precise coordinates, contacts, raw chats, private profile or reports.

Server tools read/publish the current account's summary, pause/resume discovery, find at most
12 reciprocal candidates, delete the summary, and check synthetic persistence. Publication
checks exact content digest and expected server version. The digest is not proof of honesty
or a cryptographic human signature. Candidates must themselves participate; queries are
limited to 12/hour/account and the pilot scans at most 100 active rows. No pagination or
arbitrary identity lookup/export is provided. Preferences are soft; age/city/goal are hard.

Deletion removes content but retains an account/version tombstone against stale replay.
No private analysis endpoint exists. Current responses use no-store. Platform backups and
copies saved by other participants cannot be recalled. Local profile history is separate.

Development: `node scripts/run-framework.mjs dev --hostname 127.0.0.1`; validate with
`node --test tests/matching.test.mjs`, `node node_modules/typescript/bin/tsc --noEmit` and the
Sites build helper. Generate migrations with `node node_modules/drizzle-kit/bin.cjs generate`.
Never modify an already deployed migration. Apply local D1 migrations through Wrangler;
Sites applies production migrations during publication.

Publishing: the root `scripts/sites_source_snapshot.py` creates an allowlisted one-way source
mirror under LocalAppData, outside Git/OneDrive private data. The supported Sites source
workflow owns only that mirror's separate hosting Git repository; it never changes the
original repository remote. `source-map.json` records file hashes and authority. Build the
same source before copying the deployment output. Never edit the mirror independently.
On this Windows host npm's JS entrypoint was needed because the helper's npm shim failed;
packaging required Git Bash on PATH, forward-slash absolute paths and TAR_OPTIONS=--force-local.
Credentials go to the supported helper through hidden stdin, never files or arguments.

Thanks to the Sites bundle 1.0.2-remix-a.1 and its Vinext starter. The actual copied MIT
build integration and CSS notices are retained under `build/` and `vendor/`; the root credits
register records exact reuse. These are bundled build sources, unlike design-only references.

## 中文版

本目录是原 Python 项目内的网站／MCP 权威源码，使用受支持的 Sites Vinext／Cloudflare
Workers 模板及 D1。不会托管私人 Python 档案、AI 推理或私人报告。身份由原生 Sites
入口验证；本地预览身份是模拟的，不能算真实账户验收。

私人试运行地址为 https://slowmatch-private-pilot.fizzydeer7.chatgpt.site 。验收与受阻项见
仓库 CURRENT_STATUS.md。部署成功、原生工具连接、真实认证操作成功是三种不同状态。

`lib/shareable-profile.schema.json` 来自 Python 的
`src/anti_dating_scam/schemas/shareable_profile.schema.json`，必须保持一致。共享字段仅为
化名、成年年龄段、粗略城市／接受地区、关系目标／接受目标及年龄段、受控选项的价值观／
人生方向／沟通／兴趣／偏好、摘要标识／版本、参与者范围及匹配意愿。不接受个人经历正文、
来源引文、精确坐标、联系方式、原始聊天、完整私人档案或私人报告。

服务工具读取／发布当前账号摘要、暂停／恢复匹配、查询最多十二位双向符合条件的候选、
删除摘要，以及验证合成持久化。发布核对具体内容摘要值与预期服务版本；摘要值不是诚实
证明，也不是本人加密签名。查询者必须参与匹配，每账号每小时最多十二次，试运行最多
扫描一百份活跃记录；没有分页、按任意身份查询或批量导出接口。偏好是软条件，年龄段／
城市／关系目标是硬条件。

删除会移除正文，只保留防止旧请求重放的账号／版本记录。没有上传私人分析的接口，当前
返回值不缓存。平台备份与其他参与者已保存的副本无法收回；本机档案历史独立管理。

开发使用 `node scripts/run-framework.mjs dev --hostname 127.0.0.1`。验证使用
`node --test tests/matching.test.mjs`、`node node_modules/typescript/bin/tsc --noEmit`
和 Sites 构建工具。用 `node node_modules/drizzle-kit/bin.cjs generate` 生成迁移，已部署
迁移不能改写。本地 D1 用 Wrangler 应用迁移；生产迁移由 Sites 发布流程应用。

发布时，根目录 `scripts/sites_source_snapshot.py` 按允许列表在 LocalAppData 创建单向
源码镜像，独立于 Git／OneDrive 私人资料。受支持的 Sites 源码工作流只管理镜像自己的
托管 Git 仓库，不改变原项目远端。`source-map.json` 记录文件哈希和权威来源；同一源码
构建后再复制产物，不能独立编辑镜像。本机 Windows 的 npm 命令包装器失败，改用 npm
自身 JS 入口；打包需将 Git Bash 加入当前进程 PATH、使用正斜杠绝对路径并设置
TAR_OPTIONS=--force-local。凭据只通过工具隐藏标准输入传递，不落盘或放进命令参数。

感谢 Sites 1.0.2-remix-a.1 及 Vinext 模板。实际复制的 MIT 构建整合和 CSS 许可保留在
`build/`、`vendor/`；完整来源与复用范围见根目录致谢登记。这些是实际打包的构建源码，
区别于仅参考设计的项目。
