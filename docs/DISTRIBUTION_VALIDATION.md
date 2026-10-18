# Distribution validation / 分发验收

## English

This record covers the owner-endorsed distribution supplement to the complete migration
requirements. The original repository remains authoritative. Release 0.8.0 is a **controlled
Windows x64 prerelease**, not a stable release or public plugin-directory listing.

The starting audit found no GitHub Releases, an outdated default branch, a source-dependent
launcher and no independent-account distribution proof. Existing Python data/storage,
Skills and Worker/D1 matching/planning were reused. The new portable component replaces
the source runtime requirement; it does not replace ChatGPT or deploy a server per user.

| Item | Evidence state |
|---|---|
| Versioned runtime, install/repair/uninstall | PASS: final clean-source artifact completed 29 actual EXE calls on Windows, including observed mid-copy interruption/retry, repair and retained private synthetic data; Python/Git/Node absent from child PATH. |
| Short install entry, setup Skill and deterministic download | Prepared; published-download proof pending. |
| Official plugin registration | PASS: official installer migrated the owned 0.7 source marketplace to portable 0.8.0. All 14 installed plugin files match the final package; other 20 plugin versions/enabled states unchanged. Fresh ChatGPT loading remains separate. |
| Server-controlled synthetic scope | 25 local Node/D1 tests pass, including separation from production and old-query compatibility. |
| Current hosted service | 0.8.0 private Site version 6 deployed successfully; environment revision 1. Real signed-in browser check confirmed protocol 1.0, controlled-test access enabled, database read passed, empty dating summary and plans. |
| Current ChatGPT native remote invocation | BLOCKED / not verified. Browser access cannot certify this channel. |
| Fresh ChatGPT setup conversation | NOT_CHECKED; no new model/test session created. |
| Independent account B from the same entry | BLOCKED: no second independent account available. No substitute or impersonation. |
| Actual upgrade/migration failure | NOT_CHECKED: no released compatible upgrade object exists. Unit tests cover failure rollback; do not equate them. |

The first actual candidate package failed installation when Windows AppData redirection
lengthened its storage paths beyond the ordinary path limit.
Its packaging audit also found editable-development metadata; it is retained privately and
must not be uploaded. A successful build/runtime probe did not count as install acceptance.

The original registration attempt was refused because the old local marketplace pointed at source.
The installer now migrates only the verified owned marketplace through official commands;
the successful retry preserves unrelated plugins. Windows PowerShell 5.1 was blocked before
script load by this computer's execution policy. No policy weakening or bypass was attempted.
A separate optional malformed-launcher probe was rejected by automatic approval with only
“blocked by policy”; it did not execute and is not counted as a pass.

### Evidence and cost boundaries

The deterministic CLI never calls a model. Profile index/selected topic/schema reads and
incremental update replies reduce unnecessary context transmission. Saved assessments are
historical records: no automatic cache claims that an old result remains valid after a
profile correction, relationship event, shared withdrawal or version change. Recheck current
inputs before any new interpretation. Private results stay in the owner's local boundary.

Measure actual elapsed time, subprocess/tool invocations, UTF-8 bytes and Unicode characters;
these are **not tokens**. ChatGPT setup guidance and explanation generation can consume usage.
No subscription percentage or invented saving rate is used. A private explanation serialization
or save/read measurement does not measure model generation. No new analysis session was started
solely for this benchmark. [Machine-readable costs](evidence/2026-10-18-distribution-costs.json)
will contain only redacted counts/statuses, never claim text, full paths, account bindings or credentials.

### Remaining owner/environment actions

After the available technical work is verified, use an eligible desktop to approve its own
necessary local/plugin prompts and verify one actual native authenticated call. When an
independent test account/device is available, explicitly grant that account Site access and
follow [the same controlled test guide](../CONTROLLED_TEST.md). Account B must install from
the published entry without code edits or developer configuration. Public-directory approval
and any project-wide license choice remain separate decisions; no password is requested.

