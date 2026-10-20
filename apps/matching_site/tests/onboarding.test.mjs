import test from 'node:test';
import assert from 'node:assert/strict';
import {onboardingMessages} from '../lib/onboarding.mjs';
import {interviewMessages} from '../lib/interview.mjs';
import {editorMessages,buildSummary} from '../lib/summary-editor.mjs';
import {schema,reciprocal} from '../lib/summary.mjs';
import {fixture,dating,friendship} from './helpers.mjs';

test('onboarding and sharing translations are complete and separate',()=>{
 for(const [key,pair] of Object.entries({...onboardingMessages,...editorMessages,...interviewMessages})){
  assert.equal(pair.length,2,key);assert.ok(pair.every(v=>typeof v==='string'&&v.trim()),key);
  assert.doesNotMatch(pair[0],/[\u4e00-\u9fff]/,key);assert.match(pair[1],/[\u4e00-\u9fff]/,key);
 }
});
test('summary editor copies explicit fields only, leaves omitted choices empty and rejects missing required answers',()=>{
 const fields=dating({private_analysis:'SYNTHETIC_PRIVATE',areas:''});
 const output=buildSummary(fields,schema.$defs.DatingSummary.properties,{mode:'dating',id:'b'.repeat(32),version:2,expiry:'2027-01-01',discoverable:true});
 assert.equal(output.version,2);assert.deepEqual(output.areas,[]);assert.ok(!('private_analysis' in output));
 for(const expiry of ['2027-02-30','invalid','2027-13-01'])assert.throws(()=>buildSummary(fields,schema.$defs.DatingSummary.properties,{mode:'dating',id:'b'.repeat(32),version:2,expiry,discoverable:true}));
 assert.throws(()=>buildSummary({},schema.$defs.DatingSummary.properties,{mode:'dating',id:'b'.repeat(32),version:1,expiry:'2027-01-01',discoverable:true}));
});
test('geographic acceptance requires reciprocal cities, mode and visibility in real local D1',async()=>{
 const f=await fixture();try{
  await f.publish('synthetic-toronto',dating({city:'Toronto',areas:['Toronto','Ottawa']}));
  await f.publish('synthetic-ottawa-yes',dating({city:'Ottawa',areas:['Toronto','Ottawa']}));
  await f.publish('synthetic-ottawa-no',dating({city:'Ottawa',areas:[]}));
  await f.publish('synthetic-vancouver',dating({city:'Vancouver',areas:['Toronto']}));
  await f.publish('synthetic-private',dating({discoverable:false}));
  await f.publish('synthetic-friend',friendship());
  const result=await f.call('slowmatch_find_candidates',{mode:'dating'},'synthetic-toronto');
  assert.equal(result.candidates.length,1);assert.equal(result.candidates[0].summary.city,'Ottawa');
  assert.equal(reciprocal(dating({city:'Ｔｏｒｏｎｔｏ'}),dating({city:'toronto'})),true);
  assert.equal('distance_km' in result.candidates[0],false);
 }finally{await f.dispose();}
});
