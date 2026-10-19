'use client';
import {useState} from 'react';
import {schema} from '../lib/summary.mjs';
import {editorText,buildSummary} from '../lib/summary-editor.mjs';
import {useLanguage} from './language';
type Property={type:string;enum?:string[];items?:{enum?:string[];anyOf?:{enum?:string[]}[]};maxItems?:number;minItems?:number;maxLength?:number};
export default function SummaryEditor({mode,nextVersion,disabled,onPreview}:{mode:'dating'|'friendship';nextVersion:number;disabled:boolean;onPreview:(value:any)=>void}){
 const {locale,label}=useLanguage();const e=(key:string)=>editorText(locale,key);
 const choice=(value:string)=>/^\d+(?:-\d+|\+)$/.test(value)?value:label(value);
 const [fields,setFields]=useState<Record<string,string|string[]>>({}),[expiry,setExpiry]=useState(''),[discoverable,setDiscoverable]=useState(false),[error,setError]=useState(false);
 const properties=schema.$defs[mode==='dating'?'DatingSummary':'FriendshipSummary'].properties as Record<string,Property>;
 function update(name:string,value:string|string[]){setFields({...fields,[name]:value});setError(false);onPreview(null);}
 const omitted=['schema_version','mode','summary_id','version','expires_at','visibility','discoverable'];
 return <details className="summary-editor"><summary>{e('title')}</summary><p>{e('body')}</p><p className="muted">{e('geo')}</p>
 {Object.entries(properties).filter(([name])=>!omitted.includes(name)).map(([name,property])=>{
  const options=property.enum||property.items?.enum||(property.items?.anyOf?[...new Set(property.items.anyOf.flatMap(x=>x.enum||[]))]:undefined);
  if(options&&property.type==='array')return <fieldset key={name}><legend>{e(name)} · {e(property.minItems?'required':'optional')} ({property.maxItems})</legend><div className="choice-grid">{options.map(option=><label key={option}><input type="checkbox" disabled={disabled} checked={(fields[name]||[]).includes(option)} onChange={event=>{const previous=fields[name] as string[]||[];update(name,event.target.checked?[...previous,option]:previous.filter(x=>x!==option));}}/>{choice(option)}</label>)}</div></fieldset>;
  return <label key={name}>{e(name==='areas'?'regions':name)}{options?<select value={fields[name] as string||''} disabled={disabled} onChange={event=>update(name,event.target.value)}><option value="">—</option>{options.map(option=><option value={option} key={option}>{choice(option)}</option>)}</select>:name==='areas'?<textarea rows={3} value={fields[name] as string||''} disabled={disabled} onChange={event=>update(name,event.target.value)}/>:<input maxLength={property.maxLength} value={fields[name] as string||''} disabled={disabled} onChange={event=>update(name,event.target.value)}/>}</label>;
 })}
 <label>{e('expiry')}<input type="text" inputMode="numeric" placeholder="YYYY-MM-DD" maxLength={10} value={expiry} disabled={disabled} onChange={event=>{setExpiry(event.target.value);onPreview(null);}}/></label><label className="consent"><input type="checkbox" checked={discoverable} disabled={disabled} onChange={event=>{setDiscoverable(event.target.checked);onPreview(null);}}/>{e('enable')}</label>{error&&<p role="alert">{e('invalid')}</p>}
 <button disabled={disabled} onClick={()=>{try{if(Date.parse(expiry+'T23:59:59Z')<=Date.now())throw Error();onPreview(buildSummary(fields,properties,{mode,id:crypto.randomUUID().replaceAll('-',''),version:nextVersion,expiry,discoverable}));setError(false);}catch{setError(true);}}}>{e('preview')}</button>
 </details>;
}
