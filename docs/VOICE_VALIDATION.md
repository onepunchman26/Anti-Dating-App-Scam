# Voice validation / 语音验收

## English

October 23, 2026. Original repository, branch `codex/voice-conversation`; rollback
`93acec3`. Final Windows payload uses clean source `b24b8d7e9023410d75bc0eb72cf0a2864ede55bf`,
192 manifested files. The legacy 0.5.3 application and unrelated work remain intact.

Implemented and connected: existing Python Vosk recognition through an authenticated,
exact-origin loopback-only bounded endpoint; explicit 30-second microphone capture;
editable dictation and short selected WAV handling; optional disclosed turn-based
send/read through the unchanged ChatGPT provider. Audio is ephemeral, has no Sites
transport and never updates a profile. Cancel, late microphone permission, account,
session and approved-context changes discard pending work. UI language changes keep
drafts and choices. Only localService device voices are eligible for reply reading.

Real failures corrected: an absent interview question returned as JSON null rejected
a completed AI response; normalize only that optional absence, retaining question,
evidence and strict-field validation. Browser voices load asynchronously; wait briefly
and support cancellation before declaring a language unavailable.

| Layer | Actual evidence |
|---|---|
| Python | Full regression 2,637 passed / 11 skipped; compileall and changed-file lint passed. Final pinned installer 46 passed / 1 skipped (PS5.1 policy gate). |
| Web | 51 Node checks before the asynchronous voice fix, then 6 voice checks including its new regression; TypeScript, lint, local UI and Site production builds passed. |
| Models | Both pinned official English and Chinese model downloads completed and hashes verified. Only English recognition was actually exercised. |
| Recognition | Windows generated a synthetic English WAV; original core and real authenticated source/EXE loopback returned “i enjoy quiet walks and spending time with friends”. No ambient microphone was accessed; stored=false and cloud=false. |
| Browser | Chrome connected to the local source and EXE, created an isolated synthetic vault, resumed after restart, displayed both-language voice controls and recognition readiness. Real ChatGPT response succeeded after the null-question fix; local English playback reached the completion event. This does not prove audible sound at the user's speakers. |
| Distribution | Actual packaged executable tests check install/reinstall, correction/persistence, ownership refusals, repair, retained data and interruption/retry, without developer tools on child PATH. Final result is in evidence/2026-10-23-voice-exe.json. |

Not accepted: physical microphone capture/quality, Chinese speech recognition, Chinese
local voice, a full microphone → automatic send → audible reply turn, or independent
B/C accounts. Chrome's file chooser rejected automation because the extension lacks
file-URL access; that setting was not changed. The selected-WAV browser path therefore
remains unaccepted even though the real PCM endpoint passed. Text remains usable.

[Official ChatGPT-plan limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)
exclude audio/transcription on this route. No full-duplex/native ChatGPT Voice, paid
API fallback, replacement LLM or automatic recording is claimed. Other original
product gaps (legacy import/report web parity, hosted-to-loopback, fresh accounts,
project licensing and broad eligibility) remain in CURRENT_STATUS. Publication and
public-download installation receipts are recorded there after actual completion.

## 中文版

2026年10月23日。继续原仓库`codex/voice-conversation`分支，回退点`93acec3`。最终Windows
包来自干净源码`b24b8d7e9023410d75bc0eb72cf0a2864ede55bf`，清单192个文件；保留旧0.5.3
应用与无关工作。

已实现并接通：原Python Vosk识别器、经过认证且精确限制来源的本机接口、主动开启且最长30秒
的录音、可编辑听写与主动选择的短WAV处理，以及明确披露／开启后经原ChatGPT接入逐轮发送和
朗读。音频仅在内存中处理，没有Sites传输，不更新档案。取消、延迟返回的麦克风权限、账号、
会话和获准上下文变化会丢弃待处理内容；界面语言切换保留草稿和选择。朗读只接受标记为
localService的本机声音。

已修正实际发现的问题：模型用JSON null表示没有下一题，导致已完成的AI回复被拒绝；现在仅
规范化这一可选空值，仍校验题数、证据与字段。浏览器声音异步加载，现会短暂等待并允许取消，
避免过早误报不可用。

| 层级 | 实际证据 |
|---|---|
| Python | 完整回归2,637通过／11跳过，编译及修改文件检查通过。最终固定版本安装器46通过／1跳过（PS5.1策略限制）。 |
| 网页 | 异步声音修复前51项Node通过，随后包含新回归的6项语音测试通过；TypeScript、检查、本机页面与网站生产构建通过。 |
| 模型 | 中英文固定官方模型下载及哈希核对完成，仅英语实际执行识别。 |
| 识别 | Windows生成虚构英语WAV；原核心及真实源码／EXE认证本机接口识别为“i enjoy quiet walks and spending time with friends”。未访问现场麦克风，结果stored=false、cloud=false。 |
| 浏览器 | Chrome连接源码和EXE页面，建立隔离合成库、重启恢复会话，显示双语语音控件和识别就绪。null修复后真实ChatGPT回复成功；英语本机朗读触发完成事件，不等于已听到用户扬声器的实际声音。 |
| 分发 | 真正打包EXE检查安装／重装、纠正／持久化、账号拒绝、修复、保留数据及中断重试；子进程PATH没有开发工具。最终结果见evidence/2026-10-23-voice-exe.json。 |

未验收：实体麦克风采集及质量、中文语音识别、中文本机声音、完整“麦克风→自动发送→可听
回复”回合、独立B／C账号。Chrome文件选择自动化因扩展未获文件URL访问而拒绝；没有更改
该权限。因此浏览器WAV选择流程尚未验收，不能拿真实PCM接口通过代替；文字仍可使用。

[官方套餐接入限制](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)
排除当前路线的音频／转写。没有宣称实时双向／原生ChatGPT语音、付费API回退、替换大模型或
自动录音。旧导入／完整报告的网页对应流程、托管页直连本机、新账号、项目许可与普遍接入资格等
仍在CURRENT_STATUS保留。实际发布及公开下载安装完成后，再在那里记录回执。
