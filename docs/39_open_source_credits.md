# Open-source references and thanks / 开源来源与致谢

## English

Reviewed October 16, 2026. Thank you to the authors and communities below. This
register distinguishes adapted ideas, design references and an external runtime;
it does not imply endorsement or that another client's code is shipped here.
The same sources and scope are available offline in **About → Show Details**.

| Project and license | Pinned source and use in AI-SlowMatch |
| --- | --- |
| [goutoujunshi](https://github.com/powerycy/goutoujunshi), powerycy, MIT | [Reviewed revision](https://github.com/powerycy/goutoujunshi/tree/6db7354a4002dc7c448a9c87ffdad8132570c9d3). Relationship-coaching ideas adapted into the app's own bounded policy. The MIT copyright and permission notice is bundled. We exclude scores, fixed personality labels and manipulative tactics, and require evidence and separate memory approval. |
| [CodexMonitor](https://github.com/Dimillian/CodexMonitor), Thomas Ricouard and contributors, MIT | [Model lifecycle](https://github.com/Dimillian/CodexMonitor/blob/dd61b9abd37de5ded86e82b9fe8a83fd49d46fa5/src/features/models/hooks/useModels.ts), [account lifecycle](https://github.com/Dimillian/CodexMonitor/blob/dd61b9abd37de5ded86e82b9fe8a83fd49d46fa5/src/features/app/hooks/useAccountSwitching.ts), [license](https://github.com/Dimillian/CodexMonitor/blob/dd61b9abd37de5ded86e82b9fe8a83fd49d46fa5/LICENSE). Studied distinct account/model state, remembered selection and login-event binding. Our Python/Qt implementation is independently written; no source, assets or runtime copied. We do not import its workspace/file tools or unlisted configured-model fallback. |
| [Pi](https://github.com/earendil-works/pi), Mario Zechner and contributors, MIT | [Previously reviewed AI README](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/README.md), [license rechecked](https://github.com/earendil-works/pi/blob/4954d760504c11df9b2cbdc040346107b6a8153d/LICENSE). Typed provider and model-catalog design reference. No Pi implementation or Node runtime is bundled. |
| [Chatbox Community Edition](https://github.com/chatboxai/chatbox), contributors, GPL-3.0 | [README](https://github.com/chatboxai/chatbox/blob/0ac6385ae1ff5bf778777826da3c5edcd55b61b8/README.md), [license](https://github.com/chatboxai/chatbox/blob/0ac6385ae1ff5bf778777826da3c5edcd55b61b8/LICENSE). Product-flow comparison only: configure connection, then converse. No GPL code or assets copied or bundled. |
| [OpenAI Codex](https://github.com/openai/codex), OpenAI and contributors, upstream Apache-2.0 | [Upstream license checked](https://github.com/openai/codex/blob/a45b8ccb016fb74f63a6bc29e701568e387cbe38/LICENSE). The separately installed official executable implements [app-server](https://learn.chatgpt.com/docs/app-server). It is not bundled or modified here; its installation/service terms apply separately. Runtime versions 0.162.0-alpha.17.2 and 0.163.0-alpha.10.2 were audited, independently of this upstream source revision. |

Other dependencies are declared in `pyproject.toml` and the Windows constraints;
their own licenses apply. This register is not a substitute for license notices
or a completed public-distribution legal review. Before any future copying, record
the exact revision, compatibility of the license, files changed, notices and thanks.
Update both README languages and packaged credits in the same change.

### Applying the findings to the connection loop

The root executable was still 0.5.1 because the earlier replacement had been blocked
by its running process. Native inspection also found a loaded model list alongside
an unchecked allowance confirmation and a prominent button that repeated login.
The installed Codex runtime had meanwhile advanced to 0.163.0-alpha.10.2.

0.5.3 groups model, allowance confirmation and **Enter AI Chat** together, hides the
sign-in button after authorization, and explains the missing next step. Extra options
are expandable. AI Chat offers an enabled setup action when no backend is active and
keeps a connection-change action available after activation. A language rebuild reuses
the current connection; completed setup remembers the route/model but never billing
consent across process restarts. A first setup suggests the installed Codex route,
which uses its own included allowance and application-owned login. No silent switch
or inference occurs. The standard route remains available in connection options.

The updated actual runtime passed a loopback-only hostile-tool test. Real synthetic
GUI acceptance then found a duplicated follow-up in both response fields; display
now appends the question only when it is not already the exact response suffix.
The failed receipt remains in evidence. Current verification and delivery status
are recorded in [CURRENT_STATUS](../CURRENT_STATUS.md); a successful catalog alone
does not establish working inference or the upstream's actual model ID.

## 中文版

2026 年 10 月 16 日审阅。感谢上述作者与社区。本登记区分改编理念、设计参考和外部
运行依赖，不代表上游背书，也不表示打包了其他客户端的源码。软件的**关于 → 显示详情**
可离线查看相同来源及借鉴范围。

| 项目与许可 | 固定来源及本软件的使用范围 |
| --- | --- |
| [goutoujunshi／狗头军师](https://github.com/powerycy/goutoujunshi)，powerycy，MIT | [审阅版本](https://github.com/powerycy/goutoujunshi/tree/6db7354a4002dc7c448a9c87ffdad8132570c9d3)。借鉴关系沟通理念，改编为本应用有边界的策略，打包保留 MIT 版权及许可全文。排除评分、固定人格标签和操控手段，要求证据与单独记忆批准。 |
| [CodexMonitor](https://github.com/Dimillian/CodexMonitor)，Thomas Ricouard 及贡献者，MIT | [模型生命周期](https://github.com/Dimillian/CodexMonitor/blob/dd61b9abd37de5ded86e82b9fe8a83fd49d46fa5/src/features/models/hooks/useModels.ts)、[账号生命周期](https://github.com/Dimillian/CodexMonitor/blob/dd61b9abd37de5ded86e82b9fe8a83fd49d46fa5/src/features/app/hooks/useAccountSwitching.ts)、[许可](https://github.com/Dimillian/CodexMonitor/blob/dd61b9abd37de5ded86e82b9fe8a83fd49d46fa5/LICENSE)。参考独立账号／模型状态、记住选择及绑定登录事件。本项目独立编写 Python／Qt 实现，没有复制源码、素材或运行程序；不引入其工作区／文件工具或未列出配置模型的回退。 |
| [Pi](https://github.com/earendil-works/pi)，Mario Zechner 及贡献者，MIT | [此前审阅的 AI README](https://github.com/earendil-works/pi/blob/8ce69e9d2b171d173fe4b6b2b6256f1f4411e69d/packages/ai/README.md)、[许可复核](https://github.com/earendil-works/pi/blob/4954d760504c11df9b2cbdc040346107b6a8153d/LICENSE)。参考类型化提供方及模型目录设计，不打包 Pi 实现或 Node 运行程序。 |
| [Chatbox 社区版](https://github.com/chatboxai/chatbox)，贡献者，GPL-3.0 | [README](https://github.com/chatboxai/chatbox/blob/0ac6385ae1ff5bf778777826da3c5edcd55b61b8/README.md)、[许可](https://github.com/chatboxai/chatbox/blob/0ac6385ae1ff5bf778777826da3c5edcd55b61b8/LICENSE)。仅比较“设置连接后开始聊天”的产品流程，没有复制或打包 GPL 源码及素材。 |
| [OpenAI Codex](https://github.com/openai/codex)，OpenAI 及贡献者，上游 Apache-2.0 | [上游许可核对](https://github.com/openai/codex/blob/a45b8ccb016fb74f63a6bc29e701568e387cbe38/LICENSE)。通过单独安装的官方程序使用 [app-server](https://learn.chatgpt.com/docs/app-server)，本软件不打包或修改该程序，其安装／服务条款独立适用。运行版本 0.162.0-alpha.17.2 与 0.163.0-alpha.10.2 已分别审核，并不以此上游源码版本代替运行版本。 |

其他依赖列于 `pyproject.toml` 和 Windows 约束文件，各自许可独立适用。本登记不替代
原始许可，也不代表完成公开分发法律审查。今后复制前须记录确切版本、许可兼容性、
修改文件、版权声明和致谢，并在同次变更中同步双语 README 与软件内致谢。

### 如何应用到本次连接循环

根目录仍是 0.5.1，因为此前运行中的进程阻止了替换。原生检查还发现：模型已加载，
但套餐确认未勾选，突出显示的按钮却会重复登录。与此同时，本机 Codex 更新到了
0.163.0-alpha.10.2。

0.5.3 将模型、套餐确认与**进入 AI 聊天**集中放在一起，授权后隐藏登录按钮，明确提示
下一步；其他选项可展开。尚未启用 AI 时，聊天页面提供可点击的设置入口，启用后仍可
更换连接。切换语言复用当前连接，设置完成后记住通道和模型，但不跨进程保存费用确认。
首次设置建议已安装的 Codex 通道，使用其独立套餐额度与本应用专属登录，不静默切换
或推理。连接选项中仍可选择标准通道。

新版实际运行程序已通过只使用回环地址的恶意工具隔离测试。真实合成 GUI 验收发现
回复与问题字段重复同一句追问，显示层现只在回复末尾没有完全相同问题时追加。
失败记录继续保留。当前验收与交付状态见 [CURRENT_STATUS](../CURRENT_STATUS.md)，
模型列表成功本身不能证明推理可用，也不能证明上游实际模型 ID。
