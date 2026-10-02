# Recovering a local model connection / 本地模型连接恢复

## English

This document records the earlier recovery milestone and its failed final-source
attempts. The subsequent [paired bilingual generation milestone](29_paired_report_generation.md)
changes only the full-regeneration wire format and records newer limited real-model
integration passes. It does not retroactively validate these earlier outputs.

### What the local failure established

On the inspected Windows development device, installed Ollama 0.31.1 used an
RTX 5070 Ti with NVIDIA driver 616.92. The installed `qwen3.6:latest` model has
22.294 GiB of weight files. Three explicitly requested synthetic attempts produced:

| Attempt | Result | Elapsed time |
| --- | --- | --- |
| First self-portrait | CUDA initialization failed during model warm-up; no model reply or saved copy | 65.95 s |
| Relationship criteria | Structured output, exact excerpt quotations, separate saving and reopening passed | 132.33 s |
| Additional self-portrait | A new runner again failed during warm-up; no model reply or saved copy | 44.23 s |

The criteria result was only limited acceptance. It kept revealed criteria and
fictional candidates empty and did not invent past choices. However, it strengthened
“I want” into “explicitly requests” and the Chinese “明确要求／不得”; “所有者” was also
awkward wording. Valid structure and quotations do not guarantee appropriate
interpretation or faithful translation. The criteria copy was tested before a small
position-neutral wording correction to the application notice; it is not a final-build
criteria acceptance claim. Originals and the active selection remained unchanged.

Both failed runs reported an 8845.55 MiB `CPU` model buffer; the successful run
reported the same size as `CUDA_Host`. Their GPU model buffers were identical.
Failures occurred while initializing a CUDA 13 flash-attention kernel during an
empty warm-up. This is an observed association. The logs do not explicitly show
a pinned-memory allocation failure, so that explanation remains a hypothesis.
The last failure had more free physical memory than the successful run; a free-RAM
number alone cannot predict success.

