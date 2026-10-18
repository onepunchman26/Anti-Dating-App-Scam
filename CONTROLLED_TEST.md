# Independent account test / 独立账号测试

## English

Give an authorized tester this sentence: **“Install and test AI-SlowMatch from
https://github.com/onepunchman26/Anti-Dating-App-Scam using INSTALL_WITH_CHATGPT.md and
CONTROLLED_TEST.md; use my own account and the pinned v0.8.0 preview, and stop at any
unavailable permission instead of editing source.”**

This is an opt-in synthetic product test, not part of routine installation. The current
result remains **NOT EXERCISED with a second independent account**. No password, developer
checkout, Python/Git/Node, maintainer token or client source patch is required by this flow.
The [validation record](docs/DISTRIBUTION_VALIDATION.md) separates prepared steps from proof.

### Before either person starts

- Both testers must be adults and explicitly agree to synthetic testing with separate
  ChatGPT identities. Use separate devices or Windows users/client profiles, without
  borrowing the other person's local slot or sign-in. Two tabs are not two accounts.
- The maintainer grants normal private Site access to exactly the intended participants.
  The shared pilot's default controlled scope is configured once on the server; B does not
  edit a config file or deploy a second service. Never expand the Site to public access
  merely to get this test to work. Public catalog eligibility is a separate platform gate.
- Each person follows the same [short installer guide](INSTALL_WITH_CHATGPT.md) and downloads
  the same published version. Record package integrity, install/doctor results and actual
  installed Skill loading separately from successful authenticated remote invocation.
- Through the native connected tool, each calls
  `slowmatch_channel_check({"write":false,"client_protocol":"1.0"})`. Require their own
  authenticated fingerprint and an enabled `controlled_test` scope. Both scope IDs must
  match. A remembered fingerprint or browser-only success is not native-call proof.
  Keep these identifiers out of publicly copied diagnostics.

### The bounded A/B journey

1. Use the verified fingerprint/scope to initialize and select your own local slot, following
   setup. A scope mismatch stops the call. The package's `tools/controlled-test.ps1`, invoked
   with `-Role A` or `-Role B`, `-Scope <verified test scope>` and
   `-ConfirmedAdultSyntheticTest`, creates fresh-expiry local inputs. It makes no network or
   model request and publishes nothing. Toronto and all preferences are synthetic choices,
   not user defaults. For a repeated test pass the read current `-ExpectedRevision`,
   `-DatingVersion` and `-FriendshipVersion`; never manually edit code to fix a conflict.
2. In your own ChatGPT, read `profile-index`, inspect your synthetic input, then apply the
   approved update and re-read the relevant topics. The private `SYNTHETIC_PRIVATE_A/B`
   markers must stay in their respective local profiles. No real archive import.
3. Independently draft, preview and approve each mode's exact summary. Only then export and
   publish via your authenticated native tool. The fixture file is not an upload approval.
   Query and re-read each published result. Check one positive dating candidate/explanation
   and one friendship candidate/explanation, plus hard-condition and mode mismatch cases.
4. Each person requests a private explanation using only their own profile, the permitted
   peer summary and selected authorized materials. Store locally. Inspect requests, responses,
   page content and public-safe diagnostics for absent private markers; do not upload the
   private report to “check” whether the server rejects it.
5. Explicitly create a pending activity only if both choose to continue. Each shares their
   own reviewed minimal preferences. The joint context is unavailable before both approvals.
   Use two/three actually checked public options and the isolated generator. Each confirms
   the same current option independently; changing preferences/plan invalidates confirmation.
6. Exercise own summary correction, own-mode pause, own private block and plan withdrawal.
   After each, re-query from both accounts. A must never be able to approve/confirm/update
   for B. Optional selected shared feedback stays separate from private reflection; test
   own-feedback withdrawal. Missing feedback is unknown.
7. Stop if authentication, current consent, current version or scope is uncertain. Record
   FAIL/BLOCKED rather than a success banner. Recover with a fresh read, never a blind repeat
   mutation. Explicitly test interruption/retry and expired-login behavior only within this
   authorized synthetic scope. No messages, booking, payments or calendar changes.
8. Cleanup is each person's own authenticated pause/delete/withdraw of identified synthetic
   objects in the same controlled scope. There is no global wipe. Do not remove a real profile,
   another user's material or platform sign-in. Local data deletion is separate from uninstall.

