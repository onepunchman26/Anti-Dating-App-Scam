# Site UI acceptance / 网站界面验收

## October 23 setup layout correction / 10月23日首次设置布局修正

English: The owner's screenshot correction is implemented in the original Site source.
The start page first asks whether ChatGPT is installed. Existing users continue directly
to the pinned Codex instruction; new users see the official download followed by an explicit
installed/continue action. Download and next-step controls share 15px type, weight 600 and
46px minimum height. SlowMatch's existing-user launch link remains in a compact disclosure.
The three social shortcuts now appear at the top of Friends & groups. They open discovery,
focus the add-friend section, or focus groups; without an ID, the last two focus ID setup.
No identity, consent, private-storage or service behavior changed. The Windows release
remains 0.8.6; this delivery updates the hosted Site, not the installed EXE's bundled UI.

Actual local Chrome checks: both setup branches, backward navigation, successful clipboard
copy/readback of the pinned v0.8.6 guide, language switching retaining the install step,
and all three social destinations. Social checks used an isolated synthetic fixture with
no hosted writes or real private data. English/Chinese setup screens at 390px had no horizontal
overflow; 1440px desktop layout was inspected. See [start screenshot](evidence/onboarding/start-zh.jpg).
Copy now has a two-second bound and reveals selectable instructions on failure; failure
fallback is implemented but was not forced in the browser. TypeScript and production build
passed, Node suite 52 passed, Python 2,637 passed / 11 skipped, source compilation passed.
Independent-account installation remains untested. Deployment receipt is in CURRENT_STATUS.

中文版：已按所有者截图反馈修改原网站源码。初始页面先询问是否安装 ChatGPT；已安装者直接进入
固定版本的 Codex 安装指令，未安装者先看到官方下载，再由本人点击“已安装完成，下一步”。
下载与下一步按钮统一为15px字号、600字重和46px最小高度。已有 SlowMatch 用户的启动入口保留在
简短折叠区。三个社交入口现位于好友与群组页顶部，分别打开发现、定位添加好友区和群组区；
尚无 ID 时，后两者定位到 ID 设置。身份、授权、私人存储及服务行为未改变。
Windows 发行版仍为0.8.6，本次交付更新托管网站，不代表已安装EXE内的界面重新打包。

本机 Chrome 实测：两条设置路径、返回上一步、复制并回读指向v0.8.6指南的安装指令、切换语言保留
安装步骤，以及三个社交目的地。社交操作使用隔离的合成测试数据，没有写入线上或读取真实私人资料。
390px中英文设置页无横向溢出，1440px桌面布局已检查；见上述首页截图。复制增加两秒等待上限，
失败时展开可选择的指令；失败降级已实现，本次未在浏览器强制触发。
TypeScript和生产构建通过，Node 52项通过，Python 2,637通过／11跳过，源码编译通过。
独立账号安装仍未实测。部署回执见CURRENT_STATUS。

## English

Revision: October 18, 2026. Authority: the owner-adopted
`Codex_Site_UI_Bilingual_Design_Addendum.md` from “整合Skills与界面”.
Original checkout/remote verified at `2d21f43`; work is on
`codex/sites-ui-language`. The existing private Site is the destination.
This is a UI revision over service 0.8.0 / protocol 1.0, not a new Windows binary.

### Audit and implementation

| Module | Observed evidence before modification | Reuse/change | Acceptance |
|---|---|---|---|
| Existing deployed version 6 | Owner-authenticated page mixed English and Chinese, with a long marketing section above every workspace action | Same application, authentication and audience; concise signed-out landing and signed-in workspace | Actual browser plus post-deploy read checks |
| Matching and shared profile | Real API, exact-content approval, current revision, pause/delete and reciprocal matching already present | Reuse all contracts; compact cards, expandable details, filters over returned results and separate profile page | Local D1-backed browser reads, publish and pause/resume |
| Planning | Preferences, proposals, per-participant confirmation, withdrawal and selected feedback already connected | Comparable options, source disclosures, explicit preference vs plan-confirmation status | Real local service fixture through browser; no hosted writes |
| Language | Flat bilingual enum labels and inline mixed copy; no selector | Central paired resources, same component tree, language cookie and server-selected initial text | Both languages, preserved UI state and unchanged API counts |
| Independent accounts | No second controlled account available | Preserve this limitation | NOT EXERCISED |

The visual system uses warm white, berry buttons, consistent spacing and clear focus.
Navigation separates Discover, Plans together and Shared profile. Help contains installation,
privacy and connection diagnostics. The start link resolves to the original
[short installation guide](../INSTALL_WITH_CHATGPT.md).
User-authored names/places stay original; currency and meeting instants are not converted.
Public-facing fields and approval boundaries are unchanged. The full warning remains on
summary approval and initial plan creation, with visible short reminders and expandable
detail elsewhere. No private profile, biography field, score, recording or messaging tool was added.

