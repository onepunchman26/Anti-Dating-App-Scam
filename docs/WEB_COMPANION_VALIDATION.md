# Web companion acceptance / 网页助手验收

## English

October 18, 2026 (Toronto; deployment completed October 19 UTC). Original repository,
unchanged remote, branch `codex/web-onboarding-local`, rollback `d6255d0`.
The complete latest referenced conversation was read. Its new Markdown attachment body
was not exposed; no claim is made to have read that missing file. The adopted direction
is recorded in AGENTS and the plan. Existing unrelated `.vscode/` and `paper/` were preserved.

| Module | Observed evidence | Reuse/change | Acceptance |
|---|---|---|---|
| OpenAI connection | Existing verified SIWC registrations, signed-token validation and Responses adapter | Reused; no API key or alternative inference | Live catalog and three completed synthetic requests across source, browser and EXE |
| Private data | Existing Pydantic profile, revisions and guarded local I/O | Added explicit per-registration vault selection and dedicated sessions | Source and packaged restart retain messages/profile; mismatched account and unsafe paths refused |
| Site | Existing React/Vinext Worker, D1, authentication, summary and plan flows | Added guided start and shared-summary form to the same component tree | Real local browser, real local D1; deployed saved version 9 |
| Geography | Existing reciprocal normalized-city filters | Added ordinary-user city/accepted-city controls | Toronto/Ottawa mutual match; one-sided, hidden, expired/mode boundaries tested; no GPS distance invented |
| Distribution | Existing pinned Windows build, provenance, installer and account slots | Added `companion` command and Start-SlowMatch.cmd, version 0.8.1 | 29 isolated EXE calls; no developer tools on child PATH; separate real packaged AI call |

**Implemented and connected locally:** ephemeral pairing, exact-origin/Host checks,
separate account/plan/model/inference status, private directory write/read, dedicated
conversation create/resume, natural self-understanding help, explicit cloud consent,
optional bounded confirmed-profile context, stop/failure recovery, statement confirmation,
correction/removal and separate shared-summary preview/approval. Full private content goes
directly between the browser and loopback helper; only the helper calls OpenAI. Hosted
summary generation never loads the private vault. Existing matching/planning service
contracts and owner-private audience are unchanged.

**Actually exercised:** local browser completed an OpenAI reply, saved a synthetic private
statement, preserved unsent text/consent while switching languages, and published synthetic
summary version 2 to the local D1 service after separate approval. Packaged EXE recovered
that session/profile, completed a real request, then a new EXE process recovered two sessions
with two messages each and profile revision 1. A new process does not inherit an “inference
passed” badge. No real hosted profile was published. Screenshots in
[evidence/web-onboarding](evidence/web-onboarding) show only the clean start page.

Verification: full Python **2,562 passed / 11 skipped** before final bounded refinements;
focused companion/distribution **59 passed**, final bootstrap **41 passed / 1 skipped**;
Site suite **31 passed**, final locale/editor/geography subset **6 passed**; compile,
TypeScript and supported production build passed. Both UI languages passed 360/768/1440
width checks after fixing the fourth navigation item's overflow. Bootstrap's first run
against old-version fixtures failed; updating their pinned expected version restored the
release-identity checks without relaxing integrity or origin checks.

**Deployed:** saved Site version **9**, source `1aacfbfc3d9780ba88a19624b13c63f11ee1adef`,
environment revision 1; native authenticated read-only channel/database/schema check passed.
Original app code `98ae73a`, final Site adjustment `0529530`, one-way deployment mirror.
Previous version 7 remains the pre-change Site rollback. Windows package source is exactly
`98ae73ab94cdd3cf5ee13e12739428a297aedca0`, clean, 148 manifested files. Packaging is separate
from installation, authorization and browser acceptance.

**Still blocked/unverified:**

- The in-app browser's official login page requires the owner to sign in. Thus actual
  hosted HTTPS webpage → loopback browser access (including local-network permission)
  is NOT EXERCISED. A successful HTTP client Origin-header test is not that browser proof.
- Independent account B remains unavailable and NOT EXERCISED, including installation,
  reciprocal hosted publication and both-party planning confirmation. No other identity was simulated online.
- Fresh-account SIWC authorization and general distribution eligibility of the hosted
  UI/local-runtime combination remain unverified. Original project licensing is undeclared.
- Web chat has no automatic MCP tool execution, microphone, transcription, GPS lookup or
  location permission. It cannot automatically import ChatGPT chats/memory. Existing native
  plugin and Site planning flows remain separate; their old limits still apply.
- Windows PowerShell 5.1 is policy-blocked here; no policy bypass. No stable-release,
  clean-device or universal-user setup claim.

The selected catalog model was used without fallback or paid API credentials; owner-approved
synthetic plan tests were reused. Fixed setup/review/filtering does not call a model. Context
uses at most 20 recent turns/20,000 characters, or 15,000 plus at most ten confirmed statements
within 4,500 characters. These are deterministic bounds, not a measured token reduction.

