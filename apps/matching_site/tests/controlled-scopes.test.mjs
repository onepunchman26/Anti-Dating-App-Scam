import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createService} from '../lib/matching-service.mjs';
import {accountFingerprint,parseTestScopes,parseDefaultTestScope,SERVICE_VERSION} from '../lib/service-policy.mjs';
import {digest} from '../lib/summary.mjs';
import {dating,friendship,fixture} from './helpers.mjs';

const clock=()=>new Date('2030-01-01T00:00:00Z');
const expires_at='2030-02-01T00:00:00Z';
const summary=(mode,changes={})=>(mode==='dating'?dating:friendship)({expires_at,...changes});
async function configuration(entries){
  const memberships={};
  for(const [owner,scope,expiry=expires_at] of entries)memberships[await accountFingerprint(owner)]={scope,expires_at:expiry};
  return JSON.stringify({version:1,memberships});
}
const publish=async(call,owner,mode,changes={})=>{
  const shared=summary(mode,changes);
  return call('slowmatch_publish_summary',{mode,summary:shared,approved_digest:await digest(shared),expected_version:0,client_protocol:'1.0'},owner);
};

test('server-controlled test scope never mixes either matching mode with production or another test scope',async()=>{
  const f=await fixture(clock);
  try{
    const config=await configuration([['synthetic-A','pilot-one'],['synthetic-B','pilot-one'],['synthetic-C','pilot-two']]);
    const call=createService(f.db,{clock,testScopeConfiguration:config});
    // Preserve an existing production participation for A; entering test scope
    // must never mutate or relabel this record.
    const original=await publish(f.call,'synthetic-A','friendship',{alias:'Original Cedar'});
    for(const mode of ['dating','friendship']){
      await publish(call,'synthetic-A',mode,{alias:'Test Cedar'});
      await publish(call,'synthetic-B',mode,{alias:'Test River'});
      await publish(call,'synthetic-C',mode,{alias:'Other Pilot'});
      await publish(call,'synthetic-real-one',mode,{alias:'Normal One'});
      await publish(call,'synthetic-real-two',mode,{alias:'Normal Two'});
      const testCandidates=await call('slowmatch_find_candidates',{mode},'synthetic-A');
      assert.deepEqual(testCandidates.candidates.map(c=>c.summary.alias),['Test River']);
      const production=await call('slowmatch_find_candidates',{mode},'synthetic-real-one');
      assert.equal(production.candidates.some(c=>c.summary.alias.startsWith('Test')||c.summary.alias==='Other Pilot'),false);
      assert.equal((await call('slowmatch_find_candidates',{mode},'synthetic-C')).candidates.length,0);
      const serialized=JSON.stringify(testCandidates);
      for(const text of ['account_fingerprint','slowmatch-test:','synthetic-B','test:pilot-one'])assert.equal(serialized.includes(text),false);
      const rollbackQuery=await f.db.prepare('SELECT public_id,summary FROM participations WHERE mode=? AND active=1 AND owner<>? ORDER BY public_id LIMIT 101').bind(mode,'synthetic-real-one').all();
      assert.equal(rollbackQuery.results.some(row=>JSON.parse(row.summary).alias.startsWith('Test')||JSON.parse(row.summary).alias==='Other Pilot'),false,'the prior 0.7 discovery query cannot expose test rows after rollback');
    }
    const current=await call('slowmatch_read_my_summary',{mode:'friendship'},'synthetic-A');
    await call('slowmatch_delete_my_summary',{mode:'friendship',expected_version:current.version},'synthetic-A');
    const stored=await f.db.prepare('SELECT public_id,summary,scope FROM participations WHERE owner=? AND mode=?').bind('synthetic-A','friendship').first();
    assert.equal(stored.scope,'production');assert.equal(stored.public_id,original.public_id);assert.equal(JSON.parse(stored.summary).alias,'Original Cedar');
    await assert.rejects(call('slowmatch_find_candidates',{mode:'dating',scope:'production'},'synthetic-A'),/invalid_arguments/);
    await assert.rejects(call('slowmatch_find_candidates',{mode:'dating',user_id:'synthetic-real-one'},'synthetic-A'),/invalid_arguments/);
  }finally{await f.dispose();}
});

