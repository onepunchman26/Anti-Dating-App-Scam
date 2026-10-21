'use client';
import {useState} from 'react';
import {useLanguage} from './language';
import {reflectionText} from '../lib/reflection-copy.mjs';

type Event={event_id:string;occurred_at:string;context:string;source:string;material_id:null|string;quote_or_summary:string;fact_status:string};
type Interpretation={explanation:string;evidence_ids:string[];alternative_explanations:string[];uncertainty:string};
type Content={events:Event[];interpretations:Interpretation[];repeated_event_ids:string[];repetition_context:string;concern:string;uncertainty:string;optional_actions:string[];action_status:string;personal_feelings:string;expectations_supported:string[];expectations_unknown:string[];boundaries_and_pace:string[];self_insights_to_review:string[]};
type RecordItem={record_id:string;revision:number;status:string;content?:Content|null;history?:{revision:number;updated_at:string;change:string}[]};
type Session={id:string;revision:number;messages:{role:string;content:string}[]};
type Props={call:(operation:string,args?:Record<string,unknown>)=>Promise<any>;model:string;usage:boolean;ready:boolean;session:Session|null;useNotes:(text:string)=>void};

export default function PrivateReflectionPanel({call,model,usage,ready,session,useNotes}:Props){
 const {locale}=useLanguage();const w=(key:string)=>reflectionText(locale,key);
 const [busy,setBusy]=useState(false),[generating,setGenerating]=useState(false),[error,setError]=useState(false),[feedback,setFeedback]=useState('');
 const [cloud,setCloud]=useState(false),[approved,setApproved]=useState(false),[deleteConsent,setDeleteConsent]=useState(false);
 const [content,setContent]=useState<Content|null>(null),[records,setRecords]=useState<RecordItem[]|null>(null),[record,setRecord]=useState<RecordItem|null>(null);
 const [source,setSource]=useState<{session_id:string;expected_revision:number}|null>(null);
 async function run(fn:()=>Promise<void>,isGeneration=false){setBusy(true);setGenerating(isGeneration);setError(false);setFeedback('');try{await fn();}catch{setError(true);}finally{setBusy(false);setGenerating(false);}}
 async function list(){setRecords((await call('reflection-list')).records);}
 function edit(next:Content){setContent(next);setApproved(false);setDeleteConsent(false);setFeedback('');}
 function load(item:RecordItem){setRecord(item);setContent(item.content||null);setSource(null);setApproved(false);setDeleteConsent(false);}
 const arrays=['expectations_supported','expectations_unknown','boundaries_and_pace','self_insights_to_review'] as const;
 const actions=['continue','slow_down','clarify','pause','end','seek_support'];
 const canGenerate=ready&&!!session?.messages.some(m=>m.role==='user')&&!!model&&usage&&cloud;
 return <section className="panel private-reflection"><h2>{w('title')}</h2><p>{w('body')}</p>
 {!ready&&<p className="notice">{w('upgrade')}</p>}
 {!session?.messages.some(m=>m.role==='user')&&<p>{w('select')}</p>}
 <label className="consent"><input type="checkbox" checked={cloud} disabled={busy} onChange={e=>setCloud(e.target.checked)}/>{w('disclosure')}</label>
 <div className="actions"><button disabled={busy||!canGenerate} onClick={()=>run(async()=>{const result=await call('reflection-draft',{session_id:session!.id,expected_revision:session!.revision,language:locale,model,cloud_consent:true,included_plan_confirmed:true});setSource({session_id:result.session_id,expected_revision:result.expected_revision});setContent(result.content);setRecord(null);setApproved(false);setDeleteConsent(false);},true)}>{w('generate')}</button><button className="secondary" disabled={busy||!ready} onClick={()=>run(list)}>{w('read')}</button>{busy&&generating&&<button className="secondary" onClick={()=>call('stop').catch(()=>{})}>{w('stop')}</button>}</div>
 {busy&&<p role="status">{w(generating?'busy':'working')}</p>}{error&&<p role="alert" className="error">{w('error')}</p>}{feedback&&<p role="status" className="notice">{w(feedback)}</p>}
 {records&&<div>{!records.some(r=>r.status==='active')&&<p>{w('empty')}</p>}{records.filter(r=>r.status==='active').map((r,i)=><button key={r.record_id} className="secondary" disabled={busy} onClick={()=>run(async()=>load(await call('reflection-read',{record_id:r.record_id})))}>{w('openRecord')} {i+1} · {w('revision')} {r.revision}</button>)}</div>}
 {content&&<fieldset disabled={busy} className="reflection-editor"><legend>{record?`${w('revision')} ${record.revision}`:w('preview')}</legend>
 <h3>{w('events')}</h3><p className="muted">{w('quotes')}</p>{content.events.map((e,i)=><article key={e.event_id} className="private-statement"><blockquote>{e.quote_or_summary}</blockquote><label>{w('context')}<textarea maxLength={2000} value={e.context} onChange={ev=>edit({...content,events:content.events.map((v,j)=>j===i?{...v,context:ev.target.value}:v)})}/></label><label>{w('when')}<input maxLength={300} value={e.occurred_at} onChange={ev=>edit({...content,events:content.events.map((v,j)=>j===i?{...v,occurred_at:ev.target.value}:v)})}/></label></article>)}
 <label>{w('feelings')}<textarea rows={3} maxLength={2000} value={content.personal_feelings} onChange={e=>edit({...content,personal_feelings:e.target.value})}/></label>
 <h3>{w('interpretations')}</h3>{content.interpretations.map((v,i)=><article className="private-statement" key={i}><label>{w('explanation')}<textarea maxLength={2000} value={v.explanation} onChange={e=>edit({...content,interpretations:content.interpretations.map((n,j)=>j===i?{...n,explanation:e.target.value}:n)})}/></label><label>{w('alternatives')}<textarea maxLength={8000} value={v.alternative_explanations.join('\n')} onChange={e=>edit({...content,interpretations:content.interpretations.map((n,j)=>j===i?{...n,alternative_explanations:e.target.value.split('\n')}:n)})}/></label><label>{w('uncertainty')}<textarea maxLength={2000} value={v.uncertainty} onChange={e=>edit({...content,interpretations:content.interpretations.map((n,j)=>j===i?{...n,uncertainty:e.target.value}:n)})}/></label></article>)}
 {arrays.map(key=><label key={key}>{w(key)}<span className="muted">{w('lines')}</span><textarea maxLength={12000} rows={3} value={content[key].join('\n')} onChange={e=>edit({...content,[key]:e.target.value?e.target.value.split('\n'):[]})}/></label>)}
 <label>{w('uncertainty')}<textarea rows={3} maxLength={2000} value={content.uncertainty} onChange={e=>edit({...content,uncertainty:e.target.value})}/></label>
 <label>{w('concern')}<select value={content.concern} onChange={e=>edit({...content,concern:e.target.value})}>{['ordinary_mismatch','needs_clarification','specific_risk'].map(k=><option key={k} value={k}>{w(k)}</option>)}</select></label>
 <fieldset><legend>{w('optional_actions')}</legend>{actions.map(k=><label className="consent" key={k}><input type="checkbox" checked={content.optional_actions.includes(k)} onChange={e=>edit({...content,optional_actions:e.target.checked?[...content.optional_actions,k]:content.optional_actions.filter(a=>a!==k)})}/>{w(k)}</label>)}</fieldset>
 <label>{w('action_status')}<select value={content.action_status} onChange={e=>edit({...content,action_status:e.target.value})}>{['open','paused','ended','resolved'].map(k=><option key={k} value={k}>{w(k)}</option>)}</select></label>
 <label className="consent"><input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}/>{w('approve')}</label>
 <button disabled={!approved||!content.optional_actions.length} onClick={()=>run(async()=>{const edited={...content,interpretations:content.interpretations.map(i=>({...i,alternative_explanations:i.alternative_explanations.filter(s=>s.trim())})),...Object.fromEntries(arrays.map(k=>[k,content[k].filter(s=>s.trim())]))};const next=await call(record?'reflection-save':'reflection-approve',record?{record_id:record.record_id,expected_revision:record.revision,confirmed:true,content:edited}:{...source,confirmed:true,content:edited});const wasCorrection=!!record;load(next);await list();setFeedback(wasCorrection?'corrected':'saved');})}>{w(record?'saveEdit':'save')}</button>
 {record&&<><p>{w('continueHint')}</p><button className="secondary" onClick={()=>useNotes([content.personal_feelings,...content.boundaries_and_pace,...content.expectations_unknown,content.uncertainty].join('\n').slice(0,4000))}>{w('continueChat')}</button><details><summary>{w('history')}</summary><ul>{record.history?.map(h=><li key={h.revision}>{w('revision')} {h.revision} · {w(h.change==='corrected'?'correctedAction':h.change==='deleted'?'deletedAction':h.change)} · {h.updated_at}</li>)}</ul></details><label className="consent"><input type="checkbox" checked={deleteConsent} onChange={e=>setDeleteConsent(e.target.checked)}/>{w('deleteConsent')}</label><button className="secondary" disabled={!deleteConsent} onClick={()=>run(async()=>{await call('reflection-delete',{record_id:record.record_id,expected_revision:record.revision,confirmed:true});setContent(null);setRecord(null);setDeleteConsent(false);setApproved(false);await list();setFeedback('deleted');})}>{w('delete')}</button></>}
 </fieldset>}
 </section>;
}
