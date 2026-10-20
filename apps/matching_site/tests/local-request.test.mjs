import {test} from 'node:test';
import assert from 'node:assert/strict';
import {requestLocal} from '../lib/local-request.mjs';

test('blocked local-network request times out once and can be retried',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});let calls=0;
 const waiting=(_url,{signal})=>{calls++;return new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(Error('aborted')),{once:true}));};
 const failed=assert.rejects(requestLocal('synthetic','status',{},waiting),/unreachable/);
 t.mock.timers.tick(15000);await failed;assert.equal(calls,1);
 const value=await requestLocal('synthetic','status',{},async(url,options)=>{
  assert.equal(url,'http://127.0.0.1:8911/v1');assert.equal(options.credentials,'omit');
  assert.equal(options.headers.Authorization,'Bearer synthetic');
  return {ok:true,json:async()=>({ok:true,result:{connected:true}})};
 });assert.equal(value.connected,true);
});
test('AI request has a bounded longer wait and is never automatically resubmitted',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});let calls=0,signal;
 const failed=assert.rejects(requestLocal('synthetic','send',{},async(_url,options)=>{
  calls++;signal=options.signal;return new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(Error('aborted')),{once:true}));
 }),/unreachable/);
 t.mock.timers.tick(15000);assert.equal(signal.aborted,false);
 t.mock.timers.tick(225000);await failed;assert.equal(calls,1);
});
test('server consent/revision errors are preserved without retries',async()=>{
 await assert.rejects(requestLocal('synthetic','send',{},async()=>({ok:false,json:async()=>({error:'revision_conflict'})})),/revision_conflict/);
});
