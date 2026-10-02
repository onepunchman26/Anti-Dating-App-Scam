# Desktop release and recovery / 桌面发布与恢复

## English

The sole current user entry is root `AI-SlowMatch.exe`. `pyproject.toml` is the version
source; increment it deliberately for a product change, never rename the executable.
Every build has a unique ID plus Git commit, dirty flag and source digest. Release tags
are reserved for committed, reviewed source; this local development build is not public deployment.

On the verified Python 3.12 environment: `./release.ps1 build` checks installed pinned
dependencies, creates an external source/Git backup, restores and hashes it, runs
compile/lint/pytest on that frozen copy, builds Windows GUI metadata, validates embedded
code and native speech/crypto/audio dependencies, performs isolated startup, then
promotes atomically. `./release.ps1 build -StageOnly` stops before promotion.

`./release.ps1 promote -Path <candidate-directory>` retries a verified staged candidate.
Close a running current EXE first if Windows holds it; no process is killed.
`./release.ps1 rollback -BuildId <archived-id>` restores an exact verified archive.
An interrupted replacement is reconciled from its transaction and executable hashes;
unknown/tampered entries stop safely. Failed gates leave the current EXE untouched.

`./release.ps1 backup` creates a source snapshot plus full Git history outside the
checkout/OneDrive in `%LOCALAPPDATA%/AI-SlowMatch/development-backups`.
`./release.ps1 restore -Path <snapshot-directory> -Destination <new-directory>` checks
every archive hash and restores source plus a bare history repository without overwriting work.
Backups exclude private vaults, credentials, models, caches, logs and binaries. Successful
builds keep five verified managed source backups and three promoted releases, plus the
current release and any copy containing `.keep`. Unknown, invalid and linked copies
are not deleted. A locked retention target is retained for later review.

`build_exe.ps1` defaults to this Desktop pipeline. Low-level scripts for legacy web/node
experiments are internal alternatives. GitHub workflows run only by manual dispatch;
no paid remote job or automatic network updater is required.

## 中文版

当前唯一用户入口为根目录 `AI-SlowMatch.exe`。`pyproject.toml` 是版本来源；产品变化时
明确递增版本，不改 EXE 名称。每次构建记录独立编号、Git 提交、未提交标记及源码摘要。
发布标签只对应已提交、已审阅源码；本地开发构建不等于公开部署。

在已验证的 Python 3.12 环境中，`./release.ps1 build` 检查固定依赖，创建外部源码／Git
备份并恢复核验，在冻结副本上运行编译／静态检查／测试，构建 Windows 图形程序及版本资源，
核验嵌入代码和语音／加密／音频原生依赖，执行隔离启动，再原子替换入口。
`./release.ps1 build -StageOnly` 停在正式替换之前。

`./release.ps1 promote -Path <候选目录>` 可重试已验证候选版本。若 Windows 占用当前
程序，先关闭该程序；脚本不会强制结束进程。`./release.ps1 rollback -BuildId <归档编号>`
恢复对应版本。替换中断时依据事务与程序哈希恢复一致状态；未知或被改动的入口安全停止。
检查失败不会替换当前 EXE。

`./release.ps1 backup` 在仓库及 OneDrive 之外的
`%LOCALAPPDATA%/AI-SlowMatch/development-backups` 创建源码及完整 Git 历史备份。
`./release.ps1 restore -Path <快照目录> -Destination <新目录>` 核验全部归档哈希，
恢复源码及裸历史仓库，不覆盖现有工作。备份不含私人资料库、凭据、模型、缓存、日志或二进制。
成功构建后保留最近五份经过验证的受管源码备份及三个正式版本，另保留当前版本和含 `.keep`
文件的副本。未知、无效或链接副本不会删除，被占用的清理对象会继续保留待复核。

`build_exe.ps1` 默认走此桌面流程，旧版网页／节点底层构建只作为内部替代。
GitHub 工作流仅手动触发，不要求付费远端任务或联网自动更新。
