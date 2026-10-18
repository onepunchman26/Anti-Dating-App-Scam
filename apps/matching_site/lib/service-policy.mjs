import metadata from '../package.json' with {type:'json'};
import {digest,summaryExpiry,ServiceError} from './summary.mjs';

export const SERVICE_PROTOCOL='1.0';
export const SERVICE_VERSION=metadata.version;
export const MCP_PROTOCOLS=['2026-07-28','2025-03-26'];
export const accountFingerprint=owner=>digest(['slowmatch-account-v1',owner]);
export const testOwner=(scope,fingerprint)=>digest([scope,fingerprint]).then(hash=>`slowmatch-test:${hash}`);
function validateScope(entry){
  if(!entry||Array.isArray(entry)||Object.keys(entry).sort().join()!=='expires_at,scope'||typeof entry.scope!=='string'||!/^[a-z][a-z0-9-]{2,39}$/u.test(entry.scope)||entry.scope==='production')throw Error();
  summaryExpiry(entry.expires_at);return Object.freeze(entry);
}
export function parseDefaultTestScope(raw){
  if(raw===undefined||raw===null||raw==='')return null;
  try{if(typeof raw!=='string'||raw.length>1000)throw Error();return validateScope(JSON.parse(raw));}
  catch{throw new ServiceError('test_scope_configuration_invalid',503);}
}

// This value comes only from server runtime configuration. It is never accepted
// from a tool argument, browser header, query string or candidate record.
export function parseTestScopes(raw){
  if(raw===undefined||raw===null||raw==='')return Object.freeze({});
  if(typeof raw!=='string'||raw.length>32000)throw new ServiceError('test_scope_configuration_invalid',503);
  try{
    const value=JSON.parse(raw);
    if(!value||Array.isArray(value)||Object.keys(value).sort().join()!=='memberships,version'||value.version!==1||!value.memberships||Array.isArray(value.memberships)||typeof value.memberships!=='object'||Object.keys(value.memberships).length>100)throw Error();
    for(const [fingerprint,entry] of Object.entries(value.memberships)){
      if(!/^[a-f0-9]{64}$/u.test(fingerprint))throw Error();
      validateScope(entry);
    }
    return Object.freeze(value.memberships);
  }catch{throw new ServiceError('test_scope_configuration_invalid',503);}
}

export function clientArguments(args){
  if(!args||typeof args!=='object'||Array.isArray(args))return args;
  if(!Object.hasOwn(args,'client_protocol'))return args;
  if(args.client_protocol!==SERVICE_PROTOCOL)throw new ServiceError('client_upgrade_required',426);
  const {client_protocol,...business}=args;void client_protocol;return business;
}

export async function resolvePrincipal(db,owner,memberships,defaultScope,clock){
  const account_fingerprint=await accountFingerprint(owner);
  const configured=memberships[account_fingerprint]||defaultScope;
  const enrolled=await db.prepare('SELECT scope FROM test_enrollments WHERE account_fingerprint=?').bind(account_fingerprint).first();
  if(!configured&&!enrolled)return {owner,scope:'production',account_fingerprint,scopePolicy:null,data_scope:{kind:'production',id:'production',access:'enabled'}};
  const scope=configured?`test:${configured.scope}`:enrolled.scope;
  // Only a maintainer-controlled assignment can establish/change enrollment.
  if(configured&&enrolled?.scope!==scope)await db.prepare('INSERT INTO test_enrollments(account_fingerprint,scope,enrolled_at) VALUES(?,?,?) ON CONFLICT(account_fingerprint) DO UPDATE SET scope=excluded.scope,enrolled_at=excluded.enrolled_at').bind(account_fingerprint,scope,clock().toISOString()).run();
  const access=!configured?'not_configured':summaryExpiry(configured.expires_at)<=clock().getTime()?'expired':'enabled';
  // A default pilot admits every platform-authorized signed-in visitor without
  // per-person developer setup. Explicit overrides can narrow that access.
  const ownerExpiries=new Map(await Promise.all(Object.entries(memberships).map(async([fingerprint,entry])=>[await testOwner(scope,fingerprint),`test:${entry.scope}`===scope?summaryExpiry(entry.expires_at):0])));
  const defaultExpiry=defaultScope&&`test:${defaultScope.scope}`===scope?summaryExpiry(defaultScope.expires_at):0;
  return {owner:await testOwner(scope,account_fingerprint),scope,account_fingerprint,scopePolicy:{defaultExpiry,ownerExpiries},data_scope:{kind:'controlled_test',id:scope,access}};
}
