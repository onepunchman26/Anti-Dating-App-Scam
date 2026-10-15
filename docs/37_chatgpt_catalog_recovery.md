# ChatGPT catalog recovery / ChatGPT 模型列表恢复

## English

October 14, 2026. The owner reported successful browser authorization followed by an
empty model picker and disabled chat. The previous screen hid discovery failures behind
a generic message and offered no direct catalog retry. A saved model missing from the
current catalog could also leave the activation button enabled without a valid choice.

Live, read-only checks using this application's own encrypted credential reproduced
HTTP 520 from the authenticated `GET https://api.openai.com/v1/models`. The failing
stage was model discovery, not token refresh. Both existing urllib and an independent
httpx diagnostic returned 520; changing ordinary Accept/User-Agent headers did not fix
it. The anonymous endpoint returned 401. The server-side cause is unknown: this is not
proof of a general OpenAI outage, account ineligibility or an obsolete model ID.
No credential, browser callback code, identity or provider response body is recorded.

The [official model contract](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
still specifies the OAuth bearer on `/v1/models`, visible entries from the `models`
array, `display_name` for labels and `slug` for requests. This repair keeps that contract.
It does not substitute bundled Codex models, guess available IDs or switch to paid APIs.

Version 0.5.1 adds manual **Reload models**, useful placeholders and separate safe HTTP
diagnostics. All 5xx failures are network/service failures; temporary errors preserve
authorization. A retry clears stale choices and diagnostic status. A disconnected
session loses its success badge, and activation requires an actual selected model plus
the existing extra-credit confirmation. Model discovery never sends a chat message and
does not automatically retry authorization, token rotation or inference.

94 focused checks passed: catalog failures/format validation, token protection, safe
diagnostics, empty/removed model choices, English/Chinese recovery controls, repeated
clicks, cancelled/late callbacks, and full Qt retry → selection → synthetic chat journeys.
These are synthetic model checks, not successful live inference. The authenticated
catalog remains a live external blocker; do not claim real chat has recovered until
that endpoint succeeds and a separately approved synthetic turn completes.

Full release and exact EXE identity are maintained in [current status](../CURRENT_STATUS.md).
To review: reopen the fixed root EXE, open Connect ChatGPT, and click Reload models.
If models appear, select one, confirm the app's extra credits are disabled, enter AI Chat
and click Start. A continuing HTTP 520 means model access remains unavailable; reloading
cannot guarantee service recovery. No paid workaround or automatic hourly task is added.

## 中文版

2026 年 10 月 14 日。所有者反馈浏览器授权成功后，模型选择框为空，聊天按钮不可用。
旧界面把读取模型失败简化为笼统提示，没有直接重试模型列表的入口。之前保存的模型若
已不在当前列表中，还可能导致没有有效选择时，启用按钮仍亮起。

使用本应用自己保存的加密凭据进行只读检查，复现带授权的
`GET https://api.openai.com/v1/models` 返回 HTTP 520。失败发生在模型读取，而非令牌续期。
现有 urllib 与独立 httpx 检查均返回 520；改变普通 Accept/User-Agent 请求头没有解决。
未带授权的同一接口返回 401。服务器端原因尚不明确：这不能证明 OpenAI 普遍宕机、
账号没有资格或模型 ID 过旧。没有记录凭据、浏览器回调代码、身份或服务端原始正文。

[官方模型接口规范](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
仍要求向 `/v1/models` 发送 OAuth bearer，从 `models` 数组展示可见条目，以
`display_name` 显示名称、以 `slug` 请求模型。本次保持该规范，不用内置 Codex 模型列表
冒充账号权限，不猜测可用模型 ID，也不切换至付费 API。

0.5.1 增加手动**重新加载模型**、明确的占位提示及独立的安全 HTTP 诊断。全部 5xx
归入网络／服务失败；临时错误保留授权。重试会清除过期选择及旧错误状态。连接失效时
移除成功标识；启用聊天必须实际选中可用模型，并完成原有的额外积分确认。读取模型
不会发送聊天消息，也不会自动重试登录、令牌轮换或推理。

94 项定向测试通过，覆盖列表故障／格式校验、令牌保护、安全诊断、空列表／模型移除、
中英文恢复操作、重复点击、取消／迟到回调及完整 Qt“重试 → 选择 → 合成聊天”流程。
这些属于合成模型验证，不代表真实推理成功。带账号授权的模型接口仍是外部阻碍；只有
接口恢复且另行获准的合成资料真实聊天完成，才能宣称真实聊天恢复。

完整发布结果及具体 EXE 身份以[当前交接](../CURRENT_STATUS.md)为准。人工检查时重新
打开根目录固定 EXE，进入连接 ChatGPT，点击重新加载模型。列表出现后选择模型，确认
本应用额外积分已关闭，进入 AI 聊天并点击开始。若仍显示 HTTP 520，说明模型访问尚未
恢复；重试本身不能保证服务恢复。本轮不引入付费替代方案或小时自动任务。
