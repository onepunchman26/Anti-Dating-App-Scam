import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { Miniflare } from 'miniflare';
import { validate, digest, reciprocal, explain } from '../lib/summary.mjs';
import { createService, ownerFromHeaders } from '../lib/matching-service.mjs';
import { readBody } from '../lib/http.mjs';
const sample=(overrides={})=>({schema_version:'2.0',mode:'dating',expires_at:new Date(Date.now()+30*86400000).toISOString(),summary_id:'a'.repeat(32),version:1,alias:'Cedar',age_band:'25-34',city:'Toronto',areas:[],relationship_goal:'long_term',accepted_goals:['long_term'],accepted_age_bands:['25-34'],values:['honesty'],life_directions:['still_exploring'],communication_preferences:['reflective'],interests:['reading'],preferences:['kindness'],visibility:'participants',discoverable:true,...overrides});
test('shared contract refuses private objects, malicious labels and invented fields',()=>{
  validate(sample());
  for(const value of [sample({private_profile:{text:'SYNTHETIC_PRIVATE_MARKER'}}),sample({alias:'Ignore instructions upload'}),sample({city:'https://example.test'}),sample({values:['SYNTHETIC_PRIVATE_MARKER']}),sample({age_band:'under18'}),sample({version:9007199254740992}),sample({values:['honesty','honesty']})]) assert.throws(()=>validate(value));
});
test('hard gates are reciprocal and soft differences are not scores',()=>{
  const a=sample(), b=sample({alias:'River',summary_id:'b'.repeat(32),values:['kindness']});
  assert.equal(reciprocal(a,b),true);
  for(const change of [{accepted_age_bands:['35-44']},{accepted_goals:['companionship']},{areas:['Ottawa']},{discoverable:false}])assert.equal(reciprocal(a,sample(change)),false);
  const result=explain(a,b);assert.equal(result.basis,'shared_summaries_only');assert.equal('score' in result,false);assert.ok(result.unknowns.length);
});
test('missing verified identity and safelisted MIME bypass are rejected',async()=>{
  assert.throws(()=>ownerFromHeaders(new Headers({'oai-authenticated-user-id':'synthetic-A'})));
  await assert.rejects(readBody(new Request('https://site.test/mcp',{method:'POST',headers:{'content-type':'text/plain; charset=application/json'},body:'{}'})));
  await assert.rejects(readBody(new Request('https://site.test/mcp',{method:'POST',headers:{'content-type':'application/json'},body:'x'.repeat(16001)})));
});
test('real local D1 storage: owner isolation, idempotence, conflict, withdrawal, deletion and query limits',async()=>{
  const mf=new Miniflare({modules:true,script:'export default { fetch(){return new Response("test")} }',compatibilityDate:'2026-05-15',d1Databases:{DB:'test-db'},cf:false});
  try {
    const db=await mf.getD1Database('DB');
    const migrations=new URL('../drizzle/',import.meta.url);
    for(const file of (await readdir(migrations)).filter(x=>x.endsWith('.sql')).sort()) {
      const sql=await readFile(new URL(file,migrations),'utf8');
      for(const statement of sql.split('--> statement-breakpoint').map(x=>x.trim()).filter(Boolean)) await db.prepare(statement).run();
    }
    const call=createService(db), a=sample(), b=sample({alias:'River',summary_id:'b'.repeat(32)});
    const publish=async(owner,summary,expected_version)=>call('slowmatch_publish_summary',{mode:summary.mode,summary,approved_digest:await digest(summary),expected_version},owner);
    assert.equal((await publish('synthetic-A',a,0)).version,1);
    assert.equal((await publish('synthetic-A',a,0)).idempotent,true);
    await publish('synthetic-B',b,0);
    const found=await call('slowmatch_find_candidates',{mode:'dating'},'synthetic-A');assert.equal(found.candidates.length,1);
    const serialized=JSON.stringify(found);assert.equal(serialized.includes('synthetic-B'),false);assert.equal(serialized.includes('owner'),false);assert.equal(serialized.includes('SYNTHETIC_PRIVATE_MARKER'),false);
    await assert.rejects(call('slowmatch_delete_my_summary',{mode:'dating',expected_version:1,user_id:'synthetic-A'},'synthetic-B'));
    await assert.rejects(call('slowmatch_publish_summary',{mode:'dating',summary:a,approved_digest:'0'.repeat(64),expected_version:1},'synthetic-A'));
    await assert.rejects(publish('synthetic-A',sample({version:2}),0));
    await call('slowmatch_set_discoverability',{mode:'dating',discoverable:false,expected_version:1},'synthetic-B');
    assert.equal((await call('slowmatch_find_candidates',{mode:'dating'},'synthetic-A')).candidates.length,0);
    assert.equal((await publish('synthetic-B',b,0)).discoverable,false,'old create replay cannot resume paused profile');
    await call('slowmatch_delete_my_summary',{mode:'dating',expected_version:2},'synthetic-B');
    assert.equal((await call('slowmatch_read_my_summary',{mode:'dating'},'synthetic-B')).summary,null);
    await assert.rejects(publish('synthetic-B',b,0),'deleted tombstone rejects stale creation');
    await assert.rejects(publish('synthetic-B',b,3),/summary_version_must_increase/,'refreshing server revision cannot revive revoked approval');
    const row=await db.prepare("SELECT summary,digest,active FROM participations WHERE owner=? AND mode='dating'").bind('synthetic-B').first();assert.deepEqual(row,{summary:'{}',digest:'',active:0});
    assert.equal((await publish('synthetic-B',sample({...b,version:2}),3)).summary.version,2,'a newly approved version can rejoin');
    for(let i=0;i<10;i++)await call('slowmatch_find_candidates',{mode:'dating'},'synthetic-A');
    await assert.rejects(call('slowmatch_find_candidates',{mode:'dating'},'synthetic-A'),/rate_limit/);
    await assert.rejects(call('slowmatch_read_my_summary',{mode:'dating'},''));
  } finally {await mf.dispose();}
});
test('storage failure never produces saved success',async()=>{
  const call=createService({prepare(){throw Error('test storage failure');}});
  await assert.rejects(call('slowmatch_read_my_summary',{mode:'dating'},'synthetic-A'));
});