## 中文版

本记录对应本人批准的完整迁移要求及其分发补充。原仓库继续作为唯一源码权威。
0.8.0 是 **Windows x64 受控预发布**，不是稳定版，也未上架公共插件目录。

起始审计发现 GitHub 没有 Release、默认分支过旧、启动器依赖开发源码，而且没有独立账号分发证明。
复用原 Python 数据／存储、Skills 和 Worker／D1 匹配／规划；新增便携组件消除使用者源码运行依赖，
不替代 ChatGPT，也不要求每人部署服务器。

| 项目 | 证据状态 |
|---|---|
| 版本化运行组件、安装／修复／卸载 | 通过：最终干净源码产物在 Windows 完成 29 次真实 EXE 调用，含实际复制中断后重试、修复及合成私人数据保留；子进程 PATH 无 Python／Git／Node。 |
| 短安装入口、setup Skill 与确定性下载 | 已准备；发布后下载验收待完成。 |
| 官方插件注册 | 通过：官方安装器把本项目旧 0.7 源码目录迁移到便携 0.8.0；安装的 14 个插件文件匹配最终包，其余 20 个插件版本／启用状态不变。新 ChatGPT 加载另验。 |
| 服务端合成测试范围 | 25 项本地 Node／D1 测试通过，含正式隔离及旧查询兼容。 |
| 当前托管服务 | 0.8.0 私有 Site 第 6 版部署成功，环境版本 1；真实登录浏览器确认协议 1.0、受控测试可用、数据库读取通过、恋爱摘要与计划为空。 |
| 当前 ChatGPT 原生远程调用 | 受阻／未验证；浏览器访问不能证明该通道。 |
| 新 ChatGPT 设置会话 | 未检查；没有创建新模型／测试会话。 |
| B 从同一入口独立完成 | 受阻：尚无第二独立账号；没有替代或冒充。 |
| 真实升级／迁移失败 | 未检查：尚无已发布的兼容升级对象；单元测试覆盖失败回退，不等同实测升级。 |

首个真实候选包因 Windows AppData 重定向使路径超出普通长度限制而安装失败；产物审计也发现开发环境的可编辑安装元数据。
失败产物仅在本机保留，不能上传。构建／程序探针成功没有被当作安装验收通过。

原生注册首次因旧目录仍指向源码而被拒。安装程序现仅通过官方命令迁移核验属于本项目的目录，
重试成功且其他插件保留。系统 PowerShell 5.1 在加载脚本前被本机执行策略阻止，未放宽策略或绕过。
另一项可选的临时启动器异常检查被自动审批拒绝，仅返回 “blocked by policy”；该操作未执行，不计通过。

### 证据与用量边界

确定性 CLI 不调用模型。档案索引、按主题／结构读取及增量更新响应减少不必要的上下文传输。
已存分析是历史记录；不自动声称它在档案纠正、关系事件、共享撤回或版本变化后仍有效。
新解释须重新核对当前输入，私人结果保留在本人本机边界。

测量实际耗时、子进程／工具调用、UTF-8 字节及 Unicode 字符，**不把它们当 token**。
ChatGPT 设置引导和解释生成仍可能消耗用量；不使用订阅百分比或编造节省比例。
私人解释的序列化／保存读取测量不代表模型生成用量，也不为本基准另开分析会话。
[机器可读用量](evidence/2026-10-18-distribution-costs.json)仅记录脱敏计数／状态，不含正文、
完整路径、账号绑定值或凭据。

### 余下本人／环境操作

可执行技术工作验证后，在合适桌面完成其本身要求的本机／插件确认，并验证一次本人认证的原生调用。
独立测试账号和设备可用后，明确授予该账号 Site 访问权，再按[同一受控测试指引](../CONTROLLED_TEST.md)
完成；B 必须从发布入口安装，不能改代码或由开发者补客户端配置。公共目录资格与全项目许可选择
仍是独立决定；不索要密码。
