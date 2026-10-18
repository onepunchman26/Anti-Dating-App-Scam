# Open-source references and thanks / 开源来源与致谢

## Site UI revision, October 18, 2026 / 网站界面修订

English: [Hinge](https://hinge.co/mission), [Hinge Date Ideas](https://hinge.co/newsroom/date-ideas-feature),
[Bumble](https://bumble.com/), [Bumble Chinese](https://bumble.com/zh),
[Tinder](https://tinder.com/) and [Meetup](https://www.meetup.com/) were checked on
October 18, 2026 as official design references. Actual reuse is limited to general
information hierarchy: profile-specific conversation starts, separate relationship
intents, clear language/start/help controls and activity/place/time information.
No brand layout, image, logo, profile, source code or website text is redistributed;
no software license is asserted for these references. Thanks to their designers.
[W3C language declarations](https://www.w3.org/International/questions/qa-html-language-declarations)
and [contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
informed the project-authored implementation. Actual bundled SVG icons use the
already installed **lucide-react 1.31.0**, ISC, copyright 2026 Lucide Icons and
Contributors. Its full installed notice, including the relevant Feather/MIT notice,
is preserved in [the Site license asset](../apps/matching_site/public/licenses/lucide.txt).
The deployed Site also contains [bilingual packaged credits](../apps/matching_site/public/CREDITS.md).
The released Windows package and legacy EXE are not rebuilt by this UI revision.

中文版：上列 Hinge、Hinge Date Ideas、Bumble 及其中文页面、Tinder、Meetup 官方页面于
2026 年 10 月 18 日核对，实际仅参考通用信息层级：具体资料带来的交流切入点、分别表达关系
意向、清晰的语言／开始／帮助入口，以及活动／地点／时间安排。没有重新分发品牌布局、图片、
标志、资料、源码或网页文字，不对这些参考声称软件许可，感谢其设计团队。上列 W3C 语言声明
及对比度指南用于本项目自写实现。实际随网站使用的 SVG 图标来自已安装的
**lucide-react 1.31.0**，ISC 许可，版权 2026 Lucide Icons and Contributors；完整安装
声明及其相关 Feather／MIT 条款保留在上列网站许可文件，部署包同时含完整双语致谢。
此次 UI 修订没有重新构建已发布 Windows 包或旧 EXE。

## Windows Work 0.8.0 distribution / Windows Work 0.8.0 分发

English: The controlled preview actually bundles CPython 3.12.14, Pydantic 2.13.5,
pydantic_core 2.46.5 and pinned support dependencies, using PyInstaller 6.22.3.
The build manifest records exact versions; the package's LICENSES directory retains
their full installed notices, including Python and the PyInstaller bootloader license
and exception. Thank you to their maintainers. The builder/installer is project-authored.
Official [plugin packaging](https://developers.openai.com/plugins/build/plugins) and
[commands](https://learn.chatgpt.com/docs/reference/commands), checked October 18, 2026,
are interface references only. Codex, Qt, Vosk/models and the legacy EXE are not in this
portable package. No new project license was selected; see [license status](LICENSING_STATUS.md).

中文版：受控预览实际包含 CPython 3.12.14、Pydantic 2.13.5、pydantic_core 2.46.5
及固定辅助依赖，以 PyInstaller 6.22.3 构建。构建清单记录准确版本，包内 LICENSES
保留安装依赖的完整声明，包括 Python 及 PyInstaller 启动器许可与例外，感谢各维护者。
构建／安装代码由本项目编写。上列官方插件打包及命令文档于 2026 年 10 月 18 日核对，
仅为接口参考。便携包不包含 Codex、Qt、Vosk／模型或旧 EXE。未擅选本项目新许可；
详见[许可状态](LICENSING_STATUS.md)。

## English

Reviewed October 17, 2026. Thank you to the authors and communities below. This
register distinguishes adapted ideas, design references, external runtimes and
the actual Sites starter components now retained in source. References are not
endorsements. Source packaged credits are updated in
`src/anti_dating_scam/licenses/open-source-credits.txt`; the existing 0.5.3 EXE's
**About → Show Details** retains its earlier credits until a separate rebuild.

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

### October 17 plugin and Sites migration

| Source, revision and license | Actual reuse and retained notices |
| --- | --- |
| OpenAI Sites supplied Vinext starter, installed bundle `sites/1.0.2-remix-a.1` | Actual scaffolding copied into `apps/matching_site/`: runtime/build configuration, auth helper, scripts and retained vendor assets. Project-specific matching behavior and pages are written here. This is bundled starter source, not merely design inspiration; component licenses are identified below, without asserting one blanket license for the whole supplied template. |
| `@openai/sites-vite-plugin` `0.2.0`, header provenance `openai/sites#9`, MIT, copyright 2026 OpenAI | [Build integration](../apps/matching_site/build/sites-vite-plugin.ts) is actually vendored and imported by the Site Vite config. The [full MIT notice](../apps/matching_site/build/sites-vite-plugin.LICENSE) is retained. SHA-256 matched the installed starter source at inspection: `07af20e7097d9ed1d76f7c446d02997550b8fc5ca89668b249e25eabd62c6834`. Thank you to the Sites maintainers. |
| shadcn Tailwind CSS `4.13.0`, supplied by the same Sites bundle, MIT, copyright 2023 shadcn | [Vendored stylesheet](../apps/matching_site/vendor/shadcn-tailwind-4.13.0.css) is imported by the Site's global CSS; the [full MIT notice](../apps/matching_site/vendor/shadcn-tailwind-4.13.0.LICENSE.md) remains beside it. SHA-256 matched the installed starter: `bc7d83425702955b4cb67cb14ede9d603f9d912376d57a2d81d661094d2a782a`. Thank you to shadcn and contributors. |
| goutoujunshi, reviewed revision `6db7354a4002dc7c448a9c87ffdad8132570c9d3`, MIT | The native plugin adapts evidence separation, tentative interpretation, autonomy and bounded-memory methods from the inspected Skill and memory guide. It does not copy the complete prompt or memory implementation. Mandatory MBTI/scores, gender defaults and manipulation are excluded. Both original notices remain in `plugins/slowmatch/licenses/`; see its [bilingual credits](../plugins/slowmatch/CREDITS.md). |
| Installed `grilling` Skill; inspected local copy, no upstream revision/license claimed | Development review only. It is neither bundled nor an end-user coaching module. No copied implementation or prompt, so this entry records a consulted method rather than a redistributed dependency. |
| Life direction and action planning | No separate installed Skill was found in the audited user and cached-plugin locations. `plugins/slowmatch/skills/slowmatch/references/direction.md` is new project-authored workflow text, not a claimed reuse of an unavailable Skill. |
| Official OpenAI plugin and Sites documentation, checked October 17, 2026 | [Plugin packaging](https://developers.openai.com/plugins/build/plugins), [connection/testing](https://developers.openai.com/plugins/deploy/connect-chatgpt), [desktop distribution](https://developers.openai.com/plugins/deploy/desktop-only), [Sites data](https://learn.chatgpt.com/docs/sites/data-and-connections) and [sharing](https://learn.chatgpt.com/docs/sites/publishing-and-sharing) informed interfaces and evidence boundaries. Documentation reference only; no OpenAI client code copied. |

Site dependency versions are captured in its `package.json` and lockfile; their own
licenses apply. Build and vendor notices above remain in the hosted-source mirror
and source package. The native plugin and existing desktop binary are separate
artifacts; this source credit update does not claim either was reinstalled/rebuilt.

### Full replacement scope: behavior, place and audio references

| Source and checked edition | Actual use, license scope and thanks |
|---|---|
| Department of Justice Canada, *Making appropriate parenting arrangements in family violence cases, 2023*, February 2023 summary; Jaffe, Bala, Medhekar, Scott and Oliver; [source](https://www.justice.gc.ca/eng/rp-pr/jr/rib-reb/mpafvc-capcvf/index.html), checked October 17, 2026 | Behavioral design reference: patterns/context and differentiated safety responses inform the project's own relationship-support text. No report text, diagram or code is bundled; no software license is claimed. Its family-justice setting is not a dating-AI diagnostic standard or a legal conclusion for a user's location. Thank you to the authors and publisher. |
| Official OpenAI [plugin reference](https://developers.openai.com/plugins/reference), [local security](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security), [Voice](https://learn.chatgpt.com/docs/features/voice), [web search](https://learn.chatgpt.com/docs/web-search) and [transcription API](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create), checked October 17, 2026 | Interface/documentation references only, not bundled OpenAI software. Used to distinguish optional location/file hints, local/cloud boundaries, voice versus raw-audio access and optional API capabilities. No transcription API or third-party recording service is activated by this reference. |
| Existing AI-SlowMatch voice and relationship modules | The short local Vosk adapter is reused through project code; this does not change the chosen ChatGPT analysis model. Existing Vosk/model notices and optional-install boundaries continue to apply. New meeting-support/planning references are project-authored adaptations, not an imported absent Skill or a copy of the government publication. |

### Applying the findings to the connection loop

The following records the earlier 0.5.3 repair, not the current plugin workflow.

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

2026 年 10 月 17 日审阅。感谢上述作者与社区。本登记区分改编理念、设计参考、外部运行依赖和
当前源码中实际保留的 Sites 模板组件，引用不代表上游背书。源码中的打包致谢
`src/anti_dating_scam/licenses/open-source-credits.txt` 已同步；现有 0.5.3 EXE 的
**关于 → 显示详情**仍保留旧版致谢，只有另行重建后才会包含新增内容。

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

### 10 月 17 日插件与 Sites 迁移

| 来源、版本与许可 | 实际使用及保留声明 |
| --- | --- |
| OpenAI Sites 提供的 Vinext 模板，已安装 bundle `sites/1.0.2-remix-a.1` | 模板实际复制到 `apps/matching_site/`，包括运行／构建配置、身份辅助、脚本和附带供应商资源。本项目编写具体匹配逻辑与页面。这是实际打包源码，不只是设计参考；下方按组件记录许可，不声称整个所供模板具有同一许可。 |
| `@openai/sites-vite-plugin` `0.2.0`，文件头来源 `openai/sites#9`，MIT，版权 2026 OpenAI | [构建集成源码](../apps/matching_site/build/sites-vite-plugin.ts)实际随项目保留并由 Site 的 Vite 配置导入，[完整 MIT 声明](../apps/matching_site/build/sites-vite-plugin.LICENSE)保持不变。检查时与安装模板的 SHA-256 相同：`07af20e7097d9ed1d76f7c446d02997550b8fc5ca89668b249e25eabd62c6834`。感谢 Sites 维护者。 |
| shadcn Tailwind CSS `4.13.0`，来自同一 Sites bundle，MIT，版权 2023 shadcn | [随包样式表](../apps/matching_site/vendor/shadcn-tailwind-4.13.0.css)由 Site 全局 CSS 导入，旁边保留[完整 MIT 声明](../apps/matching_site/vendor/shadcn-tailwind-4.13.0.LICENSE.md)。与安装模板 SHA-256 一致：`bc7d83425702955b4cb67cb14ede9d603f9d912376d57a2d81d661094d2a782a`。感谢 shadcn 及贡献者。 |
| goutoujunshi，审阅版本 `6db7354a4002dc7c448a9c87ffdad8132570c9d3`，MIT | 原生插件借鉴实际读取 Skill 和记忆指南中的证据区分、暂定解释、自主选择和有限记忆方法，不复制完整提示词或记忆实现；排除必填 MBTI／评分、性别默认值和操控。两份原许可保留在 `plugins/slowmatch/licenses/`，见其[双语致谢](../plugins/slowmatch/CREDITS.md)。 |
| 已安装 `grilling` Skill，读取本地副本，不声称上游版本／许可 | 只用于开发审查，不打包，也不是面向最终用户的军师模块。没有复制实现或提示词；此处记录方法参考，不将其列为重新分发依赖。 |
| 人生方向与行动规划 | 在已审计用户及插件缓存位置未发现独立已安装 Skill。`plugins/slowmatch/skills/slowmatch/references/direction.md` 是本项目新写流程，不冒充复用了不可用的 Skill。 |
| 官方 OpenAI 插件与 Sites 文档，2026 年 10 月 17 日核对 | 参考[插件打包](https://developers.openai.com/plugins/build/plugins)、[连接／测试](https://developers.openai.com/plugins/deploy/connect-chatgpt)、[桌面分发](https://developers.openai.com/plugins/deploy/desktop-only)、[Sites 数据](https://learn.chatgpt.com/docs/sites/data-and-connections)及[分享](https://learn.chatgpt.com/docs/sites/publishing-and-sharing)，用于接口与验收边界；仅文档参考，不复制 OpenAI 客户端源码。 |

Site 依赖版本记录在其 `package.json` 与锁文件，各自许可独立适用。上述构建和供应商声明继续保留在
托管源码镜像与源码包中。原生插件与旧桌面二进制是不同产物，本次源码致谢更新不表示已重装或重建。

### 完整替代范围：行为、地点与音频参考

| 来源与核对版本 | 实际用途、许可范围与致谢 |
|---|---|
| 加拿大司法部《Making appropriate parenting arrangements in family violence cases, 2023》，2023 年 2 月摘要；作者 Jaffe、Bala、Medhekar、Scott、Oliver；[原文](https://www.justice.gc.ca/eng/rp-pr/jr/rib-reb/mpafvc-capcvf/index.html)，2026 年 10 月 17 日核对 | 仅作行为设计参考：模式／背景及差异化安全回应用于本项目自写关系支持文本。不打包报告正文、图表或代码，不声称软件许可。其家庭司法背景不是约会 AI 诊断标准，也不构成用户所在地法律结论。感谢作者与发布方。 |
| 官方 OpenAI [插件参考](https://developers.openai.com/plugins/reference)、[本机安全](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security)、[语音](https://learn.chatgpt.com/docs/features/voice)、[网页检索](https://learn.chatgpt.com/docs/web-search)及[转写 API](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create)，2026 年 10 月 17 日核对 | 仅接口／文档参考，不打包 OpenAI 软件。用于区分可选位置／文件提示、本机与云端边界、原生语音与原音频访问及可选 API 能力；参考资料不激活转写 API 或第三方录音服务。 |
| 原 AI-SlowMatch 语音与关系模块 | 通过本项目代码复用短音频本机 Vosk 适配器，不改变已选择的 ChatGPT 分析模型。旧 Vosk／模型声明及可选安装边界继续有效。新增见面支持／规划参考为本项目改编文本，不冒充导入缺失 Skill，不复制政府报告。 |

### 如何应用到本次连接循环

下方记录此前 0.5.3 修复，不描述当前插件工作流。

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
