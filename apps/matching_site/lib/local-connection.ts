// Memory only. Never persist pairing credentials or send them to the Site.
let current={code:'',model:''};
export const rememberLocal=(code:string,model:string)=>{current={code,model};};
export const currentLocal=()=>({...current});
export async function localCall(code:string,operation:string,args:Record<string,unknown>={}){
 const response=await fetch('http://127.0.0.1:8911/v1',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+code.trim()},body:JSON.stringify({operation,arguments:args}),cache:'no-store',credentials:'omit'});
 const body=await response.json() as Record<string,any>;if(!response.ok||!body.ok)throw Error(body.error||'connection_failed');return body.result;
}
