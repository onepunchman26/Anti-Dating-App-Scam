// Memory only. Never persist pairing credentials or send them to the Site.
import {requestLocal} from './local-request.mjs';
let current={code:'',model:''};
export const rememberLocal=(code:string,model:string)=>{current={code,model};};
export const currentLocal=()=>({...current});
export async function localCall(code:string,operation:string,args:Record<string,unknown>={}){
 return requestLocal(code,operation,args);
}
