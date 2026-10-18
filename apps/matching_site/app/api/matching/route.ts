import { env } from 'cloudflare:workers';
import { ownerFromHeaders, createService } from '../../../lib/matching-service.mjs';
import { json, readBody, errorResponse } from '../../../lib/http.mjs';
export const dynamic='force-dynamic';
export async function POST(request:Request) {
  try {
    const origin=request.headers.get('origin');
    if(!origin || origin!==new URL(request.url).origin) return json({error:'same_origin_required'},403);
    const owner=ownerFromHeaders(request.headers);
    const body=await readBody(request);
    if(!body || Object.keys(body).sort().join()!=='arguments,name') return json({error:'invalid_arguments'},400);
    return json(await createService(env.DB,{testScopeConfiguration:env.SLOWMATCH_TEST_SCOPES,defaultTestScopeConfiguration:env.SLOWMATCH_DEFAULT_TEST_SCOPE})(body.name,body.arguments,owner));
  } catch(error) {return errorResponse(error);}
}