test('planning checks the same server-selected scope even with a known candidate or plan ID',async()=>{
  const f=await fixture(clock);
  try{
    const call=createService(f.db,{clock,testScopeConfiguration:await configuration([['synthetic-A','pilot-one'],['synthetic-B','pilot-one'],['synthetic-C','pilot-two']])});
    await publish(call,'synthetic-A','friendship');const b=await publish(call,'synthetic-B','friendship');
    const c=await publish(call,'synthetic-C','friendship'),production=await publish(call,'synthetic-real','friendship');
    const create=public_id=>({mode:'friendship',candidate_public_id:public_id,expires_at:'2030-01-10T00:00:00Z',explicit_invitation:true});
    for(const peer of [c,production])await assert.rejects(call('slowmatch_planning_create',create(peer.public_id),'synthetic-A'),/current_reciprocal_candidate_required/);
    const plan=await call('slowmatch_planning_create',create(b.public_id),'synthetic-A');
    const args={mode:'friendship',planning_id:plan.planning_id};
    assert.equal((await call('slowmatch_planning_read',args,'synthetic-B')).status,'pending');
    for(const outsider of ['synthetic-C','synthetic-real'])await assert.rejects(call('slowmatch_planning_read',args,outsider),/planning_not_found/);
    const raw=await f.db.prepare('SELECT scope FROM planning_sessions WHERE id=?').bind(plan.planning_id).first();assert.equal(raw.scope,'test:pilot-one');
    const revoked=createService(f.db,{clock,testScopeConfiguration:await configuration([['synthetic-A','pilot-one']])});
    assert.equal((await revoked('slowmatch_find_candidates',{mode:'friendship'},'synthetic-A')).candidates.length,0,'removed test member no longer appears');
    assert.equal((await revoked('slowmatch_planning_read',args,'synthetic-A')).status,'withdrawn','peer membership removal closes shared content');
    const disabled=await revoked('slowmatch_channel_check',{write:false},'synthetic-B');
    assert.equal(disabled.data_scope.access,'not_configured');assert.equal(disabled.data_scope.id,'test:pilot-one');
    await assert.rejects(revoked('slowmatch_read_my_summary',{mode:'friendship'},'synthetic-B'),/controlled_test_scope_not_configured/);
  }finally{await f.dispose();}
});

test('removed or expired test configuration fails closed and never falls back to production',async()=>{
  let current=clock();const tick=()=>current;
  const f=await fixture(tick);
  try{
    const raw=await configuration([['synthetic-A','pilot-one','2030-01-02T00:00:00Z']]);
    const testCall=createService(f.db,{clock:tick,testScopeConfiguration:raw});
    await publish(testCall,'synthetic-A','dating');
    const missing=createService(f.db,{clock:tick});
    const blocked=await missing('slowmatch_channel_check',{write:true},'synthetic-A');
    assert.equal(blocked.data_scope.kind,'controlled_test');assert.equal(blocked.data_scope.access,'not_configured');assert.equal(blocked.write_check,'blocked');
    await assert.rejects(publish(missing,'synthetic-A','friendship'),/controlled_test_scope_not_configured/);
    current=new Date('2030-01-03T00:00:00Z');
    const expired=await testCall('slowmatch_channel_check',{write:false},'synthetic-A');assert.equal(expired.data_scope.access,'expired');
    await assert.rejects(testCall('slowmatch_find_candidates',{mode:'dating'},'synthetic-A'),/controlled_test_scope_expired/);
    const rows=await f.db.prepare("SELECT COUNT(*) AS count FROM participations WHERE scope='production'").first();assert.equal(rows.count,0);
  }finally{await f.dispose();}
});

