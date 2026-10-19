import {validate,digest,canonical,summaryExpiry,ServiceError,schema} from './summary.mjs';
import {planSchema,publicSource} from './planning-service.mjs';
import preferencesSchema from './group-preferences.schema.json' with {type:'json'};
export {preferencesSchema};
const id={type:'string',pattern:'^[a-f0-9]{32}$'},version={type:'integer',minimum:0};
const approved={type:'boolean',const:true},text=(max=60)=>({type:'string',minLength:1,maxLength:max});
const object=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
const group={group_id:id,expected_version:version},activity={...group,activity_id:id};
export const analysisSchema=object({discussion_points:{type:'array',items:text(300),minItems:1,maxItems:3},uncertainty:text(300)});
export const actionSchemas={
 account_read:{},account_save:{adult_confirmed:approved,alias:text(40),discoverable:{type:'boolean'},approved,expected_version:version},
 lookup:{public_id:id},friends:{},friend_request:{public_id:id,approved},
 friend_respond:{public_id:id,choice:{enum:['accept','decline','cancel','remove','block','unblock']},expected_version:version},
 groups:{},group_create:{name:text(60),expires_at:text(40),approved},group_read:{group_id:id},
 group_invite:{...group,public_id:id,approved},group_respond:{...group,choice:{enum:['accept','decline','leave']}},
 activity_create:{...group,title:text(60),mode:{enum:['friendship','dating']},participants:{type:'array',items:id,minItems:2,maxItems:8,uniqueItems:true},expires_at:text(40),approved},
 preferences:{...activity,preferences:preferencesSchema,approved_digest:{type:'string',pattern:'^[a-f0-9]{64}$'},approved},
 preferences_withdraw:activity,context:{group_id:id,activity_id:id},
 propose:{...activity,plan:planSchema,analysis:analysisSchema,approved_digest:{type:'string',pattern:'^[a-f0-9]{64}$'},approved},
 confirm:{...activity,plan_version:version,plan_digest:{type:'string',pattern:'^[a-f0-9]{64}$'},option_id:{enum:['a','b','c']},conditions_checked:approved,approved},
 activity_leave:activity,
};
// Standalone schemas keep their reference roots during service validation.
const inline=(v,root=v)=>Array.isArray(v)?v.map(x=>inline(x,root)):!v||typeof v!=='object'?v:v.$ref?inline(v.$ref.slice(2).split('/').reduce((n,k)=>n[k],root),root):Object.fromEntries(Object.entries(v).filter(([k])=>k!=='$defs').map(([k,x])=>[k,inline(x,root)]));
export const socialRequestSchema={oneOf:Object.entries(actionSchemas).map(([action,fields])=>object({action:{const:action},...Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,inline(v)]))}))};
const norm=s=>s.normalize('NFKC').trim().toLocaleLowerCase('en');
const stamp=s=>new Date(summaryExpiry(s)).toISOString();
const fail=(code,status=409)=>{throw new ServiceError(code,status);};
function label(s,max=60){if(typeof s!=='string'||s.length>max||!new RegExp(schema.$defs.DatingSummary.properties.city.pattern,'u').test(s)||new RegExp(preferencesSchema['x-slowmatch-label-forbidden-pattern'],'iu').test(s))fail('public_label_required',400);return s.trim();}
const mergeWindows=windows=>{const out=[];for(const [a,b] of windows.filter(([a,b])=>b>a).sort((x,y)=>x[0]-y[0])){const prev=out.at(-1);if(prev&&a<=prev[1])prev[1]=Math.max(prev[1],b);else out.push([a,b]);}return out;};
export function commonConditions(preferences,now=new Date()){
 const shared=key=>preferences[0][key].filter(x=>preferences.every(p=>p[key].some(y=>norm(x)===norm(y))));
 let windows=mergeWindows(preferences[0].availability.map(w=>[summaryExpiry(w.start_at),summaryExpiry(w.end_at)]));
 for(const p of preferences.slice(1))windows=mergeWindows(windows.flatMap(([a,b])=>p.availability.map(w=>[Math.max(a,summaryExpiry(w.start_at)),Math.min(b,summaryExpiry(w.end_at))])).filter(([a,b])=>b-a>=15*60000));
 const duration=Math.min(...preferences.map(p=>p.duration_minutes));
 windows=windows.map(([a,b])=>[Math.max(a,now.getTime()+300000),b]).filter(([a,b])=>b-a>=duration*60000);
 const currency=preferences[0].budget.currency,interests=shared('interests').filter(x=>!preferences.some(p=>p.avoid_interests.includes(x))),areas=shared('areas');
 const blockers=[];if(!areas.length)blockers.push('no_shared_area');if(!interests.length)blockers.push('no_shared_interest');if(!windows.length)blockers.push('no_shared_time');if(preferences.some(p=>p.budget.currency!==currency))blockers.push('currency_agreement_required');
 return {blockers,areas,interests,values:shared('values'),communication_preferences:shared('communication_preferences'),duration_minutes:duration,currency,max_per_person_minor:Math.min(...preferences.map(p=>p.budget.max_per_person_minor)),availability:windows.map(([a,b])=>({start_at:new Date(a).toISOString(),end_at:new Date(b).toISOString()})),environment:[...new Set(preferences.flatMap(p=>p.environment))].sort(),arrangement_needs:[...new Set(preferences.flatMap(p=>p.arrangement_needs))].sort(),travel_status:'each_participant_must_check_route_before_confirmation'};
}