A report in the upstream Ollama repository describes a similar Windows/RTX 5070 Ti
warm-up failure and the same buffer-type association, using a different model and
Ollama version. It supports further investigation, not proof of this device's cause.
See [upstream issue 17380](https://github.com/ollama/ollama/issues/17380).

The GPU is listed as supported, and the observed NVIDIA driver exceeds the documented
minimum. Those facts do not guarantee every runtime path works, but the evidence does
not justify changing drivers merely because this error occurred. Ollama documents
`CUDA_VISIBLE_DEVICES=-1` for choosing CPU execution in a controlled diagnostic;
this guide does not apply it to the user's environment.
See [Ollama hardware support](https://docs.ollama.com/gpu).

### A separate output-grammar failure

An installed `gemma4:latest` portrait attempt failed before returning a reply
after 12.59 seconds. Its local log identified a grammar repetition limit rather
than a CUDA warm-up failure. The generation schema allowed narrative strings up
to 8,000 characters, which the installed grammar compiler could not handle.
This is a directly observed output-format failure; the larger model's memory
buffer explanation above remains an unproven runtime hypothesis.

The model-facing report schema now caps generated strings at 1,000 characters
per field. Input excerpts are not shortened, and the application still validates
the complete original report contract, including its existing 8,000-character
text limit, required localization, exact quotations and nonblank text. Existing
long reports can still validate and reopen. Nothing truncates an old report,
silently repairs a reply, weakens validation or sends a second request. A request
prepared with the old schema must be prepared and reviewed again.

The [upstream grammar parser](https://github.com/ggml-org/llama.cpp/blob/master/src/llama-grammar.cpp)
defines a repetition threshold of 2,000 and also checks combined rule complexity.
An [upstream boundary report](https://github.com/ggml-org/llama.cpp/issues/27859)
describes a version-specific problem at exactly 2,000. The narrower generation
limit avoids those large repetitions; it is not a guarantee that every model
will obey the report contract or interpret evidence correctly.

After this change, a fresh `gemma4` portrait request returned a reply in 11.66
seconds, confirming that this request passed grammar compilation. The application
then rejected duplicate or forbidden localization paths and source IDs used in
place of canonical text. No copy was saved. Grammar compatibility improved;
complete-report acceptance did not pass.

### Choose an already installed smaller model

The inspected device also contains `qwen3.5:latest` with 6.142 GiB of weights and
`gemma4:latest` with 8.948 GiB. `nomic-embed-text` is an embedding model, not a choice
for generating these reports. These are observations about this device, not models
that every installation must have or a request to download them.

An attempted CPU-only preflight for the larger model stopped before inference:
22.29 GiB of weights exceeded the then-available 21.27 GiB of physical memory,
before working buffers; virtual-memory headroom was 10.95 GiB. This was a decision
to avoid memory pressure, not proof that CPU execution is unsupported. A later
inspection found 20.36 GiB of physical memory and 10.84 GiB of virtual-memory
headroom. Resource availability changes. The smaller installed `qwen3.5` provides
more room for a bounded normal-GPU attempt without changing system settings.

Use the existing desktop controls:

1. Open **Connect Your AI** and choose **Ollama (local, private)** explicitly.
2. Keep **Ollama URL** on this device's loopback service, for example
   `http://127.0.0.1:11434`. Enter the exact name of an already installed chat model
   in **Ollama model**; on the inspected device, the smaller choice is
   `qwen3.5:latest`.
3. Select **Connect & Test This Mode**. This checks service/model availability;
   it does not generate or validate a report. If the model is unavailable, stop
   and inspect the local setup. This procedure does not download it.
4. Return to the report's reviewed-copy workflow and choose
   **Regenerate a full report from original excerpts**. Select the current saved
   corrections, provide the original excerpts explicitly, and prepare a fresh
   request after changing the model.
5. Read the complete request and confirm one local generation. A failure sends no
   automatic retry, schema fallback, cloud request or model download. A new attempt
   requires preparing/reviewing another request and choosing to run it.
6. Review the English and Chinese preview for scope, uncertainty, quote membership
   and wording strength. Confirm **Save separate copy** only after this review.
   Saving preserves originals and does not activate the copy; activation is a
   separate **Select active report** choice.

For the report contract and the limits of verification, see
[full report regeneration](27_full_report_regeneration.md).

### Local configuration and diagnostic boundaries

Ollama server settings come from its environment; Windows applications inherit
environment settings when started. The project's temporary diagnostic servers use
loopback and disable cloud features within their own process environment. They do
not change the user's persistent environment or an existing server. The official
[Ollama FAQ](https://docs.ollama.com/faq) describes configuration, loopback binding
and the cloud-disable setting.

No driver, page-file, operating-system or persistent Ollama configuration change,
reboot, or termination of the user's unrelated processes was performed for this
recovery. Temporary servers are stopped by their recorded owned process IDs.
Changing those system settings is not an established remedy here. A successful
smaller-model example would demonstrate that particular local path; it would not
repair or certify the larger model's CUDA path.

### Completed smaller-model checks and remaining limits

This recovery made nine explicitly chosen real requests: seven to `qwen3.5:latest`
and two to `gemma4:latest`. These are separate from the three earlier `qwen3.6`
requests above. There were no automatic retries. The two structural criteria
passes preceded the generation-schema cap; all attempts with the final source
failed strict validation.

| Model and check | Observed result | Elapsed time |
| --- | --- | --- |
| qwen3.5 initial self-portrait | GPU inference returned; strict validation rejected extra report fields and incorrect localization | 15.50 s |
| qwen3.5 self-portrait with report-specific instructions | A reply returned, but the report still failed strict validation | 6.39 s |
| qwen3.5 criteria with report-specific instructions | Structure, separate saving and reopening passed; manual content review still found problems | 11.16 s |
| qwen3.5 reproducible CLI self-portrait | Reply rejected; no generated copy saved | 5.09 s |
| qwen3.5 reproducible CLI criteria | Structure, separate saving/reopening and preservation passed; no raw reply retained for semantic review | 18.00 s |
| gemma4 initial self-portrait | Grammar compilation failed before a reply | 12.59 s |
| gemma4 self-portrait after the schema cap | Grammar compilation succeeded and a reply returned; localization validation rejected it | 11.66 s |
| qwen3.5 final-source self-portrait | A reply returned; localization validation rejected mismatched canonical text or missing mappings | 13.01 s |
| qwen3.5 final-source criteria | A reply returned; localization validation rejected missing mappings or invalid source text, including an empty source | 11.31 s |

The criteria sample preserved the strength of the first two stated wishes, with
acceptable Chinese wording for those two claims. However, it put the absence of
past choices into a third pattern claim instead of a limitation, and repeated
workflow instructions in caveats. It is not complete semantic acceptance. The
separate CLI criteria pass retained metadata only and received no manual semantic
review. The final two qwen3.5 checks used the reusable smoke flow with a separate,
temporary recording transport so the synthetic replies could be inspected
manually. Neither passed the report contract or established semantic acceptance.
A quick GPU reply establishes neither a valid full report nor a repaired
`qwen3.6` runtime. Full report regeneration remains experimental.

Original bytes and the active selection were preserved throughout; rejected
attempts saved no generated copies. The temporary server and its verified owned
runner were stopped, their children ended, and no listener remained on port
11434. No CPU inference, driver change, model download or cloud request occurred.
Further model attempts ended for this milestone. The next engineering task is
to reduce the burden of duplicating report text in the localization contract
while preserving one exactly reviewed request and strict validation; that change
is not implemented by this recovery.

### Reproducible synthetic CLI check

The source checkout provides a separate opt-in check for each report kind. It
requires an existing local Ollama service and an already installed model. For
this checkout's Windows environment, run one chosen command from the repository
root; each invocation authorizes at most one real local inference:

```powershell
.\.venv-rehab\Scripts\python.exe scripts/smoke_full_report_regeneration.py --kind self_portrait --model qwen3.5:latest --timeout 240
```

For a separately chosen criteria check, replace `--kind self_portrait` with
`--kind mate_criteria`. `--url` optionally selects another loopback endpoint;
the default is `http://127.0.0.1:11434`. The total time budget must be greater
than zero and no more than 300 seconds. It limits the remaining HTTP/socket wait
and rejects late results using elapsed-time checks; it is not a hard process
watchdog and does not stop the model server. Use `--help` to inspect the interface
without making a model request. The script requires the source checkout; it is
not an EXE or wheel command.

The script uses built-in fictional notes, an isolated temporary home/vault and
a real nonempty synthetic report selection. It validates the reply, saves and
reopens a separate synthetic copy, and checks exact preservation of the originals
and selection. It does not start a server, probe availability, install models,
download files, read a personal vault or retry. Temporary files are removed and
the prior environment is restored.

Only metadata is printed and written to `build/full-report-regeneration-smoke.json`.
Each run replaces that metadata file; preserve it before running a second check
if both records are needed. No raw requests, responses or generated reports are
retained. `status: passed` means the structural flow passed. Its
`semantic_review: not_performed` status means wording and translation still need
separate review. Offline tests inject a transport and are not real model evidence.
This check never establishes public-release readiness.

## 中文版

本文保留此前恢复里程碑及当时最终源码的失败尝试。后续
[成对双语生成里程碑](29_paired_report_generation.md)仅更改完整重新生成的模型回复格式，
记录了较新的有限真实模型集成通过结果，不会追溯性地认定此前输出有效。

### 本地故障已经证实了什么

在检查的 Windows 开发设备上，已安装的 Ollama 0.31.1 使用 RTX 5070 Ti，
NVIDIA 驱动版本为 616.92。已安装的 `qwen3.6:latest` 模型权重文件共
22.294 GiB。三次明确执行的合成样例请求得到以下结果：

| 尝试 | 结果 | 耗时 |
| --- | --- | --- |
| 第一次自我画像 | 模型预热期间 CUDA 初始化失败；没有模型回复，也没有保存副本 | 65.95 秒 |
| 择偶标准 | 结构化输出、对应摘录的逐字引文、单独保存和重新打开通过 | 132.33 秒 |
| 追加的自我画像 | 新启动的运行器再次在预热期间失败；没有模型回复，也没有保存副本 | 44.23 秒 |

择偶标准结果只构成有限验收。它保留了空的行为揭示标准和虚构候选人列表，没有虚构过去的选择。
但它把“I want”加强为“explicitly requests”，中文又使用了“明确要求／不得”；
“所有者”这一称呼也不自然。结构和引文有效，并不保证解释恰当或翻译忠实。
该择偶标准副本的测试发生在应用提示语的一处位置中性措辞修正之前，不能据此宣称最终构建的
择偶标准路径已经完成真实验收。原件及当前启用的报告均保持不变。

两次失败运行都记录了 8845.55 MiB 的 `CPU` 模型缓冲区；成功运行则把同样大小的缓冲区
记录为 `CUDA_Host`。三次运行的 GPU 模型缓冲区大小相同。故障发生在空载预热期间，
具体位置是 CUDA 13 的 FlashAttention 内核初始化。这是已观察到的关联。日志没有明确记录
固定主机内存分配失败，因此这一解释仍是假设。最后一次失败时的可用物理内存比成功运行时更多；
单看剩余内存数值不能预测成功与否。

Ollama 上游仓库中的一份问题报告描述了相似的 Windows／RTX 5070 Ti 预热失败，
以及相同的缓冲区类型关联，但使用的模型和 Ollama 版本不同。它可以作为进一步调查的线索，
不能证明本设备的根因。参见
[上游问题 17380](https://github.com/ollama/ollama/issues/17380)。

该 GPU 列在官方支持名单中，检测到的 NVIDIA 驱动也高于文档要求的最低版本。
这不能保证每条运行路径都正常，但现有证据不足以支持“出现此错误就应更换驱动”的结论。
Ollama 文档说明可以在受控诊断中使用 `CUDA_VISIBLE_DEVICES=-1` 选择 CPU 执行；
本指南没有将它应用到用户的环境。参见
[Ollama 硬件支持说明](https://docs.ollama.com/gpu)。

### 另一类输出语法故障

已安装的 `gemma4:latest` 在一次自我画像尝试中耗时 12.59 秒，但在返回回复之前失败。
本地日志指出的是语法重复次数限制，并非 CUDA 预热故障。原来的生成结构允许叙述字段
最多包含 8,000 个字符，而已安装的语法编译器无法处理。这是直接观察到的输出格式故障；
前文关于较大模型内存缓冲区的解释仍属于未经证实的运行环境假设。

提供给模型的报告生成结构现在把每个字符串字段的生成上限收紧为 1,000 个字符。
输入摘录不会缩短，应用仍按完整原有报告契约校验，包括原有的 8,000 字符文本上限、
必需的双语本地化、精确引文及非空白文字。原有较长报告仍可通过校验并重新打开。
应用不会截断旧报告、静默修复回复、放宽校验或发送第二次请求。
使用旧结构准备的请求必须重新准备并复核。

[上游语法解析器](https://github.com/ggml-org/llama.cpp/blob/master/src/llama-grammar.cpp)
定义了 2,000 的重复次数阈值，还会检查组合规则的复杂度。
另一份[上游边界问题报告](https://github.com/ggml-org/llama.cpp/issues/27859)
描述了特定版本在恰好 2,000 处出现的问题。更窄的生成上限避开了这些较大的重复次数，
但不能保证每个模型都遵守报告契约，或正确解释证据。

修改后，一次新的 `gemma4` 自我画像请求在 11.66 秒内返回回复，证明该次请求已经通过语法编译。
随后应用因重复或禁止的本地化路径、以及用来源编号代替规范原文而拒绝了回复，没有保存副本。
语法兼容性有所改善，但完整报告仍未通过验收。

### 选择已经安装的较小模型

检查的设备还安装了权重为 6.142 GiB 的 `qwen3.5:latest`，以及权重为 8.948 GiB 的
`gemma4:latest`。`nomic-embed-text` 是嵌入模型，不用于生成这些报告。
这些信息描述的是本设备现状，不代表每个安装环境都应具备这些模型，也不是下载要求。

较大模型的纯 CPU 测试在预检阶段就停止了：22.29 GiB 的权重已经超过当时可用的
21.27 GiB 物理内存，还没有计入工作缓冲区；当时的虚拟内存余量为 10.95 GiB。
这是为避免内存压力作出的决定，并不证明 CPU 执行不受支持。后一次检查得到的可用物理内存为
20.36 GiB，虚拟内存余量为 10.84 GiB。资源余量会变化。已安装的较小 `qwen3.5`
为有界的正常 GPU 尝试留下了更多余量，无需更改系统设置。

可以使用现有桌面界面操作：

1. 打开**连接你的 AI**，明确选择 **Ollama（本地·私密）**。
2. 将 **Ollama 地址**保持为本机回环服务，例如 `http://127.0.0.1:11434`。
   在 **Ollama 模型**中填写已安装聊天模型的准确名称；在检查的设备上，较小的选项是
   `qwen3.5:latest`。
3. 点击**连接并测试所选模式**。它检查服务和模型是否可用，不会生成或验证报告。
   如果模型不可用，应停止并检查本地设置；这套流程不会下载模型。
4. 返回报告的复核副本流程，选择**根据原始摘录重新生成完整报告**。选择当前有效的已保存更正，
   明确提供原始摘录，并在更换模型后重新准备请求。
5. 阅读完整请求，确认执行一次本地生成。失败不会自动重试、回退输出格式、请求云端或下载模型。
   再次尝试需要重新准备、复核请求，并明确选择执行。
6. 阅读完整中英文预览，核对解释范围、不确定性、引文与摘录的对应关系，以及措辞强度。
   完成复核后才确认**保存独立副本**。保存会保留原件，也不会启用副本；启用还需要在
   **选择当前报告**中单独决定。

报告结构和验证边界见[完整报告重新生成](27_full_report_regeneration.md)。

### 本地配置与诊断边界

Ollama 服务通过环境变量取得设置；Windows 应用在启动时继承环境设置。
项目的临时诊断服务只在自身进程环境中使用回环地址并关闭云端功能，不修改用户的持久环境，
也不改变已有服务。官方 [Ollama 常见问题](https://docs.ollama.com/faq) 说明了配置方式、
回环监听和关闭云端功能的设置。

本次恢复没有更改驱动、页面文件、操作系统或 Ollama 持久配置，没有重启设备，也没有终止
用户无关的进程。临时服务按已记录的自有进程编号停止。更改上述系统设置并不是这里已经证实的
修复办法。即使较小模型的样例成功，也只能说明该次本地路径可运行，不能据此声称较大模型的
CUDA 路径已经修复或通过认证。

### 已完成的较小模型检查及剩余局限

本次恢复共进行了九次明确选择的真实请求：`qwen3.5:latest` 七次，`gemma4:latest` 两次。
这些请求与前文更早的三次 `qwen3.6` 请求分开计算，没有自动重试。两次通过结构校验的
择偶标准检查发生在收紧生成结构之前；使用最终源码的尝试均未通过严格校验。

| 模型与检查 | 观察结果 | 耗时 |
| --- | --- | --- |
| qwen3.5 首次自我画像 | GPU 推理返回了回复；严格校验拒绝了多余报告字段及不正确的本地化内容 | 15.50 秒 |
| qwen3.5 使用报告类型专属指令的自我画像 | 返回了回复，但报告仍未通过严格校验 | 6.39 秒 |
| qwen3.5 使用报告类型专属指令的择偶标准 | 结构、单独保存和重新打开通过；人工内容复核仍发现问题 | 11.16 秒 |
| qwen3.5 可复现 CLI 的自我画像检查 | 回复被拒绝，没有保存生成副本 | 5.09 秒 |
| qwen3.5 可复现 CLI 的择偶标准检查 | 结构、单独保存、重新打开及保留原件和选择通过；未保留供语义复核的原始回复 | 18.00 秒 |
| gemma4 首次自我画像 | 在返回回复之前，语法编译失败 | 12.59 秒 |
| gemma4 收紧生成结构后的自我画像 | 语法编译成功并返回回复；本地化校验拒绝了回复 | 11.66 秒 |
| qwen3.5 最终源码的自我画像 | 返回了回复；本地化校验因规范原文不匹配或缺失映射而拒绝回复 | 13.01 秒 |
| qwen3.5 最终源码的择偶标准 | 返回了回复；本地化校验因缺失映射或无效来源文字（包括空来源）而拒绝回复 | 11.31 秒 |

择偶标准样例保留了前两项愿望的表述强度，这两条主张的中文措辞可以接受。
但它把“未描述过去的选择”放入第三条模式主张，而不是局限性说明，还在警示中重复了工作流程指令。
这不构成完整语义验收。另一次通过的 CLI 择偶标准检查只保留元数据，没有进行人工语义复核。
最后两次 qwen3.5 检查使用可复用的检查流程，并另加临时记录传输，以便人工检查合成回复。
两次都没有通过报告契约，也没有构成语义验收。GPU 很快返回回复，既不能证明完整报告有效，
也不能说明 `qwen3.6` 的运行故障已经修复。完整报告重新生成仍属实验功能。

所有尝试均保留了原件字节和当前报告选择；被拒绝的尝试没有保存生成副本。
临时服务及经身份核验的自有运行器已经停止，子进程均已结束，11434 端口没有残留监听。
本次没有进行 CPU 推理、更改驱动、下载模型或请求云端。本里程碑不再继续调用模型。
下一项工程任务是降低本地化契约中重复提供报告文字的负担，同时保留准确审核的一次请求和
严格校验；这项改动尚未在本次恢复中实现。

### 可复现的合成数据 CLI 检查

源码仓库为每种报告提供单独、主动选择的检查。它要求本机已有运行中的 Ollama 服务，
并且模型已经安装。使用本仓库的 Windows 环境时，从仓库根目录执行所选命令；
每次调用最多授权一次真实本地推理：

```powershell
.\.venv-rehab\Scripts\python.exe scripts/smoke_full_report_regeneration.py --kind self_portrait --model qwen3.5:latest --timeout 240
```

如果另行选择检查择偶标准，将 `--kind self_portrait` 替换为 `--kind mate_criteria`。
可选的 `--url` 用于指定另一个回环地址，默认值是 `http://127.0.0.1:11434`。
总时间预算必须大于零且不超过 300 秒。它限制剩余 HTTP／套接字等待时间，并通过实际耗时检查
拒绝过期结果；它不是强制终止进程的看门狗，也不会停止模型服务。使用 `--help` 可查看接口，
不会发出模型请求。该脚本需要源码仓库，不是 EXE 或 wheel 包提供的命令。

脚本使用内置虚构笔记、隔离的临时主目录和资料库，以及实际存在的非空合成报告选择记录。
它校验回复，保存并重新打开独立合成副本，检查原件的精确字节和报告选择是否保持不变。
它不会启动服务、探测可用性、安装模型、下载文件、读取个人资料库或重试。
临时文件会被移除，原有环境设置会恢复。

脚本只打印元数据，并写入 `build/full-report-regeneration-smoke.json`。
每次运行都会替换该元数据文件；如果需要保留两次记录，请在第二次检查之前另行保留首份记录。
它不保留原始请求、回复或生成的报告。`status: passed` 只表示结构流程通过；
`semantic_review: not_performed` 表示措辞和翻译仍需另外复核。
离线测试使用注入的模拟传输，不能作为真实模型证据。这项检查也不代表达到公共发布条件。
