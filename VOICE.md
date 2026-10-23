# Voice / 语音

## English

In the local conversation page, connect your account and private space, then open a
conversation. Under **Speak or type**, check voice setup, choose the spoken language,
and download its model once (English about 40 MB; Chinese about 42 MB). The download
is a public, pinned Vosk model. It contains no personal data. Text chat works without it.

**Start dictation** asks the browser for microphone access. A visible timer runs for
at most 30 seconds. **Finish recording** transcribes; **Cancel / stop** discards the
pending recording or stops the operation. Leaving/hiding the page, changing the
conversation or changing approved context stops the voice flow. Late permission
responses release the microphone immediately. Audio remains in memory on this
computer; it is not saved to the vault or sent to Sites or OpenAI.

Recognition fills the editable message draft. Correct mistakes before sending.
Alternatively choose one WAV recording of 0.1–30 seconds, up to two channels and
12 MB. Use only your own voice or material you have permission to process. Imported
audio always becomes a draft and is never automatically sent. The app does not delete
the original file you selected. Sending text follows the existing conversation
permissions and local conversation storage rules.

Optional **turn-based voice** is off by default. With an empty draft and the existing
OpenAI/context permissions, explicitly enable it to send each completed dictation
and read its reply. Recognition errors can therefore reach OpenAI before correction.
Each new recording still requires a click. Only a device-local voice for the chosen
language is used. If none exists, read the text; no remote voice is substituted.
Cancel stops playback and requests cancellation; a cloud request already sent may
have been processed. This is not full-duplex, always-listening or native ChatGPT Voice.

Current official ChatGPT-plan integration does not support audio or transcription:
[OpenAI preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations).
ChatGPT remains the conversation provider; Vosk only converts sound to text.
Do not replace this authorization with an undeclared paid API or another LLM.

Acceptance separates code/tests, real synthetic-audio recognition, browser/file
flow, installed EXE, physical microphone, audible local playback, and independent
accounts. See CURRENT_STATUS for the actual results. Download/installation alone
does not establish any of the latter. Model accuracy depends on speech and environment.

## 中文版

在本机对话页面连接账号和私人空间，再打开一段对话。在**说话或打字**中检查语音设置、
选择说话语言，按需下载一次模型（英语约40 MB、中文约42 MB）。下载的是固定版本、经过
校验的Vosk公开模型，不包含私人资料；不下载也能继续文字聊天。

点击**开始听写**后，浏览器请求麦克风权限，并显示最长30秒的录音计时。**结束录音**后
进行转写；**取消／停止**丢弃待处理录音或停止操作。离开／隐藏页面、切换对话或改变已批准
上下文会停止语音流程。取消后才返回的麦克风授权会立即释放设备。音频只在本机内存中处理，
不保存到档案库，不发送给Sites或OpenAI。

识别结果先进入可编辑的消息草稿，发送前请纠错。也可以主动选择一段0.1–30秒、最多双声道、
12 MB以内的WAV录音，仅使用本人的声音或有权处理的材料。导入录音始终先成为草稿，不会
自动发送；程序不会删除所选原文件。发送文字仍遵循原有对话授权和本机对话保存规则。

可选的**逐轮语音**默认关闭。在草稿为空且已有OpenAI／上下文授权时，明确开启后，每次
听写结束会发送文字并朗读回复。因此识别错误也可能在纠正前发送给OpenAI。下一次录音仍需
主动点击。只使用所选语言的本机声音；没有声音时保留文字，不替换成远程语音。取消会停止
朗读并请求取消处理；已经发送的云端请求仍可能已被处理。这不是实时双向、持续监听或原生
ChatGPT语音模式。

当前官方ChatGPT套餐接入不支持音频或转写，见
[OpenAI预览限制](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)。
ChatGPT仍负责对话分析，Vosk只把声音转成文字；不能改用未披露的付费API或其他大模型。

验收分别记录：代码与测试、真实合成音频识别、浏览器／文件流程、安装后EXE、实体麦克风、
实际本机朗读声音及独立账号。实际结果见CURRENT_STATUS；下载或安装成功不能代替后面的
验收。识别准确度受说话方式及环境影响。
