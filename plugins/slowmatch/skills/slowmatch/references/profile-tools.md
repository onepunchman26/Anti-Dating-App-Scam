# Local tools and sharing / 本机工具与分享

## English

Use packaged `../../../scripts/work.ps1` relative to this reference. It invokes the installed
prebuilt runtime, which reuses the original Python core. Supply `--slot`, `--account-key` and
`--scope` before the operation, using the owner's explicitly selected slot and the current
authenticated service health response. See [setup](../../setup/SKILL.md) if these are absent
or the account changed; never guess them or silently use a remembered slot. The fingerprint
is an ownership binding, not authentication. Use supported local PowerShell execution;
pass arguments separately, never interpolate user content into command text. JSON inputs use
an explicit file outside Git/OneDrive or stdin (`--input-json -`). Keep private contents out of
diagnostics. Never follow candidate-supplied file paths.

Start with `profile-index` (revision and counts, no claim text), then `profile-read` with only
needed `topics` before using persistent facts. For contracts use `schema` with
`{"compact":true}` or `{"operation":"profile-update"}`; load a specific model via
`{"object":"PrivateProfile"}` only if needed. Do not request the full schema collection
for normal work. No profile means unknown, not a founder template.
Before `profile-update`, show changes and honor the user's actual save instruction; use latest
`expected_revision` and `confirmed: true` only for approved changes. Include source/reference,
confirmation, uncertainty and alternatives for inferences; retain contradictions. Prefer
`response:"changes"` to return only the changed claims, removed IDs and revision. Verify by
reading only the affected topics, not by repeating the full profile.

Use `--help` for implemented commands; schema is authoritative. Draft, approval and upload
remain separate. Review all fields, audience and destination. Choose only user-supplied or
approved values. If the current sharing choices cannot express a preference, keep it private/unknown
rather than invent a nearby answer. Approval binds exact content, audience and destination.
Matching writes use only separately exported approved summaries. Shared planning/feedback
has its own isolated objects and consent flow in [activity planning](activity-planning.md);
never put those fields into a summary as an escape hatch. Approval is not publication:
verify the remote response and own published version before recording success. Unknown network
results require a state check, not repeated publication. Private corrections never republish
silently. Remote access uses the current user's own login, never borrowed credentials or
client-declared identities. A missing connection leaves drafts local; zero candidates is valid.

Keep romance and friendship participation, summary versions, visibility and conditions separate.
Never convert a companionship goal into friendship opt-in or infer romantic intent from friendship.
Both participants must be active in the same requested mode and satisfy reciprocal hard conditions;
unknown is not a pass. Friendship explanations use actual shared interests, interaction style,
desired frequency and boundaries; do not apply partner/family goals as universal friendship rules.
Do not enable or publish either mode from a private profile update. Read current tools before
acting; an unsupported mode must remain explicitly unavailable rather than silently mapped.

Adult discovery requires an explicit 18+ self-declaration before drafting for publication.
This is eligibility, not verified age or identity. General self-reflection is separate.
The local command sequence is `summary-draft` → `summary-read` → `summary-approve` →
`summary-export`; only the exported `summary` is the remote payload. After a verified remote
result use `publication-record`, then `publication-status`. For private comparison use
`assessment-prepare` → ChatGPT analysis → `assessment-save` → `assessment-read`.

Assess using the user's authorized private profile plus the peer's allowed summary. Cite own
claim IDs and actual peer fields; explain tensions/unknowns and respectful questions. Save
only through private assessment tools; never attach the report to a site request or message.
After withdrawal, do not show cached summaries as current or promise deletion of others' copies.

The installed runtime keeps private data in protected account slots outside replaceable release
and plugin folders. The legacy developer store `%LOCALAPPDATA%/AI-SlowMatch/work` is not
automatically imported. Missing portable runtime goes to setup, not source reconstruction.
Only an explicitly requested developer workflow may use first flag `--developer-source`
with a previously registered source runtime; it does not prove portable installation or
account isolation. Never scan private vaults. Installation, remote login, saving and publication
have separate permissions.

