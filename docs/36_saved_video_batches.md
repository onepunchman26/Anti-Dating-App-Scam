# Saved-video batches / 收藏视频批量处理

## English

### Everyday use

Open the fixed root **AI-SlowMatch.exe → Saved videos & interests**. This is optional
context for your existing personal model, not a public profile or personality score.
Connect ChatGPT from Home first if you want AI processing; importing and inspecting are local.

1. Choose one or more prepared JSON/CSV/TXT/Markdown files, paste a list of individual
   video URLs, or choose a folder containing only the notes you intend to contribute.
   Start with `examples/video_batch/mixed.json`; all its content is fictional. The
   `examples/video_batch/notes` folder demonstrates source-labeled Markdown.
2. Preview and filter by platform, collection or saved date. Unknown dates have a
   separate inclusion choice. All visible items start selected; uncheck exceptions.
   Double-click a preview row to inspect the exact supplied material. Import the
   selected batch once; you do not have to summarize or explain each item.
3. Optionally use **Public title lookup** for missing YouTube/TikTok titles. This is a
   separate disclosure to those platforms, with no account login. Then choose
   **Analyze / resume**, inspect the batch's minimized AI payload and recipient, and
   approve once for the collection. Changes to data, model/provider or a restarted app
   require a fresh review. Derived collection synthesis is included in that scope.
4. Watch imported, complete-supplied-text, partial, skipped, failed, duplicate and reused
   counts. **Pause** saves completed items; resume processes unfinished items. An
   unavailable item does not stop its neighbors. Auth/model/usage failures stop the run.
   **Retry failed** is manual, withdraws this batch's prior memory contributions and
   regenerates groups for fresh review. Nothing retries automatically.
5. Switch between **Interest profile** and **Reflection drafts**. Each group shows a
   broad subject, specific theme, tentative pattern, explanation, uncertainty and
   representative exact source quotes. **Inspect source items** shows the underlying
   links/materials, including skipped/failed items. Viewing does not mean participation;
   saving does not mean agreement. First-person drafts are AI wording until adopted.
6. Select groups to adopt, reject or remove. Edit one group or merge several of the
   same type, then adopt the changed wording separately. Quick corrections include
   visual style rather than message, work reference, and no longer relevant. If you
   want future recall, enable the existing memory in **Memory settings**. The same
   20-note limit applies; chat recalls only relevant enabled, approved notes.
7. **Export results** saves a new unencrypted JSON of findings and their representative
   excerpts; it is not a source backup or re-import file. **Undo import** removes the
   local batch and its memory support, invalidates unsupported dependent interpretations,
   and preserves still-supported approvals from other batches. Original files, manual
   exports, other backups and earlier cloud disclosures cannot be recalled by Undo.

### Actual platform coverage (checked October 2, 2026)

| Source | Implemented input/retrieval | Verification and limit |
|---|---|---|
| YouTube | Individual watch/shorts/embed/live/youtu.be URLs; prepared lists; playlist CSV with `Video Id` and `Playlist Video Creation Timestamp`, optionally preceded by playlist metadata. Optional public oEmbed title. | Synthetic CSV/parser checks and a real public documentation-example title lookup passed. A playlist URL alone is not expanded. Takeout availability varies; no private account archive was tested. No automatic caption download. |
| TikTok | Full `@name/video/id` URLs; selected likes/favorites sections of a supplied JSON or prepared list; optional public oEmbed title. | Official data-type names and synthetic fixtures checked. The real official-example title request returned HTTPError; useful title retrieval is not established here. Short redirect links are not followed. No live account or portability API connector. |
| Bilibili | BV/av video links, prepared JSON/CSV/TXT or notes with titles/summaries/transcripts. | Synthetic import verified. Privacy documentation supports access to saved records; no supported public bulk-favorites export API was established. No login, scraping, title or caption fetcher is implemented. |
| Other services | Public HTTP(S) individual URLs with supplied title/text. | Generic input is tested. The app never fetches arbitrary hosts. Link-only items are skipped instead of invented. |
| Obsidian | Explicitly selected `.md` files or a prepared folder of notes. | Synthetic folders verified; hidden folders, symlinks/reparse points and hardlinks are excluded. There is no automatic vault scan. Choose a narrow prepared folder, not an entire private vault. |

