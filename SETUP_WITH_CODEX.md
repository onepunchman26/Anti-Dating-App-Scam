# Start with Codex / 用 Codex 开始

## English

**Windows x64 preview 0.8.6.** One maintained service, a prebuilt local assistant,
no source checkout, Python, compiler or API key. Existing ChatGPT/Codex users can
skip the download. Otherwise follow the [official desktop setup](https://learn.chatgpt.com/docs/quickstart?setup=app),
sign in, choose a local folder and select **Codex**. Use a small setup folder outside
OneDrive, for example `%LOCALAPPDATA%/AI-SlowMatch/setup`; this is not your private vault.

Copy this request into Codex:

> Read this pinned guide: https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/SETUP_WITH_CODEX.md . Install or repair the released Windows assistant, verify it and open the local page. Reuse my existing ChatGPT authorization when available. Do not clone/rebuild the project, launch development agents, scan my private files, change security settings, buy credits or publish a profile. Let me complete any official sign-in and select/confirm the private folder on the local page. Report installation, AI authorization, actual inference and Site access separately.

### Bounded instructions for Codex

1. Check Windows x64 and local execution. Use the current PowerShell host; do not
   change machine execution policy. Read only this guide and a matching error-help
   section if needed. No full repository exploration or model calls during installation.
2. Download **only** `install_work_preview.ps1` and `SHA256SUMS.txt` from
   `https://github.com/onepunchman26/Anti-Dating-App-Scam/releases/download/v0.8.6/`.
   Save under `%LOCALAPPDATA%/AI-SlowMatch/setup/v0.8.6`, outside source/cloud folders.
   Compare the script's SHA-256 to its exact `install_work_preview.ps1` entry in the
   release checksum file before running. If the release/assets are missing, stop with
   that fact; do not substitute a build or an unpinned `main` script.
3. Run the verified script with `-Launch`. It verifies the pinned archive and manifest,
   installs/reuses the complete package, checks it and opens the private local page.
   `-RegisterPlugin` is optional for users who also want the native plugin route;
   local web chat does not require that plugin registration or remote Site access.
4. The permanent daily entry is `%LOCALAPPDATA%/AI-SlowMatch/portable/Start-SlowMatch.cmd`.
   Open it next time; a current running assistant is reused, not duplicated.
   An older/foreign listener is never killed automatically. If told to close an older
   assistant, identify its executable and close that specific known process only with
   appropriate authority; do not kill every Python process or weaken browser restrictions.
5. On the local page, choose **Connect this local page**. Existing authorization is
   detected; otherwise complete official login. Refresh the model list, select a model
   and explicitly allow included-plan use. Login/model-list success is not inference proof.
6. Choose the default account-specific private folder or expand **Choose another folder**.
   Confirm storage. Never select a source, OneDrive, website or deployment folder; never
   automatically scan/import another vault. Browser-private data stays on this computer;
   explicitly authorized conversation content goes to OpenAI, not the matching Site.
7. Start a conversation. A completed real reply verifies inference. Setup itself does
   not send a personal/test prompt without the user's request. Site discovery requires
   a separately reviewed summary; private AI review uses approved candidate summaries
   and only the user's separately selected private context. No automatic publication.

Report PASS/FAIL/NOT_CHECKED independently for installation, local page, authorization,
storage write/read, completed inference and remote access. Two/three-account acceptance
requires independent accounts. The maintained Site is currently owner-private; installation
does not grant another account access. No independent-account installation is claimed.

## 中文版

**Windows x64 0.8.6 预览版。** 使用统一匹配服务和预先构建的本机助手，不需要源码、Python、
编译器或 API key。已经装有 ChatGPT／Codex 可直接使用；否则按
[官方桌面安装说明](https://learn.chatgpt.com/docs/quickstart?setup=app)下载、登录，选择本地文件夹，
切换到 **Codex**。设置文件夹可选 `%LOCALAPPDATA%/AI-SlowMatch/setup`，不要放 OneDrive；
它不是私人资料库，资料库在稍后的本机页面选择。

复制给 Codex：

> 请读取固定版本指引 https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.6/SETUP_WITH_CODEX.md ，安装或修复已发布的 Windows 助手，验证并打开本机页面。有现成 ChatGPT 授权则复用。不克隆或重建项目、不启开发 agent、不扫描私人文件、不改变安全设置、不购买额度、不发布档案。需要官方登录及私人文件夹选择／确认时，由我在本机页面完成。分别报告安装、AI授权、真实推理和网站访问状态。

### 给 Codex 的有限步骤

1. 检查 Windows x64 和本机执行能力，使用当前 PowerShell，不修改机器执行策略。只读本页，
   出错时再读对应帮助段落；安装时不全库审查、不调用模型。
2. 仅从 `https://github.com/onepunchman26/Anti-Dating-App-Scam/releases/download/v0.8.6/`
   下载 `install_work_preview.ps1` 和 `SHA256SUMS.txt`，保存到
   `%LOCALAPPDATA%/AI-SlowMatch/setup/v0.8.6`。执行前将脚本 SHA-256 与校验文件里
   `install_work_preview.ps1` 的精确条目比较。版本／文件不存在就准确报告，不能自行编译或改用 main。
3. 运行已核对脚本，带 `-Launch`。脚本核对固定压缩包和清单、安装或复用完整组件、自检并打开
   本机私人页面。想同时使用原生插件时才加 `-RegisterPlugin`；本机网页聊天不依赖该插件或远程权限。
4. 以后双击 `%LOCALAPPDATA%/AI-SlowMatch/portable/Start-SlowMatch.cmd` 即可；已有当前助手就复用。
   遇到旧版或其他程序占用端口不会自动杀掉。必须退出旧助手时，先确认具体程序及相应授权，不能
   结束所有 Python 进程，不能削弱浏览器安全限制。
5. 在本机页点击“连接本机页面”。检测现有授权；没有则完成官方登录。刷新模型列表、选模型，
   明确允许使用套餐。登录或模型列表成功都不算推理成功。
6. 选择默认的账号专属私人文件夹，或者展开“选择其他文件夹”，确认保存。不能选源码、OneDrive、
   网站或部署目录；不自动扫描或导入旧库。完整记录留在电脑；明确授权的对话可交 OpenAI 分析，
   不会发给匹配网站。
7. 开始聊天，收到真实完整回复才证明推理成功。安装本身不会擅自发送个人或测试问题。发现功能需
   另行审阅并发布摘要；私人 AI 分析只使用对方获准摘要及本人单独选择的私人上下文，不自动发布。

分别用 PASS／FAIL／NOT_CHECKED 报告安装、本机页面、授权、存储写读、完整推理、远程访问。
双人／三人验收需要独立账号。目前网站仍为维护者私有测试，安装不授予其他账号访问权限，
不宣称独立账号安装已实测。
