'use client';
import {useState} from 'react';
import {useLanguage} from './language';
import {privateMatchText} from '../lib/private-match-copy.mjs';
import {editorText} from '../lib/summary-editor.mjs';
import {validate} from '../lib/summary.mjs';

const AGES=['18-24','25-34','35-44','45-54','55-64','65+'];
const INTERESTS=['reading','music','art','outdoors','cooking','games','travel','sport','learning','volunteering'];
type Session={id:string;topic:string;revision:number};
export default function PrivateMatchPanel({call,model,usage,session}:{call:(op:string,args:Record<string,unknown>)=>Promise<any>;model:string;usage:boolean;session:Session|null}){
 const {locale,label,date}=useLanguage(),w=(k:string)=>privateMatchText(locale,k),e=(k:string)=>editorText(locale,k);
 const [fields,setFields]=useState({alias:'',city:'',age_band:'',version:1,accepted_age_bands:[] as string[],interests:[] as string[]});
 const [draftConsent,setDraftConsent]=useState(false),[reviewConsent,setReviewConsent]=useState(false),[include,setInclude]=useState(false),[approved,setApproved]=useState(false);
 const [draft,setDraft]=useState<any>(null),[review,setReview]=useState<any>(null),[bundle,setBundle]=useState(''),[missing,setMissing]=useState<string[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(false);
 function change(key:string,value:any){setFields({...fields,[key]:value});setDraft(null);setApproved(false);}
 async function run(action:()=>Promise<void>){setBusy(true);setError(false);try{await action();}catch{setError(true);}finally{setBusy(false);}}
 function download(){const url=URL.createObjectURL(new Blob([JSON.stringify(validate(draft),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='slowmatch-reviewed-summary.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 return <><p>{w('recoverHint')}</p><button className="secondary" disabled={busy} onClick={()=>run(async()=>{const result=await call('matching-result',{});if(result.summary){setDraft(validate(result.summary));setApproved(false);}if(result.review)setReview(result.review);})}>{w('recover')}</button><details className="panel"><summary>{w('draft')}</summary><p>{w('intro')}</p>{!model||!usage?<p>{w('model')}</p>:null}
 {['alias','city'].map(k=><label key={k}>{e(k)}<input maxLength={k==='alias'?40:60} value={fields[k as 'alias'|'city']} onChange={ev=>change(k,ev.target.value)}/></label>)}
 <label>{e('age_band')}<select value={fields.age_band} onChange={ev=>change('age_band',ev.target.value)}><option value="">—</option>{AGES.map(v=><option key={v}>{v}</option>)}</select></label>
 {(['accepted_age_bands','interests'] as const).map(k=><fieldset key={k}><legend>{e(k)}</legend><div className="choice-grid">{(k==='interests'?INTERESTS:AGES).map(v=><label key={v}><input type="checkbox" checked={fields[k].includes(v)} disabled={!fields[k].includes(v)&&fields[k].length>=(k==='interests'?8:6)} onChange={ev=>change(k,ev.target.checked?[...fields[k],v]:fields[k].filter(x=>x!==v))}/>{k==='interests'?label(v):v}</label>)}</div></fieldset>)}
 <details><summary>{w('version')}</summary><input type="number" min={1} value={fields.version} onChange={ev=>change('version',Number(ev.target.value))} aria-label={w('version')}/></details>
 <label className="consent"><input type="checkbox" checked={draftConsent} onChange={ev=>setDraftConsent(ev.target.checked)}/>{w('consent')}</label>
 <button disabled={busy||!model||!usage||!draftConsent||!session||!['dating','friendship'].includes(session.topic)||!fields.alias||!fields.city||!fields.age_band||!fields.accepted_age_bands.length} onClick={()=>run(async()=>{setDraft(null);setApproved(false);setMissing([]);const result=await call('summary-draft',{...fields,session_id:session!.id,expected_revision:session!.revision,mode:session!.topic,model,language:locale,cloud_consent:draftConsent,included_plan_confirmed:usage});if(result.summary)setDraft(validate(result.summary));else setMissing(result.missing||[]);})}>{w('generate')}</button>
 {!!missing.length&&<p>{w('missing')} {missing.map(e).join(' · ')}</p>}
 {draft&&<><dl className="summary">{Object.entries(draft).filter(([k])=>!['schema_version','summary_id','mode'].includes(k)).map(([k,v])=><div className="summary-row" key={k}><dt>{['expires_at','visibility','discoverable'].includes(k)?w(k):k==='version'?w('version'):e(k)}</dt><dd>{k==='expires_at'?date(String(v)):k==='visibility'?w('participants'):typeof v==='boolean'?w(v?'yes':'no'):Array.isArray(v)?v.map(x=>/^\d/.test(x)?x:label(x)).join(' · ')||'—':['alias','city','age_band','version'].includes(k)?String(v):label(String(v))}</dd></div>)}</dl><label className="consent"><input type="checkbox" checked={approved} onChange={ev=>setApproved(ev.target.checked)}/>{w('reviewed')}</label><button disabled={!approved} onClick={download}>{w('export')}</button><p>{w('next')}</p></>}
 </details><details className="panel"><summary>{w('candidate')}</summary><label>{w('bundle')}<textarea rows={4} maxLength={60000} value={bundle} onChange={ev=>{setBundle(ev.target.value);setReview(null);setReviewConsent(false);}}/></label>
 <label className="consent"><input type="checkbox" checked={reviewConsent} onChange={ev=>setReviewConsent(ev.target.checked)}/>{w('reviewConsent')}</label><label className="consent"><input type="checkbox" checked={include} onChange={ev=>setInclude(ev.target.checked)}/>{w('include')}</label>
 <button disabled={busy||!model||!usage||!reviewConsent||!bundle.trim()} onClick={()=>run(async()=>{setReview(null);const parsed=JSON.parse(bundle);const result=await call('candidate-review',{bundle:parsed,model,language:locale,cloud_consent:reviewConsent,included_plan_confirmed:usage,include_profile:include});setReview({...result.review,aliases:Object.fromEntries(parsed.candidates.map((c:any)=>[c.public_id,c.summary.alias]))});})}>{w('run')}</button>
 {review&&<><p>{w('saved')}</p>{review.candidates.map((c:any)=><article key={c.public_id}><h3>{review.aliases[c.public_id]}</h3>{['reasons','differences','questions','unknowns'].map(k=><div key={k}><h4>{w(k)}</h4><ul>{c[k].map((s:string,i:number)=><li key={i}>{s}</li>)}</ul></div>)}</article>)}<p>{review.uncertainty}</p></>}
 </details>{busy&&<p role="status">{w('busy')}</p>}{error&&<p role="alert">{w('failed')}</p>}</>;
}
