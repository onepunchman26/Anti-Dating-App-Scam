'use client';
import {useLayoutEffect,useRef,useState} from 'react';
import {useLanguage} from './language';
import {captureVoice,waitForLocalVoice,pcmBase64} from '../lib/voice.mjs';
import {voiceText} from '../lib/voice-copy.mjs';
type VoiceStatus={runtime:boolean;languages:Record<string,{ready:boolean;download_mb:number}>};
type Props={call:(op:string,args?:Record<string,unknown>)=>Promise<unknown>;available:boolean;disabled:boolean;canSend:boolean;contextKey:string;draft:string;onDraft:(s:string)=>void;onBusy:(b:boolean)=>void;onSend:(s:string)=>Promise<string>;reply:string};
export default function VoicePanel(props:Props){
 const {locale}=useLanguage(),w=(k:string)=>voiceText(locale,k);
 const [language,setLanguage]=useState(locale==='zh-CN'?'zh':'en'),[status,setStatus]=useState<VoiceStatus|null>(null),[phase,setPhase]=useState(''),[notice,setNotice]=useState(''),[turn,setTurn]=useState(false),[seconds,setSeconds]=useState(0);
 const latest=useRef(props);useLayoutEffect(()=>{latest.current=props;});
 const epoch=useRef(0),capture=useRef<ReturnType<typeof captureVoice>|null>(null),tick=useRef<ReturnType<typeof setInterval>|null>(null);
 const active=useRef(false);
 const fileInput=useRef<HTMLInputElement|null>(null);
 const speechWait=useRef<AbortController|null>(null);
 function clearCapture(){capture.current?.cancel();capture.current=null;if(tick.current)clearInterval(tick.current);tick.current=null;}
 function abort(report=true){
  epoch.current++;clearCapture();speechWait.current?.abort();window.speechSynthesis?.cancel();
  if(active.current)void latest.current.call('stop').catch(()=>{});
  active.current=false;latest.current.onBusy(false);setPhase('');setTurn(false);if(report)setNotice('paused');
 }
 useLayoutEffect(()=>{
  const stop=()=>abort(false);const hide=()=>{if(document.hidden)stop();};window.addEventListener('pagehide',stop);document.addEventListener('visibilitychange',hide);
  return()=>{window.removeEventListener('pagehide',stop);document.removeEventListener('visibilitychange',hide);abort(false);};
 // Changing the account/session/approved context invalidates pending audio and auto-send.
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[props.contextKey]);
 function begin(label:string){const id=++epoch.current;active.current=true;props.onBusy(true);setNotice('');setPhase(label);return id;}
 function end(id:number){if(id!==epoch.current)return;active.current=false;latest.current.onBusy(false);setPhase('');}
 async function check(install=false){
  const id=begin('working');try{if(install)await props.call('voice-install',{language,confirmed:true});const result=await props.call('voice-status');if(id===epoch.current)setStatus(result as VoiceStatus);}catch{if(id===epoch.current)setNotice('error');}finally{end(id);}
 }
 async function read(text:string,id:number){
  if(id!==epoch.current||!text)return;
  speechWait.current?.abort();const controller=new AbortController();speechWait.current=controller;
  setPhase('loadingVoice');const synth=window.speechSynthesis;
  const voice=synth&&await waitForLocalVoice(synth,language,controller.signal) as SpeechSynthesisVoice|null;
  if(id!==epoch.current||controller.signal.aborted)return;
  if(!voice){setPhase('');setNotice('noVoice');return;}
  synth.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.voice=voice;utterance.lang=voice.lang;
  setNotice('');setPhase('reading');utterance.onend=()=>{if(id===epoch.current){setPhase('');setNotice('readDone');}};utterance.onerror=()=>{if(id===epoch.current){setPhase('');setNotice('readFailed');}};synth.speak(utterance);
 }
 async function transcribe(pcm:string,id:number,auto:boolean){
  clearCapture();if(id!==epoch.current)return;setPhase('working');
  try{
   const result=await props.call('voice-transcribe',{language,confirmed:true,pcm_base64:pcm}) as {text:string};
   if(id!==epoch.current)return;
   const p=latest.current,text=[p.draft,result.text].filter(Boolean).join('\n');
   if(text.length>4000){setNotice('overflow');return;}
   p.onDraft(text);setNotice('draft');
   if(auto&&p.canSend&&!p.draft.trim()){
    const reply=await p.onSend(text);if(id!==epoch.current)return;
    end(id);if(reply)read(reply,id);return;
   }
  }catch{if(id===epoch.current)setNotice('error');}finally{if(id===epoch.current&&active.current)end(id);}
 }
 function record(){
  if(!navigator.mediaDevices?.getUserMedia||!window.AudioContext){setNotice('unavailable');return;}
  speechWait.current?.abort();window.speechSynthesis?.cancel();const id=begin('permission');setSeconds(0);
  capture.current=captureVoice({media:navigator.mediaDevices,AudioContext:window.AudioContext,
   onFinish:(pcm:string)=>{void transcribe(pcm,id,turn);},
   onError:()=>{if(id===epoch.current){clearCapture();setNotice('error');end(id);}},
   onRecording:()=>{if(id===epoch.current){setPhase('recording');tick.current=setInterval(()=>setSeconds(s=>s+1),1000);}},
  });void capture.current.start();
 }
 async function importAudio(file:File){
  const id=begin('working');let context:AudioContext|null=null;
  try{
   if(file.size>12_000_000||file.size<44)throw Error('audio');
   const raw=await file.arrayBuffer(),header=new TextDecoder().decode(raw.slice(0,12));
   if(!header.startsWith('RIFF')||header.slice(8)!=='WAVE')throw Error('audio');
   if(id!==epoch.current)return;
   context=new AudioContext();const decoded=await context.decodeAudioData(raw);
   if(id!==epoch.current)return;
   if(decoded.duration>30||decoded.duration<0.1||decoded.numberOfChannels>2)throw Error('audio');
   const samples=new Float32Array(decoded.length);
   for(let channel=0;channel<decoded.numberOfChannels;channel++){
    const data=decoded.getChannelData(channel);for(let i=0;i<data.length;i++)samples[i]+=data[i]/decoded.numberOfChannels;
   }
   await transcribe(pcmBase64([samples],decoded.sampleRate),id,false);
  }catch{if(id===epoch.current)setNotice('error');}finally{if(context)void context.close().catch(()=>{});end(id);}
 }
 const processing=['permission','working','recording','loadingVoice'].includes(phase),ready=status?.runtime&&status.languages[language]?.ready;
 return <section className="voice-panel" aria-label={w('title')}><h3>{w('title')}</h3><p className="muted">{w('intro')}</p>
 {!props.available?<p>{w('missing')}</p>:<>
 <label>{w('language')}<select value={language} disabled={processing} onChange={e=>{abort(false);setLanguage(e.target.value);}}><option value="en">{w('en')}</option><option value="zh">{w('zh')}</option></select></label>
 <div className="actions"><button className="secondary" disabled={processing||props.disabled} onClick={()=>check()}>{w('check')}</button>{status?.runtime&&!ready&&<button className="secondary" disabled={processing||props.disabled} onClick={()=>check(true)}>{w('install')} · {status.languages[language].download_mb} {w('download')}</button>}</div>
 <p className="muted">{w(ready?'ready':status&&!status.runtime?'missing':'checkFirst')}</p>
 <button className="secondary" disabled={!ready||processing||props.disabled} onClick={()=>fileInput.current?.click()}>{w('file')}</button><input hidden ref={fileInput} aria-label={w('file')} type="file" accept=".wav,audio/wav" disabled={!ready||processing||props.disabled} onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void importAudio(file);}}/><p className="muted">{w('fileHint')}</p>
 <label className="consent"><input type="checkbox" checked={turn} disabled={processing||props.disabled||!props.canSend||!!props.draft.trim()} onChange={e=>setTurn(e.target.checked)}/>{w('turn')}</label><p className="muted">{w('turnHint')}</p>
 <div className="actions"><button className="secondary" disabled={!ready||processing||props.disabled} onClick={record}>{w('record')}</button>{phase==='recording'&&<button onClick={()=>capture.current?.finish()}>{w('stop')}</button>}<button className="secondary" disabled={processing||phase==='reading'||props.disabled||!props.reply} onClick={()=>read(props.reply,epoch.current)}>{w('read')}</button>{phase&&<button className="secondary" onClick={()=>abort()}>{w('cancel')}</button>}</div>
 </>}
 <p role="status" aria-live="polite">{phase&&w(phase)}{phase==='recording'?' · '+Math.min(seconds,30)+'s':''}{notice&&' '+w(notice)}</p>
 </section>;
}
