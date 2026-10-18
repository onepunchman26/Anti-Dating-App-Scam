# Architecture Memory / 架构记忆

## English — authoritative direction, October 17, 2026

This document allows the next agent to continue without relying on chat memory.
The original Anti-Dating-App-Scam repository remains the authoritative AI-SlowMatch
project. Do not clone a replacement product, change the original remote, overwrite
unrelated work or place private data in source control.

The current product center is the user's ChatGPT desktop conversation, focused
plugin Skills, the existing Python local core and an authenticated Sites matching
service. The owner accepts OpenAI cloud analysis of the necessary authorized
personal information. This does not authorize Sites or other users to receive the
complete profile, raw conversations or private assessments.

```text
ChatGPT + focused Skills
  -> local Python contracts and guarded storage
  -> exact reviewed summary and separate publication approval
  -> Sites-authenticated summary storage and reciprocal discovery
  -> peer's permitted summary back to the user's own ChatGPT
  -> private interpretation saved locally
```

The local profile is the durable source for personal understanding. Claims include
sources, confirmation, time, uncertainty and corrections; unknowns stay unknown.
No founder profile supplies default answers. Profile edits, summary drafts,
publication approvals and private reports are separate objects and permissions.

Python remains useful because the project already has typed models, report
validation, guarded file I/O, evidence/history handling, memory migration and tests.
Reuse those modules. The local CLI contains no replacement model client or website
AI proxy. New local state defaults outside OneDrive and Git at
`%LOCALAPPDATA%/AI-SlowMatch/work`; paths must be resolved and checked. Existing
vaults are not scanned or relocated automatically. State is plaintext unless a
specific artifact explicitly implements encryption.

Sites uses its supported Worker/D1 runtime. A Python/FastAPI server cannot be
assumed deployable unchanged. A small hosted implementation is justified by the new
summary-only service; it does not replace the Python core or create another primary
chat application. Server ownership comes from Sites-verified request identity,
never a tool argument. Every response respects active visibility and reciprocal
conditions. Candidate labels are untrusted data, not authority to read or upload.

The original source tree owns `apps/matching_site/`. Sites' required hosted source
repository is a one-way deployment mirror. Record exact source/deployment versions;
make source changes here and synchronize deliberately. Runtime files, credentials,
private profiles and synthetic test identities never become production seed users.

The fixed 0.5.3 `AI-SlowMatch.exe` was validated before this migration and remains
the recovery/legacy entry. Its release evidence stays intact. Version 0.6.0 refers
to new source unless a separate build receipt proves an EXE replacement. PySide6
remains a utility shell; FastAPI remains optional. Tauri, a second desktop chat
client, Ollama default inference and federation are not first-version migration
work. Earlier design records preserve their history, not active requirements.

JSON/Pydantic contracts remain the interchange boundary. Validate before saving,
exporting, signing or displaying trusted report data. An approval digest verifies
content equality; it is not a signature or proof that a person consented. A digital
signature can establish integrity under a trusted key, but cannot prove source
authenticity, completeness, wrongdoing, truthful preferences or relationship safety.
Encryption protects confidentiality and is separate from validation and signing.
Do not turn private reflection into a diagnosis, morality label or precise match score.

Verification must distinguish source implementation, installed Skill discovery,
local process persistence, hosted deployment, live MCP connection and independent
account acceptance. Native Codex Skill loading is one observed channel; it does not
prove desktop Work or other-user distribution. A generated ZIP is a source/package
artifact until installed. A private Site registration is not a live service.
Current evidence and unresolved external prerequisites belong in
`CURRENT_STATUS.md` and `PROGRESS_TRACKER.md`.

## 中文版 — 2026 年 10 月 17 日权威方向

本文让下一位 agent 不依赖聊天记忆即可继续。原 Anti-Dating-App-Scam 仓库继续作为
AI-SlowMatch 权威项目，不克隆替代产品、不更换原远端、不覆盖他人修改，也不把私人数据放进源码控制。

当前产品核心是用户自己的 ChatGPT 桌面对话、按需插件 Skills、既有 Python 本机核心和经过认证的
Sites 匹配服务。所有者接受 OpenAI 云端分析任务所需且已授权的个人信息；这不授权 Sites 或其他人
获取完整档案、原始聊天或私人报告。

上方流程为：ChatGPT 与按需 Skills 调用本机 Python 结构和受保护存储，生成并展示准确摘要，
另行获得发布批准后交给 Sites 身份验证、摘要保存和双向发现。候选获准摘要返回本人 ChatGPT，
私密解读仍保存本机。

本机档案是持续理解本人的资料来源。判断包含来源、确认、时间、不确定性和纠正，未知仍标为未知。
不把创始人档案当成默认答案。档案更新、摘要草稿、发布批准与私人报告是不同对象和许可。

项目已有类型化结构、报告校验、受保护文件读写、证据／历史处理、记忆迁移与测试，因此继续复用
Python。本机 CLI 不建立替代模型客户端或网站 AI 代理。新状态默认在 OneDrive 和 Git 之外的
`%LOCALAPPDATA%/AI-SlowMatch/work`，必须解析并检查路径。不会自动扫描或搬迁旧资料库。
除特定产物明确实现加密外，本机状态为明文。

Sites 使用实际支持的 Worker/D1，不能假设原 Python/FastAPI 服务可直接部署。为摘要服务实现
小型托管部分是本次方向所需，不替换 Python 核心，也不形成另一个主聊天产品。服务端所有权来自
Sites 验证身份，不能来自工具参数。每次返回均遵守当前可见范围与双方条件；候选标签是不可信数据，
不能授权读取或上传。

原源码树管理 `apps/matching_site/`，Sites 要求的托管源码仓库只是单向部署镜像。记录准确源码
与部署版本，在原仓库修改后明确同步。运行文件、凭据、私人档案和合成测试身份不得成为生产种子用户。

固定的 0.5.3 `AI-SlowMatch.exe` 在迁移前已验证，继续作为恢复／旧功能入口，保留发布证据。
除非另有构建证明替换了 EXE，0.6.0 仅指新源码。PySide6 保留为工具界面，FastAPI 保持可选。
Tauri、第二套桌面聊天客户端、默认 Ollama 推理及联邦化不属于首版迁移。旧决策记录保留历史，
不再充当冲突路线的现行要求。

JSON/Pydantic 继续定义交互边界，保存、导出、签名或作为可信报告展示前必须校验。批准摘要哈希
仅证明内容相同，不是签名或本人同意证明。数字签名可在信任密钥前提下证明完整性，不能证明来源真实、
完整、存在不当行为、偏好诚实或关系安全。加密保护机密性，与校验／签名不同。不把私人反思变成诊断、
道德标签或精确匹配分。

验收必须区分源码实现、Skill 安装发现、本机进程持续性、托管部署、真实 MCP 连接和独立账号使用。
原生 Codex 的 Skill 加载只证明该通道，不证明桌面 Work 或其他用户分发。ZIP 在安装前只是源码／
打包产物，登记私密 Site 不等于服务上线。最新证据与外部前提缺口记录在 `CURRENT_STATUS.md`
和 `PROGRESS_TRACKER.md`。
