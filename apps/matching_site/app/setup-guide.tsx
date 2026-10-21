'use client';
import {useState} from 'react';
import {useLanguage} from './language';
import {setupPrompt,setupText} from '../lib/setup-copy.mjs';
export default function SetupGuide(){
 const {locale}=useLanguage();const s=(key:string)=>setupText(locale,key);const [copied,setCopied]=useState(false);
 return <section className="panel setup-guide"><h2>{s('title')}</h2><p>{s('installed')}</p><a className="text-link" href="https://learn.chatgpt.com/docs/quickstart?setup=app" target="_blank" rel="noreferrer">{s('download')}</a><p>{s('folder')}</p><button onClick={async()=>{try{await navigator.clipboard.writeText(setupPrompt(locale));setCopied(true);}catch{setCopied(false);}}}>{s('copy')}</button>{copied&&<p role="status">{s('copied')}</p>}<details><summary>{s('copy')}</summary><textarea readOnly rows={7} value={setupPrompt(locale)} aria-label={s('copy')}/></details><p>{s('startHint')}</p><a className="button" href="http://127.0.0.1:8911/app" target="_blank" rel="noreferrer">{s('start')}</a></section>;
}
