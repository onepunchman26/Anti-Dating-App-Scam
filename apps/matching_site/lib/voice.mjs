// PCM stays in memory. No browser/cloud recognition service is used.
export function pcmBase64(chunks, rate) {
 if (!Number.isFinite(rate)||rate<8000||rate>96000) throw Error('audio');
 const count=chunks.reduce((n,c)=>n+c.length,0);
 if(count<rate/10||count>rate*30)throw Error('audio');
 const samples=new Float32Array(count);let at=0;
 for(const chunk of chunks){samples.set(chunk,at);at+=chunk.length;}
 const bytes=new Uint8Array(Math.round(count*16000/rate)*2),view=new DataView(bytes.buffer);
 for(let i=0;i<bytes.length/2;i++){
  const pos=i*rate/16000,left=Math.min(Math.floor(pos),count-1),right=Math.min(left+1,count-1);
  const value=samples[left]*(1-(pos-left))+samples[right]*(pos-left);
  if(!Number.isFinite(value))throw Error('audio');
  view.setInt16(i*2,Math.round(Math.max(-1,Math.min(1,value))*32767),true);
 }
 let raw='';for(let i=0;i<bytes.length;i+=8192)raw+=String.fromCharCode(...bytes.subarray(i,i+8192));
 return btoa(raw);
}

export function localVoice(voices, language){
 return voices.find(v=>v.localService===true&&v.lang.toLowerCase().split('-')[0]===language)||null;
}

export function waitForLocalVoice(synth,language,signal,timeout=2000){
 return new Promise(resolve=>{
  let timer;
  const finish=value=>{clearTimeout(timer);synth.removeEventListener('voiceschanged',changed);signal.removeEventListener('abort',cancel);resolve(value);};
  const cancel=()=>finish(null);
  const changed=()=>{const voice=localVoice(synth.getVoices(),language);if(voice)finish(voice);};
  if(signal.aborted){resolve(null);return;}
  const current=localVoice(synth.getVoices(),language);if(current){resolve(current);return;}
  synth.addEventListener('voiceschanged',changed);signal.addEventListener('abort',cancel,{once:true});
  timer=setTimeout(()=>finish(null),timeout);changed();
 });
}

// Injected browser APIs let lifecycle tests exercise late permissions and cleanup.
export function captureVoice({media,AudioContext,onFinish,onError,onRecording}){
 let cancelled=false,closed=false,stream,context,source,processor,gain,timer,chunks=[],count=0;
 function cleanup(){
  clearTimeout(timer);
  if(processor){processor.onaudioprocess=null;processor.disconnect();}
  source?.disconnect();gain?.disconnect();
  stream?.getTracks().forEach(t=>{t.onended=null;t.stop();});
  if(context&&context.state!=='closed')void context.close().catch(()=>{});
 }
 function cancel(){cancelled=true;closed=true;cleanup();chunks=[];}
 function finish(){
  if(closed)return;closed=true;cleanup();
  try{const pcm=pcmBase64(chunks,context.sampleRate);chunks=[];onFinish(pcm);}
  catch{chunks=[];onError();}
 }
 async function start(){
  try{
   stream=await media.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true},video:false});
   if(cancelled){cleanup();return;}
   context=new AudioContext();await context.resume();
   if(cancelled){cleanup();return;}
   source=context.createMediaStreamSource(stream);
   processor=context.createScriptProcessor(4096,1,1);gain=context.createGain();gain.gain.value=0;
   processor.onaudioprocess=e=>{
    if(closed)return;
    const remaining=Math.floor(context.sampleRate*30)-count;
    const data=e.inputBuffer.getChannelData(0).slice(0,remaining);
    chunks.push(data);count+=data.length;
    if(count>=context.sampleRate*30)finish();
   };
   source.connect(processor);processor.connect(gain);gain.connect(context.destination);
   stream.getAudioTracks().forEach(t=>{t.onended=()=>{if(!closed){cancel();onError();}};});
   timer=setTimeout(finish,30000);onRecording();
  }catch{if(!cancelled){cancel();onError();}}
 }
 return {start,finish,cancel};
}
