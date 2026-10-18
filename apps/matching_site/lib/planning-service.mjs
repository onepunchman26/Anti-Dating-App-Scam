import {validate,digest,canonical,reciprocal,summaryExpiry,summaryExpired,ServiceError} from './summary.mjs';
import preferencesSchema from './shared-planning-preferences.schema.json' with {type:'json'};
import planSchema from './meeting-plan.schema.json' with {type:'json'};
export {preferencesSchema,planSchema};

const closed=new Set(['withdrawn','expired']);
const resetPlan="plan='{}',plan_digest='',plan_approved_by='',plan_approved_at='',confirmation_a=0,confirmation_b=0,option_a='',option_b='',feedback_a='',feedback_b=''";
const purge=`preferences_a='{}',preferences_b='{}',preferences_digest_a='',preferences_digest_b='',preferences_expires_a='',preferences_expires_b='',${resetPlan}`;
export const closePlanningSql=(guard='1=1')=>`UPDATE planning_sessions SET status='withdrawn',revision=revision+1,${purge},updated_at=? WHERE (owner_a=? OR owner_b=?) AND mode=? AND scope=? AND status NOT IN ('withdrawn','expired') AND ${guard}`;
const validId=value=>{if(typeof value!=='string'||!/^[a-f0-9]{32}$/u.test(value))throw new ServiceError('invalid_identifier');};
const utc=value=>{
  return new Date(summaryExpiry(value)).toISOString();
};
function future(value,now,ceiling=null){const time=utc(value);if(time<=now||Date.parse(time)-Date.parse(now)>30*86400000||(ceiling&&time>ceiling))throw new ServiceError('invalid_expiry');return time;}
const ready=row=>row.preferences_a!=='{}'&&row.preferences_b!=='{}';
const contextOf=row=>({schema_version:'1.0',planning_id:row.id,mode:row.mode,revision:row.context_revision,participants:[
  {public_id:row.public_a,preferences:JSON.parse(row.preferences_a),approved_digest:row.preferences_digest_a},
  {public_id:row.public_b,preferences:JSON.parse(row.preferences_b),approved_digest:row.preferences_digest_b},
].sort((a,b)=>a.public_id.localeCompare(b.public_id))});

