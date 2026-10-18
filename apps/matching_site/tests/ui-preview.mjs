// Local browser QA only. This file is never imported by the app or Worker.
// Synthetic identities exercise the real D1 service, not independent ChatGPT accounts.
import {createServer,request as forward} from 'node:http';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fixture,dating,friendship} from './helpers.mjs';
import {digest} from '../lib/summary.mjs';
if(process.env.SLOWMATCH_UI_QA!=='1'||!process.argv[2])throw Error('Explicit local QA flag and artifact directory required');
const directory=resolve(process.argv[2]);await mkdir(directory,{recursive:true});
const f=await fixture();
const owner='synthetic-ui-owner';
const at=days=>new Date(Date.now()+days*86400000).toISOString();
const calls=[];
for(const mode of ['dating','friendship']){
 const make=mode==='dating'?dating:friendship;
 await f.publish(owner,make({alias:'Cedar',interests:['reading','art','outdoors'],values:['honesty','curiosity']}));
 for(const [index,alias] of ['Rowan','Lumi','River'].entries())await f.publish('synthetic-ui-peer-'+index,make({summary_id:String(index+2).repeat(32),alias,interests:index===0?['reading','art']:index===1?['reading','outdoors']:['reading','music'],values:['honesty','curiosity'],areas:['Toronto','North York']}));
 const peers=await f.call('slowmatch_find_candidates',{mode},owner);
 const peer=peers.candidates.find(p=>p.summary.alias==='Rowan');
 const created=await f.call('slowmatch_planning_create',{mode,candidate_public_id:peer.public_id,expires_at:at(8),explicit_invitation:true},owner);
 const scope={mode,planning_id:created.planning_id};
 const prefs={schema_version:'1.0',mode,areas:['Toronto'],availability:[{start_at:at(2),end_at:at(4)}],budget:{currency:'CAD',max_per_person_minor:2500},duration_minutes:120,interests:['reading','art'],environment:['public_place','easy_exit'],arrangement_needs:[],expires_at:at(7)};
 for(const who of [owner,'synthetic-ui-peer-0']){const current=await f.call('slowmatch_planning_read',scope,who);await f.call('slowmatch_planning_preferences',{...scope,preferences:prefs,approved_digest:await digest(prefs),approved:true,expected_version:current.version},who);}
 const context=await f.call('slowmatch_planning_context',scope,owner);
 const option=(option_id,place_name,activity_type)=>({option_id,activity_type,place_name,address_or_area:'Toronto',planning_area:'Toronto',source_open_window:null,source_admission:null,source_event_at:null,source_urls:['https://example.org/qa-venue'],checked_at:at(-1),verification:'not_verified',verified_facts:[],unknowns:['all_details_unverified','booking_not_made','price_may_change'],start_at:at(3),duration_minutes:60,estimated_budget_minor:1500,currency:'CAD',sequence:['meet_public',activity_type==='museum'?'visit_exhibit':'coffee','leave_independently'],shared_interest_reasons:['reading'],conversation_starters:['shared_hobby','recent_learning'],arrival_exit:'independent_arrival_easy_exit',fallback:'reschedule',booking_status:'not_booked'});
 const plan={budget_basis:'shared_budget_ceiling_not_verified_price',requirements:{environment:['easy_exit','public_place'],arrangement_needs:[],status:'confirm_venue_suitability_before_agreeing'},schema_version:'1.0',mode,context_digest:context.context_digest,version:1,expires_at:at(6),options:[option('a','Synthetic Gallery','museum'),option('b','Synthetic Reading Cafe','cafe_walk')]};
 let current=await f.call('slowmatch_planning_read',scope,owner);
 await f.call('slowmatch_planning_propose',{...scope,plan,approved_digest:await digest(plan),approved:true,expected_version:current.version},owner);
 current=await f.call('slowmatch_planning_read',scope,'synthetic-ui-peer-0');
 await f.call('slowmatch_planning_confirm',{...scope,plan_version:current.plan_version,plan_digest:current.plan_digest,option_id:'a',expected_version:current.version},'synthetic-ui-peer-0');
 await writeFile(resolve(directory,mode+'-summary.json'),JSON.stringify(make({version:2,alias:'Cedar',interests:['reading','art'],values:['honesty','curiosity']})));
 await writeFile(resolve(directory,mode+'-preferences.json'),JSON.stringify(prefs));
 await writeFile(resolve(directory,mode+'-plan.json'),JSON.stringify(plan));
}
await writeFile(resolve(directory,'invalid-summary.json'),JSON.stringify({raw_chat:'SYNTHETIC_REJECTED_PRIVATE_FIELD'}));
const server=createServer(async(req,res)=>{
 if(req.headers.host!=='127.0.0.1:5174'){res.writeHead(403);res.end();return;}
 if(req.url==='/__qa/calls'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(calls));return;}
 if(req.url==='/api/matching'){
  if(req.method!=='POST'||req.headers.origin!=='http://127.0.0.1:5174'||!req.headers.cookie?.split(';').some(v=>v.trim()==='__sites_local_auth=1')){res.writeHead(403);res.end(JSON.stringify({error:'sign_in_required'}));return;}
  try{let body='';for await(const part of req){body+=part;if(body.length>32768)throw Error('invalid_arguments');}const input=JSON.parse(body);calls.push({name:input.name,mode:input.arguments?.mode||null});const result=await f.call(input.name,input.arguments,owner);res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(result));}
  catch(error){res.writeHead(400,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify({error:error.message}));}return;
 }
 if(!req.url?.startsWith('/')||req.url.startsWith('//')){res.writeHead(400);res.end();return;}
 const headers={...req.headers,host:'127.0.0.1:5173'};
 if(headers.origin==='http://127.0.0.1:5174')headers.origin='http://127.0.0.1:5173';
 const proxy=forward({host:'127.0.0.1',port:5173,path:req.url,method:req.method,headers},upstream=>{res.writeHead(upstream.statusCode||502,upstream.headers);upstream.pipe(res);});
 proxy.on('error',()=>{res.writeHead(502);res.end('Local preview unavailable');});req.pipe(proxy);
});
server.listen(5174,'127.0.0.1',()=>console.log('Synthetic UI QA: http://127.0.0.1:5174 — no independent accounts or hosted data'));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(async()=>{await f.dispose();process.exit(0);}));
