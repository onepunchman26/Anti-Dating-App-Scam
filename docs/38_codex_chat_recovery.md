# Real interview recovery / 真实访谈恢复

## English

Historical October 15 record. For the current compact flow and audited runtime update,
see [the October 16 repair and credits](39_open_source_credits.md).

October 15, 2026 (UTC). The original Sign in with ChatGPT (SIWC) connection still
returned HTTP 520 for authenticated model-list and synthetic inference requests,
including after reauthorization. Anonymous controls returned normal 401 JSON.
The app's token signature, issuer, audience, expiry and registration binding were
checked without retaining credentials. These observations do not identify the
upstream cause or prove a general outage. Repeated login is not a demonstrated fix.

The local desktop application now offers **Try local Codex connection** on Connect
ChatGPT. This uses the installed official Codex app-server's managed ChatGPT login,
with a separate application-owned Windows keyring entry. It does not reuse another
app's tokens, inspect existing Codex conversations or control the ChatGPT desktop UI.
The owner separately confirmed Codex extra credits and automatic top-ups are off.
This route consumes included Codex allowance; it is not an API-key subscription.

Choose the compatibility connection, click **Connect through local Codex**, finish
browser login if requested, select a model, confirm the Codex billing settings and
click **Use ChatGPT for AI Chat → Start**. The current lightweight suggestion is
`gpt-6-luna`; selection uses the returned candidate catalog and is not a benchmark.
The candidate catalog alone does not establish account access. Completed real turns
establish that the selected request worked for this account at the recorded time.
The interface does not report the upstream actual model ID or token usage, so these
remain explicitly unknown. There is no silently substituted model or mock reply.

### Isolation and failure handling

The adapter pins `codex-cli 0.162.0-alpha.17.2`. A different installed version fails
with a compatibility message until audited; this is an external runtime dependency,
not a bundled standalone model. Official documentation permits managed app-server
login for existing local/open-source applications, not arbitrary hosted/commercial
services. Distribution beyond this local prototype needs a fresh integration review.

Each process receives an app-owned home, a new empty working directory and a minimal
environment without inherited API keys. Tools, shell, browser, connectors, plugins,
skills, web search, history and environment instructions are disabled. Only exact
reviewed messages and the app's system/schema contract enter an ephemeral thread.
Unexpected instruction sources, model changes, tool activity and approval requests
are rejected. Every inference checks `ordinaryUsageAllowed`; unknown/unavailable
included usage blocks the request. This cannot inspect or change the owner's billing
switches. The app adds no inference retry; the official runtime may retry transport
internally. End discards late replies and closes its owned process on cancellation;
it cannot promise that a remote computation consumes no allowance.

The keyring retains this app's login across restarts. Disconnect logs out this app's
own keyring context even after restart. Codex creates local operational databases
inside its isolated app home; do not treat those as an encrypted user vault or upload
them with source. Raw errors, tokens and account identifiers are excluded from saved
test evidence. Source backups and Git do not include these runtime directories.

A loopback-only adversarial test used the actual installed runtime and a fake model
server. The outbound tool catalog was empty. An injected `exec_command` was rejected
as unsupported and a synthetic private canary did not appear in either request.
This is an isolation test, not real model inference or a general security proof.

### Evidence and repeatability

Three service-level real runs are retained: the first two failed the interview
quality check because follow-ups were missing. After clarifying the distinction
between pausing a relationship disagreement and pausing this AI interview, the
[final three-turn run](evidence/2026-10-15-codex-interview-final.json) passed.
All inputs are synthetic. This establishes functional conversation behavior on a
small sample, not psychological validity or access to every listed model.

The EXE also has an explicit developer acceptance command:

```powershell
.\AI-SlowMatch.exe --synthetic-chat-check <new-receipt.json> --confirm-included-plan
```

Run it only after confirming Codex extra credits and top-ups are disabled. It uses
the normal Qt controls/workers, an empty temporary vault and four fixed synthetic
turns, including a request for no more questions. It checks model selection, rendered
answers, End and Back. It never runs on normal startup and refuses to overwrite an
existing receipt. The flag authorizes only this fixed test, not future private data.
Actual source, packaged and delivery results belong in [current status](../CURRENT_STATUS.md).
Physical microphone capture and Chinese playback remain separate device checks.

