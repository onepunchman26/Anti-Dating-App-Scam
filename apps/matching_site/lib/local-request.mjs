// Pairing stays in memory and is sent only to the fixed loopback companion.
export async function requestLocal(code,operation,args={},transport=fetch){
 const controller=new AbortController();
 const timeout=setTimeout(()=>controller.abort(),['send','group-suggest','summary-draft','candidate-review','reflection-draft','voice-install'].includes(operation)?240000:['models','voice-transcribe'].includes(operation)?60000:15000);
 try{
  let response;
  try{response=await transport('http://127.0.0.1:8911'+(operation==='voice-transcribe'?'/voice/v1':'/v1'),{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+code.trim()},body:JSON.stringify({operation,arguments:args}),cache:'no-store',credentials:'omit',signal:controller.signal});}
  catch{throw Error('unreachable');}
  let body;try{body=await response.json();}catch{throw Error('unreachable');}
  if(!response.ok||!body.ok)throw Error(body.error||'connection_failed');
  return body.result;
 }finally{clearTimeout(timeout);}
}
