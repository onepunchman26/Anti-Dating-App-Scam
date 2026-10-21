import { validate, validateStored, summaryMode, summaryExpiry, summaryExpired, digest, canonical, reciprocal, explain, ServiceError } from './summary.mjs';
import { createPlanningService, closePlanningSql } from './planning-service.mjs';
import {createSocialService} from './social-service.mjs';
import {discoveryFilter,acceptsFilter} from './discovery.mjs';
import {parseTestScopes,parseDefaultTestScope,resolvePrincipal,clientArguments,SERVICE_VERSION,SERVICE_PROTOCOL,MCP_PROTOCOLS} from './service-policy.mjs';

export function ownerFromHeaders(headers) {
  const owner=headers.get('oai-authenticated-user-id');
  if(!owner || !headers.get('oai-authenticated-user-email')) throw new ServiceError('sign_in_required',401);
  return owner;
}
export function shape(args, keys) {
  if(!args || typeof args!=='object' || Array.isArray(args) || Object.keys(args).length!==keys.length || keys.some(k=>!Object.hasOwn(args,k))) throw new ServiceError('invalid_arguments');
}
export function revision(value) { if(!Number.isSafeInteger(value)||value<0) throw new ServiceError('invalid_version'); }
export function modeValue(value) {if(!['dating','friendship'].includes(value)) throw new ServiceError('invalid_mode');}

export function createService(database, {clock=()=>new Date(),testScopeConfiguration='',defaultTestScopeConfiguration=''}={}) {
  if(!database) throw new ServiceError('storage_unavailable',503);
  const db=database.withSession?database.withSession('first-primary'):database;
  const memberships=parseTestScopes(testScopeConfiguration);
  const defaultScope=parseDefaultTestScope(defaultTestScopeConfiguration);
  return async function authenticatedOperation(name,args,authenticatedOwner){
    if(!authenticatedOwner)throw new ServiceError('sign_in_required',401);
    args=clientArguments(args);
    const principal=await resolvePrincipal(db,authenticatedOwner,memberships,defaultScope,clock);
    if(name==='slowmatch_channel_check'){
      shape(args,['write']);if(typeof args.write!=='boolean')throw new ServiceError('invalid_arguments');
      const write=args.write&&principal.data_scope.access==='enabled';
      await db.prepare('SELECT scope FROM participations LIMIT 0').all();
      await db.prepare('SELECT scope FROM planning_sessions LIMIT 0').all();
      await db.prepare('SELECT scope FROM social_accounts LIMIT 0').all();
      await db.prepare('SELECT scope FROM social_groups LIMIT 0').all();
      if(write)await db.prepare('INSERT INTO channel_checks(owner,marker) VALUES (?,?) ON CONFLICT(owner) DO UPDATE SET marker=excluded.marker').bind(principal.owner,'slowmatch-channel-v1').run();
      const marker=await db.prepare('SELECT marker FROM channel_checks WHERE owner=?').bind(principal.owner).first();
      return {authenticated:true,account_fingerprint:principal.account_fingerprint,data_scope:principal.data_scope,service_name:'AI-SlowMatch',service_version:SERVICE_VERSION,service_protocol_version:SERVICE_PROTOCOL,mcp_protocol_versions:MCP_PROTOCOLS,summary_schema_versions:['2.0'],planning_schema_versions:['1.0'],database_read:'passed',database_schema:'passed',write_check:write?'passed':args.write?'blocked':'not_checked',persisted:marker?.marker==='slowmatch-channel-v1',synthetic:true,client_skill:'not_checked',client_local_tools:'not_checked'};
    }
    if(principal.data_scope.access!=='enabled')throw new ServiceError(`controlled_test_scope_${principal.data_scope.access}`,403);
    return createScopedService(db,{clock,scope:principal.scope,scopePolicy:principal.scopePolicy})(name,args,principal.owner);
  };
}

