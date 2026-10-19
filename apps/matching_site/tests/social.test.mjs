import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture} from './helpers.mjs';
import {digest} from '../lib/summary.mjs';
import {socialCopy} from '../lib/social-copy.mjs';
import {createService} from '../lib/matching-service.mjs';
export const preferences=(extra={})=>({schema_version:'1.0',mode:'friendship',areas:['Toronto'],origin_area:'Toronto',max_travel_minutes:30,availability:[{start_at:'2030-01-03T16:00:00Z',end_at:'2030-01-03T20:00:00Z'}],budget:{currency:'CAD',max_per_person_minor:2000},duration_minutes:60,interests:['reading'],avoid_interests:[],values:['honesty'],communication_preferences:['reflective'],environment:['public_place','easy_exit'],arrangement_needs:[],allow_shared_ai:true,allow_romance_analysis:false,expires_at:'2030-01-09T00:00:00Z',...extra});
export async function socialFixture(){
 let time=new Date('2030-01-01T00:00:00Z');const f=await fixture(()=>time);
 const call=(owner,action,fields={})=>f.call('slowmatch_social',{request:{action,...fields}},owner);
 const ids={};for(const owner of ['A','B','C','outsider'])ids[owner]=(await call(owner,'account_save',{alias:'Synthetic '+owner,adult_confirmed:true,discoverable:true,approved:true,expected_version:0})).account.public_id;
 const connect=async(peer)=>{await call('A','friend_request',{public_id:ids[peer],approved:true});const {friends}=await call(peer,'friends');await call(peer,'friend_respond',{public_id:ids.A,choice:'accept',expected_version:friends[0].version});};
 await connect('B');await connect('C');
 let g=await call('A','group_create',{name:'Synthetic circle',expires_at:'2030-01-10T00:00:00Z',approved:true});const group_id=g.group_id;
 const get=(owner='A')=>call(owner,'group_read',{group_id});
 const change=async(owner,action,fields={})=>call(owner,action,{group_id,expected_version:(await get(owner)).version,...fields});
 for(const peer of ['B','C']){await change('A','group_invite',{public_id:ids[peer],approved:true});assert.equal((await get(peer)).status,'invited');await change(peer,'group_respond',{choice:'accept'});}
 g=await change('A','activity_create',{title:'Synthetic afternoon',mode:'friendship',participants:[ids.A,ids.B,ids.C],expires_at:'2030-01-09T00:00:00Z',approved:true});const activity_id=g.activities[0].id;
 const share=async(owner,p=preferences())=>change(owner,'preferences',{activity_id,preferences:p,approved_digest:await digest(p),approved:true});
 const context=()=>call('A','context',{group_id,activity_id});
 return {...f,call,ids,get,change,share,context,group_id,activity_id,time:t=>time=new Date(t)};
}
const option=(option_id)=>({option_id,activity_type:'cafe_walk',place_name:'Synthetic public cafe',address_or_area:'Toronto',planning_area:'Toronto',source_open_window:null,source_admission:null,source_event_at:null,source_urls:['https://example.org/cafe'],checked_at:'2029-12-31T18:00:00Z',verification:'not_verified',verified_facts:[],unknowns:['all_details_unverified'],start_at:'2030-01-03T17:00:00Z',duration_minutes:60,estimated_budget_minor:1000,currency:'CAD',sequence:['meet_public','coffee','leave_independently'],shared_interest_reasons:['reading'],conversation_starters:['shared_hobby'],arrival_exit:'independent_arrival_easy_exit',fallback:'end_without_pressure',booking_status:'not_booked'});
const draft=c=>({plan:{schema_version:'1.0',mode:'friendship',context_digest:c.context_digest,version:c.next_plan_version,expires_at:'2030-01-08T00:00:00Z',budget_basis:'shared_budget_ceiling_not_verified_price',requirements:{environment:['easy_exit','public_place'],arrangement_needs:[],status:'confirm_venue_suitability_before_agreeing'},options:[option('a'),option('b')]},analysis:{discussion_points:['Discuss a shared reading interest.'],uncertainty:'Self-reports only; check venue conditions.'}});
test('three synthetic identities: no discovery needed, individually scoped preferences and exact confirmations',async()=>{
 const f=await socialFixture();try{
 assert.equal((await f.db.prepare('SELECT count(*) AS n FROM participations').first()).n,0);
 await assert.rejects(f.get('outsider'),/group_not_found/);
 await f.share('A');await f.share('B');await assert.rejects(f.context(),/all_preferences_required/);
 await f.share('C');const c=await f.context();assert.equal(c.context.participants.length,3);assert.equal(c.ai_allowed,true);assert.equal(c.context_digest,await digest(c.context));assert.equal(c.next_plan_version,1);
 const d=draft(c),approved_digest=await digest(d);let g=await f.change('A','propose',{activity_id:f.activity_id,...d,approved_digest,approved:true});
 for(const owner of ['A','B','C'])g=await f.change(owner,'confirm',{activity_id:f.activity_id,plan_version:1,plan_digest:approved_digest,option_id:'a',approved:true,conditions_checked:true});
 assert.equal(g.activities[0].all_confirmed,true);
 await f.share('C',preferences({budget:{currency:'CAD',max_per_person_minor:500}}));assert.equal((await f.get()).activities[0].plan,null);
 await assert.rejects(f.change('A','propose',{activity_id:f.activity_id,...d,approved_digest,approved:true}),/context_changed/);
 const newId=(await f.call('A','account_save',{alias:'Changed alias',adult_confirmed:true,discoverable:false,approved:true,expected_version:1})).account.public_id;assert.equal(newId,f.ids.A);
 }finally{await f.dispose();}
});
test('one person can refuse AI, remove overlap, withdraw, or leave; others cannot override',async()=>{
 const f=await socialFixture();try{
 await f.share('A');await f.share('B');await f.share('C',preferences({allow_shared_ai:false}));let c=await f.context();assert.equal(c.ai_allowed,false);
 let d=draft(c);await assert.rejects(f.change('A','propose',{activity_id:f.activity_id,...d,approved_digest:await digest(d),approved:true}),/shared_ai_not_approved/);
 await f.share('C',preferences({areas:['Ottawa']}));c=await f.context();assert.ok(c.conditions.blockers.includes('no_shared_area'));
 d=draft(c);await assert.rejects(f.change('A','propose',{activity_id:f.activity_id,...d,approved_digest:await digest(d),approved:true}),/conditions_do_not_overlap/);
 await f.share('C');c=await f.context();d=draft(c);await f.change('C','preferences_withdraw',{activity_id:f.activity_id});await assert.rejects(f.change('A','propose',{activity_id:f.activity_id,...d,approved_digest:await digest(d),approved:true}),/all_preferences_required/);
 await assert.rejects(f.share('C',preferences({private_profile:'SYNTHETIC_PRIVATE_MARKER'})));
 await f.change('B','group_respond',{choice:'leave'});await assert.rejects(f.get('B'),/group_not_found/);assert.equal((await f.get()).activities[0].status,'unavailable');
 }finally{await f.dispose();}
});
test('blocking a friend revokes shared groups; outsiders cannot spoof identity or read invitations',async()=>{
 const f=await socialFixture();try{
 const rel=(await f.call('A','friends')).friends.find(p=>p.public_id===f.ids.B);
 await f.call('A','friend_respond',{public_id:f.ids.B,choice:'block',expected_version:rel.version});
 assert.equal((await f.get('B')).status,'unavailable');await assert.rejects(f.call('B','lookup',{public_id:f.ids.A}),/person_not_available/);
 await assert.rejects(f.call('B','friend_request',{public_id:f.ids.A,approved:true}),/person_not_available/);
 await assert.rejects(f.call('outsider','group_read',{group_id:f.group_id,user_id:'A'}));
 assert.equal((await f.db.prepare('SELECT data FROM social_groups WHERE id=?').bind(f.group_id).first()).data.includes('max_per_person_minor'),false);
 }finally{await f.dispose();}
});

