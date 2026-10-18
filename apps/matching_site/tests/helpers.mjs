import {readFile,readdir} from 'node:fs/promises';
import {Miniflare} from 'miniflare';
import {createService} from '../lib/matching-service.mjs';
import {digest} from '../lib/summary.mjs';

export const dating=(changes={})=>({schema_version:'2.0',mode:'dating',expires_at:new Date(Date.now()+30*86400000).toISOString(),summary_id:'a'.repeat(32),version:1,alias:'Cedar',age_band:'25-34',city:'Toronto',areas:[],relationship_goal:'long_term',accepted_goals:['long_term'],accepted_age_bands:['25-34'],values:['honesty'],life_directions:['still_exploring'],communication_preferences:['reflective'],interests:['reading'],preferences:['kindness'],visibility:'participants',discoverable:true,...changes});
export const friendship=(changes={})=>{
  const {relationship_goal,accepted_goals,life_directions,...common}=dating();
  void relationship_goal;void accepted_goals;void life_directions;
  return {...common,mode:'friendship',friendship_intent:'activity_companions',accepted_friendship_intents:['activity_companions'],activity_styles:['quiet'],interaction_frequency:'flexible',accepted_frequencies:['flexible'],boundaries:['platonic_only'],...changes};
};
export async function fixture(clock=()=>new Date(),{throughMigration=Infinity}={}) {
  const mf=new Miniflare({modules:true,script:'export default {fetch(){return new Response("synthetic")}}',compatibilityDate:'2026-05-15',d1Databases:{DB:'test-db'},cf:false});
  const db=await mf.getD1Database('DB');
  const migrations=new URL('../drizzle/',import.meta.url);
  for(const file of (await readdir(migrations)).filter(x=>x.endsWith('.sql')&&Number(x.slice(0,4))<=throughMigration).sort()) {
    for(const sql of (await readFile(new URL(file,migrations),'utf8')).split('--> statement-breakpoint').map(x=>x.trim()).filter(Boolean)) await db.prepare(sql).run();
  }
  const call=createService(db,{clock});
  const publish=async(owner,summary,expected_version=0)=>call('slowmatch_publish_summary',{mode:summary.mode,summary,approved_digest:await digest(summary),expected_version},owner);
  return {db,call,publish,dispose:()=>mf.dispose()};
}
