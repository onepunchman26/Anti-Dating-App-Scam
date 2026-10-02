# Current handoff / 当前交接

## English

October 2, 2026. The autonomous implementation of the new chat/personal-model request
is complete. **Open root `AI-SlowMatch.exe` (0.3.0)**. Physical voice and subjective
owner acceptance remain open in [Owner review](OWNER_REVIEW.md). Hourly automation
`ai-slowmatch` remains PAUSED; work resumes only on the owner's instruction.

The app now connects typed or reviewed local speech input to the selected ChatGPT
cloud model, retrieves bounded relevant approved context, displays a useful response,
offers optional interruptible local speech, and evaluates personal-model updates.
The authoritative bilingual [Skill v2](src/anti_dating_scam/skills/relationship-reflection/SKILL.md)
is loaded into actual requests and verified inside the EXE. The existing Python core,
PySide interface and local memory store are retained; no second database was added.

Personal-model candidates show exact user quotes, context, inference/report origin,
alternatives and uncertainty. Every item needs approval before persistence. Inspect,
correct, question, reject, export or delete items in My approved notes. Changes clear
dependent interpretations and invalidate stale replies/evaluations. Revision locking,
idempotency and selected-folder isolation are enforced in code. Session-only mode
ignores the saved model, including after a language change. No update is valid; a
malformed proposal does not discard an otherwise valid conversational response.

The frozen-source release passed **2,187 tests, 10 skips** and one upstream deprecation
warning, plus compilation, lint, module/resource/native dependency checks and isolated
startup. Native Computer Use verified the packaged startup and About identity. Build
`592e04a53b9c4eb38e489e492f589a4d` uses source commit `2dc8cc85dd0d`; subsequent commits record
acceptance/docs only. SHA-256: `f96704093b5b40a1a39c2b23cfc780fd31f1f0d3165182bda6548cc6716e4437`.
Full local receipts are in `releases/current.json` and the corresponding build archive.
There is one root EXE. Verified older releases remain available for rollback. The
honest development/dirty flag includes original untracked `.vscode/` and `paper/`;
those folders are neither included in snapshots nor uploaded.

New live tests used synthetic data and the authorized ChatGPT plan with extra credits
disabled: **14 accepted service calls**, plus one direct diagnostic response, used
GPT-5.6-Luna with matching known requested/reported IDs. They covered first motivation,
uncertain ideals, self-description versus a reported action, approved context in a
returning session, childhood without assumed causality, corrections, no update,
financial pressure and session-only behavior. An early sample repeated earlier advice;
the Skill was tightened and targeted final checks addressed only the latest concern.
One later service attempt failed without a retained raw reply, so its cause remains
unclassified; later diagnostics succeeded. This is bounded sample evidence, not a
claim of universal reliability. [Sanitized receipt](docs/evidence/2026-10-02-evolving-model.json).
The earlier successful portrait/encrypted exchange/comparison samples remain in
[the prior receipt](docs/evidence/2026-10-02-chatgpt-plan.json).

Actual offline English Vosk recognition of generated synthetic speech passed separately;
that optional downloaded-model check is skipped in the isolated source build. Native
UI checks observed English SAPI Speaking/Finished states and the missing-Chinese-voice
fallback. The environment reports **0 microphones, 1 output device, English/Spanish
SAPI voices and no Chinese voice**. Physical capture, spoken-Chinese accuracy and
actual audibility still require the owner's device. Automated interruption tests do
not establish human listening quality. Missing hardware never produces simulated success.

Local chat/portrait/model storage is unencrypted; sharing attachments alone are
authenticated-encrypted. Deletion clears this model and its dependents, not earlier
cloud disclosures, independent saved sessions/reports, exports or external backups.
No private backup or automatic restoration exists. Development source/Git backups
are verified by restoration outside the checkout. Old-copy cleanup was deferred
safely during this release; older verified copies remain rather than being forced away.
Source and bilingual handoff are delivered on GitHub branch `codex/standards-correction`.
No purchases, paid API keys, real private archives, emails or public deployment were used.

[Progress](PROGRESS_TRACKER.md) · [Approved scope](PLAN_FOR_ONEPUCHMAN.md) ·
[Architecture/storage limits](docs/32_standards_correction.md) · [Build/recovery](packaging/README.md).

