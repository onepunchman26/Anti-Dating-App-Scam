# 0.8.4 usability acceptance / 易用性验收

## English

Original authority: `onepunchman26/Anti-Dating-App-Scam`, branch
`codex/easy-setup-discovery`, rollback `cb82d22`. Unrelated `.vscode/` and `paper/`
remain untouched. No original private vault was scanned or migrated.

| Area | Evidence and decision | Acceptance |
| --- | --- | --- |
| Setup | 0.8.3 required manual pairing; hosted requests timed out in Chrome and IAB | Add a pinned Codex setup prompt, fixed daily launcher, reuse one loopback process |
| Local conversation | Existing Python provider/storage and React onboarding reused | Chrome connected without copying a code; real synthetic interview reply and durable QA storage passed |
| Summary | Old Site form required manual tags | Real AI draft from selected synthetic conversation passed; fixed age/city/interest choices preserved, publication still separate |
| Discovery | Old region/interest filter ran after first 12 candidates | Real local D1 test with 16 synthetic peers found the qualifying late candidate; city aliases, age and interests execute server-side |
| Private AI review | Previous shared-token reasons were deterministic | Real Chrome AI review of synthetic summaries completed; reasons/differences/questions/unknowns saved locally |
| Failure recovery | First AI review hit the old 15-second UI timeout | New model operations use the bounded four-minute wait, no automatic retry; latest saved result can be read without inference |

No exact radius/GPS/geocoding is claimed. A finite Chinese/English city-alias list
normalizes common spellings; other areas must use equivalent names. Discovery still
checks both parties' published conditions and the existing server-enforced scope.
The controlled pilot scans up to 100 eligible records and reports when that pool is
limited; these changes do not claim unrestricted database-wide ranking.

Detailed private comparison can use at most ten of the owner's explicitly selected
confirmed/corrected statements, bounded to 4,500 characters. It cannot read a peer's
private profile. Candidate summaries are untrusted self-report. No diagnostic score,
honesty guarantee or empirical improvement in relationship outcomes is asserted.

Local `/app` uses an in-memory capability only after the connect click. Strict Host,
exact allowed origins, no cross-site embedding, no-store and bounded operations remain.
The launcher does not initialize a vault, call a model, duplicate a running helper or
kill an unknown/older listener. The local UI includes no Site write transport.

Final package, public-download installation and deployment receipts are recorded in
CURRENT_STATUS after verification. Independent B/C accounts are unavailable, so genuine
cross-account matching and fresh-account installation remain **NOT TESTED**. Owner-private
Site access is preserved. No real profiles or synthetic people were published in production.

## 中文版

继续使用原仓库，分支 `codex/easy-setup-discovery`，回退点 `cb82d22`。保留无关的`.vscode/`
和`paper/`；不扫描、不迁移原私人库。

| 模块 | 证据与改造 | 验收 |
| --- | --- | --- |
| 安装 | 旧版手动配对，Chrome与IAB的托管请求超时 | 加固定版本Codex指令和日常入口，复用一个本机进程 |
| 私人聊天 | 复用Python提供方／存储和React组件 | Chrome免复制码连接；真实合成访谈回复和QA持久化通过 |
| 摘要 | 原来需手动选择大量标签 | AI根据所选合成对话生成草稿通过；年龄、城市、兴趣固定保留，发布独立批准 |
| 发现 | 原筛选只作用于前12人 | 真实本地D1的16个合成人物中找到靠后合格候选；地区别名、年龄、兴趣在服务端筛选 |
| 私人AI解释 | 原共享标签交集属于固定规则 | Chrome真实AI解释已给出契合、差异、问题和未知，结果仅本机保存 |
| 恢复 | 首次候选分析遇到旧15秒界面超时 | 改为有界四分钟等待，不自动重发；可不耗推理读取最新已保存结果 |

不声称GPS、半径或地理编码。有限中英文城市别名归一化，其他地区需使用一致名称；仍检查双方
发布的条件和服务端隔离范围。受控测试最多扫描100条符合范围记录，达到上限会报告，未宣称
对无限数据进行全量排序。

详细私人比较可另选最多十条本人已确认／修正陈述，上限4,500字符，不能读取对方私人档案。
候选摘要是未经独立核实的自述，不做人格式诊断、诚实保证，也不声称关系效果经实验证明提高。

本机页仅在连接点击后使用内存能力码，保留严格Host、精确来源、防嵌入、不缓存和有限操作。
启动器不初始化资料库、不调用AI、不重复起服务、不结束不明或旧进程。本机UI不向网站写入。

最终打包、公开下载安装和部署证据验收后记入CURRENT_STATUS。缺独立B／C账号，真实多账号匹配
和新账号安装明确为**未实测**。保持网站所有者私有，未向生产发布真实档案或合成人物。