export function createSocialService(db,{clock,scope,ownerAllowed,limit,shape}){
 const now=()=>clock().toISOString();
 const account=owner=>db.prepare('SELECT * FROM social_accounts WHERE scope=? AND owner=?').bind(scope,owner).first();
 const byId=id=>db.prepare('SELECT * FROM social_accounts WHERE scope=? AND public_id=?').bind(scope,id).first();
 const pair=(a,b)=>digest([a,b].sort());
 const relation=async(a,b)=>db.prepare('SELECT * FROM social_friends WHERE scope=? AND pair_key=?').bind(scope,await pair(a,b)).first();
 const publicAccount=a=>a?{public_id:a.public_id,alias:a.alias,discoverable:!!a.discoverable,version:a.revision}:null;
 const expiry=(v,ceiling=null)=>{const x=stamp(v);if(x<=now()||Date.parse(x)-clock().getTime()>30*86400000||(ceiling&&x>ceiling))fail('invalid_expiry',400);return x;};
 async function friend(a,b){const rel=await relation(a,b);if(!ownerAllowed(b)||rel?.status!=='accepted')fail('accepted_friend_required',403);return rel;}
 async function load(id,owner,write=false){
  const row=await db.prepare('SELECT * FROM social_groups WHERE id=? AND scope=?').bind(id,scope).first();
  if(!row)fail('group_not_found',404);const data=JSON.parse(row.data),member=data.members.find(m=>m.owner===owner);
  if(!member||!['accepted','pending'].includes(member.status))fail('group_not_found',404);
  let purged=false;
  if(!data.closed&&row.expires_at<=now()){data.closed=true;data.activities=[];purged=true;}
  for(const activity of data.activities){
   if(!activity.closed&&(activity.expires_at<=now()||Object.values(activity.preferences).some(p=>stamp(p.expires_at)<=now()))){activity.closed=true;activity.preferences={};activity.digests={};reset(activity);purged=true;}
   else if(activity.plan&&stamp(activity.plan.expires_at)<=now()){reset(activity);purged=true;}
  }
  if(purged){const changed=await db.prepare('UPDATE social_groups SET data=?,revision=revision+1,updated_at=? WHERE id=? AND scope=? AND revision=?').bind(canonical(data),now(),id,scope,row.revision).run();if(changed.meta.changes!==1)fail('version_conflict');row.revision++;}
  if(write&&(row.expires_at<=now()||data.closed))fail('group_unavailable',410);
  return {...row,data,member};
 }
 async function save(row,expected){
  if(row.revision!==expected)fail('version_conflict');
  const guard=row.friendGuard;
  const result=await db.prepare("UPDATE social_groups SET data=?,revision=revision+1,updated_at=? WHERE id=? AND scope=? AND revision=? AND expires_at>? AND coalesce(json_extract(data,'$.closed'),0)=0"+(guard?" AND EXISTS(SELECT 1 FROM social_friends WHERE scope=? AND pair_key=? AND revision=? AND status='accepted')":'')).bind(canonical(row.data),now(),row.id,scope,expected,now(),...(guard?[scope,guard.pair_key,guard.revision]:[])).run();
  if(result.meta.changes!==1)fail('version_conflict');
 }
 const accepted=row=>row.data.members.filter(m=>m.status==='accepted');
 function accessActivity(row,id){
  if(row.member.status!=='accepted')fail('group_accept_required',403);
  const a=row.data.activities.find(a=>a.id===id);
  if(!a||!a.roster.includes(row.member.owner))fail('activity_not_found',404);
  if(a.closed||a.expires_at<=now()||!a.roster.every(o=>accepted(row).some(m=>m.owner===o)&&ownerAllowed(o)))fail('activity_unavailable',410);
  return a;
 }
 function reset(a){a.plan=null;a.analysis=null;a.plan_digest=null;a.confirmations={};}
 function livePreferences(a){return a.roster.every(o=>a.preferences[o]&&stamp(a.preferences[o].expires_at)>now());}
 function context(row,a){
  if(!livePreferences(a))fail('all_preferences_required');
  return {schema_version:'group-1.0',planning_id:a.id,mode:a.mode,revision:a.context_revision,participants:a.roster.map(o=>({public_id:row.data.members.find(m=>m.owner===o).public_id,preferences:a.preferences[o],approved_digest:a.digests[o]})).sort((a,b)=>a.public_id.localeCompare(b.public_id))};
 }
 function result(row,owner){
  if(row.expires_at<=now()||row.data.closed)return {group_id:row.id,version:row.revision,status:'unavailable',expires_at:row.expires_at};
  if(row.member.status==='pending')return {group_id:row.id,version:row.revision,status:'invited',name:row.data.name,expires_at:row.expires_at};
  const members=accepted(row).map(m=>({public_id:m.public_id,alias:m.alias}));
  const invitations=row.data.members.filter(m=>m.status==='pending').map(m=>({public_id:m.public_id,alias:m.alias}));
  const activities=row.data.activities.filter(a=>a.roster.includes(owner)).map(a=>{
   const available=!a.closed&&a.expires_at>now()&&a.roster.every(o=>accepted(row).some(m=>m.owner===o)&&ownerAllowed(o));
   const ready=available&&livePreferences(a),plan=ready&&a.plan&&stamp(a.plan.expires_at)>now()?a.plan:null;
   const confirmations=plan?a.roster.map(o=>a.confirmations[o]||null):[];
   const confirmed=!!plan&&confirmations.every(c=>c&&c.version===a.plan_version&&c.option_id===confirmations[0].option_id);
   return {id:a.id,title:a.title,mode:a.mode,expires_at:a.expires_at,status:!available?'unavailable':!ready?'pending':confirmed?'confirmed':plan?'proposed':'ready',participants:a.roster.map(o=>({public_id:row.data.members.find(m=>m.owner===o).public_id,approved:available&&!!a.preferences[o]&&stamp(a.preferences[o].expires_at)>now(),confirmation:plan?a.confirmations[o]||null:null})),my_preferences:available?a.preferences[owner]||null:null,conditions:ready?commonConditions(Object.values(a.preferences),clock()):null,plan,analysis:plan?a.analysis:null,plan_version:a.plan_version,plan_digest:plan?a.plan_digest:null,generated_by:plan?a.generated_by:null,all_confirmed:confirmed};
  });
  return {group_id:row.id,name:row.data.name,version:row.revision,status:'member',expires_at:row.expires_at,members,invitations,activities};
 }
 async function checkedPlan(row,a,r){
  const c=context(row,a),hash=await digest(c),prefs=a.roster.map(o=>a.preferences[o]),conditions=commonConditions(prefs,clock());
  if(conditions.blockers.length)fail('conditions_do_not_overlap');
  if(!prefs.every(p=>p.allow_shared_ai&&(a.mode!=='dating'||p.allow_romance_analysis)))fail('shared_ai_not_approved');
  const plan=r.plan;validate(plan,planSchema);validate(r.analysis,analysisSchema);
  if(plan.context_digest!==hash||plan.mode!==a.mode||plan.version!==a.plan_version+1)fail('context_changed');
  expiry(plan.expires_at,[a.expires_at,...prefs.map(p=>stamp(p.expires_at))].sort()[0]);
  for(const key of ['environment','arrangement_needs'])if(canonical([...plan.requirements[key]].sort())!==canonical(conditions[key]))fail('requirements_changed');
  if(new Set(plan.options.map(o=>o.option_id)).size!==plan.options.length)fail('duplicate_option');
  for(const o of plan.options){
   // Public source evidence is checked by the existing pair validator's rules below.
   for(const url of o.source_urls)publicSource(url);
   if(o.verification!=='not_verified'||o.verified_facts.length||o.source_open_window||o.source_admission||o.source_event_at||!o.unknowns.includes('all_details_unverified'))fail('unverified_venue_required');
   if(stamp(o.checked_at)>now())fail('future_source_check');
   const start=stamp(o.start_at),end=new Date(Date.parse(start)+o.duration_minutes*60000).toISOString();
   if(start<=now()||end>stamp(plan.expires_at))fail('invalid_plan_time');
   if(o.activity_type!=='online_chat'&&!o.sequence.includes('meet_public'))fail('public_meeting_required');
   for(const p of prefs){
    if(!p.areas.some(x=>norm(x)===norm(o.planning_area))||o.currency!==p.budget.currency||o.estimated_budget_minor>p.budget.max_per_person_minor||o.duration_minutes>p.duration_minutes||!p.availability.some(w=>start>=stamp(w.start_at)&&end<=stamp(w.end_at))||o.shared_interest_reasons.some(x=>!p.interests.includes(x)||p.avoid_interests.includes(x)))fail('plan_exceeds_member_conditions');
   }
  }
  if(r.approved_digest!==await digest({plan:r.plan,analysis:r.analysis}))fail('approval_content_mismatch');
 }
 return async function social(args,owner){
  shape(args,['request']);const r=args.request;validate(r,socialRequestSchema);const action=r.action;
  await limit(owner,'social_'+(['lookup','friend_request'].includes(action)?'lookup':'operations'),['lookup','friend_request'].includes(action)?30:240);
  const own=await account(owner);
  if(action==='account_read')return {account:publicAccount(own)};
  if(action==='account_save'){
   label(r.alias,40);if((own?.revision||0)!==r.expected_version)fail('version_conflict');
   const s=own?db.prepare('UPDATE social_accounts SET alias=?,discoverable=?,revision=revision+1 WHERE scope=? AND owner=? AND revision=?').bind(r.alias,Number(r.discoverable),scope,owner,r.expected_version):db.prepare('INSERT INTO social_accounts(scope,owner,public_id,alias,discoverable,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT DO NOTHING').bind(scope,owner,crypto.randomUUID().replaceAll('-',''),r.alias,Number(r.discoverable),now());
   if((await s.run()).meta.changes!==1)fail('version_conflict');return {account:publicAccount(await account(owner))};
  }
  if(!own)fail('social_account_required');
  if(action==='lookup'||action==='friend_request'||action==='friend_respond'){
   const peer=await byId(r.public_id);if(!peer||peer.owner===owner||!ownerAllowed(peer.owner))fail('person_not_available',404);
   const rel=await relation(owner,peer.owner);
   if(action==='lookup'){if(rel?.status==='blocked'||(!peer.discoverable&&rel?.status!=='accepted'))fail('person_not_available',404);return {person:{public_id:peer.public_id,alias:peer.alias}};}
   if(action==='friend_request'){
    if(!peer.discoverable||rel?.status==='blocked')fail('person_not_available',404);
    if(rel?.status==='accepted'||rel?.status==='pending')return {status:rel.status};
    const key=await pair(owner,peer.owner);const result=rel?await db.prepare("UPDATE social_friends SET sender=?,recipient=?,status='pending',revision=revision+1,updated_at=? WHERE scope=? AND pair_key=? AND revision=? AND status IN ('declined','removed')").bind(owner,peer.owner,now(),scope,key,rel.revision).run():await db.prepare("INSERT INTO social_friends(scope,pair_key,sender,recipient,status,updated_at) VALUES(?,?,?,?,'pending',?) ON CONFLICT DO NOTHING").bind(scope,key,owner,peer.owner,now()).run();
    if(result.meta.changes!==1)fail('version_conflict');return {status:'pending'};
   }
   if(!rel||rel.revision!==r.expected_version)fail('version_conflict');let next;
   if(r.choice==='accept'||r.choice==='decline'){if(rel.status!=='pending'||rel.recipient!==owner)fail('recipient_required',403);next=r.choice==='accept'?'accepted':'declined';}
   else if(r.choice==='cancel'){if(rel.status!=='pending'||rel.sender!==owner)fail('sender_required',403);next='removed';}
   else if(r.choice==='unblock'){if(rel.status!=='blocked'||rel.blocked_by!==owner)fail('block_owner_required',403);next='removed';}
   else if(r.choice==='remove'){if(rel.status!=='accepted')fail('accepted_friend_required');next='removed';}else next='blocked';
   const queries=[db.prepare('UPDATE social_friends SET status=?,blocked_by=?,revision=revision+1,updated_at=? WHERE scope=? AND pair_key=? AND revision=?').bind(next,next==='blocked'?owner:'',now(),scope,rel.pair_key,r.expected_version)];
   if(next==='blocked'||next==='removed')queries.push(db.prepare("UPDATE social_groups SET data=json_set(data,'$.closed',json('true'),'$.activities',json('[]')),revision=revision+1,updated_at=? WHERE changes()=1 AND scope=? AND EXISTS(SELECT 1 FROM json_each(data,'$.members') WHERE json_extract(value,'$.owner')=? AND json_extract(value,'$.status') IN ('accepted','pending')) AND EXISTS(SELECT 1 FROM json_each(data,'$.members') WHERE json_extract(value,'$.owner')=? AND json_extract(value,'$.status') IN ('accepted','pending'))").bind(now(),scope,owner,peer.owner));
   const changed=await db.batch(queries);if(changed[0].meta.changes!==1)fail('version_conflict');return {status:next};
  }
  if(action==='friends'){
   const rows=await db.prepare("SELECT * FROM social_friends WHERE scope=? AND (sender=? OR recipient=?) AND status IN ('pending','accepted','blocked') ORDER BY updated_at DESC LIMIT 100").bind(scope,owner,owner).all();const friends=[];
   for(const r of rows.results){const p=await account(r.sender===owner?r.recipient:r.sender);if(p&&ownerAllowed(p.owner)&&!(r.status==='blocked'&&r.blocked_by!==owner))friends.push({public_id:p.public_id,alias:p.alias,status:r.status,direction:r.sender===owner?'outgoing':'incoming',version:r.revision,blocked_by_me:r.blocked_by===owner});}return {friends};
  }
  if(action==='groups'){
   const rows=await db.prepare("SELECT id FROM social_groups WHERE scope=? AND expires_at>? AND EXISTS(SELECT 1 FROM json_each(data,'$.members') WHERE json_extract(value,'$.owner')=? AND json_extract(value,'$.status') IN ('accepted','pending')) ORDER BY updated_at DESC LIMIT 21").bind(scope,now(),owner).all();const groups=[];for(const x of rows.results.slice(0,20)){const row=await load(x.id,owner);groups.push({group_id:row.id,name:row.data.name,version:row.revision,status:row.data.closed?'unavailable':row.member.status==='pending'?'invited':'member',expires_at:row.expires_at});}return {groups,limited:rows.results.length>20};
  }
  if(action==='group_create'){
   label(r.name);const expires=expiry(r.expires_at);const count=await db.prepare("SELECT count(*) AS n FROM social_groups WHERE scope=? AND expires_at>? AND coalesce(json_extract(data,'$.closed'),0)=0 AND EXISTS(SELECT 1 FROM json_each(data,'$.members') WHERE json_extract(value,'$.owner')=?)").bind(scope,now(),owner).first();if(count.n>=20)fail('group_limit');
   const id=crypto.randomUUID().replaceAll('-',''),data={name:r.name,members:[{owner,public_id:own.public_id,alias:own.alias,status:'accepted'}],activities:[],closed:false};
   await db.prepare('INSERT INTO social_groups(id,scope,data,expires_at,updated_at) VALUES(?,?,?,?,?)').bind(id,scope,canonical(data),expires,now()).run();return result(await load(id,owner),owner);
  }
  const row=await load(r.group_id,owner,action!=='group_read');
  if(action==='group_read')return result(row,owner);
  if(row.revision!==r.expected_version&&action!=='context')fail('version_conflict');
  if(action==='group_respond'){
   if(r.choice==='accept'||r.choice==='decline'){
    if(row.member.status!=='pending')fail('pending_invitation_required');row.friendGuard=await friend(owner,row.member.invited_by);
    row.member.status=r.choice==='accept'?'accepted':'declined';
   }else{if(row.member.status!=='accepted')fail('group_accept_required');row.member.status='left';}
   for(const a of row.data.activities){a.closed=true;a.preferences={};a.digests={};reset(a);}
   await save(row,r.expected_version);return {status:row.member.status};
  }
  if(row.member.status!=='accepted')fail('group_accept_required',403);
  if(action==='group_invite'){
   const peer=await byId(r.public_id);if(!peer)fail('person_not_available',404);row.friendGuard=await friend(owner,peer.owner);
   if(row.data.members.some(m=>m.owner===peer.owner&&['accepted','pending'].includes(m.status)))fail('already_invited');
   if(row.data.members.filter(m=>['accepted','pending'].includes(m.status)).length>=8)fail('group_full');
   row.data.members=row.data.members.filter(m=>m.owner!==peer.owner);row.data.members.push({owner:peer.owner,public_id:peer.public_id,alias:peer.alias,status:'pending',invited_by:owner});
  }else if(action==='activity_create'){
   if(row.data.activities.length>=10)fail('activity_limit');label(r.title);const roster=r.participants.map(id=>accepted(row).find(m=>m.public_id===id)?.owner);
   if(roster.some(x=>!x)||!roster.includes(owner)||(r.mode==='dating'&&roster.length!==2))fail('invalid_activity_roster');
   row.data.activities.push({id:crypto.randomUUID().replaceAll('-',''),title:r.title,mode:r.mode,roster,expires_at:expiry(r.expires_at,row.expires_at),preferences:{},digests:{},context_revision:1,plan_version:0,confirmations:{},plan:null,analysis:null,closed:false});
  }else{
   const a=accessActivity(row,r.activity_id);
   if(action==='context'){const c=context(row,a),conditions=commonConditions(a.roster.map(o=>a.preferences[o]),clock());return {context:c,context_digest:await digest(c),conditions,ai_allowed:a.roster.every(o=>a.preferences[o].allow_shared_ai&&(a.mode!=='dating'||a.preferences[o].allow_romance_analysis)),version:row.revision,next_plan_version:a.plan_version+1};}
   if(action==='preferences'){
    const p=r.preferences;validate(p,preferencesSchema);label(p.origin_area);p.areas.forEach(x=>label(x));expiry(p.expires_at,a.expires_at);
    if(p.mode!==a.mode||p.interests.some(x=>p.avoid_interests.includes(x)))fail('invalid_preferences');
    for(const field of ['areas','interests','environment','arrangement_needs','avoid_interests','values','communication_preferences'])if(new Set(p[field]).size!==p[field].length)fail('duplicate_preferences');
    for(const w of p.availability)if(stamp(w.start_at)<=now()||stamp(w.end_at)<=stamp(w.start_at)||stamp(w.end_at)>stamp(p.expires_at))fail('invalid_availability');
    if(r.approved_digest!==await digest(p))fail('approval_content_mismatch');a.preferences[owner]=p;a.digests[owner]=r.approved_digest;a.context_revision++;reset(a);
   }else if(action==='preferences_withdraw'){delete a.preferences[owner];delete a.digests[owner];a.context_revision++;reset(a);}
   else if(action==='activity_leave'){a.closed=true;a.preferences={};a.digests={};reset(a);}
   else if(action==='propose'){await checkedPlan(row,a,r);a.plan=r.plan;a.analysis=r.analysis;a.plan_digest=r.approved_digest;a.plan_version=r.plan.version;a.confirmations={};a.generated_by=own.public_id;}
   else if(action==='confirm'){
    const c=context(row,a);if(!a.plan||a.plan_version!==r.plan_version||a.plan_digest!==r.plan_digest||a.plan.context_digest!==await digest(c)||stamp(a.plan.expires_at)<=now()||!a.plan.options.some(o=>o.option_id===r.option_id))fail('plan_changed');
    a.confirmations[owner]={version:r.plan_version,option_id:r.option_id};
   }else fail('unknown_action',404);
  }
  await save(row,r.expected_version);return result(await load(row.id,owner),owner);
 };
}