test('health reports only verified server facts and a caller-only stable account binding',async()=>{
  const f=await fixture(clock);
  try{
    const health=await f.call('slowmatch_channel_check',{write:false,client_protocol:'1.0'},'synthetic-A');
    assert.equal(health.authenticated,true);assert.equal(health.account_fingerprint,await accountFingerprint('synthetic-A'));assert.equal(health.account_fingerprint.length,64);
    assert.equal(health.service_version,SERVICE_VERSION);assert.equal(health.service_protocol_version,'1.0');
    assert.equal(health.write_check,'not_checked');assert.equal(health.persisted,false);assert.equal(health.client_skill,'not_checked');assert.equal(health.client_local_tools,'not_checked');
    assert.deepEqual(health.data_scope,{kind:'production',id:'production',access:'enabled'});
    assert.equal(JSON.stringify(health).includes('synthetic-A'),false);
    const written=await f.call('slowmatch_channel_check',{write:true},'synthetic-A');assert.equal(written.write_check,'passed');assert.equal(written.persisted,true);
    assert.equal((await f.call('slowmatch_channel_check',{write:false},'synthetic-B')).persisted,false);
    assert.notEqual((await f.call('slowmatch_channel_check',{write:false},'synthetic-B')).account_fingerprint,health.account_fingerprint);
    await assert.rejects(f.call('slowmatch_channel_check',{write:false},''),/sign_in_required/);
    await assert.rejects(f.call('slowmatch_channel_check',{write:false,scope:'test:pilot'},'synthetic-A'),/invalid_arguments/);
  }finally{await f.dispose();}
});

test('declared incompatible clients and invalid maintainer configuration fail before mutations',async()=>{
  let queries=0;const db={prepare(){queries++;throw Error('must not query');}};
  const call=createService(db);
  await assert.rejects(call('slowmatch_channel_check',{write:true,client_protocol:'2.0'},'synthetic-A'),error=>error.message==='client_upgrade_required'&&error.status===426);
  assert.equal(queries,0);
  for(const value of ['not json','[]',JSON.stringify({version:1,memberships:{fake:{scope:'pilot-one',expires_at}}}),JSON.stringify({version:1,memberships:{['a'.repeat(64)]:{scope:'production',expires_at}}}),JSON.stringify({version:1,memberships:{['a'.repeat(64)]:{scope:'pilot-one',expires_at:'2030-02-30T00:00:00Z'}}})])assert.throws(()=>parseTestScopes(value),/test_scope_configuration_invalid/);
  assert.throws(()=>createService(db,{testScopeConfiguration:'invalid'}),/test_scope_configuration_invalid/);assert.equal(queries,0);
  for(const raw of ['[]','{}',JSON.stringify({scope:'production',expires_at}),JSON.stringify({scope:'pilot-one',expires_at,owner:'synthetic-A'})])assert.throws(()=>parseDefaultTestScope(raw),/test_scope_configuration_invalid/);
});

