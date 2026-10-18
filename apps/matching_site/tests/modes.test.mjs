import test from 'node:test';
import assert from 'node:assert/strict';
import {validate,validateStored,reciprocal,explain,digest,summaryExpiry} from '../lib/summary.mjs';
import {dating,friendship,fixture} from './helpers.mjs';

test('friendship has separate reciprocal intent, frequency and activity conditions',()=>{
  const a=friendship(),b=friendship({alias:'River'});
  validate(a);assert.equal(reciprocal(a,b),true);
  assert.equal(reciprocal(a,dating()),false);
  for(const change of [{accepted_friendship_intents:['conversation']},{accepted_frequencies:['weekly']},{interests:['music']},{activity_styles:['active']},{discoverable:false}]) assert.equal(reciprocal(a,friendship(change)),false);
  for(const change of [{relationship_goal:'long_term'},{life_directions:['build_family']},{private_report:'SYNTHETIC_PRIVATE_MARKER'},{interests:[]},{activity_styles:[]}]) assert.throws(()=>validate(friendship(change)));
  const reason=explain(a,b);assert.equal(reason.mode,'friendship');assert.equal('life_directions' in reason.shared,false);assert.equal('score' in reason,false);
});

test('mode-specific consent: friend-only never enters dating and pausing dating leaves friendship active',async()=>{
  const f=await fixture();
  try {
    await f.publish('synthetic-A',friendship());
    await f.publish('synthetic-B',friendship({summary_id:'b'.repeat(32)}));
    assert.equal((await f.call('slowmatch_find_candidates',{mode:'friendship'},'synthetic-A')).candidates.length,1);
    await assert.rejects(f.call('slowmatch_find_candidates',{mode:'dating'},'synthetic-A'),/publish_and_enable/);
    await f.publish('synthetic-A',dating());await f.publish('synthetic-B',dating({summary_id:'c'.repeat(32)}));
    await f.call('slowmatch_set_discoverability',{mode:'dating',discoverable:false,expected_version:1},'synthetic-B');
    assert.equal((await f.call('slowmatch_find_candidates',{mode:'dating'},'synthetic-A')).candidates.length,0);
    assert.equal((await f.call('slowmatch_find_candidates',{mode:'friendship'},'synthetic-A')).candidates.length,1);
    const friend=friendship();
    await assert.rejects(f.call('slowmatch_publish_summary',{mode:'dating',summary:friend,approved_digest:await digest(friend),expected_version:1},'synthetic-A'),/mode_summary_mismatch/);
    await assert.rejects(f.call('slowmatch_find_candidates',{},'synthetic-A'),/invalid_mode/);
  } finally {await f.dispose();}
});

test('legacy publication is preserved only as paused dating and cannot replay old approval',async()=>{
  const f=await fixture();
  try {
    const {mode,expires_at,...old}=dating({schema_version:'1.0'});void mode;void expires_at;validateStored(old);
    await f.db.prepare('INSERT INTO profiles(owner,public_id,summary,digest,revision,last_summary_version,active,updated_at) VALUES(?,?,?,?,1,1,1,?)').bind('synthetic-legacy','d'.repeat(32),JSON.stringify(old),await digest(old),'2026-01-01T00:00:00.000Z').run();
    const read=await f.call('slowmatch_read_my_summary',{mode:'dating'},'synthetic-legacy');assert.equal(read.status,'paused');assert.equal(read.summary.schema_version,'1.0');
    assert.equal((await f.call('slowmatch_read_my_summary',{mode:'friendship'},'synthetic-legacy')).status,'not_joined');
    await assert.rejects(f.call('slowmatch_set_discoverability',{mode:'dating',discoverable:true,expected_version:1},'synthetic-legacy'),/new_approved_summary_required/);
    await assert.rejects(f.call('slowmatch_publish_summary',{mode:'dating',summary:old,approved_digest:await digest(old),expected_version:1},'synthetic-legacy'));
    assert.equal((await f.db.prepare('SELECT active FROM profiles WHERE owner=?').bind('synthetic-legacy').first()).active,1,'legacy table retained unchanged');
    assert.equal((await f.publish('synthetic-legacy',dating({version:2}),1)).discoverable,true);
    await f.call('slowmatch_delete_my_summary',{mode:'dating',expected_version:2},'synthetic-legacy');
    const deleted=await f.db.prepare('SELECT summary,digest,active FROM profiles WHERE owner=?').bind('synthetic-legacy').first();
    assert.deepEqual(deleted,{summary:'{}',digest:'',active:0},'explicit deletion also redacts retained legacy public data');
  } finally {await f.dispose();}
});

test('nested references and anyOf remain strict against unknown fields and invalid types',()=>{
  const rule={$defs:{item:{type:'object',additionalProperties:false,required:['kind'],properties:{kind:{const:'ok',type:'string'}}}},anyOf:[{$ref:'#/$defs/item'},{type:'null'}]};
  validate({kind:'ok'},rule);validate(null,rule);
  for(const value of [{kind:'ok',private_profile:{}},{kind:'bad'},[],false])assert.throws(()=>validate(value,rule));
  for(const value of ['2030-02-30T00:00:00Z','2030-01-01T24:00:00Z','2030-01-01T00:00:00-05:00'])assert.throws(()=>summaryExpiry(value));
  assert.equal(summaryExpiry('2032-02-29T00:00:00Z'),Date.parse('2032-02-29T00:00:00Z'));
});

test('summary consent expiry removes discovery, prevents replay and needs a newly approved version',async()=>{
  let time=new Date('2030-01-01T00:00:00Z');
  const f=await fixture(()=>time);
  try{
    const a=friendship({expires_at:'2030-02-01T00:00:00Z'}),b=friendship({summary_id:'b'.repeat(32),expires_at:'2030-01-02T00:00:00Z'});
    await f.publish('synthetic-A',a);await f.publish('synthetic-B',b);
    assert.equal((await f.call('slowmatch_find_candidates',{mode:'friendship'},'synthetic-A')).candidates.length,1);
    time=new Date('2030-01-03T00:00:00Z');
    assert.equal((await f.call('slowmatch_find_candidates',{mode:'friendship'},'synthetic-A')).candidates.length,0);
    const own=await f.call('slowmatch_read_my_summary',{mode:'friendship'},'synthetic-B');assert.equal(own.status,'expired');assert.equal(own.discoverable,false);
    await assert.rejects(f.call('slowmatch_find_candidates',{mode:'friendship'},'synthetic-B'),/summary_expired/);
    await assert.rejects(f.call('slowmatch_set_discoverability',{mode:'friendship',discoverable:true,expected_version:1},'synthetic-B'),/summary_expired/);
    await assert.rejects(f.publish('synthetic-B',b,1),/invalid_summary_expiry/);
    await assert.rejects(f.publish('synthetic-C',friendship({expires_at:'2032-01-01T00:00:00Z'})),/invalid_summary_expiry/);
    await assert.rejects(f.publish('synthetic-C',friendship({expires_at:'2030-01-04T00:00:00-05:00'})),/utc_timestamp_required/);
    assert.equal((await f.publish('synthetic-B',{...b,version:2,expires_at:'2030-02-01T00:00:00Z'},1)).discoverable,true);
  }finally{await f.dispose();}
});