## 中文版

2026 年 10 月 2 日。本次聊天／个人模型请求中可自主完成的实现已完成。
**打开根目录 `AI-SlowMatch.exe`（0.3.0）**。实体语音及主观实用性仍需按
[所有者审阅](OWNER_REVIEW.md)验收。小时任务 `ai-slowmatch` 保持 PAUSED，下一轮由所有者发出指令启动。

现在应用可以将打字或经核对的本地语音输入交给所选 ChatGPT 云端模型，检索有限的相关
已批准背景，显示有效回复，按需本机朗读并随时打断，同时评估个人模型更新。
权威双语 [Skill v2](src/anti_dating_scam/skills/relationship-reflection/SKILL.md)
真正加载进请求，并已核验包含在 EXE 中。沿用 Python 核心、PySide 界面及现有记忆存储，
没有第二套数据库。

候选展示准确原话、情境、自述／AI 推断类别、其他解释和不确定性，每条明确批准才保存。
在“我批准的记忆”中可查看、纠正、质疑、拒绝、导出或删除。变更联动清理依赖解释，使旧
回复／候选失效；版本锁、幂等及按选定文件夹隔离由代码执行。“仅本次会话”忽略已存模型，
切换语言后仍保持。无需更新是有效结果；候选不合格不会丢弃原本有效的聊天回复。

冻结源码发布通过 **2,187 项测试、10 项跳过**，有一项上游弃用警告；编译、静态检查、
模块／资源／原生依赖及隔离启动均通过。原生 Computer Use 核验了打包程序启动及“关于”
身份。构建编号 `592e04a53b9c4eb38e489e492f589a4d`，源码提交 `2dc8cc85dd0d`，
后续提交仅记录验收／文档。SHA-256：`f96704093b5b40a1a39c2b23cfc780fd31f1f0d3165182bda6548cc6716e4437`。
完整本地记录见 `releases/current.json` 及对应构建归档。根目录仅一个 EXE，旧的已验证
版本可供回滚。开发／脏工作区标记如实包含原有 `.vscode/` 和 `paper/` 未跟踪目录；
这两个目录未进入快照，也未上传。

本轮真实测试只用合成资料，使用已授权且关闭额外积分的 ChatGPT 套餐：**14 次服务调用
获接纳**，另一次直接诊断回复。使用 GPT-5.6-Luna，已知请求／返回标识一致，覆盖初次
动机、理想不明、自述与单次行为、返回会话中的批准背景、童年非自动因果、纠正、无更新、
金钱压力及仅本次会话。较早样本重复了之前的建议，已收紧 Skill，最终定向检查只回答最新
问题。另一次后续服务请求失败且未保留原始回复，因此尚未归因；后续诊断成功。这是有限
样本依据，不是普遍可靠性保证。[脱敏记录](docs/evidence/2026-10-02-evolving-model.json)。
此前画像／加密交换／比较的成功样本仍保存在[上一份记录](docs/evidence/2026-10-02-chatgpt-plan.json)。

真实离线英文 Vosk 已单独识别生成的合成语音；隔离源码构建不带下载模型，所以跳过该
可选检查。原生界面看到英文 SAPI 朗读／完成状态，以及缺少中文声音时的提示。
环境检测到 **0 个麦克风、1 个输出设备、英语／西语 SAPI 声音，没有中文声音**。
实体录音、中文口述准确性及实际可听效果仍需所有者设备。自动停止测试不能代替人的听感
验收；缺设备时不会制造模拟成功。

本地聊天／画像／模型仍未加密，只有分享附件使用带完整性保护的加密。删除清理本模型及
依赖项，不会抹除之前云端披露、独立会话／报告、导出或外部备份；没有私人自动备份或自动
恢复。开发源码／Git 备份在仓库之外经恢复核验。本次发布安全地暂缓了旧副本清理，继续
保留已验证旧副本，没有强行移除。源码和双语交接交付到 GitHub 的
`codex/standards-correction` 分支。未购买服务、使用付费 API key、读取真实私人档案、
发送邮件或公开部署。

[进度](PROGRESS_TRACKER.md) · [批准范围](PLAN_FOR_ONEPUCHMAN.md) ·
[架构及存储限制](docs/32_standards_correction.md) · [构建与恢复](packaging/README.md)。
