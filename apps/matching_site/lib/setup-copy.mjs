export const setupMessages={
 title:['Get ready in a few guided steps','跟着引导，完成首次设置'],
 installed:['Already have ChatGPT? Skip the download. Choose Codex, open a local chat, and paste the setup instruction below.','已有ChatGPT？跳过下载，在应用中选择Codex，打开本机任务，粘贴下面的安装指令。'],
 download:['Download ChatGPT · official guide','下载ChatGPT · 官方指引'],
 folder:['Choose a new empty local folder for the Codex setup task, outside OneDrive or a source repository. Your private vault is selected separately in SlowMatch; the recommended account-owned folder is ready to use.','为Codex安装任务选择一个新的空本机文件夹，避开OneDrive和源码仓库。私人资料库在SlowMatch内另行选择，可直接使用推荐的账号专属位置。'],
 copy:['Copy setup instruction for Codex','复制给Codex的安装指令'],copied:['Copied. Paste into a local Codex chat.','已复制，请粘贴到Codex本机任务。'],
 start:['Open my installed assistant','打开已启动的助手'],
 startHint:['After setup, open Start-SlowMatch again whenever needed. The private conversation page runs on your computer, with no pairing-code copying. If the link cannot open, ask Codex to run the setup instruction.','安装后，日常打开Start-SlowMatch即可。私人对话页面在本机运行，不用复制配对码。链接打不开时，让Codex执行安装指令。'],
 advanced:['Advanced: connect this hosted page','高级：连接当前托管页面'],
 localTitle:['Your private conversation space','你的私人对话空间'],
 localBody:['This page is served by the installed assistant on this computer. Connect below, confirm your private folder, then start chatting. OpenAI processes only the context you authorize.','此页面由这台电脑上的助手提供。点击连接，确认私人文件夹，即可开始聊天。OpenAI仅处理你授权的上下文。'],
 connect:['Connect this local page','连接本机页面'],
 service:['Open discovery and friends on the Site','前往网站发现与好友'],
 custom:['Choose a different private folder','选择其他私人文件夹'],
 defaultFolder:['Use the recommended account-owned folder, or reconnect this account’s previously chosen folder. Nothing is published.','使用推荐的账号专属文件夹，或重连此账号上次选择的位置，不发布任何内容。'],
 bridgeFailure:['The hosted page could not reach your computer. Open the local conversation page instead; do not disable browser security settings.','当前托管页面未能连接电脑，请打开本机对话页面；无需关闭浏览器安全设置。'],
};
export const setupText=(locale,key)=>setupMessages[key]?.[locale==='zh-CN'?1:0]||key;
export function setupPrompt(locale){
 const guide='https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/v0.8.5/SETUP_WITH_CODEX.md';
 return locale==='zh-CN'?`请在这台Windows电脑为我安装或修复AI-SlowMatch 0.8.5，并启动可使用的本机对话页面。先只读取 ${guide}，按其中固定发布、哈希校验和确定性步骤执行。复用已有安装；无需克隆或审阅源码，不重新开发，不调用开发agent，不自动购买点数。保留已有资料和配置，不扫描旧档案。默认采用账号专属的非OneDrive本机位置；其他位置由我选择。完成程序自检和页面连接检查，明确区分安装、登录授权、私人库读写和真实AI回复。需要我亲自登录或批准时指出确切一步，不索要密码。安装完后告诉我下次只需打开哪个入口。`:
 `Install or repair AI-SlowMatch 0.8.5 on this Windows computer and open its usable local conversation page. Read only ${guide} first, then follow its pinned release, hash verification and deterministic setup. Reuse the existing installation. Do not clone/review source, rebuild the product, spawn development agents or buy credits. Preserve data/configuration and do not scan old vaults. Recommend the account-owned local folder outside OneDrive; let me select any alternative. Verify installation and the page connection; report sign-in permission, private storage and real AI reply separately. Identify the exact step requiring my own login or approval; never request passwords. Tell me the single entry to open next time.`;
}
