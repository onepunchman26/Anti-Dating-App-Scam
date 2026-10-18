import { validate, digest, canonical, reciprocal, explain, ServiceError } from './summary.mjs';

export function ownerFromHeaders(headers) {
  const owner=headers.get('oai-authenticated-user-id');
  if(!owner || !headers.get('oai-authenticated-user-email')) throw new ServiceError('sign_in_required',401);
  return owner;
}
function shape(args, keys) {
  if(!args || typeof args!=='object' || Array.isArray(args) || Object.keys(args).length!==keys.length || keys.some(k=>!Object.hasOwn(args,k))) throw new ServiceError('invalid_arguments');
}
function revision(value) { if(!Number.isSafeInteger(value)||value<0) throw new ServiceError('invalid_version'); }
export function createService(db) {
  if(!db) throw new ServiceError('storage_unavailable',503);
  const read=owner=>db.prepare('SELECT * FROM profiles WHERE owner=?').bind(owner).first();
  async function limit(owner,operation,max) {
    const window=Math.floor(Date.now()/3600000);
    const row=await db.prepare('INSERT INTO query_limits(owner,window,count) VALUES (?,?,1) ON CONFLICT(owner) DO UPDATE SET window=excluded.window,count=CASE WHEN query_limits.window=excluded.window THEN query_limits.count+1 ELSE 1 END RETURNING count').bind(owner+':'+operation,window).first();
    if(row.count>max) throw new ServiceError('rate_limit_try_next_hour',429);
  }
  const self=row=>row?{summary:row.summary==='{}'?null:validate(JSON.parse(row.summary)),version:row.revision,last_summary_version:row.last_summary_version,discoverable:!!row.active,public_id:row.public_id,summary_digest:row.digest||null,updated_at:row.updated_at}:{summary:null,version:0,last_summary_version:0,discoverable:false};
  return async function operate(name,args,owner) {
    if(!owner) throw new ServiceError('sign_in_required',401);
    if(name==='slowmatch_read_my_summary') {shape(args,[]);return self(await read(owner));}
    if(name==='slowmatch_channel_check') {
      shape(args,['write']); if(typeof args.write!=='boolean') throw new ServiceError('invalid_arguments');
      if(args.write) await db.prepare('INSERT INTO channel_checks(owner,marker) VALUES (?,?) ON CONFLICT(owner) DO UPDATE SET marker=excluded.marker').bind(owner,'slowmatch-channel-v1').run();
      const row=await db.prepare('SELECT marker FROM channel_checks WHERE owner=?').bind(owner).first();
      return {authenticated:true,persisted:row?.marker==='slowmatch-channel-v1',synthetic:true};
    }
    if(name==='slowmatch_publish_summary') {
      shape(args,['summary','approved_digest','expected_version']);revision(args.expected_version);
      const summary=validate(args.summary); const hash=await digest(summary);
      if(args.approved_digest!==hash) throw new ServiceError('approval_content_mismatch');
      await limit(owner,'write',60);
      const prior=await read(owner);
      if(prior?.digest===hash && prior.summary!=='{}') return {...self(prior),idempotent:true};
      if((prior?.revision||0)!==args.expected_version) throw new ServiceError('version_conflict',409);
      if(prior && summary.version<=prior.last_summary_version) throw new ServiceError('summary_version_must_increase',409);
      const now=new Date().toISOString();
      const statement=prior
        ? db.prepare('UPDATE profiles SET summary=?,digest=?,revision=revision+1,last_summary_version=?,active=?,updated_at=? WHERE owner=? AND revision=?').bind(canonical(summary),hash,summary.version,Number(summary.discoverable),now,owner,args.expected_version)
        : db.prepare('INSERT INTO profiles(owner,public_id,summary,digest,revision,last_summary_version,active,updated_at) VALUES (?,?,?,?,1,?,?,?) ON CONFLICT(owner) DO NOTHING').bind(owner,crypto.randomUUID().replaceAll('-',''),canonical(summary),hash,summary.version,Number(summary.discoverable),now);
      const result=await statement.run();
      if(result.meta.changes!==1) throw new ServiceError('version_conflict',409);
      return self(await read(owner));
    }
    if(name==='slowmatch_set_discoverability' || name==='slowmatch_delete_my_summary') {
      shape(args,name==='slowmatch_set_discoverability'?['discoverable','expected_version']:['expected_version']);revision(args.expected_version);
      if(name==='slowmatch_set_discoverability' && typeof args.discoverable!=='boolean') throw new ServiceError('invalid_arguments');
      await limit(owner,'write',60);const prior=await read(owner);
      if(!prior || prior.revision!==args.expected_version) throw new ServiceError('version_conflict',409);
      if(name==='slowmatch_set_discoverability' && (prior.summary==='{}' || (args.discoverable && !JSON.parse(prior.summary).discoverable))) throw new ServiceError('new_approved_summary_required');
      const deleting=name==='slowmatch_delete_my_summary';
      const result=await db.prepare(deleting
        ? "UPDATE profiles SET summary='{}',digest='',active=0,revision=revision+1,updated_at=? WHERE owner=? AND revision=?"
        : 'UPDATE profiles SET active=?,revision=revision+1,updated_at=? WHERE owner=? AND revision=?')
        .bind(...(deleting?[]:[Number(args.discoverable)]),new Date().toISOString(),owner,args.expected_version).run();
      if(result.meta.changes!==1) throw new ServiceError('version_conflict',409);
      return self(await read(owner));
    }
    if(name==='slowmatch_find_candidates') {
      shape(args,[]); await limit(owner,'query',12);
      const own=await read(owner);
      if(!own?.active || own.summary==='{}') throw new ServiceError('publish_and_enable_discovery_first',403);
      const summary=validate(JSON.parse(own.summary));
      const rows=await db.prepare('SELECT public_id,summary FROM profiles WHERE active=1 AND owner<>? ORDER BY public_id LIMIT 101').bind(owner).all();
      const candidates=[];
      for(const row of rows.results.slice(0,100)) {
        const other=validate(JSON.parse(row.summary));
        if(reciprocal(summary,other)) candidates.push({public_id:row.public_id,summary:other,explanation:explain(summary,other)});
        if(candidates.length===12) break;
      }
      return {candidates,limit:12,pilot_pool_limit:100,pool_limited:rows.results.length>100,scope:'current_shared_summaries',no_automatic_contact:true};
    }
    throw new ServiceError('unknown_tool',404);
  };
}
