import { ServiceError } from './summary.mjs';
export const json=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Vary':'Cookie'}});
export async function readBody(request,limit=16000) {
  if(request.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='application/json') throw new ServiceError('json_required',415);
  if(Number(request.headers.get('content-length'))>limit) throw new ServiceError('request_too_large',413);
  const reader=request.body?.getReader();if(!reader) throw new ServiceError('json_required');
  let size=0;const parts=[];
  while(true) {const {value,done}=await reader.read();if(done) break;size+=value.length;if(size>limit){await reader.cancel();throw new ServiceError('request_too_large',413);}parts.push(value);}
  const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
  try{return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}catch{throw new ServiceError('invalid_json');}
}
export function errorResponse(error) { return json({error:error instanceof ServiceError?error.message:'storage_unavailable'},error instanceof ServiceError?error.status:503); }