Record PASS/FAIL/BLOCKED/NOT_CHECKED for: B's ordinary final-package installation, new-session
Skill/local tool use, own native remote login, both modes, privacy markers, individual planning
consent, withdrawal, diagnostics and scope-limited cleanup. Include version and short error codes;
exclude profiles, fingerprints, tokens and complete paths. A local simulation is not this acceptance.

## 中文版

给获准测试者这一句话：**“请从 https://github.com/onepunchman26/Anti-Dating-App-Scam 按
INSTALL_WITH_CHATGPT.md 与 CONTROLLED_TEST.md 安装并测试 AI-SlowMatch；使用我的独立账号
和固定 v0.8.0 预览版，缺权限就停在该步骤并记录，不修改源码。”**

这是明确选择加入的合成产品测试，不是普通安装的默认行为。当前**第二独立账号仍尚未实测**。
流程不需要密码、开发仓库、Python／Git／Node、维护者令牌或修改客户端源码。
[验证记录](docs/DISTRIBUTION_VALIDATION.md)区分准备步骤与实际证明。

### 双方开始前

- 两位测试者须为成年人，明确同意合成测试并使用独立 ChatGPT 身份。在不同设备或 Windows
  用户／客户端配置中操作，不借用对方本机槽位或登录。两个标签页不是两个账户。
- 维护者按正常平台流程仅给指定参与者私有站访问权，共同试运行范围只在服务端配置一次；B 不改
  配置、不部署另一个服务。不为通过测试把网站改成公开；公共目录资格是独立平台条件。
- 各自从同一[短安装入口](INSTALL_WITH_CHATGPT.md)下载同一发布版本，分别记录完整性、安装／
  doctor、实际加载 Skill 和本人认证的远程调用，不能混为一项。
- 各自在已连接原生工具调用
  `slowmatch_channel_check({"write":false,"client_protocol":"1.0"})`，要求本人的认证指纹及
  已启用 `controlled_test` 范围，双方范围 ID 一致。旧指纹或浏览器成功不是原生调用证明；
  这些标识不放进公开复制的诊断。

### 有限 A/B 流程

1. 按设置流程，用核实的指纹／范围初始化并选择自己的本机槽位；不匹配就停止。包内
   `tools/controlled-test.ps1` 配合 `-Role A` 或 `-Role B`、`-Scope <已核实测试范围>` 和
   `-ConfirmedAdultSyntheticTest` 生成带新期限的本机输入；它不联网、不调用模型、不发布。
   多伦多及偏好均为合成选择，不是默认画像。重复测试时传入刚读取的 `-ExpectedRevision`、
   `-DatingVersion`、`-FriendshipVersion`，不为解决冲突手改代码。
2. 在自己的 ChatGPT 读取 `profile-index`、审阅合成输入，批准后增量更新并重读相关主题。
   `SYNTHETIC_PRIVATE_A/B` 标记只能留在各自本机，不导入真实旧档案。
3. 两模式各自草拟、预览、批准准确摘要，再导出并通过本人认证原生工具发布，重读发布结果。
   测试输入文件不等于发布授权。恋爱与交友各测一条正向候选／解释，并验证硬条件冲突与模式不符。
4. 各自用本人档案、许可的对方摘要和选定获准材料获得私人解释，留本机。检查请求、响应、页面和
   可公开诊断中无私密标记；不通过上传私人报告来“测试服务端是否拒绝”。
5. 双方愿意继续才明确创建待处理活动，各自分享审阅过的最小偏好。双方批准前共同上下文不可用。
   使用两三个实际核对公开地点及隔离生成器，各自独立确认同版同项；偏好／方案改变使旧确认失效。
6. 测试本人摘要纠正、单模式暂停、本机屏蔽及计划退出，每次双方重查。A 不能替 B 批准、确认或
   修改。可选选定共享反馈与私人复盘分离，并测试仅撤回本人反馈；缺反馈含义未知。
7. 身份、当前同意、版本或范围不确定时停止，记录 FAIL／BLOCKED，不显示成功。先重读再恢复，
   不盲目重放变更。中断重试、过期登录测试仅在已授权合成范围内进行；不发消息、订位、付款或写日历。
8. 清理仅由各人以自己的认证，在同一受控范围暂停／删除／撤回已识别的合成对象，不做全局清空，
   不删除真实档案、他人材料或平台登录。本机数据删除与卸载分开。

逐项记录 PASS／FAIL／BLOCKED／NOT_CHECKED：B 从最终包普通安装、新会话 Skill／本机工具、
本人原生远程登录、两模式、隐私标记、各自规划批准、撤回、诊断和限定清理。附版本及简短错误码，
不附档案、指纹、令牌或完整路径。本地模拟不算这项验收。
