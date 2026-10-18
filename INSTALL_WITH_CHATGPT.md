# Install AI-SlowMatch / 安装慢慢相识

## English

**Install an existing product; do not rebuild it.** The exact project is
[onepunchman26/Anti-Dating-App-Scam](https://github.com/onepunchman26/Anti-Dating-App-Scam).
Give ChatGPT this sentence: “Install AI-SlowMatch from this project's
INSTALL_WITH_CHATGPT.md, using its pinned Windows preview, and report each setup check honestly.”

The intended release is [v0.8.0 controlled preview](https://github.com/onepunchman26/Anti-Dating-App-Scam/releases/tag/v0.8.0),
**a prerelease, not a stable or public-catalog release**. If that page or its Windows assets
are unavailable, stop at `BLOCKED: release unavailable`; do not substitute a branch ZIP or
a similarly named project. The Release records the source commit, asset names and checksums.

1. Use the Windows x64 ChatGPT desktop environment with permitted local execution and
   plugin installation. Web-only chat cannot manage this computer's files. Other systems
   and independent-account installation are not certified by this preview.
2. Download the prebuilt Windows package and checksum from that exact Release. Verify the
   origin, version and checksum, then extract into a local, nonsynced staging folder.
   A checksum checks integrity; it does not replace trusting the publisher. Keep the entire
   package together. No Git, Python, Node, Docker or compilation should be needed.
3. From the extracted package folder, run `./SlowMatch-Work.exe install --package .`,
   then `./SlowMatch-Work.exe register-plugin`, then `./SlowMatch-Work.exe doctor`.
   Details and checksum pinning are in [distribution help](docs/DISTRIBUTION_HELP.md).
   Do not overwrite ChatGPT settings, bypass system protections or reconstruct source code.
   The component installs outside the plugin cache; private account slots are separate.
4. Complete the desktop's own install/local-access confirmations and your own sign-in.
   Run the bundled **AI-SlowMatch setup** Skill. It connects to the one maintained
   [matching service](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site), checks the
   current authenticated account and scope, and initializes only your selected local slot.
   A visible website or installed owner-private app mapping does not prove your account can
   call it. If access is unavailable, record the blocked step; never borrow another login.
5. Distinguish the results: component/connection check; actual loaded Skill plus synthetic
   local write/read and authenticated remote call; independent A/B flow. Each must say
   `PASS`, `FAIL`, `BLOCKED` or `NOT_CHECKED`. A command-line pass cannot certify desktop
   invocation. Setup never publishes a profile or contacts another person.

After necessary checks pass, end setup and begin ordinary conversation, for example
“Help me understand what matters to me in a long-term relationship.” Save only what you
approve; sharing a separate summary requires a separate review. Missing remote access does
not prevent conversation, but new bound local persistence stays blocked until account binding
can be verified. Never load an old user's slot to work around this.

The assistant should read only this guide, short program results and a relevant help section
if something fails. No full-repository audit, development agents, business-code edits or
repeated rebuilds. Retry a diagnosed step only with new evidence. Installation scripts make
no model requests; ChatGPT guidance and real invocation checks can consume usage. For updates,
uninstall, account changes and remaining platform gates, use [distribution help](docs/DISTRIBUTION_HELP.md).

## 中文版

**这是安装现成产品，不是重新开发。** 正确项目是
[onepunchman26/Anti-Dating-App-Scam](https://github.com/onepunchman26/Anti-Dating-App-Scam)。
把这一句话交给 ChatGPT：“请按这个项目的 INSTALL_WITH_CHATGPT.md 安装 AI-SlowMatch
慢慢相识，使用固定的 Windows 预览发布包，并如实报告各层设置检查。”

目标发布为 [v0.8.0 受控预览](https://github.com/onepunchman26/Anti-Dating-App-Scam/releases/tag/v0.8.0)，
**这是预发布，不是稳定版或公共插件目录上架版**。若该页面或 Windows 产物不可取得，
报告 `BLOCKED: release unavailable`；不改用分支源码 ZIP 或同名项目。Release 记录源码提交、
产物名称和校验值。

1. 使用允许本机执行和插件安装的 Windows x64 ChatGPT 桌面环境。纯网页聊天不能管理本机文件。
   本预览尚不证明其他系统或独立账号安装已获验证。
2. 从该 Release 下载预编译 Windows 包和校验文件，核对来源、版本和校验值，再解压到本机非同步
   临时目录。校验值证明完整性，不能代替对发布者的信任。保留完整目录；不应要求安装 Git、Python、
   Node、Docker 或编译。
3. 在解压包目录运行 `./SlowMatch-Work.exe install --package .`，再运行
   `./SlowMatch-Work.exe register-plugin`、`./SlowMatch-Work.exe doctor`。
   详情与固定校验值见[分发帮助](docs/DISTRIBUTION_HELP.md)。不覆盖 ChatGPT 设置、不绕过系统保护、不重建源码。
   组件安装在插件缓存之外，私人账号槽位另存。
4. 完成桌面软件本身要求的安装／本机访问确认及本人登录，运行随包的 **AI-SlowMatch 设置** Skill。
   它连接统一维护的[匹配服务](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)，核对当前
   已认证账号和范围，只初始化本人选择的本机槽位。网站能打开或装有维护者私有连接映射，不证明
   本人账号可调用；无权限就记录受阻项，不借用他人登录。
5. 分别报告：程序／连接检查；实际加载 Skill、合成本机写读和本人认证远程调用；独立 A/B 流程。
   每项使用 `PASS`、`FAIL`、`BLOCKED` 或 `NOT_CHECKED`。终端通过不证明桌面调用通过。
   初始化不发布档案、不联系别人。

必要检查完成就结束设置，开始日常聊天，例如“帮我理解长期关系里真正看重什么”。只保存本人批准的
内容；共享摘要另行审阅。远程受阻时仍可普通聊天，但在身份绑定可核实前，新账号槽位保存仍受阻，
不能加载旧用户槽位来绕过。

安装助手默认只读本页、简短程序结果和必要故障段落，不全库审计、不启开发 agent、不改业务代码、
不反复重建；只有新证据时才重试已定位步骤。固定安装程序不请求模型；ChatGPT 引导和真实调用检查
仍可能消耗额度。更新、卸载、切换账号与未通过的平台条件见[分发帮助](docs/DISTRIBUTION_HELP.md)。