Official sources: [SIWC models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
[SIWC app-server integration](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server),
[Codex app-server authentication and protocol](https://learn.chatgpt.com/docs/app-server),
[configuration schema](https://learn.chatgpt.com/docs/config-schema.json).

## 中文版

本页为 10 月 15 日历史记录。最新集中流程与运行版本更新见
[10 月 16 日修复与来源说明](39_open_source_credits.md)。

2026 年 10 月 15 日（UTC）。原有 Sign in with ChatGPT（SIWC）连接在重新授权后，
带授权的模型列表及合成推理请求仍返回 HTTP 520；匿名对照正常返回 401 JSON。
已检查本应用令牌的签名、签发者、受众、有效期及注册绑定，未保存凭据内容。
这些现象不能确定上游原因，也不能证明全网故障；重复登录尚未被证明能解决问题。

本地桌面应用现提供“连接 ChatGPT → **尝试本机 Codex 兼容连接**”。它通过已安装的
官方 Codex app-server 单独登录 ChatGPT，使用本应用独立的 Windows 凭据存储。
不会复用其他应用令牌、读取已有 Codex 对话或操控 ChatGPT 桌面界面。所有者已另外
确认关闭 Codex 额外积分及自动充值；此通道使用已有 Codex 套餐额度，不使用付费 API key。

选择兼容连接，点击“**通过本机 Codex 连接**”，若出现浏览器登录则完成登录；选择模型，
确认 Codex 积分设置，再点击“**用 ChatGPT 开始 AI 聊天 → 开始**”。当前轻量建议为
`gpt-6-luna`，按返回的候选列表选择，并非性能排名。候选目录本身不证明账号实际访问权限；
完成的真实回答只证明该账号在记录时间内的所选请求成功。接口没有报告上游实际模型 ID
或 token 用量，因此明确保留为未知，没有把请求模型冒充返回模型，也没有静默替换或模拟回复。

### 隔离与失败处理

适配器固定兼容 `codex-cli 0.162.0-alpha.17.2`；已安装版本改变时会提示需要兼容更新，
通过审计后才能继续使用。这是外部运行程序依赖，不是内置离线模型。官方文档允许现有
本地／开源应用使用此托管登录方式，不适用于任意托管／商业服务；超出本地原型的分发
需要重新检查集成方式。

每个进程使用本应用自己的目录、新建空工作目录及不含继承 API 密钥的最小环境。
禁用工具、终端、浏览器、连接器、插件、skills、网页搜索、历史与环境指令，仅向临时
会话传入逐次审核过的消息和本应用系统／格式协议。发现意外指令文件、模型变化、工具
活动或权限请求即拒绝。每次推理检查 `ordinaryUsageAllowed`，无法确认或套餐不可用时
停止；此检查无法读取或更改所有者的积分开关。本应用不追加推理重试，但官方程序内部
可能重试传输。结束操作丢弃迟到回答，取消时关闭本应用子进程；不能保证远程已开始的
计算不消耗额度。

本应用独立凭据在重启后可以复用；“断开此账号”在重启后也会退出该独立凭据。
Codex 会在隔离目录内创建本地运行数据库，不能将其视为加密个人资料库，也不得随源码
上传。保存的测试证据不含原始服务错误、令牌或账号标识，源码备份和 Git 不包含这些
运行目录。

回环地址对抗检查使用实际已安装的 Codex 和模拟模型服务：请求中的工具目录为空，
故意注入的 `exec_command` 被判定为不支持，两个请求都未出现合成私人标记。
这是隔离检查，不是真实模型推理，也不是全面安全保证。

### 证据与复现

保留三次服务层真实测试：前两次因缺少追问而未通过访谈质量检查。明确区分“关系争执
时暂停”和“暂停本次 AI 访谈”后，[最终三轮测试](evidence/2026-10-15-codex-interview-final.json)
通过。全部输入均为合成资料，只证明小样本功能可用，不证明心理科学效度或全部模型可访问。

EXE 另有需主动执行的开发验收命令：

```powershell
.\AI-SlowMatch.exe --synthetic-chat-check <新的记录.json> --confirm-included-plan
```

仅在确认 Codex 额外积分及自动充值关闭后使用。它通过正常 Qt 按钮／工作线程，在空的
临时资料库中发送四轮固定合成内容，包括“请不要再问问题”；检查模型选择、实际显示
的回答、结束与返回。正常启动绝不运行该检查，也不覆盖已有记录。该参数只授权这一
固定测试，不代表批准后续私人资料发送。源码、打包和交付结果以[当前状态](../CURRENT_STATUS.md)
为准；实体麦克风与中文朗读仍需独立设备验收。

官方依据：[SIWC 模型及推理](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)、
[SIWC app-server 集成](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)、
[Codex app-server 认证及协议](https://learn.chatgpt.com/docs/app-server)、
[配置格式](https://learn.chatgpt.com/docs/config-schema.json)。