Official references: [SIWC quickstart](https://developers.openai.com/siwc/quickstart),
[local app route](https://developers.openai.com/siwc/token-sharing-open-source),
[models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
[preview limits](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations).
Live catalog, `store:false`, streaming and completed-event checks use the retained adapter.

## 中文版

2026 年 10 月 18 日（多伦多；部署完成时 UTC 为 10 月 19 日）。继续原仓库和原远端，
分支 `codex/web-onboarding-local`，回退点 `d6255d0`。已读取最新引用对话的完整内容，
但工具没有返回新 Markdown 附件正文，不声称读过缺失文件。新方向已写入 AGENTS 与计划；
保留无关的 `.vscode/` 和 `paper/` 工作。

| 模块 | 实际证据 | 复用或改造 | 验收 |
|---|---|---|---|
| OpenAI 连接 | 原有 SIWC 登记、签名令牌验证、Responses 接口 | 直接复用，无 API key 或替代推理 | 真实模型发现，源码／浏览器／EXE 合计三次完整合成请求 |
| 私人数据 | 原有 Pydantic 档案、版本及受保护本机读写 | 增加明确的账号登记分槽、选库及专用会话 | 源码和打包重启保留记录，拒绝错误账号与不安全路径 |
| Site | 现有 React／Vinext Worker、D1、认证、摘要和计划流程 | 在同一组件树增加新手入口与共享表单 | 真实本机浏览器及 D1，通过部署为第 9 版 |
| 地区筛选 | 原有规范化城市的双向条件 | 增加本人城市及愿意见面城市表单 | Toronto／Ottawa 双向通过；单向、隐藏、有效期与模式边界检查，不虚构 GPS 距离 |
| 分发 | 原有固定 Windows 构建、来源、安装器及分槽 | 增加 companion 命令和启动脚本，0.8.1 | 29 项独立 EXE 调用，子进程 PATH 无开发工具，另测真实打包推理 |

**已实现并本机连接：**临时配对、精确来源与 Host 检查，账号／套餐／模型／推理分开显示，
私人目录实际写读，专用会话创建和恢复，自然自我探索，单独云端授权，可选的有限已确认档案上下文，
暂停和失败恢复，陈述确认／修正／移除，以及独立共享摘要预览与批准。私人内容只在浏览器与
回环地址助手之间传递，再由助手调用 OpenAI。托管摘要生成不读取私人档案。
原匹配／计划服务契约与所有者私有受众保持不变。

**已实测：**本机浏览器获得真实 OpenAI 回复，保存合成私人陈述，切换语言保留未发送文字及批准，
独立确认后将合成摘要第 2 版写入本机 D1。打包 EXE 读回会话和档案、完成一次真实请求；
重新启动的 EXE 再读回两个各含两条消息的会话和档案第 1 版。重启不沿用“推理已通过”标记。
没有发布真实线上档案。[截图](evidence/web-onboarding)只包含干净的新手入口。

检查结果：最后几项有限修订前，完整 Python **2,562 通过／11 跳过**；针对性助手／分发
**59 通过**，最终安装器 **41 通过／1 跳过**；Site 全套 **31 通过**，最终语言／编辑器／
地区子集 **6 通过**；编译、TypeScript、受支持生产构建通过。修复第四个导航项溢出后，
中英文 360／768／1440 宽度通过。安装器首次遇到旧版本测试夹具而失败，更新明确预期版本后恢复；
未放宽完整性或来源检查。

**已部署：**Site 保存版本 **9**，托管源码 `1aacfbfc3d9780ba88a19624b13c63f11ee1adef`，
环境版本 1；原生认证只读通道、数据库读取和结构检查通过。原项目实现 `98ae73a`，
最终网页调整 `0529530`，单向同步托管镜像；第 7 版仍为改动前回退点。
Windows 包严格来自干净提交 `98ae73ab94cdd3cf5ee13e12739428a297aedca0`，含 148 个清单文件。
打包、安装、授权和浏览器验收分别记录。

**仍受阻或未实测：**

- 应用内浏览器出现官方登录页，需要本人登录。因此正式 HTTPS 网页到本机助手的浏览器调用，
  包括本机网络权限，尚未实测。HTTP 客户端设置 Origin 成功不能代替浏览器证据。
- 独立 B 账号仍不可用，安装、双方线上发布及计划确认均尚未实测，未在网上模拟他人身份。
- 全新账号 SIWC 授权及“托管 UI＋本机运行”广泛发行资格未确认；原项目整体许可仍未声明。
- 网页聊天未自动接入 MCP 工具、麦克风、转写、GPS 查询或位置授权，也不能自动导入 ChatGPT
  历史和记忆。原生插件及 Site 计划流程仍分别保留，其原有限制继续适用。
- 本机 PowerShell 5.1 被策略限制，未绕过；不宣称稳定版、干净设备或所有用户设置通过。

测试使用实际模型目录中的选择，无模型回退或付费 API 凭据，沿用本人已批准的合成套餐测试。
固定设置、审阅和筛选不调用模型。上下文最多二十条近期消息／两万字符，或一万五千字符加最多
十条、四千五百字符以内的已确认档案。这是程序确定的上限，不是已测得的 token 节省量。

官方依据：[SIWC 入门](https://developers.openai.com/siwc/quickstart)、
[本地应用路线](https://developers.openai.com/siwc/token-sharing-open-source)、
[模型与推理](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)、
[预览限制](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)。
实际模型目录、store:false、流式及完成事件检查复用原适配器。
