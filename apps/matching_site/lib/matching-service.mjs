import { validate, validateStored, summaryMode, summaryExpiry, summaryExpired, digest, canonical, reciprocal, explain, ServiceError } from './summary.mjs';
import { createPlanningService, closePlanningSql } from './planning-service.mjs';

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

export function createService(database, {clock=()=>new Date()}={}) {
  if(!database) throw new ServiceError('storage_unavailable',503);
  const db=database.withSession?database.withSession('first-primary'):database;
  const read=(owner,mode)=>db.prepare('SELECT * FROM participations WHERE owner=? AND mode=?').bind(owner,mode).first();
  async function limit(owner,operation,max) {
    const window=Math.floor(clock().getTime()/3600000);
    const row=await db.prepare('INSERT INTO query_limits(owner,window,count) VALUES (?,?,1) ON CONFLICT(owner) DO UPDATE SET window=excluded.window,count=CASE WHEN query_limits.window=excluded.window THEN query_limits.count+1 ELSE 1 END RETURNING count').bind(owner+':'+operation,window).first();
    if(row.count>max) throw new ServiceError('rate_limit_try_next_hour',429);
  }
  const planning=createPlanningService(db,{clock,read,limit,shape,revision,modeValue});
  const self=(row,mode)=>{
    if(!row)return {mode,summary:null,version:0,last_summary_version:0,discoverable:false,status:'not_joined'};
    const summary=row.summary==='{}'?null:validateStored(JSON.parse(row.summary)),expired=summary?summaryExpired(summary,clock()):false;
    return {mode,summary,version:row.revision,last_summary_version:row.last_summary_version,discoverable:!!row.active&&!expired,status:!summary?'withdrawn':expired?'expired':row.active?'active':'paused',public_id:row.public_id,summary_digest:row.digest||null,updated_at:row.updated_at};
  };
  return async function operate(name,args,owner) {
    if(!owner) throw new ServiceError('sign_in_required',401);
    if(typeof name!=='string')throw new ServiceError('invalid_arguments');
    if(name==='slowmatch_channel_check') {
      shape(args,['write']); if(typeof args.write!=='boolean') throw new ServiceError('invalid_arguments');
      if(args.write) await db.prepare('INSERT INTO channel_checks(owner,marker) VALUES (?,?) ON CONFLICT(owner) DO UPDATE SET marker=excluded.marker').bind(owner,'slowmatch-channel-v1').run();
      const row=await db.prepare('SELECT marker FROM channel_checks WHERE owner=?').bind(owner).first();
      return {authenticated:true,persisted:row?.marker==='slowmatch-channel-v1',synthetic:true};
    }
    if(name.startsWith('slowmatch_planning_')) return planning(name,args,owner);
    modeValue(args?.mode);
    // Bounded owner-scoped conversion. Old approvals never turn on either pool.
    if(args.mode==='dating') await db.prepare("INSERT INTO participations(owner,mode,public_id,summary,digest,revision,last_summary_version,active,updated_at) SELECT owner,'dating',public_id,summary,digest,revision,last_summary_version,0,updated_at FROM profiles WHERE owner=? ON CONFLICT(owner,mode) DO NOTHING").bind(owner).run();
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
        ? db.prepare('UPDATE participations SET summary=?,digest=?,revision=revision+1,last_summary_version=?,active=?,updated_at=? WHERE owner=? AND mode=? AND revision=?').bind(canonical(summary),hash,summary.version,Number(summary.discoverable),now,owner,args.mode,args.expected_version)
        : db.prepare('INSERT INTO participations(owner,mode,public_id,summary,digest,revision,last_summary_version,active,updated_at) VALUES (?,?,?,?,?,1,?,?,?) ON CONFLICT(owner,mode) DO NOTHING').bind(owner,args.mode,crypto.randomUUID().replaceAll('-',''),canonical(summary),hash,summary.version,Number(summary.discoverable),now);
      // Summary changes invalidate planning consent in the same D1 transaction.
      const results=await db.batch([statement,db.prepare(closePlanningSql('changes()=1')).bind(now,owner,owner,args.mode)]);
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
        ? "UPDATE participations SET summary='{}',digest='',active=0,revision=revision+1,updated_at=? WHERE owner=? AND mode=? AND revision=?"
        : 'UPDATE participations SET active=?,revision=revision+1,updated_at=? WHERE owner=? AND mode=? AND revision=?')
        .bind(...(deleting?[]:[Number(args.discoverable)]),now,owner,args.mode,args.expected_version);
      const queries=[mutation];
      if(deleting||!args.discoverable) queries.push(db.prepare(closePlanningSql('changes()=1')).bind(now,owner,owner,args.mode));
      if(args.mode==='dating'&&(deleting||!args.discoverable))queries.push(db.prepare(deleting
        ? "UPDATE profiles SET summary='{}',digest='',active=0,updated_at=? WHERE owner=? AND EXISTS(SELECT 1 FROM participations WHERE owner=? AND mode='dating' AND revision=? AND summary='{}')"
        : "UPDATE profiles SET active=0,updated_at=? WHERE owner=? AND EXISTS(SELECT 1 FROM participations WHERE owner=? AND mode='dating' AND revision=? AND active=0)")
        .bind(now,owner,owner,args.expected_version+1));
      const result=await db.batch(queries);
      if(result[0].meta.changes!==1) throw new ServiceError('version_conflict',409);
      return self(await read(owner,args.mode),args.mode);
    }
    if(name==='slowmatch_find_candidates') {
      shape(args,['mode']); await limit(owner,'query',12);
      const own=await read(owner,args.mode);
      if(!own?.active || own.summary==='{}') throw new ServiceError('publish_and_enable_discovery_first',403);
      const summary=validate(JSON.parse(own.summary));
      if(summaryExpired(summary,clock()))throw new ServiceError('summary_expired',403);
      const rows=await db.prepare('SELECT public_id,summary FROM participations WHERE mode=? AND active=1 AND owner<>? ORDER BY public_id LIMIT 101').bind(args.mode,owner).all();
      const candidates=[];
      for(const row of rows.results.slice(0,100)) {
        const other=validate(JSON.parse(row.summary));
        if(reciprocal(summary,other,clock())) candidates.push({public_id:row.public_id,summary:other,explanation:explain(summary,other)});
        if(candidates.length===12) break;
      }
      return {mode:args.mode,candidates,limit:12,pilot_pool_limit:100,pool_limited:rows.results.length>100,scope:'current_shared_summaries',no_automatic_contact:true};
    }
    throw new ServiceError('unknown_tool',404);
  };
}