Observed bugs corrected during QA: the old summary field continued to say enabled after
discovery was paused; it now uses current server visibility. Expired and withdrawn sharing
have distinct states. Activity card labels match the option selector, and each participant's
preference approval is distinguished from their exact plan-version confirmation.

### Verification performed

- Python source compilation passed; full regression: **2,549 passed, 11 skipped**, one existing
  Starlette/httpx deprecation warning. No inference, paid service or real private archive used.
- Existing Node/D1 suite: **25 passed**; language resource/preference/component checks:
  **3 passed**. TypeScript passed. Production build and packaging results are recorded below.
- Actual local browser checks at **360, 768 and 1440 CSS pixels**, in English and Simplified
  Chinese: landing, discovery, shared profile and planning. No horizontal overflow was found.
- Same synthetic fixtures used for language comparisons. The proxy uses the real application
  and existing D1 service; identity is explicitly synthetic. It is excluded from deployment.
- Changing language preserved mode, region/interest filters, an expanded candidate, summary
  file, local preview and approval checkbox. API log remained exactly the same two entries
  (read summary, find candidates). Planning also preserved the selected option, open review,
  preference file and consent with **zero additional API calls**.
- Summary local preview did not upload. Explicit publish saved version 2; this appropriately
  invalidated the old plan in that mode. Other-mode planning stayed separate.
- Browser exercised plan list/read, the caller's exact-version confirmation, selected-feedback
  publication, feedback withdrawal and full plan withdrawal. Each used real local D1 behavior.
  This does not claim every hosted mutation or every error path was exercised.
- Invalid/private-field summary rejected locally; error text is localized. Pause/resume readback
  showed consistent current visibility. Field preview and source disclosures remained usable.
- Refresh recovered the saved language; title and `html.lang` updated. Keyboard Tab reached
  sign-in with a visible berry focus outline. The measured landing text contrast check covered
  28 visible text elements with no failures (minimum 5.03:1). This is not a full WCAG certification.
- Denied-cookie fallback is implemented as in-session state; a browser with storage blocked
  was not separately available. Full screen-reader/device-microphone testing is not claimed.

### Browser captures

These are actual screenshots from the local, synthetic test service, not actual matched people.
The owner-private hosted Site may correctly show no shared profiles.

| English | 中文 |
|---|---|
| [Desktop discovery](images/site-ui-discover-en-desktop.png) | [桌面发现页](images/site-ui-discover-zh-desktop.png) |
| [Mobile discovery](images/site-ui-discover-en-mobile.png) | [手机发现页](images/site-ui-discover-zh-mobile.png) |
| [Landing](images/site-ui-home-en.png) | [首页](images/site-ui-home-zh.png) |

### Deployment and remaining gates

Deployment: **saved version 7 succeeded** at the [same private URL](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site).
Hosting source: `4b3ef648a7e3ffcfbcfbdbe0e493897dbbf53c2f`; original implementation:
`e4d6f065e911b44dfe9215c98c00e4cb1960c346`. Environment revision 1 and owner-only access
revision 1 are unchanged. The archive, version and sanitized results are in the
[deployment receipt](evidence/2026-10-18-site-ui.json). Version 6 remains a rollback point.
Final TypeScript, localization checks, supported production build and source packaging passed.
The Windows npm shim initially failed path resolution; an isolated build-only wrapper invoked
the existing official npm CLI. No dependency, system policy or user installer was changed.
After deployment the actual browser passed English/Chinese switching, refresh persistence,
both-mode empty summary reads, an empty plan read and service diagnostics. Deployed discovery
also passed both languages at 360/768/1440 with no horizontal overflow or browser errors.
The existing installed native plugin made a real authenticated read-only health call:
0.8.0 / 1.0, controlled test, access enabled, database read passed. Hosted publication and
cross-account operations were not performed.
Windows v0.8.0 release files and the legacy 0.5.3 EXE remain unchanged.
No second independent account is available: independent installation, reciprocal hosted
publication and cross-account confirmation remain **NOT EXERCISED**. No access grant,
impersonation or invitation was made to simulate them. Existing automation stays paused.

## 中文版

修订日期：2026 年 10 月 18 日。权威为所有者采用的“整合Skills与界面”中
`Codex_Site_UI_Bilingual_Design_Addendum.md`。原目录和远端核对至 `2d21f43`，
修改在 `codex/sites-ui-language` 分支进行，目标仍为原私有站。
本次是在服务 0.8.0／协议 1.0 上的界面修订，不是新的 Windows 程序。

### 审计与实现

| 模块 | 修改前实际证据 | 复用或改造 | 验收 |
|---|---|---|---|
| 已部署第 6 版 | 所有者已登录页面中英混排，工作区上方有很长介绍 | 同一应用、认证和访问范围；精简未登录首页与登录工作区 | 实际浏览器及部署后读取 |
| 匹配与共享资料 | 已有真实接口、具体内容批准、当前版本、暂停／删除及双向匹配 | 保留契约；简洁卡片、可展开详情、仅筛选已返回结果及独立资料页 | 本机 D1 浏览器读取、发布及暂停／恢复 |
| 共同计划 | 偏好、提案、各自确认、撤回与选定反馈已连接 | 可比较选项、展开来源，清楚区分偏好批准与计划确认 | 浏览器连接真实本机服务设施，无托管写入 |
| 语言 | 平面双语枚举和行内混排，没有选择器 | 集中文字资源、同一组件树、语言 Cookie 与服务端初始语言 | 双语状态保留及接口调用数不变 |
| 独立账号 | 没有第二个可控账号 | 保留限制 | 尚未实测 |

