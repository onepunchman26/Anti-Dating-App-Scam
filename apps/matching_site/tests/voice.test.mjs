import test from 'node:test';
import assert from 'node:assert/strict';
import {captureVoice,pcmBase64,localVoice,waitForLocalVoice} from '../lib/voice.mjs';
import {requestLocal} from '../lib/local-request.mjs';

test('PCM duration, rates, finite samples and little-endian conversion',()=>{
 const pcm=Buffer.from(pcmBase64([new Float32Array(4800).fill(0.5)],48000),'base64');
 assert.equal(pcm.length,3200);assert.equal(pcm.readInt16LE(0),16384);
 for(const [samples,rate] of [[new Float32Array(1599),16000],[new Float32Array(480001),16000],[new Float32Array(3200),NaN],[new Float32Array(3200).fill(NaN),16000]])assert.throws(()=>pcmBase64([samples],rate));
});
test('playback never substitutes a remote voice',()=>{
 const voices=[{localService:false,lang:'en-US'},{localService:true,lang:'zh-CN'}];
 assert.equal(localVoice(voices,'en'),null);assert.equal(localVoice(voices,'zh'),voices[1]);
});
test('asynchronous device voices load once and cancellation cleans pending listeners',async()=>{
 const synth=new EventTarget();let voices=[];synth.getVoices=()=>voices;
 const controller=new AbortController(),pending=waitForLocalVoice(synth,'en',controller.signal);
 voices=[{localService:true,lang:'en-US'}];synth.dispatchEvent(new Event('voiceschanged'));
 assert.equal(await pending,voices[0]);
 voices=[];const cancelled=waitForLocalVoice(synth,'en',controller.signal);controller.abort();assert.equal(await cancelled,null);
 assert.equal(await waitForLocalVoice(synth,'en',new AbortController().signal,1),null);
});
test('cancel while permission pending stops late tracks without constructing audio context',async()=>{
 let resolve,stopped=0;
 const stream={getTracks:()=>[{stop:()=>stopped++}]};
 const cap=captureVoice({media:{getUserMedia:()=>new Promise(r=>{resolve=r;})},AudioContext:class{constructor(){assert.fail('late capture');}},onFinish:()=>assert.fail(),onError:()=>assert.fail(),onRecording:()=>assert.fail()});
 const start=cap.start();cap.cancel();resolve(stream);await start;assert.equal(stopped,1);
});
test('normal finish and repeated cancellation release capture and suppress late callbacks',async()=>{
 let processor,stopped=0,closed=0,completed=0,recording=0;
 const track={stop:()=>stopped++},stream={getTracks:()=>[track],getAudioTracks:()=>[track]};
 const node=()=>({connect(){},disconnect(){}});
 class Context{
  state='running';sampleRate=16000;destination={};
  resume(){return Promise.resolve();}close(){closed++;this.state='closed';return Promise.resolve();}
  createMediaStreamSource(){return node();}createGain(){return {...node(),gain:{value:1}};}
  createScriptProcessor(){processor={...node(),onaudioprocess:null};return processor;}
 }
 const cap=captureVoice({media:{getUserMedia:async()=>stream},AudioContext:Context,onFinish:pcm=>{completed++;assert.equal(Buffer.from(pcm,'base64').length,8192);},onError:()=>assert.fail(),onRecording:()=>recording++});
 await cap.start();processor.onaudioprocess({inputBuffer:{getChannelData:()=>new Float32Array(4096)}});cap.finish();cap.finish();cap.cancel();
 assert.equal(completed,1);assert.equal(closed,1);assert.ok(stopped>=1);assert.equal(recording,1);assert.equal(processor.onaudioprocess,null);
});
test('voice bytes only use authenticated fixed loopback voice endpoint',async()=>{
 let called;
 await requestLocal('synthetic','voice-transcribe',{pcm_base64:'synthetic'},async(url,options)=>{called={url,options};return {ok:true,json:async()=>({ok:true,result:{}})};});
 assert.equal(called.url,'http://127.0.0.1:8911/voice/v1');assert.equal(called.options.credentials,'omit');assert.equal(called.options.headers.Authorization,'Bearer synthetic');
});
