import { env } from 'cloudflare:workers';
import { createService, ownerFromHeaders } from '../../lib/matching-service.mjs';
import { ServiceError } from '../../lib/summary.mjs';
import { tools } from '../../lib/tools.mjs';
import {SERVICE_VERSION,MCP_PROTOCOLS} from '../../lib/service-policy.mjs';
import { json, readBody, errorResponse } from '../../lib/http.mjs';
export const dynamic='force-dynamic';
export async function POST(request:Request) {
  let id=null;
  try {
    const origin=request.headers.get('origin');
    if(origin && origin!==new URL(request.url).origin) return json({error:'same_origin_required'},403);
    const owner=ownerFromHeaders(request.headers);
    const message=await readBody(request);id=message.id??null;
    if(message.jsonrpc!=='2.0') return json({jsonrpc:'2.0',id,error:{code:-32600,message:'Invalid request'}},400);
    let result;
    if(message.method==='server/discover') result={supportedVersions:[MCP_PROTOCOLS[0]],capabilities:{tools:{}}};
    else if(message.method==='initialize') result={protocolVersion:MCP_PROTOCOLS.includes(message.params?.protocolVersion)?message.params.protocolVersion:'2025-03-26',serverInfo:{name:'slowmatch',version:SERVICE_VERSION},capabilities:{tools:{}}};
    else if(message.method==='notifications/initialized') return new Response(null,{status:202});
    else if(message.method==='tools/list') result={tools};
    else if(message.method==='tools/call') {
      try {
        const output=await createService(env.DB,{testScopeConfiguration:env.SLOWMATCH_TEST_SCOPES,defaultTestScopeConfiguration:env.SLOWMATCH_DEFAULT_TEST_SCOPE})(message.params?.name,message.params?.arguments,owner);
        result={content:[{type:'text',text:JSON.stringify(output)}],isError:false};
      } catch(error) {
        result={content:[{type:'text',text:JSON.stringify({error:error instanceof ServiceError?error.message:'storage_unavailable'})}],isError:true};
      }
    } else return json({jsonrpc:'2.0',id,error:{code:-32601,message:'Unknown method'}});
    return json({jsonrpc:'2.0',id,result});
  } catch(error) { return errorResponse(error); }
}