视觉使用暖白、莓紫按钮、统一间距和清楚焦点。“发现／共同计划／共享资料”各有入口；
帮助中保留安装、隐私与连接诊断。开始链接指向原项目[短安装指引](../INSTALL_WITH_CHATGPT.md)。
用户写入的名字与地点保持原文，不转换币种或见面时刻；允许共享字段和批准边界不变。
完整提醒保留在摘要批准及首次建立计划处，其他位置显示短提醒并可展开详情。
没有新增私人档案、传记字段、评分、录音或自动发送工具。

验收中修复了原有问题：暂停匹配后摘要字段仍显示启用，现在使用服务返回的当前可见性，
并区分到期与撤回。活动卡片标识与选择器一致，分别显示每位参与者的偏好批准及对具体
计划版本的确认，避免将两种状态混淆。

### 已执行验证

- Python 源码编译通过；完整回归 **2,549 项通过、11 项跳过**，一条既有 Starlette/httpx
  弃用提示。没有调用推理或付费服务，没有读取真实私人档案。
- 原 Node／D1 **25 项通过**，新增语言资源／偏好／组件检查 **3 项通过**；TypeScript
  通过。生产构建与打包结果见下方。
- 实际本机浏览器在中英两种语言下检查首页、发现、共享资料和计划，宽度为
  **360、768、1440 CSS 像素**，未发现横向溢出。
- 双语对照使用同一组合成资料，代理连接真实应用和原 D1 服务，身份明确为合成身份；
  此测试代理被部署白名单排除。
- 切换语言后保留模式、地区／兴趣筛选、展开的候选、摘要文件、本机预览与批准勾选。
  接口日志仍只有原来的两条（读取摘要、查找候选）。计划中的选项、展开审阅、偏好文件
  和批准同样保留，**没有新增接口调用**。
- 摘要预览没有上传；明确点击发布后保存版本 2，并按原规则使当前模式旧计划失效，
  另一模式计划保持独立。
- 浏览器实际执行计划列表／读取、本人对具体版本的确认、选定反馈分享、反馈撤回和
  完整计划撤回，均连接真实本机 D1。此结果不代表所有托管写入或错误分支都已实测。
- 含不允许私人字段的摘要在本机被拒绝，错误文案可切换语言；暂停／恢复重读显示一致，
  文件预览与来源展开可用。
- 刷新恢复已保存语言，页面标题与 `html.lang` 随之变化。键盘 Tab 到达登录链接时有
  可见莓紫焦点。首页 28 个可见文字元素的实测对比度检查无失败，最低 5.03:1，
  不宣称通过完整 WCAG 认证。
- 已实现 Cookie 被拒绝时保留当前会话语言，但没有另行取得阻止存储的浏览器环境；
  不宣称已完成完整读屏软件或实体麦克风验收。

### 浏览器截图

上表链接均来自实际本机合成测试服务，不是真实匹配用户；所有者私有站没有共享资料时，
正确显示空状态。

### 部署与剩余事项

部署状态：**第 7 版已成功发布**至[原私有网址](https://slowmatch-private-pilot.fizzydeer7.chatgpt.site)。
托管源码 `4b3ef648a7e3ffcfbcfbdbe0e493897dbbf53c2f`，原项目实现提交
`e4d6f065e911b44dfe9215c98c00e4cb1960c346`，环境版本 1 和所有者私有访问版本 1 不变。
归档、版本及脱敏结果见[部署回执](evidence/2026-10-18-site-ui.json)，第 6 版保留为回退点。
最终 TypeScript、语言检查、受支持生产构建和源码打包均通过。Windows npm 包装命令初次
路径解析失败，以隔离的构建专用包装器调用已有官方 npm CLI 后通过，没有更改依赖、系统策略
或普通用户安装程序。
部署后真实浏览器通过中英切换、刷新保持语言、双模式空摘要读取、空计划读取及连接自检；
线上发现页也在双语 360／768／1440 下无横向溢出，浏览器没有错误。当前已安装的原生插件
实际完成本人认证的只读健康调用，确认 0.8.0／1.0、受控范围、访问启用及数据库读取通过。
没有进行线上发布资料或跨账号操作。
Windows v0.8.0 发布文件及旧 0.5.3 EXE 保持不变。
目前没有第二独立账号，其独立安装、双方托管发布与跨账号确认仍为**尚未实测**。
没有扩大授权、冒充账号或邀请他人来替代验收，已有自动化保持暂停。
