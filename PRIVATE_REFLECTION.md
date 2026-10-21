# Private relationship support / 私人关系支持

## English

In the local assistant, connect your existing account and private space. Choose
**Help with a relationship**, **Before a meeting**, **Help right now**, **Reflecting on
an interaction**, or **Life direction and next steps**, then start a conversation.
These routes provide help without a dating interview or the other person's permission.
You choose whether to send each message. No messages are sent to the other person.

To keep a reflection, open **Your private reflection** below the conversation:

1. Select the conversation, review the OpenAI disclosure and choose **Draft a reflection**.
   Only its last 20 messages, at most 20,000 characters, are supplied. Other sessions,
   files and your private profile are excluded. This uses your selected authorized model;
   reading, editing, saving and deleting use no model calls.
2. Review original quotations, tentative explanations, alternatives, feelings, unknowns,
   boundaries and optional actions. Quotations must occur in your supplied words; that
   does not verify the events or prove that an interpretation follows. You can edit the
   interpretation and choose a different concern/action. It is not a personality diagnosis.
3. Confirm the wording and save. An unsaved draft is discarded when the page closes.
   Saving a reflection does not update your profile, publish a summary, inform a friend
   or change a group plan. Those remain separate choices.
4. **Read my saved reflections** reopens the local records. Correct and save another
   version, or explicitly delete its content. Revision history contains operation/time
   metadata, not previous report wording. A stale save is rejected; re-read before retrying.
5. **Use these reviewed notes in my next message** starts a separate reflection
   conversation and fills a bounded message draft. Review and explicitly send it to use
   it with OpenAI. It does not silently become a verified fact in your personal profile.

The existing account-owned `relationship-support/state.json` service stores these records
outside Git, OneDrive, install folders and Sites. Local storage is not encrypted by this
feature. Deleting a reflection does not delete its source conversation, prior cloud
processing or copies exported elsewhere. No microphone, recording, monitoring or emergency
response is activated. Text help remains available without audio or joining discovery.

For setup use [the pinned installation entry](SETUP_WITH_CODEX.md). Current delivery and
real test limits are in [CURRENT_STATUS.md](CURRENT_STATUS.md); preserving the original
product requirements is tracked in [PRODUCT_CONTINUITY.md](PRODUCT_CONTINUITY.md).

## 中文版

打开本机助手，连接已有账号与私人空间。选择**关系中的困惑与支持**、**见面前准备**、
**相处中即时求助**、**相处复盘**或**人生方向与行动**，开始对话。这些入口不要求先完成
恋爱访谈，也不要求讨论对象许可。每条消息是否发送由本人决定，不会联系对方。

希望保留复盘时，打开对话下方的**你的私人复盘**：

1. 选中会话，审阅OpenAI处理说明，再选择**整理复盘草稿**。仅提供最近最多20条消息、
   总计最多20,000字符，不包含其他会话、文件或私人档案。使用已选且获授权的模型；
   读取、编辑、保存和删除不调用模型。
2. 审阅本人原话、暂定解释、其他可能、感受、未知、边界与可选行动。引文必须出现在
   本人提供的文字中，但不证明事件已核实，也不证明解释一定成立。可以修改解释及
   选择不同关切／行动，这不是人格诊断。
3. 确认措辞后保存，关闭页面会丢弃未保存草稿。保存复盘不更新个人档案、不发布摘要、
   不通知好友，也不更改群组计划；这些仍是不同选择。
4. **读取已保存复盘**可打开本机记录，纠正并保存新版本，或明确删除正文。版本历史只含
   操作／时间等元数据，不保留旧报告措辞。过时保存会被拒绝，请先重新读取再试。
5. **将审阅后的记录放入下一条消息**会建立单独复盘会话，并填入有限消息草稿。
   审阅后明确发送，才供OpenAI继续讨论；不会暗中成为个人档案中的已核实事实。

复用属于本账号的`relationship-support/state.json`存储服务，位置在Git、OneDrive、安装目录
及Sites之外。本功能不加密本机存储。删除复盘不删除来源会话、此前云端处理及其他导出副本。
不会开启麦克风、录音、监控或紧急响应；无音频、不参与发现也能获得文字帮助。

安装见[固定版本入口](SETUP_WITH_CODEX.md)。当前交付及真实测试限制见[CURRENT_STATUS.md](CURRENT_STATUS.md)，
原产品要求的保留与缺口见[PRODUCT_CONTINUITY.md](PRODUCT_CONTINUITY.md)。
