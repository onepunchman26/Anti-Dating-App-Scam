'use client';
import {useState,useEffect} from 'react';
import {useLanguage} from './language';
import {onboardingText} from '../lib/onboarding.mjs';
import type {View} from './site-app';
import {rememberLocal,localCall} from '../lib/local-connection';
import {socialText} from '../lib/social-copy.mjs';
import SiteReminder from './site-reminder';
import InterviewPanel,{type InterviewState} from './interview-panel';
import {interviewText} from '../lib/interview.mjs';
import SetupGuide from './setup-guide';
import PrivateMatchPanel from './private-match-panel';
import {setupText} from '../lib/setup-copy.mjs';

const LOCAL='http://127.0.0.1:8911';
type Status={capabilities?:string[];account_label:string;connected:boolean;plan_permission:boolean;vault_ready:boolean;vault_path:string;inference_passed:boolean;models:{slug:string;display_name:string}[]};
type Session={id:string;topic:string;revision:number;messages:{role:string;content:string}[];interview?:InterviewState|null};
type Profile={revision:number;claims:{id:string;text:string}[]};
export default function OnboardingClient({navigate,localMode=false}:{navigate:(view:View)=>void;localMode?:boolean}){
 const {locale}=useLanguage();const w=(key:string)=>onboardingText(locale,key);
 const [code,setCode]=useState(()=>localMode?document.querySelector('meta[name="slowmatch-pair"]')?.getAttribute('content')||'':''),[status,setStatus]=useState<Status|null>(null),[model,setModel]=useState('');
 const [path,setPath]=useState(''),[vaultConsent,setVaultConsent]=useState(false),[cloudConsent,setCloudConsent]=useState(false),[usage,setUsage]=useState(false),[includeProfile,setIncludeProfile]=useState(false);
 const [topic,setTopic]=useState('dating'),[session,setSession]=useState<Session|null>(null),[sessions,setSessions]=useState<Session[]>([]),[message,setMessage]=useState(''),[reuseId,setReuseId]=useState('');
 const [profile,setProfile]=useState<Profile|null>(null),[claim,setClaim]=useState(''),[claimId,setClaimId]=useState<string|null>(null),[claimConsent,setClaimConsent]=useState(false);
 const [busy,setBusy]=useState(false),[feedback,setFeedback]=useState(''),[failed,setFailed]=useState(false);
 useEffect(()=>{rememberLocal(code,model);},[code,model]);
 async function call(operation:string,args:Record<string,unknown>={}){
  return localCall(code,operation,args);
 }
 async function run(action:()=>Promise<void>){setBusy(true);setFeedback('');setFailed(false);try{await action();}catch(error){const key=error instanceof Error?error.message:'';setFeedback(key==='unreachable'||key==='pairing_required'?'unreachable':key==='account_changed'?'accountChanged':key==='revision_conflict'?'conflict':key.includes('vault')||key==='private_directory_required'?'existingVault':'error');setFailed(true);}finally{setBusy(false);}}
 async function check(){const next=await call('status');if(next.protocol!=='1.0')throw Error('error');if(next.connected&&!next.models.length){next.models=await call('models');}if(!model&&next.models.length)setModel(next.models.find((m:{slug:string})=>m.slug==='gpt-6.1-sol')?.slug||next.models[0].slug);setStatus(next);}
 async function readSessions(){setSessions(await call('sessions'));}
 async function readProfile(){setProfile(await call('profile-read'));}
 async function send(text=message){await run(async()=>{try{const next=await call('send',{session_id:session!.id,expected_revision:session!.revision,text,language:locale,model,cloud_consent:cloudConsent,included_plan_confirmed:usage,include_profile:includeProfile});setSession(next);setMessage('');await check();}catch(error){try{setSession(await call('session-read',{session_id:session!.id}));}catch{}throw error;}});}
 async function controlInterview(action:string,area?:string,text=''){await run(async()=>{setSession(await call('interview-control',{session_id:session!.id,expected_revision:session!.revision,action,...(area?{area}:{}),text,confirmed:true}));});}
 const guided=topic==='dating'||topic==='friendship';
 const interviewReady=status?.capabilities?.includes('relationship-interview-v1');
 const iw=(key:string)=>interviewText(locale,key);
 const sw=(key:string)=>setupText(locale,key);
 async function updateClaim(remove=false){await run(async()=>{
  const current=profile||await call('profile-read');
  const changes=remove?[{action:'remove',claim_id:claimId}]:[{action:'upsert',claim:{...(claimId?{id:claimId}:{}),topic:'open_question',text:claim,source:{source_type:'self_report',reference:'Owner-reviewed web statement',quote:claim},confirmation:claimId?'corrected':'confirmed',uncertainty:'User report; not independently verified.',alternatives:[],sensitive:true}}];
  setProfile(await call('profile-update',{expected_revision:current.revision,confirmed:true,changes}));setClaim('');setClaimId(null);setClaimConsent(false);setFeedback('profileSaved');
 });}
 return <div className="onboarding-page">
  <div className="page-heading"><p className="eyebrow">AI-SLOWMATCH</p><h1>{w('intro')}</h1><p>{w('pace')}</p></div>
  <SiteReminder/>
  <div className="actions"><button className="secondary" onClick={()=>navigate('discover')}>{socialText(locale,'meetNew')}</button><button className="secondary" onClick={()=>navigate('friends')}>{socialText(locale,'add')}</button><button className="secondary" onClick={()=>navigate('friends')}>{socialText(locale,'friends')}</button></div>
  <div role={failed?'alert':'status'} aria-live="polite">{feedback&&<p className={failed?'error':'notice'}>{w(feedback)}</p>}</div>
  {!localMode&&<SetupGuide/>}
  <details className="panel" open={localMode||!!status}><summary>{localMode?sw('localTitle'):sw('advanced')}</summary><p>{localMode?sw('localBody'):w('assistantBody')}</p>
  {!localMode&&<>
   <label>{w('pair')}<input type="password" autoComplete="off" disabled={busy} value={code} onChange={e=>{setCode(e.target.value);setStatus(null);setSession(null);setProfile(null);setSessions([]);setMessage('');setClaim('');setClaimId(null);setClaimConsent(false);setPath('');setModel('');setCloudConsent(false);setUsage(false);setIncludeProfile(false);setVaultConsent(false);}}/></label><p className="muted">{w('pairHint')}</p>
  </>}
   <button disabled={busy||!code.trim()} onClick={()=>run(check)}>{localMode?sw('connect'):w('check')}</button>{status&&!localMode&&<button disabled={busy} className="secondary" onClick={()=>{setCode('');setStatus(null);setSession(null);setSessions([]);setProfile(null);setMessage('');setClaim('');setCloudConsent(false);setUsage(false);setIncludeProfile(false);}}>{w('disconnect')}</button>}
   {failed&&!localMode&&<p>{sw('bridgeFailure')} <a href={LOCAL+'/app'} target="_blank" rel="noreferrer">{sw('start')}</a></p>}
  </details>
  {status&&<><section className="panel"><h2>{w('authorize')}</h2><p>{status.account_label}</p><ul className="readiness"><li>{w(status.connected?'identityReady':'identityPending')}</li><li>{w(status.plan_permission?'permissionReady':'permissionPending')}</li><li>{w(status.inference_passed?'inferenceReady':'inferencePending')}</li></ul>
   <div className="actions"><button disabled={busy} onClick={()=>run(async()=>{await call('login',{confirmed:true});setSession(null);setProfile(null);setSessions([]);setModel('');setCloudConsent(false);setUsage(false);setIncludeProfile(false);await check();})}>{w('login')}</button><button className="secondary" disabled={busy||!status.connected} onClick={()=>run(async()=>{const models=await call('models');setStatus({...status,models});if(!models.some((m:{slug:string})=>m.slug===model))setModel('');})}>{w('refreshModels')}</button></div>
   <label>{w('selectModel')}<select value={model} onChange={e=>setModel(e.target.value)}><option value="">—</option>{status.models?.map(m=><option key={m.slug} value={m.slug}>{m.display_name}</option>)}</select></label>
   <a className="text-link" href="https://chatgpt.com/settings/usage" target="_blank" rel="noreferrer">{w('manageUsage')}</a><label className="consent"><input type="checkbox" checked={usage} onChange={e=>setUsage(e.target.checked)}/>{w('usage')}</label>
  </section>
  <section className="panel"><h2>{w('vault')}</h2><p>{w(status.vault_ready?'vaultReady':'vaultPending')}</p>{status.vault_ready?<p className="local-path">{w('savedHere')}: <code>{status.vault_path}</code></p>:<><p>{sw('defaultFolder')}</p><details><summary>{sw('custom')}</summary><label>{w('path')}<input value={path} onChange={e=>{setPath(e.target.value);setVaultConsent(false);}}/></label></details><label className="consent"><input type="checkbox" checked={vaultConsent} onChange={e=>setVaultConsent(e.target.checked)}/>{w('vaultConsent')}</label><button disabled={busy||!status.connected||!vaultConsent} onClick={()=>run(async()=>{setStatus(await call('vault',{confirmed:true,path}));await readSessions();await readProfile();})}>{w('vaultConnect')}</button></>}</section>
  {status.vault_ready&&<><section className="panel"><h2>{w('conversation')}</h2><label>{w('topic')}<select value={topic} onChange={e=>{setTopic(e.target.value);setReuseId('');}}>{['self','dating','friendship','reflection'].map(key=><option key={key} value={key}>{w(key)}</option>)}</select></label>{guided&&<><p>{iw('intro')}</p>{!interviewReady&&<p className="notice">{iw('upgrade')}</p>}<label>{iw('reuseChoice')}<select value={reuseId} disabled={busy} onChange={e=>setReuseId(e.target.value)}><option value="">—</option>{sessions.filter(s=>s.topic===topic&&s.interview).map((s,i)=><option key={s.id} value={s.id}>{w(s.topic)} · {i+1}</option>)}</select></label><p className="muted">{iw('reuse')}</p></>}
  <div className="actions"><button disabled={busy||(guided&&!interviewReady)} onClick={()=>run(async()=>{setSession(await call('session-new',{topic,guided,language:locale,...(reuseId?{reuse_session_id:reuseId}:{})}));setMessage('');await readSessions();})}>{w('newChat')}</button><button className="secondary" disabled={busy} onClick={()=>run(readSessions)}>{w('refreshSessions')}</button></div>
  {sessions.length>0&&<label>{w('resume')}<select value={session?.id||''} disabled={busy} onChange={e=>{const id=e.target.value;if(id)run(async()=>{setSession(await call('session-read',{session_id:id}));setMessage('');});}}><option value="">—</option>{sessions.map((s,i)=><option key={s.id} value={s.id}>{w(s.topic)} · {i+1}</option>)}</select></label>}
  {session&&<><div className="conversation-log" aria-live="polite">{!session.messages.length&&<p>{session.interview?iw('intro'):w('empty')}</p>}{session.messages.map((m,i)=><article key={i} className={'chat-message '+m.role}><strong>{w(m.role==='user'?'you':'ai')}</strong><p>{m.content}</p></article>)}</div>{session.interview&&<InterviewPanel key={session.id} state={session.interview} busy={busy} control={controlInterview} useStatement={text=>{setClaim(text);setClaimId(null);setClaimConsent(false);}}/>}<p className="muted">{w('context')}</p><label className="consent"><input type="checkbox" checked={cloudConsent} onChange={e=>setCloudConsent(e.target.checked)}/>{w('cloudConsent')}</label><label className="consent"><input type="checkbox" checked={includeProfile} onChange={e=>setIncludeProfile(e.target.checked)}/>{w('profileContext')}</label><label>{w('message')}<textarea rows={4} maxLength={4000} value={message} onChange={e=>setMessage(e.target.value)}/></label><div className="actions"><button disabled={busy||!!session.interview?.paused||!message.trim()||!model||!usage||!cloudConsent||!status.plan_permission} onClick={()=>send()}>{w('send')}</button>{session.interview&&<button className="secondary" disabled={busy||!!session.interview.paused||!model||!usage||!cloudConsent||!status.plan_permission} onClick={()=>send(iw('next'))}>{iw('nextButton')}</button>}{busy&&<button className="secondary" onClick={()=>call('stop').catch(()=>{})}>{w('stop')}</button>}</div>{busy&&<p role="status">{w('busy')}</p>}</>}
  </section><details className="panel"><summary>{w('review')}</summary><p>{w('reviewBody')}</p><button className="secondary" disabled={busy} onClick={()=>run(readProfile)}>{w('readProfile')}</button>{profile?.claims.map(c=><article key={c.id} className="private-statement"><p>{c.text}</p><button className="secondary" disabled={busy} onClick={()=>{setClaimId(c.id);setClaim(c.text);setClaimConsent(false);}}>{w('editClaim')}</button></article>)}
  <label>{w('reviewText')}<textarea rows={4} maxLength={2000} value={claim} onChange={e=>{setClaim(e.target.value);setClaimConsent(false);}}/></label><label className="consent"><input type="checkbox" checked={claimConsent} onChange={e=>setClaimConsent(e.target.checked)}/>{w('reviewConsent')}</label><div className="actions"><button disabled={busy||!claim.trim()||!claimConsent} onClick={()=>updateClaim()}>{w('saveProfile')}</button>{claimId&&<button className="secondary" disabled={busy||!claimConsent} onClick={()=>updateClaim(true)}>{w('removeClaim')}</button>}</div></details></>}
  </>}
  {status?.vault_ready&&<PrivateMatchPanel key={status.vault_path} call={call} model={model} usage={usage&&status.plan_permission} session={session}/>}
  {status?.vault_ready&&<section className="panel"><h2>{w('share')}</h2><p>{w('shareBody')}</p><button className="secondary" onClick={()=>navigate('profile')}>{w('sharedProfile')}</button></section>}
 </div>;
}