function createScopedService(db,{clock,scope,scopePolicy}) {
  // Older deployed Workers discover only active=1. Keeping test activation at
  // a distinct server-only value prevents a rollback from exposing test rows.
  const activeValue=scope==='production'?1:2;
  const ownerAllowed=owner=>scopePolicy===null||(scopePolicy.ownerExpiries.has(owner)?scopePolicy.ownerExpiries.get(owner):scopePolicy.defaultExpiry)>clock().getTime();
  const read=(owner,mode)=>ownerAllowed(owner)?db.prepare('SELECT * FROM participations WHERE owner=? AND mode=? AND scope=?').bind(owner,mode,scope).first():Promise.resolve(null);
  async function limit(owner,operation,max) {
    const window=Math.floor(clock().getTime()/3600000);
    const row=await db.prepare('INSERT INTO query_limits(owner,window,count) VALUES (?,?,1) ON CONFLICT(owner) DO UPDATE SET window=excluded.window,count=CASE WHEN query_limits.window=excluded.window THEN query_limits.count+1 ELSE 1 END RETURNING count').bind(owner+':'+operation,window).first();
    if(row.count>max) throw new ServiceError('rate_limit_try_next_hour',429);
  }
  const planning=createPlanningService(db,{clock,read,limit,shape,revision,modeValue,scope,ownerAllowed,activeValue});
  const social=createSocialService(db,{clock,scope,ownerAllowed,limit,shape});
  const self=(row,mode)=>{
    if(!row)return {mode,summary:null,version:0,last_summary_version:0,discoverable:false,status:'not_joined'};
    const summary=row.summary==='{}'?null:validateStored(JSON.parse(row.summary)),expired=summary?summaryExpired(summary,clock()):false;
    const active=row.active===activeValue;
    return {mode,summary,version:row.revision,last_summary_version:row.last_summary_version,discoverable:active&&!expired,status:!summary?'withdrawn':expired?'expired':active?'active':'paused',public_id:row.public_id,summary_digest:row.digest||null,updated_at:row.updated_at};
  };
  return async function operate(name,args,owner) {
    if(!owner) throw new ServiceError('sign_in_required',401);
    if(typeof name!=='string')throw new ServiceError('invalid_arguments');
    if(name==='slowmatch_social')return social(args,owner);
    if(name.startsWith('slowmatch_planning_')) return planning(name,args,owner);
    modeValue(args?.mode);
    // Bounded owner-scoped conversion. Old approvals never turn on either pool.
    if(scope==='production'&&args.mode==='dating') await db.prepare("INSERT INTO participations(owner,mode,public_id,summary,digest,revision,last_summary_version,active,updated_at) SELECT owner,'dating',public_id,summary,digest,revision,last_summary_version,0,updated_at FROM profiles WHERE owner=? ON CONFLICT(owner,mode) DO NOTHING").bind(owner).run();
    if(name==='slowmatch_read_my_summary') {shape(args,['mode']);return self(await read(owner,args.mode),args.mode);}
    if(name==='slowmatch_publish_summary') {
      shape(args,['mode','summary','approved_digest','expected_version']);revision(args.expected_version);
      const summary=validate(args.summary);
      if(summary.schema_version!=='2.0'||summaryMode(summary)!==args.mode) throw new ServiceError('mode_summary_mismatch');
      const expiry=summaryExpiry(summary.expires_at),time=clock().getTime();
      if(expiry<=time||expiry-time>365*86400000)throw new ServiceError('invalid_summary_expiry');
      const hash=await digest(summary);
      if(args.approved_digest!==hash) throw new ServiceError('approval_content_mismatch');
      await limit(owner,'write',60);
      const prior=await read(owner,args.mode);
      if(prior?.digest===hash && prior.summary!=='{}') return {...self(prior,args.mode),idempotent:true};
      if((prior?.revision||0)!==args.expected_version) throw new ServiceError('version_conflict',409);
      if(prior && summary.version<=prior.last_summary_version) throw new ServiceError('summary_version_must_increase',409);
      const now=clock().toISOString();
      const statement=prior
        ? db.prepare('UPDATE participations SET summary=?,digest=?,revision=revision+1,last_summary_version=?,active=?,updated_at=? WHERE owner=? AND mode=? AND revision=? AND scope=?').bind(canonical(summary),hash,summary.version,summary.discoverable?activeValue:0,now,owner,args.mode,args.expected_version,scope)
        : db.prepare('INSERT INTO participations(owner,scope,mode,public_id,summary,digest,revision,last_summary_version,active,updated_at) VALUES (?,?,?,?,?,?,1,?,?,?) ON CONFLICT(owner,mode) DO NOTHING').bind(owner,scope,args.mode,crypto.randomUUID().replaceAll('-',''),canonical(summary),hash,summary.version,summary.discoverable?activeValue:0,now);
      // Summary changes invalidate planning consent in the same D1 transaction.
      const results=await db.batch([statement,db.prepare(closePlanningSql('changes()=1')).bind(now,owner,owner,args.mode,scope)]);
      if(results[0].meta.changes!==1) throw new ServiceError('version_conflict',409);
      return self(await read(owner,args.mode),args.mode);
    }
    if(name==='slowmatch_set_discoverability' || name==='slowmatch_delete_my_summary') {
      shape(args,name==='slowmatch_set_discoverability'?['mode','discoverable','expected_version']:['mode','expected_version']);revision(args.expected_version);
      if(name==='slowmatch_set_discoverability' && typeof args.discoverable!=='boolean') throw new ServiceError('invalid_arguments');
      await limit(owner,'write',60);const prior=await read(owner,args.mode);
      if(!prior || prior.revision!==args.expected_version) throw new ServiceError('version_conflict',409);
      if(name==='slowmatch_set_discoverability'&&args.discoverable&&prior.summary!=='{}'&&summaryExpired(JSON.parse(prior.summary),clock()))throw new ServiceError('summary_expired');
      if(name==='slowmatch_set_discoverability' && (prior.summary==='{}' || (args.discoverable && (!JSON.parse(prior.summary).discoverable || JSON.parse(prior.summary).schema_version!=='2.0')))) throw new ServiceError('new_approved_summary_required');
      const deleting=name==='slowmatch_delete_my_summary', now=clock().toISOString();
      const mutation=db.prepare(deleting
        ? "UPDATE participations SET summary='{}',digest='',active=0,revision=revision+1,updated_at=? WHERE owner=? AND mode=? AND revision=? AND scope=?"
        : 'UPDATE participations SET active=?,revision=revision+1,updated_at=? WHERE owner=? AND mode=? AND revision=? AND scope=?')
        .bind(...(deleting?[]:[args.discoverable?activeValue:0]),now,owner,args.mode,args.expected_version,scope);
      const queries=[mutation];
      if(deleting||!args.discoverable) queries.push(db.prepare(closePlanningSql('changes()=1')).bind(now,owner,owner,args.mode,scope));
      if(scope==='production'&&args.mode==='dating'&&(deleting||!args.discoverable))queries.push(db.prepare(deleting
        ? "UPDATE profiles SET summary='{}',digest='',active=0,updated_at=? WHERE owner=? AND EXISTS(SELECT 1 FROM participations WHERE owner=? AND mode='dating' AND revision=? AND summary='{}')"
        : "UPDATE profiles SET active=0,updated_at=? WHERE owner=? AND EXISTS(SELECT 1 FROM participations WHERE owner=? AND mode='dating' AND revision=? AND active=0)")
        .bind(now,owner,owner,args.expected_version+1));
      const result=await db.batch(queries);
      if(result[0].meta.changes!==1) throw new ServiceError('version_conflict',409);
      return self(await read(owner,args.mode),args.mode);
    }
    if(name==='slowmatch_find_candidates') {
      shape(args,Object.hasOwn(args,'filters')?['mode','filters']:['mode']);
      let filters;try{filters=discoveryFilter(args.filters);}catch{throw new ServiceError('invalid_discovery_filter');}
      await limit(owner,'query',12);
      const own=await read(owner,args.mode);
      if(own?.active!==activeValue || own.summary==='{}') throw new ServiceError('publish_and_enable_discovery_first',403);
      const summary=validate(JSON.parse(own.summary));
      if(summaryExpired(summary,clock()))throw new ServiceError('summary_expired',403);
      const defaultEnabled=scopePolicy!==null&&scopePolicy.defaultExpiry>clock().getTime();
      const members=scopePolicy===null?null:[...scopePolicy.ownerExpiries.keys()].filter(member=>ownerAllowed(member)!==defaultEnabled);
      const membershipClause=members?.length?` AND owner ${defaultEnabled?'NOT IN':'IN'} (${members.map(()=>'?').join(',')})`:scopePolicy!==null&&!defaultEnabled?' AND 0=1':'';
      const rows=await db.prepare(`SELECT public_id,summary FROM participations WHERE mode=? AND active=? AND owner<>? AND scope=?${membershipClause} ORDER BY public_id LIMIT 101`).bind(args.mode,activeValue,owner,scope,...(members||[])).all();
      const candidates=[];
      for(const row of rows.results.slice(0,100)) {
        const other=validate(JSON.parse(row.summary));
        if(reciprocal(summary,other,clock())&&acceptsFilter(other,filters)) candidates.push({public_id:row.public_id,summary:other,explanation:explain(summary,other)});
        if(candidates.length===12) break;
      }
      return {mode:args.mode,candidates,filters,matching_method:'deterministic_reciprocal_filters',ai_review:'not_run',limit:12,pilot_pool_limit:100,pool_limited:rows.results.length>100,scope:'current_shared_summaries',no_automatic_contact:true};
    }
    throw new ServiceError('unknown_tool',404);
  };
}
