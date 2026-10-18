'use client';
import { useState } from 'react';
import { validate, digest } from '../lib/summary.mjs';
import { label } from '../lib/labels.mjs';
type SummaryValue = {
  alias:string; age_band:string; city:string; areas:string[]; relationship_goal:string;
  accepted_age_bands:string[]; accepted_goals:string[]; values:string[];
  life_directions:string[]; communication_preferences:string[]; interests:string[];
  preferences:string[]; discoverable:boolean; version:number;
};
type Candidate = {public_id:string; summary:SummaryValue; explanation:{shared:Record<string,string[]>;potential_conflicts:string[]}};
type Shared = {summary?:SummaryValue; version:number;last_summary_version:number;discoverable:boolean;candidates:Candidate[];pool_limited:boolean;error?:string};
const errors:Record<string,string>={
  version_conflict:'The server has a newer version. Reload your summary before trying again. / 服务端已有新版本，请重新读取摘要。',
  summary_version_must_increase:'Approve a newer summary version in ChatGPT, including after deletion. / 请在 ChatGPT 中批准更高版本的摘要；删除后重新发布也需要新版本。',
  rate_limit_try_next_hour:'Pilot query limit reached. Try next hour. / 已达试运行查询上限，请下一小时再试。',
  sign_in_required:'Your sign-in has expired. Sign in again. / 登录已过期，请重新登录。',
  invalid_summary:'This file is not an allowed summary. Export an approved summary from the plugin. / 此文件不是允许的摘要，请使用插件导出已批准摘要。',
  approval_content_mismatch:'Summary content changed after approval. Review again. / 摘要与批准内容不一致，请重新审阅。',
  publish_and_enable_discovery_first:'Publish your own approved summary and enable discovery first. / 请先发布本人批准的摘要并启用匹配。',
  new_approved_summary_required:'This change needs a new approved summary in ChatGPT. / 此变更需要在 ChatGPT 中批准新摘要。',
};
function Summary({value}:{value:SummaryValue}) {
  return <dl className="summary">
    <dt>Alias / 化名</dt><dd>{value.alias}</dd><dt>Age band / 年龄段</dt><dd>{value.age_band}</dd>
    <dt>City / 城市</dt><dd>{value.city}</dd><dt>Accepted areas / 接受地区</dt><dd>{value.areas.join(' · ')||value.city}</dd>
    <dt>Goal / 关系目标</dt><dd>{label(value.relationship_goal)}</dd>
    <dt>Mutual conditions / 双方条件</dt><dd>{value.accepted_age_bands.join(', ')}<br/>{value.accepted_goals.map(label).join(' · ')}</dd>
    {(['values','life_directions','communication_preferences','interests','preferences'] as const).map((key,i)=><div className="summary-row" key={key}><dt>{['Values / 价值观','Life direction / 人生方向','Communication / 沟通偏好','Interests / 兴趣','Soft preferences / 软偏好'][i]}</dt><dd>{value[key].map(label).join(' · ')||'Not shared / 未分享'}</dd></div>)}
    <dt>Audience / 范围</dt><dd>Eligible signed-in participants / 符合条件的已登录参与者</dd>
    <dt>Discovery / 匹配</dt><dd>{value.discoverable?'Enabled / 启用':'Paused / 暂停'}</dd>
    <dt>Summary version / 摘要版本</dt><dd>{value.version}</dd>
  </dl>;
}
export default function MatchingClient() {
  const [mine,setMine]=useState<Shared|null>(null);const [draft,setDraft]=useState<SummaryValue|null>(null);
  const [candidates,setCandidates]=useState<Candidate[]|null>(null);const [approved,setApproved]=useState(false);
  const [busy,setBusy]=useState(false);const [status,setStatus]=useState('');
  async function call(name:string,args:Record<string,unknown>):Promise<Shared> {
    const response=await fetch('/api/matching',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,arguments:args}),cache:'no-store'});
    const body=await response.json() as Shared;if(!response.ok||body.error) throw Error(body.error||'unavailable');return body;
  }
  async function run(action:()=>Promise<void>) {
    setBusy(true);setStatus('');
    try{await action();}catch(error){const key=error instanceof Error?error.message:'';setStatus(errors[key]||'Operation not confirmed. Check your connection and reload before retrying. / 操作未确认成功，请检查连接并重新读取后再试。');}
    finally{setBusy(false);}
  }
  async function load() {setMine(await call('slowmatch_read_my_summary',{}));setCandidates(null);}
  async function pick(file:File|undefined) {
    setDraft(null);setApproved(false);if(!file)return;
    await run(async()=>{if(file.size>12000)throw Error('invalid_summary');const value=validate(JSON.parse(await file.text()));setDraft(value);setStatus('Previewed locally; nothing uploaded. / 已在本地预览，尚未上传。');});
  }
  return <div className="workspace">
    <section className="panel"><div className="section-title"><span className="step">01</span><div><h2>Your shared summary / 我的共享摘要</h2><p>Read the current server version before publishing. / 发布前先读取当前服务版本。</p></div></div>
      <button disabled={busy} onClick={()=>run(load)}>Read my summary / 读取我的摘要</button>
      {mine && <><p className="status">Server version {mine.version} / 服务版本 {mine.version} · Last summary version {mine.last_summary_version} / 最近摘要版本 {mine.last_summary_version} · {mine.discoverable?'Discoverable / 可被发现':'Not discoverable / 不可被发现'}</p>
        {mine.summary?<Summary value={mine.summary}/>:<p>No shared summary. / 尚无共享摘要。</p>}
        {mine.summary&&<div className="actions"><button disabled={busy} onClick={()=>run(async()=>{setMine(await call('slowmatch_set_discoverability',{discoverable:!mine.discoverable,expected_version:mine.version}));setCandidates(null);})}>{mine.discoverable?'Pause matching / 暂停匹配':'Resume matching / 恢复匹配'}</button>
        <button className="quiet" disabled={busy} onClick={()=>{if(confirm('Delete your shared summary and leave matching? Previously saved copies cannot be recalled. / 删除共享摘要并退出匹配？无法收回他人已保存的副本。'))run(async()=>{setMine(await call('slowmatch_delete_my_summary',{expected_version:mine.version}));setCandidates(null);setDraft(null);setApproved(false);});}}>Delete shared summary / 删除共享摘要</button></div>}
      </>}
    </section>
    <section className="panel"><div className="section-title"><span className="step">02</span><div><h2>Review, then share / 审阅后再分享</h2><p>Normally publish through the plugin. This optional file route accepts only its approved summary export. / 日常可直接通过插件发布；此备用入口只接收插件导出的批准摘要。</p></div></div>
      <label className="file">Choose approved summary JSON / 选择已批准的摘要 JSON<input type="file" accept="application/json,.json" disabled={busy} onChange={e=>pick(e.target.files?.[0])}/></label>
      {draft&&<><Summary value={draft}/><label className="consent"><input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}/>I confirm I am 18 or older and approve sharing exactly these fields with eligible signed-in participants on this Site. / 我确认本人已满 18 岁，并批准将这里展示的具体字段分享给本站符合条件的已登录参与者。</label>
      <button disabled={busy||!approved||!mine} onClick={()=>run(async()=>{setMine(await call('slowmatch_publish_summary',{summary:draft,approved_digest:await digest(draft),expected_version:mine!.version}));setCandidates(null);setDraft(null);setApproved(false);setStatus('Server confirmed saved summary. / 服务端已确认保存摘要。');})}>Publish this version / 发布此版本</button></>}
    </section>
    <section className="panel wide"><div className="section-title"><span className="step">03</span><div><h2>Start with shared ground / 从共同点开始</h2><p>Both people’s city, age-band and goal conditions must pass. Preferences guide discussion, not a score. / 双方地区、年龄段和关系目标条件均须满足；偏好用于交流，不产生评分。</p></div></div>
      <button disabled={busy||!mine?.discoverable} onClick={()=>run(async()=>{const result=await call('slowmatch_find_candidates',{});setCandidates(result.candidates);if(result.pool_limited)setStatus('Pilot searches at most 100 active summaries. / 试运行最多检索一百份活跃摘要。');})}>Find candidates / 查看候选</button>
      {candidates?.length===0&&<div className="empty"><h3>No candidates yet / 暂无候选</h3><p>No active shared summary currently meets both sides’ conditions. / 当前没有活跃共享摘要符合双方条件。</p></div>}
      <div className="candidate-grid">{candidates?.map(c=><article className="candidate" key={c.public_id}><h3>{c.summary.alias}</h3><Summary value={c.summary}/>
        <h4>Shared reasons / 共享依据</h4><p>{Object.values(c.explanation.shared).flat().map(label).join(' · ')||'Mutual basic conditions pass; shared interests remain unknown. / 双方基础条件满足，共同兴趣仍待了解。'}</p>
        <p>{c.explanation.potential_conflicts.length?'Family plans may differ; discuss respectfully. / 家庭计划可能不同，值得尊重地交流。':'Other differences may be acceptable; ask each other. / 其他差异是否可接受，需要彼此交流。'}</p>
        <p className="muted">Identity and self-reports are not verified. Private profiles were not compared. / 身份和自述未经核验，未比较私人档案。</p>
        <p>In your ChatGPT, ask SlowMatch to discuss this candidate privately using your local profile. / 在自己的 ChatGPT 中，请 SlowMatch 结合本机档案私下讨论这位候选。</p>
      </article>)}</div>
    </section>
    <p role="status" aria-live="polite" className="feedback">{busy?'Working… / 正在处理…':status}</p>
  </div>;
}
