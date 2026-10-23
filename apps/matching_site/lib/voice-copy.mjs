const en={
 title:'Speak or type',intro:'Dictation runs on this computer. Audio is not saved or sent to Sites or OpenAI. Review the text before sending it to ChatGPT.',
 file:'Or choose a short WAV recording',fileHint:'Up to 30 seconds. Use your own voice or a recording you have permission to process. Imported audio always becomes an editable draft, even in voice mode.',
 check:'Check voice setup',language:'Spoken language',en:'English',zh:'Chinese',install:'Download dictation model',download:'MB · public language model from Vosk; no conversation is sent.',
 missing:'Update the local assistant to a version with voice support. Text chat remains available.',ready:'Local dictation is ready.',checkFirst:'Check voice setup first. Download the selected language once if needed.',
 record:'Start dictation',stop:'Finish recording',cancel:'Cancel / stop',recording:'Recording · up to 30 seconds',permission:'Waiting for microphone permission. You can cancel.',working:'Processing locally…',error:'Voice could not finish. Check microphone permission and the selected language model, then try again or type.',
 draft:'Text added to your editable draft. Check recognition before sending.',overflow:'The draft would exceed 4,000 characters. Shorten it before recording again.',
 turn:'Enable turn-based voice: after I finish each recording, send its recognized text and my currently approved context to OpenAI, then read the reply on this device. I start each recording myself.',
 turnHint:'Requires an empty draft and the chat permissions above. Recognition can be wrong; leave this off to review text first. This is not continuous, full-duplex voice.',
 readDone:'Local playback finished.',readFailed:'Local playback could not finish. The text reply remains available.',read:'Read latest reply',reading:'Reading reply…',noVoice:'No local voice for this language is available. Text replies still work; no remote voice is substituted.',
 unavailable:'This browser cannot capture audio here. Open the local page in a supported desktop browser, or type.',paused:'Voice flow stopped. A request already sent to OpenAI may still have been processed.',
};
const zh={
 title:'说话或打字',intro:'听写在本机完成，音频不会保存或发送给Sites、OpenAI。默认先审阅文字，再发送给ChatGPT。',
 file:'或选择一段WAV录音',fileHint:'最长30秒，仅使用本人的声音或已获准处理的录音。导入录音始终先放入可编辑草稿，逐轮语音模式也不会自动发送。',
 check:'检查语音设置',language:'说话语言',en:'英语',zh:'中文',install:'下载听写模型',download:'MB · 来自Vosk的公开语言模型；不发送对话。',
 missing:'请更新到支持语音的本机助手。文字聊天仍可使用。',ready:'本机听写已就绪。',checkFirst:'先检查语音设置，需要时为所选语言下载一次模型。',
 record:'开始听写',stop:'结束录音',cancel:'取消／停止',recording:'正在录音 · 最长30秒',permission:'等待麦克风授权，可以取消。',working:'正在本机处理…',error:'语音未能完成。请检查麦克风权限和所选语言模型，然后重试或打字。',
 draft:'文字已放入可编辑草稿，发送前请检查识别结果。',overflow:'草稿将超过4000字，请缩短后再录音。',
 turn:'启用逐轮语音：每次结束录音后，将识别文字及当前已批准的上下文发送给OpenAI，再由本机朗读回复。每次录音仍由我主动开始。',
 turnHint:'需要空白草稿及上方聊天授权。识别可能有误；关闭此选项即可先审阅。这不是持续监听、实时双向语音。',
 readDone:'本机朗读已结束。',readFailed:'本机朗读未能完成，仍可阅读文字。',read:'朗读最新回复',reading:'正在朗读回复…',noVoice:'本机没有此语言的可用声音。仍可阅读文字，不会改用远程语音。',
 unavailable:'此浏览器当前无法录音。请在支持的桌面浏览器打开本机页面，或继续打字。',paused:'语音流程已停止；已经发送给OpenAI的请求仍可能已被处理。',
};
export function voiceText(locale,key){return (locale==='zh-CN'?zh:en)[key]||key;}
