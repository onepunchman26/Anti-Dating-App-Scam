'use client';
import {useState} from 'react';
import {Compass,MapPin,ArrowRight,Heart,Users,ShieldCheck} from 'lucide-react';
import {validate,digest} from '../lib/summary.mjs';
import {errorKey} from '../lib/i18n.mjs';
import {useLanguage} from './language';
import SiteReminder from './site-reminder';
import FilePicker from './file-picker';
import PlanningClient from './planning-client';
import type {View} from './site-app';

type Mode='dating'|'friendship';
type SummaryValue={
 expires_at?:string;mode?:Mode;friendship_intent?:string;accepted_friendship_intents?:string[];activity_styles?:string[];interaction_frequency?:string;accepted_frequencies?:string[];boundaries?:string[];
 alias:string;age_band:string;city:string;areas:string[];relationship_goal:string;accepted_age_bands:string[];accepted_goals?:string[];values:string[];life_directions?:string[];communication_preferences:string[];interests:string[];preferences?:string[];discoverable:boolean;version:number;
};
type Candidate={public_id:string;summary:SummaryValue;explanation:{shared:Record<string,string[]>;potential_conflicts:string[]}};
type Shared={status?:'not_joined'|'withdrawn'|'expired'|'active'|'paused';summary?:SummaryValue;version:number;last_summary_version:number;discoverable:boolean;candidates:Candidate[];pool_limited:boolean;error?:string};
function Summary({value,currentDiscoverable}:{value:SummaryValue;currentDiscoverable?:boolean}){
 const {t,label,date}=useLanguage();
 return <dl className="summary">
  <dt>{t('alias')}</dt><dd>{value.alias}</dd><dt>{t('age')}</dt><dd>{value.age_band}</dd>
  <dt>{t('city')}</dt><dd>{value.city}</dd><dt>{t('areas')}</dt><dd>{value.areas.join(' · ')||value.city}</dd>
  <dt>{t('mode')}</dt><dd>{t(value.mode==='friendship'?'friendship':'dating')}</dd>
  <dt>{t('intent')}</dt><dd>{label(value.mode==='friendship'?value.friendship_intent:value.relationship_goal)}</dd>
  <dt>{t('mutual')}</dt><dd>{value.accepted_age_bands.join(', ')}<br/>{(value.accepted_goals||value.accepted_friendship_intents||[]).map(label).join(' · ')}</dd>
  {(['values','life_directions','communication_preferences','interests','preferences'] as const).map(key=>value.mode==='friendship'&&key==='life_directions'?null:<div className="summary-row" key={key}><dt>{t(key)}</dt><dd>{(value[key]||[]).map(label).join(' · ')||t('notShared')}</dd></div>)}
  {value.mode==='friendship'&&<><dt>{t('activity_styles')}</dt><dd>{value.activity_styles?.map(label).join(' · ')}</dd><dt>{t('frequency')}</dt><dd>{label(value.interaction_frequency)} · {value.accepted_frequencies?.map(label).join(' · ')}</dd><dt>{t('boundaries')}</dt><dd>{value.boundaries?.map(label).join(' · ')||t('notShared')}</dd></>}
  <dt>{t('audience')}</dt><dd>{t('eligible')}</dd><dt>{t('visibility')}</dt><dd>{t((currentDiscoverable??value.discoverable)?'enabled':'pausedShort')}</dd>
  <dt>{t('expiry')}</dt><dd>{value.expires_at?date(value.expires_at):t('legacy')}</dd><dt>{t('version')}</dt><dd>{value.version}</dd>
 </dl>;
}
export default function MatchingClient({view,navigate}:{view:View;navigate:(view:View)=>void}){
 const {t,label}=useLanguage();
 const [mode,setMode]=useState<Mode>('dating');
 const [planningPeer,setPlanningPeer]=useState<{id:string;alias:string}|null>(null);
 const [mine,setMine]=useState<Shared|null>(null),[draft,setDraft]=useState<SummaryValue|null>(null);
 const [candidates,setCandidates]=useState<Candidate[]|null>(null),[approved,setApproved]=useState(false);
 const [busy,setBusy]=useState(false),[status,setStatus]=useState(''),[failed,setFailed]=useState(false);
 const [region,setRegion]=useState(''),[interest,setInterest]=useState(''),[expanded,setExpanded]=useState<string|null>(null);
 const [fileKey,setFileKey]=useState(0);
 async function call(name:string,args:Record<string,unknown>):Promise<Shared>{
  const response=await fetch('/api/matching',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,arguments:{...args,mode}}),cache:'no-store'});
  const body=await response.json() as Shared;if(!response.ok||body.error)throw Error(body.error||'unavailable');return body;
 }
 async function run(action:()=>Promise<void>){
  setBusy(true);setStatus('');setFailed(false);
  try{await action();}catch(error){setStatus(errorKey(error instanceof Error?error.message:''));setFailed(true);}finally{setBusy(false);}
 }
 async function load(){setMine(await call('slowmatch_read_my_summary',{}));setCandidates(null);setExpanded(null);}
 async function pick(file:File|undefined){
  setDraft(null);setApproved(false);if(!file)return;
  await run(async()=>{if(file.size>12000)throw Error('invalid_summary');let value;try{value=validate(JSON.parse(await file.text()));}catch{throw Error('invalid_summary');}
   if(value.mode!==mode)throw Error('mode_mismatch');setDraft(value);setStatus('localPreview');});
 }
 function changeMode(next:Mode){
  if(next===mode)return;
  setMode(next);setMine(null);setDraft(null);setCandidates(null);setApproved(false);setPlanningPeer(null);setStatus('');setRegion('');setInterest('');setExpanded(null);setFileKey(k=>k+1);
 }
 const sharingLabel=mine?.status==='expired'?'profileExpired':mine?.status==='withdrawn'?'profileWithdrawn':mine?.summary?(mine.discoverable?'visible':'paused'):'notShared';
 const filtered=candidates?.filter(c=>(!region.trim()||[c.summary.city,...c.summary.areas].some(a=>a.toLocaleLowerCase().includes(region.trim().toLocaleLowerCase())))&&(!interest||c.summary.interests.includes(interest)));
 const interests=[...new Set(candidates?.flatMap(c=>c.summary.interests)||[])].sort();
 return <div className="workspace" hidden={view==='help'}>
  <div className="page-heading"><div className="heading-kicker"><p className="eyebrow">AI-SLOWMATCH</p><span className="pilot">{t('pilot')}</span></div><h1>{t(view==='profile'?'profileTitle':view==='plans'?'plansTitle':'discoverTitle')}</h1><p>{t(view==='profile'?'profileIntro':view==='plans'?'plansIntro':'discoverIntro')}</p></div>
  <div className="mode-row"><div className="segmented" role="group" aria-label={t('mode')}>{(['dating','friendship'] as const).map(m=><button key={m} disabled={busy} aria-pressed={mode===m} onClick={()=>changeMode(m)}>{m==='dating'?<Heart size={17} aria-hidden="true"/>:<Users size={17} aria-hidden="true"/>}{t(m)}</button>)}</div><p>{t('modeHint')}</p></div>
  <p role="status" aria-live="polite" className={'feedback '+(failed?'error':'')} hidden={!busy&&!status}>{busy?t('working'):status?t(status):''}</p>
  <section hidden={view!=='discover'} aria-label={t('discover')}>
   <SiteReminder/>
   {!mine?<div className="empty"><span className="empty-icon"><Compass size={32} aria-hidden="true"/></span><h2>{t('notLoaded')}</h2><p>{t('notLoadedBody')}</p><button disabled={busy} onClick={()=>run(load)}>{t('loadSummary')}<ArrowRight size={17} aria-hidden="true"/></button></div>:!mine.summary?<div className="empty"><span className="empty-icon"><HeartHandshakeIcon/></span><h2>{t('noSummary')}</h2><p>{t('noSummaryBody')}</p><button onClick={()=>navigate('profile')}>{t('manageProfile')}<ArrowRight size={17} aria-hidden="true"/></button></div>:<>
    <div className="status-strip"><span><span className={'status-dot '+(!mine.discoverable?'paused-dot':'')}/>{t(sharingLabel)}</span><button className="text-button" onClick={()=>navigate('profile')}>{t('manageProfile')}<ArrowRight size={16} aria-hidden="true"/></button></div>
    {!mine.discoverable?<div className="empty"><h2>{t(sharingLabel)}</h2><p>{t(mine.status==='expired'?'expiredBody':'pauseBody')}</p></div>:<div className="search-heading"><div><h2>{t('findIntro')}</h2><p>{t('findBody')}</p></div><button disabled={busy} onClick={()=>run(async()=>{const result=await call('slowmatch_find_candidates',{});setCandidates(result.candidates);setExpanded(null);if(result.pool_limited)setStatus('poolLimited');})}>{t('find')}<ArrowRight size={17} aria-hidden="true"/></button></div>}
    {candidates&&candidates.length>0&&<div className="filters"><label>{t('region')}<input type="search" value={region} onChange={e=>setRegion(e.target.value)} placeholder={t('regionPlaceholder')}/></label><label>{t('interest')}<select value={interest} onChange={e=>setInterest(e.target.value)}><option value="">{t('allInterests')}</option>{interests.map(i=><option key={i} value={i}>{label(i)}</option>)}</select></label><button className="quiet" disabled={!region&&!interest} onClick={()=>{setRegion('');setInterest('');}}>{t('reset')}</button><p className="filter-caption">{t('resultCount',{count:filtered?.length||0})} · {t('filterHint')}</p></div>}
    {candidates?.length===0&&<div className="empty"><span className="empty-icon"><Compass size={32} aria-hidden="true"/></span><h2>{t('noCandidates')}</h2><p>{t('noCandidatesBody')}</p></div>}
    {candidates&&candidates.length>0&&filtered?.length===0&&<div className="empty"><h2>{t('noFiltered')}</h2><button className="quiet" onClick={()=>{setRegion('');setInterest('');}}>{t('reset')}</button></div>}
    <div className="candidate-grid">{filtered?.map(c=><article className={'candidate '+(expanded===c.public_id?'is-expanded':'')} key={c.public_id}>
     <div className="candidate-top"><span className="avatar" aria-hidden="true">{Array.from(c.summary.alias)[0]}</span><div><h2>{c.summary.alias}</h2><p><MapPin size={14} aria-hidden="true"/>{c.summary.city} · {c.summary.age_band}</p></div></div>
     <p className="candidate-intent">{label(mode==='friendship'?c.summary.friendship_intent:c.summary.relationship_goal)}</p>
     <div className="tags">{c.summary.interests.slice(0,4).map(i=><span key={i}>{label(i)}</span>)}</div>
     <div className="shared-reason"><ShieldCheck size={17} aria-hidden="true"/><p>{Object.values(c.explanation.shared).flat().slice(0,3).map(label).join(' · ')||t('basicMatch')}</p></div>
     <button className="quiet full-width" aria-expanded={expanded===c.public_id} aria-controls={'candidate-'+c.public_id} onClick={()=>setExpanded(expanded===c.public_id?null:c.public_id)}>{t(expanded===c.public_id?'closeProfile':'viewProfile')}<ArrowRight size={16} aria-hidden="true"/></button>
     <div id={'candidate-'+c.public_id} hidden={expanded!==c.public_id} className="candidate-detail">
      <Summary value={c.summary}/><h3>{t('common')}</h3><p>{Object.values(c.explanation.shared).flat().map(label).join(' · ')||t('basicMatch')}</p>
      <h3>{t('questions')}</h3><p>{t(c.explanation.potential_conflicts.length?'familyDifference':'otherUnknowns')}</p><p className="muted">{t('unverified')}</p><SiteReminder/>
      <p>{t('privateNext')}</p><button disabled={busy} onClick={()=>{setPlanningPeer({id:c.public_id,alias:c.summary.alias});navigate('plans');}}>{t('activity')}<ArrowRight size={17} aria-hidden="true"/></button>
     </div>
    </article>)}</div>
   </>}
  </section>
  <section hidden={view!=='profile'} className="profile-layout" aria-label={t('profile')}>
   <div className="panel"><div className="section-heading"><h2>{t('currentProfile')}</h2><button className="quiet" disabled={busy} onClick={()=>run(load)}>{t(mine?'refresh':'loadSummary')}</button></div>
    {mine?<><p className="status-badge">{t(sharingLabel)}</p>{mine.summary?<Summary value={mine.summary} currentDiscoverable={mine.discoverable}/>:<p>{t('noSummary')}</p>}
     <details className="record-details"><summary>{t('version')}</summary><p>{t('serverVersion')}: {mine.version} · {t('lastVersion')}: {mine.last_summary_version}</p></details>
     {mine.summary&&<div className="actions"><button disabled={busy||mine.status==='expired'} onClick={()=>run(async()=>{setMine(await call('slowmatch_set_discoverability',{discoverable:!mine.discoverable,expected_version:mine.version}));setCandidates(null);})}>{t(mine.discoverable?'pause':'resume')}</button><button className="text-button danger" disabled={busy} onClick={()=>{if(confirm(t('deleteConfirm')))run(async()=>{setMine(await call('slowmatch_delete_my_summary',{expected_version:mine.version}));setCandidates(null);setDraft(null);setApproved(false);setFileKey(k=>k+1);});}}>{t('deleteSummary')}</button></div>}
    </>:<p>{t('loadBeforePublish')}</p>}
   </div>
   <div className="panel"><h2>{t('reviewShare')}</h2><p>{t('importIntro')}</p><FilePicker key={fileKey} title={t('importSummary')} disabled={busy} onPick={pick}/>{failed&&['error_invalid_summary','error_mode_mismatch'].includes(status)&&<p className="field-error">{t(status)}</p>}
    {draft&&<><p className="status-badge">{t('localPreview')}</p><Summary value={draft}/><SiteReminder compact={false}/><label className="consent"><input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}/><span>{t('reviewConsent')}</span></label>{!mine&&<p>{t('loadBeforePublish')}</p>}<button disabled={busy||!approved||!mine} onClick={()=>run(async()=>{setMine(await call('slowmatch_publish_summary',{summary:draft,approved_digest:await digest(draft),expected_version:mine!.version}));setCandidates(null);setDraft(null);setApproved(false);setFileKey(k=>k+1);setStatus('published');})}>{t('publish')}</button></>}
   </div>
  </section>
  <div hidden={view!=='plans'}><PlanningClient key={mode} mode={mode} candidatePublicId={planningPeer?.id||null} candidateAlias={planningPeer?.alias}/></div>
 </div>;
}
function HeartHandshakeIcon(){return <Users size={32} aria-hidden="true"/>;}