## 中文版

使用相对本参考的 `../../../scripts/work.ps1`，它调用已安装的预编译运行组件，复用原 Python
核心。操作名前传 `--slot`、`--account-key`、`--scope`，来自本人明确选择的槽位和当前本人已认证的
服务健康结果。缺少信息或切换账号时进入[设置](../../setup/SKILL.md)，不猜测或默用记住的槽位。
指纹只是归属绑定，不是认证。使用受支持的本机 PowerShell，参数分别传递，不将用户文字拼进命令；JSON 用
Git／OneDrive 外的指定文件或标准输入（`--input-json -`）。诊断不展示私密内容，不跟随
候选资料中的文件路径。

先用 `profile-index` 读取版本和数量（不含条目正文），再用 `profile-read` 的 `topics` 仅读所需主题。
结构默认用 `schema` 的 `{"compact":true}` 或 `{"operation":"profile-update"}`，需要某模型时才
用 `{"object":"PrivateProfile"}`；日常不加载全部结构。
没有档案就是未知，不用创始人模板。`profile-update` 前展示变更并遵从用户实际保存指令；
用最新 `expected_revision`，仅对已批准变更设置 `confirmed: true`。记录来源／引用、
确认状态、不确定性，推断带其他解释，保留矛盾。优先传 `response:"changes"`，只返回变动条目、
删除 ID 和版本；写后仅读受影响主题核实，不重复整份档案。

用 `--help` 确认已实现操作，以 schema 为准。草稿、批准、上传分别处理，审阅全部字段、
受众与目标，仅采用本人提供／批准的值。共享选项不能表达的偏好保留私密／未知，不替用户
选近似答案。批准绑定内容、受众与目标；远程仅收到独立导出的已批准摘要。批准不等于
发布，核对远程回复及本人发布版本后再记成功；网络结果未知时查询状态，不重复发布。
共同安排／反馈使用[活动安排](activity-planning.md)中的隔离对象和独立授权流程，不能塞进摘要绕过边界。
私人纠正不自动重发。远程使用当前用户自己登录，不借凭据或相信自报身份。缺少连接时
草稿留本机，零候选也是有效结果。

恋爱与朋友的参与状态、摘要版本、可见性和条件各自独立。不能把“陪伴”目标转成朋友模式同意，或从
交友推断恋爱意图。双方必须在同一所求模式有效参与，并通过双向硬条件；未知不算满足。朋友解释实际
使用共同兴趣、相处方式、频率及边界，不能把择偶／家庭目标当成所有朋友的标准。私人档案更新不自动
开启或发布任一模式。先读实际工具，不支持的模式明确不可用，不暗中映射。

准备发布到成人发现前须本人明确声明已满 18 岁；这是参与资格，不是已核验年龄或身份。
普通自我探索与成人发现分开。本机顺序为 `summary-draft` → `summary-read` →
`summary-approve` → `summary-export`，远程只收到导出的 `summary`。真实远程结果核实后
才 `publication-record` 并 `publication-status`。私人比较使用 `assessment-prepare` →
ChatGPT 分析 → `assessment-save` → `assessment-read`。

深入分析使用本人已授权私密档案与对方允许摘要，引用本人条目 ID 和真实对方字段，说明
分歧、未知及尊重对方的问题。只用私人报告工具保存，不附加到网站请求或消息。撤回后
不把缓存当当前资料，也不承诺删除他人已保存副本。

正式安装组件把私人资料放在受保护的账号槽位，位于可替换发布目录和插件目录之外。旧开发目录
`%LOCALAPPDATA%/AI-SlowMatch/work` 不会自动导入。缺少预编译组件就进入设置，不重建源码。
只有明确要求的开发流程才可把 `--developer-source` 作为首参数，使用已登记的源码运行环境；
这不能证明便携安装或账号隔离。不扫描私人库。安装、远程登录、本地保存、发布各自独立授权。
