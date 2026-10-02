# Historical snapshot / 历史快照

English: Superseded on October 2, 2026; current scope is in the root plan.

中文版：2026 年 10 月 2 日起被替代；当前范围以根目录计划为准。

# Packaging / 应用打包

## Conversation-first desktop checkpoint / 聊天优先桌面里程碑

### English

The rebuilt `AI-SlowMatch-Desktop.exe` is the current simplified entry point.
Use [the opening guide](../../../../packaging/GETTING_STARTED.md). This cycle rebuilds and independently
verifies Desktop only; earlier browser, wheel and source-distribution artifacts are
preserved. Their old snapshot/checksums are historical. The current desktop and guide
are certified by `dist/CONVERSATION_BUILD_SNAPSHOT.json` and
`dist/CONVERSATION_SHA256SUMS.txt`. Real ChatGPT sign-in and model behavior remain
unverified by development's synthetic tests.

### 中文版

重建的 `AI-SlowMatch-Desktop.exe` 是当前精简主入口，使用方法见[打开指南](../../../../packaging/GETTING_STARTED.md)。
本轮只重建并独立核验桌面程序；先前的浏览器版、wheel 和源码包保留，旧快照及校验和属于
历史记录。当前桌面程序和指南使用 `dist/CONVERSATION_BUILD_SNAPSHOT.json` 及
`dist/CONVERSATION_SHA256SUMS.txt` 核对。开发使用合成测试，未验证真实 ChatGPT 登录或模型表现。

## English

The desktop app is the primary local product. A wheel includes the desktop
package, JSON schemas, and browser HTML. Installing it does not require this
source checkout to remain present. Python 3.11+ is required for a wheel install;
a frozen Windows executable includes Python and Qt.

### Install and run a wheel

```powershell
python -m pip install "dist/anti_dating_scam-0.1.0-py3-none-any.whl[desktop]"
slowmatch
# Optional local browser interface:
slowmatch-web
```

`slowmatch --smoke-test` uses a temporary home, disables provider autoconnection,
checks bundled schemas and browser HTML, starts the Qt event loop offscreen,
and exits automatically. The browser command
binds only to `127.0.0.1` and disables request access logs. Choosing remote AI or
an external matching node can transmit explicitly selected data; installing or
starting the application does not authorize that transmission.

### Build and verify from source

```powershell
python -m pip install -e ".[desktop,dev]" pyinstaller
python -m compileall src
python -m pytest
python -m ruff check src tests
python -m build --wheel
python packaging/smoke_install.py
```

`constraints-windows-py312.txt` records the tested Windows/Python 3.12 package
versions. To reuse them, add `-c packaging/constraints-windows-py312.txt` to the
install command. This is a platform-specific snapshot, not a reviewed cross-platform
lock or a guarantee of future package availability.

The installation smoke check builds a wheel, creates a fresh environment outside
the checkout, installs its dependencies, checks schemas and browser resources,
tests rejection of an untrusted browser origin, starts the real desktop event
loop, and checks an actual loopback HTTP server. It uses temporary synthetic
state. It can download free Python packages; it never calls a model or uses
payment information. Pass `--wheel <path>` to test a specific wheel.

### Portable Windows executables

Build on Windows using Python 3.11+ with PyInstaller; building on a different
operating system does not produce a Windows executable.

```powershell
.\packaging\build_windows.ps1 -Python .\.venv-rehab\Scripts\python.exe -Target Desktop
.\packaging\build_windows.ps1 -Python .\.venv-rehab\Scripts\python.exe -Target Web
.\packaging\build_windows.ps1 -Python .\.venv-rehab\Scripts\python.exe -Target Node
```

Outputs are `dist/AI-SlowMatch-Desktop.exe`, `dist/AI-SlowMatch.exe` (local
browser client), and `dist/AI-SlowMatch-Node.exe` (experimental rendezvous node).
Desktop builds have no console window; add `-Console` for diagnostics. Desktop
and browser builds test their executable outside the checkout with temporary data.
Build scripts stop if a tool or startup check fails. `build_exe.ps1` remains a compatibility wrapper
whose default target is the browser client.

These artifacts are unsigned local prototypes. The node remains experimental;
this packaging workflow does not approve public deployment. Its state is
in memory and is lost when the process stops. Freezing does not encrypt the
local vault or remove the need to review provider disclosures.