test('group capacity includes pending invites; unrelated scopes cannot resolve personal IDs',async()=>{
 const f=await socialFixture();try{
 for(let i=0;i<6;i++){
  const owner='extra-'+i,id=(await f.call(owner,'account_save',{alias:'Synthetic extra',adult_confirmed:true,discoverable:true,approved:true,expected_version:0})).account.public_id;
  await f.call('A','friend_request',{public_id:id,approved:true});const rel=(await f.call(owner,'friends')).friends[0];await f.call(owner,'friend_respond',{public_id:f.ids.A,choice:'accept',expected_version:rel.version});
  if(i<5)await f.change('A','group_invite',{public_id:id,approved:true});else await assert.rejects(f.change('A','group_invite',{public_id:id,approved:true}),/group_full/);
 }
 const scoped=createService(f.db,{clock:()=>new Date('2030-01-01T00:00:00Z'),defaultTestScopeConfiguration:JSON.stringify({scope:'circle-test',expires_at:'2030-01-10T00:00:00Z'})});
 assert.equal((await scoped('slowmatch_social',{request:{action:'account_read'}},'A')).account,null);
 await scoped('slowmatch_social',{request:{action:'account_save',alias:'Scoped synthetic',adult_confirmed:true,discoverable:true,approved:true,expected_version:0}},'A');
 await assert.rejects(scoped('slowmatch_social',{request:{action:'lookup',public_id:f.ids.B}},'A'),/person_not_available/);
 }finally{await f.dispose();}
});

test('concurrent edits are version guarded; expired context and plans cannot be reused',async()=>{
 const f=await socialFixture();try{
 for(const o of ['A','B','C'])await f.share(o);
 const c=await f.context(),d=draft(c),hash=await digest(d);
 await f.change('A','propose',{activity_id:f.activity_id,...d,approved_digest:hash,approved:true});
 const g=await f.get();const changes=await Promise.allSettled(['B','C'].map(o=>f.call(o,'preferences_withdraw',{group_id:f.group_id,activity_id:f.activity_id,expected_version:g.version})));
 assert.equal(changes.filter(x=>x.status==='fulfilled').length,1);
 assert.equal((await f.get()).activities[0].plan,null);
 for(const o of ['A','B','C'])await f.share(o);const next=draft(await f.context());await f.change('A','propose',{activity_id:f.activity_id,...next,approved_digest:await digest(next),approved:true});
 f.time('2030-01-08T01:00:00Z');assert.equal((await f.get()).activities[0].plan,null);
 await assert.rejects(f.change('A','confirm',{activity_id:f.activity_id,plan_version:next.plan.version,plan_digest:await digest(next),option_id:'a',approved:true,conditions_checked:true}),/plan_changed/);
 f.time('2030-01-10T01:00:00Z');assert.equal((await f.get()).status,'unavailable');await assert.rejects(f.context(),/group_unavailable/);
 }finally{await f.dispose();}
});

test('social UI copy has complete single-language resources',()=>{
 for(const [key,pair] of Object.entries(socialCopy)){assert.equal(pair.length,2,key);assert.ok(pair.every(x=>typeof x==='string'&&x.trim()),key);assert.ok(!/[\u3400-\u9fff]/u.test(pair[0]),key);assert.ok(/[\u3400-\u9fff]/u.test(pair[1]),key);}
});
