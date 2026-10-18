'use client';
import {useEffect,useState} from 'react';
import {CalendarDays,Clock,Wallet,UserRound} from 'lucide-react';
import {digest,validate} from '../lib/summary.mjs';
import preferenceSchema from '../lib/shared-planning-preferences.schema.json';
import planSchema from '../lib/meeting-plan.schema.json';
import {errorKey} from '../lib/i18n.mjs';
import {useLanguage} from './language';
import SiteReminder from './site-reminder';
import FilePicker from './file-picker';
type Preferences={mode:string;areas:string[];availability:{start_at:string;end_at:string}[];budget:{currency:string;max_per_person_minor:number};duration_minutes:number;interests:string[];environment:string[];arrangement_needs:string[];expires_at:string};
type Option={planning_area:string;source_open_window?:{start_at:string;end_at:string}|null;source_admission?:{currency:string;amount_minor:number}|null;source_event_at?:string|null;option_id:string;place_name:string;address_or_area:string;source_urls:string[];checked_at:string;verification:string;verified_facts:string[];unknowns:string[];start_at:string;duration_minutes:number;estimated_budget_minor:number;currency:string;sequence:string[];shared_interest_reasons:string[];conversation_starters:string[];fallback:string};
type Plan={requirements:{environment:string[];arrangement_needs:string[];status:string};budget_basis:string;mode:string;version:number;expires_at:string;options:Option[]};
type Session={planning_id:string;version:number;status:string;expires_at:string;my_public_id:string;my_preferences:Preferences|null;plan:Plan|null;plan_digest:string|null;plan_version:number;both_confirmed:boolean;agreed_option_id:string|null;participants:{public_id:string;preferences_status:string;confirmation:{plan_version:number;option_id:string}|null;feedback:{choice:string}|null}[]};
function sourceHost(value:string){try{const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password||u.search||u.hash||u.port||!u.hostname.includes('.')||/^[\d.]+$/.test(u.hostname)||u.hostname.endsWith('.local')||u.hostname.endsWith('.internal'))return null;return u.hostname;}catch{return null;}}
function Prefs({value}:{value:Preferences}){
 const {t,label,date}=useLanguage();
 return <dl className="summary">
 <dt>{t('areas')}</dt><dd>{value.areas.join(' · ')}</dd><dt>{t('available')}</dt><dd>{value.availability.map(w=><p key={w.start_at}>{date(w.start_at)} – {date(w.end_at)}</p>)}</dd>
 <dt>{t('budget')}</dt><dd>{value.budget.currency} {value.budget.max_per_person_minor/100}</dd><dt>{t('duration')}</dt><dd>{t('minutes',{count:value.duration_minutes})}</dd>
 <dt>{t('interests')}</dt><dd>{value.interests.map(label).join(' · ')}</dd><dt>{t('environment')}</dt><dd>{value.environment.map(label).join(' · ')}</dd>
 <dt>{t('arrangement')}</dt><dd>{value.arrangement_needs.map(label).join(' · ')||t('notShared')}</dd><dt>{t('expiry')}</dt><dd>{date(value.expires_at)}</dd></dl>;
}
function Plans({plan}:{plan:Plan}){
 const {t,label,date}=useLanguage();
 return <><p className="muted small">{t('timezone')}</p><p className="muted">{t('suitability')}: {[...plan.requirements.environment,...plan.requirements.arrangement_needs].map(label).join(' · ')}</p>
 <div className="planning-grid">{plan.options.map(o=><article className="planning-card" key={o.option_id}>
  <span className="option-number">{o.option_id.toUpperCase()}</span><h3>{o.place_name}</h3><p className="muted">{o.address_or_area} · {o.planning_area}</p>
  <div className="plan-facts"><p><CalendarDays size={17} aria-hidden="true"/>{date(o.start_at)}</p><p><Clock size={17} aria-hidden="true"/>{t('minutes',{count:o.duration_minutes})}</p><p><Wallet size={17} aria-hidden="true"/>{o.currency} {o.estimated_budget_minor/100}</p><small>{t('priceHint')}</small></div>
  <p>{o.sequence.map(label).join(' → ')}</p><div className="tags">{o.shared_interest_reasons.map(v=><span key={v}>{label(v)}</span>)}</div>
  <h4>{t('conversationIdeas')}</h4><p>{o.conversation_starters.map(label).join(' · ')}</p>
  <details className="sources"><summary>{t('sources')}</summary><p>{t('checked')}: {date(o.checked_at)} · {label(o.verification)}</p>
   {o.source_open_window&&<p>{t('opening')}: {date(o.source_open_window.start_at)} – {date(o.source_open_window.end_at)}</p>}
   {o.source_admission&&<p>{t('admission')}: {o.source_admission.currency} {o.source_admission.amount_minor/100}</p>}
   {o.source_event_at&&<p>{t('eventTime')}: {date(o.source_event_at)}</p>}
   <p>{t('checkedFields')}: {o.verified_facts.map(label).join(' · ')||t('none')}</p>
   {o.source_urls.map(url=><p key={url}>{sourceHost(url)?<a href={url} target="_blank" rel="noreferrer">{sourceHost(url)} ↗</a>:t('invalidSource')}</p>)}
   <p>{t('unknowns')}: {o.unknowns.map(label).join(' · ')}</p>
  </details>
  <p className="muted small">{t('independentArrival')}</p><p className="fallback">{t('fallback')}: {label(o.fallback)}</p>
 </article>)}</div></>;
}
export default function PlanningClient({mode,candidatePublicId,candidateAlias}:{mode:'dating'|'friendship';candidatePublicId:string|null;candidateAlias?:string}){
 const {t,label,date}=useLanguage();
 const [sessions,setSessions]=useState<Session[]|null>(null),[selected,setSelected]=useState<Session|null>(null),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[failed,setFailed]=useState(false);
 const [createConsent,setCreateConsent]=useState(false),[expires,setExpires]=useState(''),[prefs,setPrefs]=useState<Preferences|null>(null),[plan,setPlan]=useState<Plan|null>(null),[approved,setApproved]=useState(false),[option,setOption]=useState(''),[feedback,setFeedback]=useState(''),[fileKey,setFileKey]=useState(0);
 useEffect(()=>{setCreateConsent(false);setExpires('');},[candidatePublicId]);
 async function call<T=Session>(name:string,args:Record<string,unknown>={}):Promise<T>{
  const response=await fetch('/api/matching',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'slowmatch_planning_'+name,arguments:{mode,...args}}),cache:'no-store'});
  const value=await response.json() as T & {error?:string};if(!response.ok||value.error)throw Error(value.error||'unavailable');return value;
 }
 async function run(action:()=>Promise<void>){setBusy(true);setMessage('');setFailed(false);try{await action();}catch(error){setMessage(errorKey(error instanceof Error?error.message:''));setFailed(true);}finally{setBusy(false);}}
 function choose(s:Session){setSelected(s);setPrefs(null);setPlan(null);setApproved(false);setOption('');setFeedback('');setFileKey(k=>k+1);setSessions(previous=>previous?.map(p=>p.planning_id===s.planning_id?s:p)||null);}
 async function pick(file:File|undefined,kind:'preferences'|'plan'){
  setPrefs(null);setPlan(null);setApproved(false);if(!file||!selected)return;
  await run(async()=>{
   if(file.size>14000)throw Error('invalid_file');
   let envelope;try{envelope=JSON.parse(await file.text());}catch{throw Error('invalid_file');}
   if(envelope.content&&(envelope.destination!==location.origin||!selected.participants.some(p=>p.public_id!==selected.my_public_id&&p.public_id===envelope.recipient_public_id)))throw Error('scope_mismatch');
   const value=envelope.content||envelope;try{validate(value,kind==='preferences'?preferenceSchema:planSchema);}catch{throw Error('invalid_file');}
   if(value.mode!==mode)throw Error('mode_mismatch');
   if(kind==='plan'&&value.options.some((o:Option)=>o.source_urls.some(u=>!sourceHost(u))))throw Error('invalid_source');
   if(kind==='preferences')setPrefs(value);else setPlan(value);setMessage('localPreview');
  });
 }
 const closed=selected&&['withdrawn','expired'].includes(selected.status);
 return <section aria-label={t('plans')}>
  <SiteReminder/><p className="muted">{t('optionalPlan')}</p>
  {candidatePublicId&&<section className="panel new-plan"><h2>{t('newPlan')}</h2><p className="selected-person"><UserRound size={20} aria-hidden="true"/>{candidateAlias}</p><SiteReminder compact={false}/>
   <label>{t('planExpiry')}<input type="datetime-local" value={expires} onChange={e=>setExpires(e.target.value)}/></label>
   <label className="consent"><input type="checkbox" checked={createConsent} onChange={e=>setCreateConsent(e.target.checked)}/><span>{t('createConsent')}</span></label>
   <button disabled={busy||!createConsent||!expires} onClick={()=>run(async()=>{choose(await call('create',{candidate_public_id:candidatePublicId,expires_at:new Date(expires).toISOString(),explicit_invitation:true}));setCreateConsent(false);setMessage('created');})}>{t('createPlan')}</button>
  </section>}
  <div className="section-heading"><h2>{t('plans')}</h2><button className="quiet" disabled={busy} onClick={()=>run(async()=>{const result=await call<{sessions:Session[]}>('list');setSessions(result.sessions);})}>{t('readPlans')}</button></div>
  {sessions?.length===0&&<div className="empty"><span className="empty-icon"><CalendarDays size={32} aria-hidden="true"/></span><h3>{t('noPlans')}</h3><p>{t('noPlansBody')}</p></div>}
  <div className="session-list">{sessions?.map((s,i)=><button key={s.planning_id} className="quiet session-button" disabled={busy} aria-pressed={selected?.planning_id===s.planning_id} onClick={()=>run(async()=>choose(await call('read',{planning_id:s.planning_id})))}><strong>{t('planNumber',{count:i+1})}</strong><span>{label(s.status)} · {date(s.expires_at)}</span></button>)}</div>
  {selected&&<section className="panel selected-plan"><div className="section-heading"><div><h2>{label(selected.status)}</h2><span className="status-badge">{t(selected.both_confirmed?'bothConfirmed':'awaitingConfirmation')}</span></div><button className="quiet" disabled={busy} onClick={()=>run(async()=>choose(await call('read',{planning_id:selected.planning_id})))}>{t('refreshPlan')}</button></div><p>{t('planExpiry')}: {date(selected.expires_at)}</p>
   {!closed&&<>
    <div className="participant-grid">{selected.participants.map(p=><div key={p.public_id}><strong>{t(p.public_id===selected.my_public_id?'you':'peer')}</strong><p>{t('prefsState',{state:label(p.preferences_status)})}</p><p>{p.confirmation?t('choiceConfirmed',{option:p.confirmation.option_id.toUpperCase(),version:p.confirmation.plan_version}):t('choicePending')}</p></div>)}</div>
    {selected.my_preferences&&<details><summary>{t('myPreferences')}</summary><Prefs value={selected.my_preferences}/></details>}
    <details className="planning-import"><summary>{t('reviewShare')}</summary><p>{t('preparePlan')}</p><div className="import-grid">
     <FilePicker key={'prefs'+fileKey} title={t('importPrefs')} disabled={busy} onPick={file=>pick(file,'preferences')}/>
     <FilePicker key={'plan'+fileKey} title={t('importPlan')} disabled={busy} onPick={file=>pick(file,'plan')}/>
    </div>
    {prefs&&<Prefs value={prefs}/ >}{plan&&<Plans plan={plan}/>}
    {(prefs||plan)&&<><p className="status-badge">{t('localPreview')}</p><label className="consent"><input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}/><span>{t('planningConsent')}</span></label><button disabled={busy||!approved} onClick={()=>run(async()=>{const content=prefs||plan;choose(await call(prefs?'preferences':'propose',{planning_id:selected.planning_id,[prefs?'preferences':'plan']:content,approved_digest:await digest(content),approved:true,expected_version:selected.version}));})}>{t('shareVersion')}</button></>}
    </details>
    <button className="quiet context-button" disabled={busy||selected.participants.some(p=>p.preferences_status!=='approved')} onClick={()=>run(async()=>{const value=await call('context',{planning_id:selected.planning_id});const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='slowmatch-shared-planning-context.json';link.click();URL.revokeObjectURL(url);setMessage('contextDownloaded');})}>{t('getContext')}</button>
    {selected.plan&&<section className="proposal"><h2>{t('proposalVersion',{version:selected.plan.version})}</h2><Plans plan={selected.plan}/><div className="choice-row"><label>{t('myChoice')}<select value={option} onChange={e=>setOption(e.target.value)}><option value="">{t('chooseReviewed')}</option>{selected.plan.options.map(o=><option key={o.option_id} value={o.option_id}>{o.option_id.toUpperCase()} · {o.place_name}</option>)}</select></label><button disabled={busy||!option} onClick={()=>run(async()=>choose(await call('confirm',{planning_id:selected.planning_id,plan_version:selected.plan_version,plan_digest:selected.plan_digest,option_id:option,expected_version:selected.version})))}>{t('confirmChoice')}</button></div></section>}
    {selected.both_confirmed&&<section className="feedback-section"><p>{t('agreed',{option:selected.agreed_option_id?.toUpperCase()||''})}</p><label>{t('feedback')}<select value={feedback} onChange={e=>setFeedback(e.target.value)}><option value="">{t('feedbackPrivate')}</option>{['again','undecided','not_now','no_again'].map(v=><option key={v} value={v}>{label(v)}</option>)}</select></label><button disabled={busy||!feedback} onClick={()=>run(async()=>choose(await call('feedback',{planning_id:selected.planning_id,plan_version:selected.plan_version,choice:feedback,expires_at:selected.expires_at,approved:true,expected_version:selected.version})))}>{t('shareFeedback')}</button>{selected.participants.map(p=><p key={p.public_id}>{t(p.public_id===selected.my_public_id?'you':'peer')}: {p.feedback?label(p.feedback.choice):t('feedbackUnknown')}</p>)}</section>}
    <div className="withdraw-actions">{selected.participants.some(p=>p.public_id===selected.my_public_id&&p.feedback)&&<button className="text-button" disabled={busy} onClick={()=>run(async()=>choose(await call('feedback_withdraw',{planning_id:selected.planning_id,expected_version:selected.version})))}>{t('withdrawFeedback')}</button>}
    <button className="text-button danger" disabled={busy} onClick={()=>run(async()=>choose(await call('withdraw',{planning_id:selected.planning_id,expected_version:selected.version})))}>{t('withdrawPlan')}</button></div>
   </>}
  </section>}
  <p role="status" aria-live="polite" className={'feedback '+(failed?'error':'')} hidden={!busy&&!message}>{busy?t('working'):message?t(message):''}</p>
 </section>;
}