The Windows artifacts do not include optional Playwright browser automation or
downloaded browser engines. Manual file import works without that integration;
assisted-browser export requires a source installation with the `browser` extra
and its browser engine setup.

`packaging/build_macos.sh` builds the experimental node on macOS; `APP=1` selects
its windowed form. The GitHub build workflow can create platform artifacts when
explicitly triggered or when a version tag is pushed. Local build verification
does not establish that remote CI or macOS builds passed. No artifact is uploaded
by the local scripts.

## 中文版

桌面应用是本项目的主要本地产品。wheel 安装包包含桌面代码、JSON Schema 和浏览器
HTML；安装后无需保留源码目录。wheel 安装需要 Python 3.11 或更新版本，独立的
Windows 可执行文件则自带 Python 与 Qt。

### 安装并启动 wheel

```powershell
python -m pip install "dist/anti_dating_scam-0.1.0-py3-none-any.whl[desktop]"
slowmatch
# 可选的本地浏览器界面：
slowmatch-web
```

`slowmatch --smoke-test` 使用临时主目录、禁用提供方自动连接，检查打包的 Schema 与
浏览器 HTML，在无界面模式启动 Qt 事件循环，然后自动退出。浏览器命令只监听
`127.0.0.1`，并关闭请求访问日志。选择
远程 AI 或外部匹配节点可能发送你明确选定的数据；安装或启动应用不代表授权发送。

### 从源码构建并验证

```powershell
python -m pip install -e ".[desktop,dev]" pyinstaller
python -m compileall src
python -m pytest
python -m ruff check src tests
python -m build --wheel
python packaging/smoke_install.py
```

`constraints-windows-py312.txt` 记录了已测试的 Windows/Python 3.12 软件包版本。
如需复用，在安装命令中加入 `-c packaging/constraints-windows-py312.txt`。
这是一份针对特定平台的版本快照，不是经过审查的跨平台锁定文件，也不保证软件包
未来始终可用。

安装检查会构建 wheel，在源码目录以外创建全新环境并安装依赖，验证 Schema 与浏览器
资源，测试拒绝不可信浏览器来源，启动真实桌面事件循环，并检查实际的回环 HTTP 服务。
全程使用临时合成状态。它可能下载免费的 Python 软件包，但不会调用模型，也不会使用
支付信息。可传入 `--wheel <路径>` 检查指定 wheel。

### Windows 独立可执行文件

请在 Windows 上使用 Python 3.11 或更新版本及 PyInstaller 构建；在其他操作系统上
构建不能生成 Windows 可执行文件。

```powershell
.\packaging\build_windows.ps1 -Python .\.venv-rehab\Scripts\python.exe -Target Desktop
.\packaging\build_windows.ps1 -Python .\.venv-rehab\Scripts\python.exe -Target Web
.\packaging\build_windows.ps1 -Python .\.venv-rehab\Scripts\python.exe -Target Node
```

产物依次为 `dist/AI-SlowMatch-Desktop.exe`、`dist/AI-SlowMatch.exe`（本地浏览器
客户端）和 `dist/AI-SlowMatch-Node.exe`（实验性会合节点）。桌面版本默认不显示
终端；添加 `-Console` 可构建带终端的诊断版本。桌面与浏览器构建会在源码目录之外
使用临时数据验证可执行文件。工具执行或启动检查失败时，构建脚本会停止。
`build_exe.ps1` 保留为兼容入口，默认构建浏览器客户端。

这些产物属于未签名的本地原型。节点仍处于实验阶段，此打包流程不代表批准公开部署。
节点状态存于内存，进程停止后即消失。冻结成可执行文件不会加密本地档案库，也不能
代替对提供方披露内容的审核。

Windows 产物不包含可选的 Playwright 浏览器自动化组件或下载的浏览器引擎。手动导入
文件无需此集成；辅助浏览器导出需要源码安装、`browser` 可选依赖及对应浏览器引擎配置。

`packaging/build_macos.sh` 可在 macOS 构建实验节点；设置 `APP=1` 可选择无终端
版本。显式触发 GitHub 构建工作流或推送版本标签时，可以生成各平台产物。本地验证
不代表远端 CI 或 macOS 构建已通过。本地脚本不会上传任何产物。