Google's [export guidance](https://support.google.com/accounts/answer/3024190?hl=en)
does not guarantee identical fields or date filtering across products. YouTube's
[caption download API](https://developers.google.com/youtube/v3/docs/captions/download)
requires authorization/appropriate permissions; the app does not claim arbitrary public
transcripts. The [oEmbed specification](https://oembed.com/) documents the YouTube example.
TikTok documents [personal data requests](https://support.tiktok.com/en/account-and-privacy/personalized-ads-and-data/requesting-your-data),
[likes/favorites data types](https://developers.tiktok.com/docs/en/data-portability-data-types),
and [public embeds](https://developers.tiktok.com/doc/embed-videos/).
Its [portability API](https://developers.tiktok.com/products/data-portability-api/) has
approval, scope and regional restrictions; it is not an installed connector here.
Bilibili's [privacy statement](https://www.bilibili.com/blackboard/privacy-policy.html)
does not establish a supported public favorites-download endpoint.

### Formats and honest limits

Prepared JSON is an array of objects; CSV uses equivalent columns: `url`, `title`,
`collection`, `saved_at` (ISO date), `transcript`, `description`, `summary`, `annotation`.
These text origins stay separate. TikTok imports recognize named likes/favorites sections
only, not messages or watch history. Markdown uses headings `Transcript`, `Description`,
`Summary`, `User annotation`, or their Chinese equivalents; unlabeled prose is an existing
summary of unknown authorship, never automatically the user's own view.

The bounded prototype accepts at most 1,000 distinct videos, 5,000 rows, 2 MB per file
and 16 MB of selected input. ZIP archives are not opened. A stored excerpt is at most
4,000 characters; AI sees at most 2,000 per excerpt, and truncation is labeled. “Full”
means all supplied transcript text was processed, not that the app watched the whole
video or verified the transcript. Descriptions/summaries/annotations and titles are
partial evidence. Missing source content is never reconstructed.

Per-item analysis runs once per unfinished item. Identical canonical videos merge, and
unchanged validated results can be reused while their prior batch remains. A derivative
summary does not add another video observation. Collection synthesis uses at most 24
themes and 23,000 characters, produces up to 12 interest groups, four reflection drafts
and three optional questions. Omitted themes are shown as a count; this is not a claim
to exhaustively synthesize every item in a very large collection. Model-created theme
names can vary; merge related groups during review. Recurring saves require at least
three distinct dated supplied materials across 30 days; work/aspiration labels require
an explicit user annotation. These conditions do not establish a lasting personality trait.

### Architecture, storage and evidence

`batch_context` implements validated import, public retrieval, AI contracts and
checkpoint/review lifecycle; the PySide screen calls that core. AI stays behind the
existing reviewed provider interface. Exact quotes and origins are validated before
findings can be adopted. The app's packaged conversational Skill is version 4 and
requires source-aware recall, user corrections and no sensitive inference from saves.

Batch checkpoints/cache live in `.video-context` inside the selected data folder.
There is no second profile database: adopted groups enter `.relationship-memory` with
timestamps, uncertainty and source evidence. Both are **ordinary unencrypted local files**.
They are excluded from Git and source backups. No automatic private-data backup is
added. AI receives selected minimized excerpts and derived groups, not local paths,
account tokens, the full archive or the whole personal model. Optional public-title
lookup sends URLs to fixed endpoints. It follows no redirects or arbitrary links.
No background monitor, email, publication, paid API or automatic retry was added.

Tests cover mixed imports, truncation, title-only cases, duplicate/repeated imports,
failures, cancellation/restart, scoped consent, corrections/merge, memory recall and
cascading deletion, plus English/Chinese Qt journeys. Six real included-plan calls used
synthetic materials with extra credits disabled: three item calls and three synthesis
attempts. Two failed syntheses were rejected and retained as failures. The final result
has three interests and one reflection draft; adoption/undo passed. This is a small
functional sample, not psychological validation. See the [initial receipt](evidence/2026-10-02-video-batch-plan.json),
[second attempt](evidence/2026-10-02-video-batch-corrected.json) and
[successful result](evidence/2026-10-02-video-batch-final.json). Full release gates are
reported in [current status](../CURRENT_STATUS.md).

## 中文版

### 日常使用

打开根目录固定的 **AI-SlowMatch.exe → 收藏视频与兴趣**。这是现有个人模型的可选背景，
不形成公开档案或人格分数。若要 AI 分析，先在主页连接 ChatGPT；导入和查看本身在本机完成。

1. 选择一批已准备的 JSON／CSV／TXT／Markdown 文件，粘贴独立视频链接列表，或选择只含
   本次愿意提供的笔记文件夹。可先用完全虚构的 `examples/video_batch/mixed.json`；
   `examples/video_batch/notes` 演示按来源标注的 Markdown。
2. 预览并按平台、收藏夹或收藏日期筛选；缺失日期有独立包含选项。当前可见条目默认全选，
   可以取消例外；双击行查看确切材料。一次导入选中集合，不需要逐个视频摘要或解释。
3. 缺少标题时，可选 **查询公开标题**，只查 YouTube／TikTok。这是向对应平台单独披露，
   不登录账户。再点 **分析／继续**，审阅本批最小 AI 输入和接收方，一次批准整批。
   材料、模型／提供方变化或重启应用后需重新审阅；集合综合属于该范围内的衍生处理。
4. 查看导入、完整处理所供文本、部分处理、跳过、失败、重复和复用数量。**暂停**保存已完成
   条目；继续只做未完成项。一项不可用不阻断其他项；鉴权、模型或额度错误会停下。
   **重试失败项**须手动，会撤回此批先前的记忆贡献并重新生成分组，须重新审阅，不自动重试。
5. 切换 **兴趣概况** 与 **反思草稿**。每组显示大主题、具体偏好、暂定模式、解释、不确定性和
   代表性原文引用。**查看来源条目**显示底层链接和材料，也包括跳过／失败项。观看不等于
   实践，收藏不等于认同；第一人称反思在采纳前属于 AI 拟稿。
6. 选组采纳、拒绝或移除；可修改一组或合并多个同类分组，再单独采纳修改稿。快捷纠正包括
   只喜欢视觉风格、工作参考和不再代表我。若希望日后召回，在 **记忆设置** 启用现有记忆。
   沿用最多 20 条限制，聊天只召回相关、已启用且已批准的条目。
7. **导出结果**新建未加密 JSON，包含结论及代表性片段，不是原材料备份或重新导入文件。
   **撤销导入**删除本机批次及其记忆支持，移除失去依据的衍生解释，并保留其他批次仍支持
   的批准内容。原文件、手动导出、其他备份和此前云端披露不能通过撤销收回。

### 实际平台支持（2026 年 10 月 2 日核查）

| 来源 | 已实现的输入／获取 | 验证与限制 |
|---|---|---|
| YouTube | 独立 watch／shorts／embed／live／youtu.be 链接、准备好的列表、含 `Video Id` 与 `Playlist Video Creation Timestamp` 的播放列表 CSV，可带前置列表元数据；可选公开 oEmbed 标题。 | 合成 CSV／解析测试及真实公开文档示例标题查询通过。单独播放列表网址不会展开；Takeout 字段可能不同，没有读取私人账户导出，不自动下载字幕。 |
| TikTok | 完整 `@name/video/id` 链接、所供 JSON 中指定的点赞／收藏区段或准备好的列表；可选公开 oEmbed 标题。 | 核对官方类型名并测试合成样例；真实官方示例标题请求返回 HTTPError，因此本环境尚未证实可用标题获取。不跟随短链接，没有账号或数据迁移 API 连接器。 |
| Bilibili | BV／av 链接、带标题／摘要／字幕的准备好 JSON／CSV／TXT 或笔记。 | 合成导入已验证。隐私文档支持用户查看收藏记录，但未找到受支持的公开整批收藏导出 API；未实现登录、爬取、标题或字幕获取。 |
| 其他服务 | 带所供标题／正文的公开 HTTP(S) 独立网址。 | 通用输入已测试，不访问任意主机；只有链接时跳过，不编造内容。 |
| Obsidian | 明确选定 `.md` 文件或已准备笔记文件夹。 | 合成文件夹已验证，跳过隐藏文件夹、符号链接／重解析点和硬链接，不自动扫描资料库；请选小范围准备好的文件夹，而非整个私人库。 |

Google 的[导出说明](https://support.google.com/accounts/answer/3024190?hl=en)不保证所有产品字段和日期
筛选一致；YouTube [字幕下载 API](https://developers.google.com/youtube/v3/docs/captions/download)需要
鉴权及适当权限，应用不承诺任意公开视频字幕。[oEmbed 规范](https://oembed.com/)提供 YouTube 示例。
TikTok 公开说明了[个人数据申请](https://support.tiktok.com/en/account-and-privacy/personalized-ads-and-data/requesting-your-data)、
[点赞／收藏字段](https://developers.tiktok.com/docs/en/data-portability-data-types)和[嵌入接口](https://developers.tiktok.com/doc/embed-videos/)。
其[数据迁移 API](https://developers.tiktok.com/products/data-portability-api/)有审核、范围和地区限制，
本应用没有安装该连接器。Bilibili [隐私声明](https://www.bilibili.com/blackboard/privacy-policy.html)
不能据以认定存在公开收藏下载接口。

### 格式与实际限制

准备好的 JSON 为对象数组；CSV 使用对应列：`url`、`title`、`collection`、`saved_at`（ISO 日期）、
`transcript`、`description`、`summary`、`annotation`，这些来源分别保留。TikTok 只识别命名的
点赞／收藏区段，不读消息或观看历史。Markdown 用 `Transcript`、`Description`、`Summary`、
`User annotation`，或“字幕”“描述”“摘要”“我的备注”标题；无标签正文视作作者未核实的已有摘要，
不会自动当成用户观点。

此有限原型最多接受 1,000 个不同视频、5,000 行、单文件 2 MB、选定输入合计 16 MB；不解压 ZIP。
单段最多本地保留 4,000 字，AI 每段最多接收 2,000 字，截断会标注。“完整”只表示完整处理所供
字幕文本，不表示看完视频或验证字幕。描述／摘要／备注和标题是部分证据，不补造缺失内容。

每个未完成条目调用一次；规范化后相同视频合并，先前批次仍在时可复用未变且验证过的结果，
衍生摘要不增加视频观察次数。集合综合最多 24 个主题、23,000 字，最多生成 12 组兴趣、4 份
反思草稿和 3 个可选问题；遗漏主题显示数量，不承诺对超大集合全部穷尽。模型主题命名可能
不同，可人工合并近义分组。反复收藏至少需跨 30 天的三项不同带日期材料；工作／愿望标签需
明确用户备注，这些门槛也不证明稳定人格。

### 架构、存储与证据

`batch_context` 负责验证导入、公开查询、AI 契约及进度／审阅生命周期，PySide 界面调用核心，
继续使用现有已审阅提供方接口。结论采纳前验证原文和来源。应用内对话 Skill 升级到版本 4，
要求按来源召回、遵守用户纠正，不从收藏推断敏感信息。

批次进度及缓存保存在选定资料文件夹内的 `.video-context`，没有另建人格数据库；采纳分组带
时间、不确定性和来源进入现有 `.relationship-memory`。两者均为 **未加密本地文件**，从 Git
和源码备份排除，没有新增自动私人资料备份。AI 只收到选定最小片段及衍生分组，不发送本机
路径、账号令牌、整个导出或全部个人模型；可选标题查询只向固定平台接口发送网址，不跟随
重定向或任意链接。没有新增后台监视、邮件、发布、付费 API 或自动重试。

测试涵盖混合导入、截断、仅标题、重复导入、失败、取消／重启、限定授权、修改／合并、记忆
召回及联动删除，以及中英文 Qt 流程。关闭额外积分后，用合成材料真实调用套餐六次：三次
条目分析、三次集合综合。前两次综合失败被拦截并保留失败记录；最终得到三组兴趣、一份反思，
采纳及撤销通过。少量功能样本不是心理科学验证，详见[初次记录](evidence/2026-10-02-video-batch-plan.json)、
[第二次尝试](evidence/2026-10-02-video-batch-corrected.json)及[成功结果](evidence/2026-10-02-video-batch-final.json)。
完整发布检查以[当前交接](../CURRENT_STATUS.md)为准。