export function createPlanningService(db,{clock,read,limit,shape,revision,modeValue,scope,ownerAllowed,activeValue}){
  const now=()=>clock().toISOString();
  const fetchRow=(id,mode,owner)=>db.prepare('SELECT * FROM planning_sessions WHERE id=? AND mode=? AND (owner_a=? OR owner_b=?) AND scope=?').bind(id,mode,owner,owner,scope).first();
  async function current(row){
    if(closed.has(row.status))return row;
    const time=now();
    let status=null;
    if(row.expires_at<=time||(row.preferences_expires_a&&row.preferences_expires_a<=time)||(row.preferences_expires_b&&row.preferences_expires_b<=time)||(row.plan!=='{}'&&utc(JSON.parse(row.plan).expires_at)<=time))status='expired';
    const [a,b]=await Promise.all([read(row.owner_a,row.mode),read(row.owner_b,row.mode)]);
    if(!status&&a?.summary!=='{}'&&b?.summary!=='{}'&&a&&b&&(summaryExpired(JSON.parse(a.summary),clock())||summaryExpired(JSON.parse(b.summary),clock())))status='expired';
    if(!status&&(a?.active!==activeValue||b?.active!==activeValue||!reciprocal(validate(JSON.parse(a.summary)),validate(JSON.parse(b.summary)),clock())))status='withdrawn';
    if(status){
      const result=await db.prepare(`UPDATE planning_sessions SET status=?,revision=revision+1,${purge},updated_at=? WHERE id=? AND revision=? AND scope=?`).bind(status,time,row.id,row.revision,scope).run();
      if(result.meta.changes!==1)throw new ServiceError('version_conflict',409);
      return {...row,status,revision:row.revision+1,preferences_a:'{}',preferences_b:'{}',plan:'{}',plan_digest:'',confirmation_a:0,confirmation_b:0,option_a:'',option_b:'',feedback_a:'',feedback_b:''};
    }
    return {...row,participation_revision_a:a.revision,participation_revision_b:b.revision};
  }
  async function load(args,owner,write=false){
    modeValue(args.mode);validId(args.planning_id);
    const stored=await fetchRow(args.planning_id,args.mode,owner);
    if(!stored)throw new ServiceError('planning_not_found',404);
    const row=await current(stored);
    if(write&&closed.has(row.status))throw new ServiceError('planning_unavailable',410);
    return row;
  }
  function receipt(row,owner){
    const isClosed=closed.has(row.status),side=row.owner_a===owner?'a':'b';
    const confirmed=!isClosed&&row.plan!=='{}'&&row.confirmation_a===row.plan_version&&row.confirmation_b===row.plan_version&&row.option_a===row.option_b;
    const participants=['a','b'].map(s=>{
      const feedback=row[`feedback_${s}`]?JSON.parse(row[`feedback_${s}`]):null;
      return {public_id:row[`public_${s}`],preferences_status:isClosed?'unavailable':row[`preferences_${s}`]==='{}'?'pending':'approved',preferences_version:row[`preferences_version_${s}`],confirmation:!isClosed&&row[`confirmation_${s}`]===row.plan_version&&row.plan!=='{}'?{plan_version:row.plan_version,option_id:row[`option_${s}`]}:null,feedback:!isClosed&&feedback&&feedback.expires_at>now()?feedback:null};
    });
    return {planning_id:row.id,mode:row.mode,version:row.revision,status:isClosed?row.status:confirmed?'confirmed':row.plan!=='{}'?'proposed':ready(row)?'ready':'pending',expires_at:row.expires_at,my_public_id:row[`public_${side}`],participants,my_preferences:!isClosed&&row[`preferences_${side}`]!=='{}'?JSON.parse(row[`preferences_${side}`]):null,my_preferences_digest:!isClosed?row[`preferences_digest_${side}`]||null:null,plan:!isClosed&&row.plan!=='{}'?JSON.parse(row.plan):null,plan_digest:!isClosed?row.plan_digest||null:null,plan_version:row.plan_version,both_confirmed:confirmed,agreed_option_id:confirmed?row.option_a:null,no_external_message_sent:true};
  }
  // The row revision and both live participation revisions guard every write.
  // This prevents an approval racing a pause, summary edit, withdrawal or expiry.
  async function change(row,args,set,values){
    revision(args.expected_version);
    if(args.expected_version!==row.revision)throw new ServiceError('version_conflict',409);
    const time=now();
    if(!ownerAllowed(row.owner_a)||!ownerAllowed(row.owner_b))throw new ServiceError('planning_unavailable',410);
    const result=await db.prepare(`UPDATE planning_sessions SET ${set},revision=revision+1,updated_at=? WHERE id=? AND mode=? AND revision=? AND scope=? AND status NOT IN ('withdrawn','expired') AND expires_at>? AND (preferences_expires_a='' OR preferences_expires_a>?) AND (preferences_expires_b='' OR preferences_expires_b>?) AND EXISTS(SELECT 1 FROM participations WHERE owner=owner_a AND mode=planning_sessions.mode AND scope=planning_sessions.scope AND active=CASE WHEN scope='production' THEN 1 ELSE 2 END AND revision=? AND julianday(json_extract(summary,'$.expires_at'))>julianday(?)) AND EXISTS(SELECT 1 FROM participations WHERE owner=owner_b AND mode=planning_sessions.mode AND scope=planning_sessions.scope AND active=CASE WHEN scope='production' THEN 1 ELSE 2 END AND revision=? AND julianday(json_extract(summary,'$.expires_at'))>julianday(?))`).bind(...values,time,row.id,row.mode,row.revision,scope,time,time,time,row.participation_revision_a,time,row.participation_revision_b,time).run();
    if(result.meta.changes!==1)throw new ServiceError('version_conflict',409);
  }
  function approve(args){if(args.approved!==true)throw new ServiceError('explicit_approval_required');}
  async function checkedPreferences(value,mode,row,args){
    validate(value,preferencesSchema);
    if(value.mode!==mode)throw new ServiceError('mode_summary_mismatch');
    const expiry=future(value.expires_at,now(),row.expires_at);
    for(const window of value.availability){const start=utc(window.start_at),end=utc(window.end_at);if(start<=now()||end<=start||end>expiry)throw new ServiceError('invalid_availability');}
    if([value.areas,value.environment,value.interests,value.arrangement_needs].some(values=>values.length!==new Set(values).size))throw new ServiceError('duplicate_preference');
    if(args.approved_digest!==await digest(value))throw new ServiceError('approval_content_mismatch');
    return expiry;
  }
  function publicSource(value){
    if(/[\s\\\u0000-\u001f\u007f]|%(?:0[0-9a-f]|1[0-9a-f]|7f)/iu.test(value))throw new ServiceError('invalid_public_source');
    let url;try{url=new URL(value);}catch{throw new ServiceError('invalid_public_source');}
    if(url.protocol!=='https:'||url.username||url.password||url.hash||url.search||url.port||url.hostname==='localhost'||/\.(?:local|localhost|internal|test|invalid)$/u.test(url.hostname)||!url.hostname.includes('.')||/^[\d.]+$/u.test(url.hostname)||url.hostname.includes(':'))throw new ServiceError('invalid_public_source');
    const labels=url.hostname.split('.');
    if(!/^[A-Za-z]{2,63}$/u.test(labels.at(-1))||labels.some(label=>!/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/u.test(label)))throw new ServiceError('invalid_public_source');
    let pathname;try{pathname=decodeURIComponent(url.pathname);}catch{throw new ServiceError('invalid_public_source');}
    if(new RegExp(planSchema['x-slowmatch-label-forbidden-pattern'],'iu').test(pathname))throw new ServiceError('invalid_public_source');
  }
  async function checkedPlan(plan,row,args){
    validate(plan,planSchema);
    if(!ready(row))throw new ServiceError('both_preferences_required',409);
    if(plan.mode!==row.mode||plan.context_digest!==await digest(contextOf(row)))throw new ServiceError('context_changed',409);
    if(plan.version!==row.plan_version+1)throw new ServiceError('plan_version_must_increase',409);
    const prefs=[JSON.parse(row.preferences_a),JSON.parse(row.preferences_b)];
    for(const field of ['environment','arrangement_needs']){
      const required=[...new Set(prefs.flatMap(pref=>pref[field]))].sort();
      if(canonical([...plan.requirements[field]].sort())!==canonical(required))throw new ServiceError('shared_requirements_mismatch');
    }
    const ceiling=[row.expires_at,row.preferences_expires_a,row.preferences_expires_b].sort()[0];
    const expiry=future(plan.expires_at,now(),ceiling);
    if(new Set(plan.options.map(o=>o.option_id)).size!==plan.options.length)throw new ServiceError('duplicate_option');
    for(const option of plan.options){
      for(const source of option.source_urls)publicSource(source);
      if(utc(option.checked_at)>now())throw new ServiceError('future_source_check');
      if(option.verification==='not_verified'&&(option.verified_facts.length||!option.unknowns.includes('all_details_unverified')))throw new ServiceError('unverified_details');
      if(new Set(option.verified_facts).size!==option.verified_facts.length)throw new ServiceError('duplicate_facts');
      for(const [fact,value] of [['hours',option.source_open_window],['admission_price',option.source_admission],['event_date',option.source_event_at]]){
        if(option.verified_facts.includes(fact)&&value==null)throw new ServiceError('verified_fact_value_required');
        if(value!=null&&(!option.verified_facts.includes(fact)||option.verification!=='official_source_checked'))throw new ServiceError('source_value_requires_checked_fact');
      }
      const start=utc(option.start_at),end=new Date(Date.parse(start)+option.duration_minutes*60000).toISOString();
      if(start<=now()||end>expiry)throw new ServiceError('invalid_plan_time');
      if(option.source_open_window&&(start<utc(option.source_open_window.start_at)||end>utc(option.source_open_window.end_at)))throw new ServiceError('outside_checked_open_window');
      if(option.source_admission&&(option.source_admission.currency!==option.currency||option.source_admission.amount_minor>option.estimated_budget_minor))throw new ServiceError('admission_exceeds_budget_ceiling');
      if(option.source_event_at&&start!==utc(option.source_event_at))throw new ServiceError('event_time_mismatch');
      for(const pref of prefs){
        if(!pref.areas.some(area=>area.trim().toLowerCase()===option.planning_area.trim().toLowerCase()))throw new ServiceError('place_outside_approved_area');
        if(option.currency!==pref.budget.currency||option.estimated_budget_minor>pref.budget.max_per_person_minor||option.duration_minutes>pref.duration_minutes)throw new ServiceError('plan_exceeds_approved_preferences');
        if(!pref.availability.some(w=>start>=utc(w.start_at)&&end<=utc(w.end_at)))throw new ServiceError('plan_outside_approved_availability');
        if(option.shared_interest_reasons.some(v=>!pref.interests.includes(v)))throw new ServiceError('unsupported_shared_interest');
      }
      if(option.activity_type!=='online_chat'&&!option.sequence.includes('meet_public'))throw new ServiceError('public_meeting_required');
    }
    if(args.approved_digest!==await digest(plan))throw new ServiceError('approval_content_mismatch');
  }
  return async function operate(name,args,owner){
    modeValue(args?.mode);
    if(name==='slowmatch_planning_create'){
      shape(args,['mode','candidate_public_id','expires_at','explicit_invitation']);
      if(args.explicit_invitation!==true)throw new ServiceError('explicit_invitation_required');
      validId(args.candidate_public_id);await limit(owner,'planning_write',30);
      const expiry=future(args.expires_at,now());
      const a=await read(owner,args.mode),b=await db.prepare('SELECT * FROM participations WHERE public_id=? AND mode=? AND owner<>? AND scope=?').bind(args.candidate_public_id,args.mode,owner,scope).first();
      if(a?.active!==activeValue||b?.active!==activeValue||!ownerAllowed(b.owner)||!reciprocal(validate(JSON.parse(a.summary)),validate(JSON.parse(b.summary)),clock()))throw new ServiceError('current_reciprocal_candidate_required',403);
      const pairKey=await digest([owner,b.owner].sort());
      const existing=await db.prepare("SELECT * FROM planning_sessions WHERE pair_key=? AND mode=? AND scope=? AND status NOT IN ('withdrawn','expired')").bind(pairKey,args.mode,scope).first();
      if(existing){const live=await current(existing);if(!closed.has(live.status))return {...receipt(live,owner),idempotent:true};}
      const id=crypto.randomUUID().replaceAll('-',''),time=now();
      const result=await db.prepare("INSERT INTO planning_sessions(id,pair_key,scope,mode,owner_a,owner_b,public_a,public_b,expires_at,created_at,updated_at) SELECT ?,?,?,?,?,?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM participations WHERE owner=? AND mode=? AND revision=? AND scope=? AND active=CASE WHEN scope='production' THEN 1 ELSE 2 END AND julianday(json_extract(summary,'$.expires_at'))>julianday(?)) AND EXISTS(SELECT 1 FROM participations WHERE owner=? AND mode=? AND revision=? AND scope=? AND active=CASE WHEN scope='production' THEN 1 ELSE 2 END AND julianday(json_extract(summary,'$.expires_at'))>julianday(?)) ON CONFLICT DO NOTHING").bind(id,pairKey,scope,args.mode,owner,b.owner,a.public_id,b.public_id,expiry,time,time,owner,args.mode,a.revision,scope,time,b.owner,args.mode,b.revision,scope,time).run();
      if(result.meta.changes!==1){
        const retry=await db.prepare("SELECT * FROM planning_sessions WHERE pair_key=? AND mode=? AND scope=? AND status NOT IN ('withdrawn','expired')").bind(pairKey,args.mode,scope).first();
        if(retry){const live=await current(retry);if(!closed.has(live.status))return {...receipt(live,owner),idempotent:true};}
        throw new ServiceError('version_conflict',409);
      }
      return receipt(await load({planning_id:id,mode:args.mode},owner),owner);
    }
    if(name==='slowmatch_planning_list'){
      shape(args,['mode']);await limit(owner,'planning_query',30);
      const rows=await db.prepare('SELECT * FROM planning_sessions WHERE mode=? AND (owner_a=? OR owner_b=?) AND scope=? ORDER BY updated_at DESC LIMIT 21').bind(args.mode,owner,owner,scope).all();
      const sessions=[];for(const row of rows.results.slice(0,20))sessions.push(receipt(await current(row),owner));
      return {sessions,limit:20,limited:rows.results.length>20,no_external_message_sent:true};
    }
    const fields={
      slowmatch_planning_read:['mode','planning_id'],slowmatch_planning_context:['mode','planning_id'],
      slowmatch_planning_preferences:['mode','planning_id','preferences','approved_digest','approved','expected_version'],
      slowmatch_planning_propose:['mode','planning_id','plan','approved_digest','approved','expected_version'],
      slowmatch_planning_confirm:['mode','planning_id','plan_version','plan_digest','option_id','expected_version'],
      slowmatch_planning_withdraw:['mode','planning_id','expected_version'],
      slowmatch_planning_feedback:['mode','planning_id','plan_version','choice','expires_at','approved','expected_version'],
      slowmatch_planning_feedback_withdraw:['mode','planning_id','expected_version'],
    }[name];
    if(!fields)throw new ServiceError('unknown_tool',404);shape(args,fields);
    const readOnly=name==='slowmatch_planning_read'||name==='slowmatch_planning_context';
    if(!readOnly)await limit(owner,'planning_write',60);
    const row=await load(args,owner,!readOnly),side=row.owner_a===owner?'a':'b';
    if(name==='slowmatch_planning_read')return receipt(row,owner);
    if(name==='slowmatch_planning_context'){
      if(closed.has(row.status))throw new ServiceError('planning_unavailable',410);
      if(!ready(row))throw new ServiceError('both_preferences_required',409);
      const context=contextOf(row);return {context,context_digest:await digest(context),scope:'approved_planning_only'};
    }
    if(name==='slowmatch_planning_preferences'){
      approve(args);const expiry=await checkedPreferences(args.preferences,args.mode,row,args);
      await change(row,args,`preferences_${side}=?,preferences_digest_${side}=?,preferences_version_${side}=preferences_version_${side}+1,preferences_expires_${side}=?,preferences_approved_${side}=?,context_revision=context_revision+1,${resetPlan},status='pending'`,[canonical(args.preferences),args.approved_digest,expiry,now()]);
    }else if(name==='slowmatch_planning_propose'){
      approve(args);await checkedPlan(args.plan,row,args);
      await change(row,args,"plan=?,plan_digest=?,plan_version=?,plan_approved_by=?,plan_approved_at=?,confirmation_a=0,confirmation_b=0,option_a='',option_b='',feedback_a='',feedback_b='',status='proposed'",[canonical(args.plan),args.approved_digest,args.plan.version,side,now()]);
    }else if(name==='slowmatch_planning_confirm'){
      revision(args.plan_version);
      if(row.plan==='{}'||args.plan_version!==row.plan_version||args.plan_digest!==row.plan_digest||JSON.parse(row.plan).context_digest!==await digest(contextOf(row)))throw new ServiceError('plan_changed',409);
      if(!JSON.parse(row.plan).options.some(o=>o.option_id===args.option_id))throw new ServiceError('invalid_option');
      await change(row,args,`confirmation_${side}=?,option_${side}=?`,[row.plan_version,args.option_id]);
    }else if(name==='slowmatch_planning_withdraw'){
      await change(row,args,`status='withdrawn',${purge}`,[]);
    }else if(name==='slowmatch_planning_feedback'){
      approve(args);revision(args.plan_version);
      if(!receipt(row,owner).both_confirmed||args.plan_version!==row.plan_version)throw new ServiceError('confirmed_current_plan_required',409);
      if(!['again','undecided','not_now','no_again'].includes(args.choice))throw new ServiceError('invalid_feedback');
      const expires_at=future(args.expires_at,now(),row.expires_at);
      await change(row,args,`feedback_${side}=?`,[canonical({choice:args.choice,plan_version:row.plan_version,expires_at})]);
    }else if(name==='slowmatch_planning_feedback_withdraw'){
      await change(row,args,`feedback_${side}=''`,[]);
    }
    return receipt(await load(args,owner),owner);
  };
}
