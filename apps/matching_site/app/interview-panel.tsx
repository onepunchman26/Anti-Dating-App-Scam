'use client';
import {useState} from 'react';
import {useLanguage} from './language';
import {interviewText,initialInterviewAreas} from '../lib/interview.mjs';
export type InterviewState={phase:string;paused:boolean;question_count:number;focus:string|null;awaiting:string|null;notes:Record<string,{area:string;text:string;quote:string;status:string}>};
export default function InterviewPanel({state,busy,control,useStatement}:{state:InterviewState;busy:boolean;control:(action:string,area?:string,text?:string)=>Promise<void>;useStatement:(text:string)=>void}){
 const {locale}=useLanguage();const w=(key:string)=>interviewText(locale,key);
 const [editing,setEditing]=useState(''),[wording,setWording]=useState(''),[approved,setApproved]=useState(false),[focus,setFocus]=useState('mind');
 const areas=Array.from(new Set([...initialInterviewAreas,...Object.keys(state.notes),...(state.focus?[state.focus]:[])]));
 return <section className="interview-draft"><p>{w('count')}: <strong>{state.question_count}/8</strong></p>
  <div className="actions"><button disabled={busy} className="secondary" onClick={()=>control('draft')}>{w('draft')}</button><button disabled={busy} className="secondary" onClick={()=>control(state.paused?'resume':'pause')}>{w(state.paused?'resume':'pause')}</button>
  {state.awaiting&&!state.paused&&['skip','unknown','inexperienced'].map(action=><button key={action} disabled={busy} className="secondary" onClick={()=>control(action)}>{w(action)}</button>)}</div>
  {state.paused&&<p role="status">{w('paused')}</p>}
  <details open={state.phase==='draft'||undefined}><summary>{w('title')}</summary><p className="muted">{w('private')}</p>
   {areas.map(area=>{const note=state.notes[area];return <article className="private-statement" key={area}><h3>{w(area)}</h3><p className="muted">{w(note?(note.status==='draft'?'draftStatus':note.status):'missing')}</p>{note?.text&&<p>{note.text}</p>}{note?.quote&&<blockquote><small>{w('quote')}</small><p>{note.quote}</p></blockquote>}<div className="actions"><button className="secondary" disabled={busy} onClick={()=>{setEditing(area);setWording(note?.text||'');setApproved(false);}}>{w('edit')}</button>{note&&<button className="secondary" disabled={busy} onClick={()=>control('remove',area)}>{w('remove')}</button>}{note?.status==='confirmed'&&<button className="secondary" disabled={busy} onClick={()=>useStatement(note.text)}>{w('use')}</button>}</div></article>;})}
   {editing&&<div className="panel"><h3>{w(editing)}</h3><label>{w('editLabel')}<textarea rows={3} maxLength={400} value={wording} onChange={e=>{setWording(e.target.value);setApproved(false);}}/></label><label className="consent"><input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}/>{w('consent')}</label><button disabled={busy||!approved||!wording.trim()} onClick={async()=>{await control('review',editing,wording);setApproved(false);}}>{w('save')}</button></div>}
  </details>
  <details><summary>{w('later')}</summary><label>{w('focus')}<select value={focus} onChange={e=>setFocus(e.target.value)}>{[...initialInterviewAreas,'mind','body','spirit','vocation'].map(area=><option key={area} value={area}>{w(area)}</option>)}</select></label><p className="muted">{w('laterHint')}</p><button className="secondary" disabled={busy} onClick={()=>control('explore',focus)}>{w('explore')}</button></details>
 </section>;
}
