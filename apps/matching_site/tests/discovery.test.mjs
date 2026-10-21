import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture,dating} from './helpers.mjs';
import {discoveryFilter,normalizePlace} from '../lib/discovery.mjs';
import {validate} from '../lib/summary.mjs';
import {tools} from '../lib/tools.mjs';

test('coarse aliases, strict filter allowlist and optional tool contract',()=>{
 assert.equal(normalizePlace(' 多倫多 '),'toronto');
 assert.equal(normalizePlace(' Montréal '),'montreal');
 const rule=tools.find(t=>t.name==='slowmatch_find_candidates').inputSchema;
 validate({mode:'dating'},rule);validate({mode:'dating',filters:{regions:['Toronto'],age_bands:['25-34'],interests:['reading']}},rule);
 for(const bad of [{latitude:43}, {regions:['123 Main St']}, {age_bands:['25-29']},{interests:['secret']},{regions:['Toronto','Toronto']},{regions:'Toronto'}]){
  // Street-like digits cannot be interpreted as a coarse supported label.
  assert.throws(()=>discoveryFilter(bad));
 }
});
test('server filters precede twelve-result cutoff and preserve reciprocal restrictions',async()=>{
 const f=await fixture();
 try{
  await f.publish('synthetic-viewer',dating({areas:['Toronto','Ottawa'],accepted_age_bands:['25-34','35-44']}));
  for(let i=0;i<16;i++)await f.publish('synthetic-'+i,dating({summary_id:i.toString(16).padStart(32,'0'),alias:'Synthetic',city:i===15?'多伦多':'Ottawa',areas:['Toronto'],age_band:i===15?'35-44':'25-34',interests:i===15?['music']:['reading']}));
  const all=await f.call('slowmatch_find_candidates',{mode:'dating'},'synthetic-viewer');assert.equal(all.candidates.length,12);
  const found=await f.call('slowmatch_find_candidates',{mode:'dating',filters:{regions:['Toronto'],age_bands:['35-44'],interests:['music']}},'synthetic-viewer');
  assert.equal(found.candidates.length,1);assert.equal(found.candidates[0].summary.city,'多伦多');assert.equal(found.ai_review,'not_run');
  const none=await f.call('slowmatch_find_candidates',{mode:'dating',filters:{regions:['Toronto'],age_bands:['65+']}},'synthetic-viewer');assert.equal(none.candidates.length,0);
  await assert.rejects(f.call('slowmatch_find_candidates',{mode:'dating',filters:{private_profile:'x'}},'synthetic-viewer'),/invalid_discovery_filter/);
 }finally{await f.dispose();}
});
