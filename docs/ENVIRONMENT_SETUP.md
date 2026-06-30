# Environment Setup / 环境配置

> Human-facing doc — kept bilingual per `AGENTS.md`. / 面向用户的文档 —— 依据 `AGENTS.md` 规定保持中英双语。
>
> Last verified / 最近验证: 2026-06-29 — `compileall` clean, **54 tests passed**, `ruff check` clean. / `compileall` 通过，**54 项测试全部通过**，`ruff` 检查通过。

---

## English

### The one rule that matters: Python 3.11+

This project **requires Python 3.11 or newer**. It uses `datetime.UTC` and `enum.StrEnum`, both added in Python 3.11. On Python 3.10 or older you will see this error and nothing will run:

```
ImportError: cannot import name 'UTC' from 'datetime'
```

If you hit that error, your Python is too old — that is the whole "environment issue." Fix the version and everything works.

### Step 1 — Check your Python version

In PowerShell, from the project root:

```powershell
python --version
```

If it prints `Python 3.11.x` or higher, skip to Step 2. If it prints 3.10 or lower (or "not recognized"), install a current Python first:

```powershell
winget install Python.Python.3.12
```

Then close and reopen PowerShell. You can now target it explicitly with `py -3.12`.

### Step 2 — Create and activate a virtual environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by execution policy, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Step 3 — Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -e ".[desktop,dev]"
```

`desktop` pulls in PySide6 (the GUI). `dev` pulls in pytest and ruff (tests + linter).

### Step 4 — Verify

```powershell
python -m compileall src
pytest
ruff check src tests
```

Expected: compile clean, all tests pass, `All checks passed!`.

### Step 5 — Run the app

```powershell
python run_desktop.py
```

A PySide6 desktop window opens with the onboarding flow (Welcome → Safety & Consent → … → Home).

### Shortcut

From the project root, the bundled script does Steps 2–4 for you:

```powershell
.\setup_windows.ps1
```

### Note on OneDrive "cloud-only" files

This repo lives in a OneDrive-synced folder. Some files may show as cloud-only (not downloaded) and can fail to open until synced. If a tool reports a file as missing or unreadable, right-click the project folder → **Always keep on this device**, or open each file once to force a download.

---

## 中文版

### 唯一关键的要求：Python 3.11 及以上

本项目**要求 Python 3.11 或更高版本**。代码使用了 `datetime.UTC` 和 `enum.StrEnum`，这两者都是 Python 3.11 才新增的。如果使用 Python 3.10 或更低版本，会立即报下面这个错误，程序完全无法运行：

```
ImportError: cannot import name 'UTC' from 'datetime'
```

如果你遇到这个错误，说明你的 Python 版本太旧 —— 这就是所谓「环境问题」的全部原因。把版本升上去，一切就正常了。

### 第一步 —— 检查 Python 版本

在 PowerShell 中，进入项目根目录后运行：

```powershell
python --version
```

如果显示 `Python 3.11.x` 或更高，直接跳到第二步。如果显示 3.10 或更低（或提示「无法识别」），请先安装新版 Python：

```powershell
winget install Python.Python.3.12
```

然后关闭并重新打开 PowerShell。之后可以用 `py -3.12` 明确指定该版本。

### 第二步 —— 创建并激活虚拟环境

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果激活时被执行策略（execution policy）拦截，先运行一次：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 第三步 —— 安装依赖

```powershell
python -m pip install --upgrade pip
pip install -e ".[desktop,dev]"
```

`desktop` 会安装 PySide6（图形界面）。`dev` 会安装 pytest 和 ruff（测试与代码检查工具）。

### 第四步 —— 验证

```powershell
python -m compileall src
pytest
ruff check src tests
```

预期结果：编译无错误、所有测试通过、显示 `All checks passed!`。

### 第五步 —— 运行程序

```powershell
python run_desktop.py
```

会弹出一个 PySide6 桌面窗口，进入引导流程（欢迎 → 安全与同意 → …… → 主页）。

### 快捷方式

在项目根目录下，附带的脚本会自动帮你完成第二到第四步：

```powershell
.\setup_windows.ps1
```

### 关于 OneDrive「仅云端」文件的说明

本仓库位于 OneDrive 同步文件夹中。部分文件可能显示为「仅云端」（尚未下载到本地），在同步完成前可能打不开。如果某个工具提示文件缺失或无法读取，请右键点击项目文件夹 →「始终保留在此设备上」，或逐个打开文件以强制下载。
