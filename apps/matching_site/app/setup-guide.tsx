'use client';
import {useRef,useState} from 'react';
import {useLanguage} from './language';
import {setupPrompt,setupText} from '../lib/setup-copy.mjs';
export default function SetupGuide(){
 const {locale}=useLanguage();const s=(key:string)=>setupText(locale,key);
 const [step,setStep]=useState<'choose'|'download'|'install'>('choose');
 const [copiedLocale,setCopiedLocale]=useState(''),[copyFailed,setCopyFailed]=useState(false),[showPrompt,setShowPrompt]=useState(false),[copying,setCopying]=useState(false);
 const heading=useRef<HTMLHeadingElement>(null),prompt=useRef<HTMLTextAreaElement>(null),copyRequest=useRef(0);
 function go(next:typeof step){copyRequest.current++;setStep(next);setCopying(false);setCopyFailed(false);setCopiedLocale('');heading.current?.focus();}
 async function copy(){
  const request=++copyRequest.current;let timer:ReturnType<typeof setTimeout>|undefined;setCopying(true);setCopyFailed(false);setCopiedLocale('');
  try{await Promise.race([navigator.clipboard.writeText(setupPrompt(locale)),new Promise<never>((_,reject)=>{timer=setTimeout(()=>reject(Error('clipboard_timeout')),2000);})]);if(request===copyRequest.current){setCopiedLocale(locale);setCopyFailed(false);}}
  catch{if(request===copyRequest.current){setCopiedLocale('');setCopyFailed(true);setShowPrompt(true);requestAnimationFrame(()=>{prompt.current?.focus();prompt.current?.select();});}}
  finally{clearTimeout(timer);if(request===copyRequest.current)setCopying(false);}
 }
 return <section className="panel setup-guide" aria-labelledby="setup-title">
  <ol className="setup-progress" aria-label={s('title')}><li aria-current={step!=='install'?'step':undefined}><span aria-hidden="true">1</span>{s('stepChatGPT')}</li><li aria-current={step==='install'?'step':undefined}><span aria-hidden="true">2</span>{s('stepInstall')}</li></ol>
  <h2 id="setup-title" ref={heading} tabIndex={-1}>{s(step==='install'?'installTitle':'haveChatGPT')}</h2>
  {step==='choose'&&<><p>{s('chooseHint')}</p><div className="actions setup-actions"><button onClick={()=>go('install')}>{s('haveApp')}</button><button className="quiet" onClick={()=>go('download')}>{s('needApp')}</button></div></>}
  {step==='download'&&<><p>{s('downloadHint')}</p><div className="actions setup-actions"><a className="button quiet" href="https://learn.chatgpt.com/docs/quickstart?setup=app" target="_blank" rel="noreferrer">{s('download')}</a><button onClick={()=>go('install')}>{s('downloaded')}</button></div><button className="text-button" onClick={()=>go('choose')}>{s('back')}</button></>}
  {step==='install'&&<>
   <ol className="setup-instructions"><li>{s('openCodex')}</li><li>{s('chooseFolder')}</li><li>{s('pastePrompt')}</li></ol>
   <button disabled={copying} onClick={copy}>{s(copying?'copying':'copy')}</button>
   <div aria-live="polite">{copiedLocale===locale&&<p className="setup-feedback" role="status">{s('copied')}</p>}{copyFailed&&<p className="setup-feedback" role="alert">{s('copyFailed')}</p>}</div>
   <details open={showPrompt} onToggle={e=>setShowPrompt(e.currentTarget.open)}><summary>{s('viewPrompt')}</summary><textarea ref={prompt} readOnly rows={7} value={setupPrompt(locale)} aria-label={s('copy')}/></details>
   <p className="setup-note">{s('folderHint')}</p><button className="text-button" onClick={()=>go('choose')}>{s('back')}</button>
  </>}
  <details className="setup-returning"><summary>{s('alreadySetup')}</summary><p>{s('startHint')}</p><a className="button quiet" href="http://127.0.0.1:8911/app" target="_blank" rel="noreferrer">{s('start')}</a></details>
 </section>;
}
