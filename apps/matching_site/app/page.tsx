import { getChatGPTUser, chatGPTSignInPath, chatGPTSignOutPath } from './chatgpt-auth';
import MatchingClient from './matching-client';
import SiteReminder from './site-reminder';
import Link from 'next/link';
export const dynamic='force-dynamic';
export default async function Home() {
  const user=await getChatGPTUser();
  return <><header className="top"><Link href="/" className="brand"><span className="brand-icon">S</span> AI-SlowMatch <small>慢慢相识</small></Link><span className="pilot">Private pilot / 私人试运行</span><a href={user?chatGPTSignOutPath('/'):chatGPTSignInPath('/')} target="_top">{user?'Sign out / 退出登录':'Sign in / 登录'}</a></header>
    <main><section className="hero"><p className="eyebrow">YOUR CONVERSATION. YOUR CHOICES. YOUR PACE.</p><h1>Make room for<br/><em>a real connection.</em></h1><h2>给真实的关系，留一点时间。</h2><p>Begin in your own ChatGPT. Understand what matters to you.<br/>Share a little, ask thoughtfully, and decide for yourself.</p><p>从自己的 ChatGPT 开始，理解内心与人生方向。<br/>适度分享，认真交流，把选择留给自己。</p></section>
    <section className="boundary"><div><b>Private with you / 私密内容由你掌握</b><p>Full profile and personal analysis stay in your local workflow. OpenAI cloud processing follows your ChatGPT settings. / 完整档案与私人分析以本机工作流为主存；OpenAI 云端处理遵循你的 ChatGPT 设置。</p></div><div><b>Shared by choice / 分享由你决定</b><p>This Site stores separately approved dating or friendship summaries, shared activity preferences and plans, optional minimal feedback, and essential account/status data. / 本站保存分别批准的恋爱或交友摘要、共享活动偏好与计划、可选的最少反馈及必要账号／状态；不保存原始聊天或私人分析。</p></div></section>
    <SiteReminder/>
    {user?<MatchingClient/>:<section className="panel"><h2>A small step, on your terms / 按自己的节奏迈出一步</h2><p>Open the AI-SlowMatch plugin in desktop ChatGPT Work. Your profile begins empty. Sign in here to manage the summary you choose to publish. / 在桌面 ChatGPT Work 中打开 AI-SlowMatch 插件，档案初始为空。登录本站后可管理你决定发布的摘要。</p><a className="button" href={chatGPTSignInPath('/')} target="_top">Continue with ChatGPT / 使用 ChatGPT 继续</a></section>}
    <footer><p>Adults only. Self-reported information, never a diagnosis, personality rank or safety guarantee. / 仅限成年人。资料来自本人自述，不构成诊断、人格排名或安全保证。</p><p>Withdrawal removes current discovery and display. Copies saved by others and platform backups may remain. / 撤回会停止当前匹配与展示；他人保存的副本及平台备份可能仍然存在。</p><p>Built on the original AI-SlowMatch Python project. Sites/Vinext starter and MIT build integration used with thanks. / 基于原 AI-SlowMatch Python 项目，感谢 Sites／Vinext 模板与 MIT 构建整合。</p></footer>
    </main></>;
}