test('one maintainer default automatically enrolls authorized A and B without per-account setup',async()=>{
  let time=clock();const tick=()=>time;
  const f=await fixture(tick);
  try{
    const original=await publish(f.call,'synthetic-A','friendship',{alias:'Original Cedar'});
    const defaultTestScopeConfiguration=JSON.stringify({scope:'pilot-default',expires_at:'2030-01-10T00:00:00Z'});
    const call=createService(f.db,{clock:tick,defaultTestScopeConfiguration});
    for(const owner of ['synthetic-A','synthetic-B']){
      const health=await call('slowmatch_channel_check',{write:false,client_protocol:'1.0'},owner);
      assert.deepEqual(health.data_scope,{kind:'controlled_test',id:'test:pilot-default',access:'enabled'});
      assert.equal(health.database_schema,'passed');
      for(const mode of ['dating','friendship'])await publish(call,owner,mode);
    }
    assert.equal((await call('slowmatch_find_candidates',{mode:'dating'},'synthetic-A')).candidates.length,1);
    assert.equal((await call('slowmatch_find_candidates',{mode:'friendship'},'synthetic-B')).candidates.length,1);
    const real=await f.db.prepare('SELECT public_id,summary,active,scope FROM participations WHERE owner=? AND mode=?').bind('synthetic-A','friendship').first();
    assert.equal(real.public_id,original.public_id);assert.equal(JSON.parse(real.summary).alias,'Original Cedar');assert.equal(real.active,1);assert.equal(real.scope,'production');
    await assert.rejects(call('slowmatch_channel_check',{write:false},''),/sign_in_required/);
    const override=createService(f.db,{clock:tick,defaultTestScopeConfiguration,testScopeConfiguration:await configuration([['synthetic-B','other-pilot']])});
    assert.equal((await override('slowmatch_find_candidates',{mode:'friendship'},'synthetic-A')).candidates.length,0,'a peer moved by an explicit override leaves the old default pool');
    const removed=createService(f.db,{clock:tick});
    assert.equal((await removed('slowmatch_channel_check',{write:false},'synthetic-A')).data_scope.access,'not_configured');
    await assert.rejects(removed('slowmatch_read_my_summary',{mode:'friendship'},'synthetic-A'),/controlled_test_scope_not_configured/);
    time=new Date('2030-01-11T00:00:00Z');
    assert.equal((await call('slowmatch_channel_check',{write:false},'synthetic-B')).data_scope.access,'expired');
    await assert.rejects(call('slowmatch_find_candidates',{mode:'dating'},'synthetic-B'),/controlled_test_scope_expired/);
  }finally{await f.dispose();}
});

test('additive scope migration preserves existing production records and channel markers',async()=>{
  const f=await fixture(clock,{throughMigration:4});
  try{
    const original=JSON.stringify(summary('friendship'));
    await f.db.prepare('INSERT INTO participations(owner,mode,public_id,summary,digest,revision,last_summary_version,active,updated_at) VALUES(?,?,?,?,?,4,3,1,?)').bind('synthetic-existing','friendship','a'.repeat(32),original,'b'.repeat(64),'2030-01-01T00:00:00Z').run();
    await f.db.prepare("INSERT INTO planning_sessions(id,pair_key,mode,owner_a,owner_b,public_a,public_b,expires_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)").bind('c'.repeat(32),'d'.repeat(64),'friendship','synthetic-existing','synthetic-peer','a'.repeat(32),'e'.repeat(32),expires_at,'2030-01-01T00:00:00Z','2030-01-01T00:00:00Z').run();
    await f.db.prepare('INSERT INTO channel_checks(owner,marker) VALUES(?,?)').bind('synthetic-existing','slowmatch-channel-v1').run();
    const migration=await readFile(new URL('../drizzle/0005_wandering_zarda.sql',import.meta.url),'utf8');
    assert.equal(/\b(?:DROP|DELETE|UPDATE|INSERT)\b/iu.test(migration),false,'migration changes schema only');
    for(const statement of migration.split('--> statement-breakpoint').map(sql=>sql.trim()).filter(Boolean))await f.db.prepare(statement).run();
    const row=await f.db.prepare('SELECT scope,summary,revision,last_summary_version,active FROM participations WHERE owner=?').bind('synthetic-existing').first();
    assert.deepEqual(row,{scope:'production',summary:original,revision:4,last_summary_version:3,active:1});
    assert.equal((await f.db.prepare('SELECT scope FROM planning_sessions WHERE id=?').bind('c'.repeat(32)).first()).scope,'production');
    const health=await f.call('slowmatch_channel_check',{write:false},'synthetic-existing');assert.equal(health.persisted,true);assert.equal(health.data_scope.kind,'production');
    assert.equal((await f.call('slowmatch_read_my_summary',{mode:'friendship'},'synthetic-existing')).version,4);
  }finally{await f.dispose();}
});
