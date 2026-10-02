# Local Profile MPMD

## English

MPMD means Markdown Personal Memory Document.

The primary local profile file is:

```text
<selected-vault>/profile/profile.mpm.md
```

The structured companion file is:

```text
<selected-vault>/profile/profile.json
```

## Why Markdown First

The Markdown profile is user-readable and user-editable. It should feel like a local personal document, not a hidden database or model artifact.

## What It Is

- A self-reflection aid.
- A local relationship values and boundaries document.
- A companion to risk education and trust ladder coaching.
- A profile the user owns and can edit.

## What It Is Not

- Not a psychological diagnosis.
- Not a social score.
- Not proof of personality.
- Not proof of safety or danger.
- Not training a personal model.

## Default Sections

- Source Summary
- Relationship Values
- Communication Preferences
- Boundary Preferences
- Risk Tolerance Notes
- Trust Ladder Preferences
- Social Connection Notes
- Self-Reflection Notes
- Things to Verify Later
- User Editable Notes

### Historical flat layout

Earlier versions stored both fixed filenames directly in the vault root. Opening
that vault now offers explicit preview and exact-byte copying into `profile/`.
Originals stay intact and a nonempty destination is never merged or overwritten.
Unsupported JSON remains available for literal review but blocks copying. See
[profile layout migration](24_profile_layout_migration.md) for full limits.

## 中文版

MPMD 指 Markdown Personal Memory Document（Markdown 个人记忆文档）。
当前主要档案文件为 `<所选档案库>/profile/profile.mpm.md`，结构化配套文件为
`<所选档案库>/profile/profile.json`。

### 为什么以 Markdown 为主

Markdown 档案由用户阅读和编辑，是用户拥有的本地个人文档，不是隐藏数据库或模型产物。
它用于自我反思，记录关系价值观及边界，并辅助风险教育和信任阶梯指导。

它不是心理诊断、社交评分、人格证明或安全/危险证明，也不是个人模型训练数据。

### 默认章节

- 来源摘要
- 关系价值观
- 沟通偏好
- 边界偏好
- 风险容忍说明
- 信任阶梯偏好
- 社交联系说明
- 自我反思笔记
- 待核实事项
- 用户可编辑笔记

### 历史扁平布局

早期版本将两个固定文件直接放在档案库根目录。现在打开此类档案库时，会提供明确预览及
逐字节复制到 `profile/` 的操作。原件保持不变；目标非空时不合并、不覆盖。不受支持的
JSON 仍可按原文复核，但会阻止复制。完整限制见[个人档案布局迁移](24_profile_layout_migration.md)。
