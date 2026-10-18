// Generated JSON schema is copied from the Python core by the source sync check.
import schema from './shareable-profile.schema.json' with { type: 'json' };
import legacySchema from './shareable-profile-v1.schema.json' with { type: 'json' };
export { schema };
export class ServiceError extends Error {
  constructor(code, status=400) { super(code); this.status=status; }
}
/** @param {*} value @param {object} [rule] @param {object} [root] */
export function validate(value, rule=schema, root=rule) {
  const fail=()=>{ throw new ServiceError('invalid_summary'); };
  if(!rule || typeof rule!=='object') fail();
  if(rule.$ref) {
    if(!rule.$ref.startsWith('#/')) fail();
    const target=rule.$ref.slice(2).split('/').reduce((node,key)=>node?.[key.replaceAll('~1','/').replaceAll('~0','~')],root);
    if(!target) fail();
    validate(value,target,root);
  }
  if(rule.anyOf) {
    if(!rule.anyOf.some(r=>{try {validate(value,r,root);return true;} catch{return false;}})) fail();
  }
  if(rule.oneOf && rule.oneOf.filter(r=>{try {validate(value,r,root);return true;} catch{return false;}}).length!==1) fail();
  if(rule.allOf) for(const branch of rule.allOf) validate(value,branch,root);
  if(rule.const!==undefined && value!==rule.const) fail();
  if(rule.enum && !rule.enum.includes(value)) fail();
  if(rule.type==='object') {
    if(!value || Array.isArray(value) || typeof value!=='object') fail();
    if(Object.keys(value).some(k=>!Object.hasOwn(rule.properties||{},k))) fail();
    if((rule.required||[]).some(k=>!Object.hasOwn(value,k))) fail();
    for(const [key,item] of Object.entries(value)) validate(item,rule.properties[key],root);
  } else if(rule.type==='array') {
    if(!Array.isArray(value) || value.length<(rule.minItems||0) || value.length>(rule.maxItems??100)) fail();
    if(rule.uniqueItems && new Set(value.map(v=>JSON.stringify(v))).size!==value.length) fail();
    value.forEach(v=>validate(v,rule.items,root));
  } else if(rule.type==='string') {
    if(typeof value!=='string' || [...value].length<(rule.minLength||0) || [...value].length>(rule.maxLength??2000)) fail();
    if(rule.pattern && !new RegExp(rule.pattern,'u').test(value)) fail();
    if(rule.format==='date-time' && (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/u.test(value) || !Number.isFinite(Date.parse(value)))) fail();
    if(rule.format==='uri') {try {const url=new URL(value);if(!['https:','http:'].includes(url.protocol)||url.username||url.password) fail();}catch{fail();}}
  } else if(rule.type==='boolean') { if(typeof value!=='boolean') fail(); }
  else if(rule.type==='integer') {if(!Number.isSafeInteger(value) || value<(rule.minimum??0) || value>(rule.maximum??Number.MAX_SAFE_INTEGER)) fail();}
  else if(rule.type==='number') {if(typeof value!=='number'||!Number.isFinite(value)||value<(rule.minimum??-Infinity)||value>(rule.maximum??Infinity)) fail();}
  else if(rule.type==='null') {if(value!==null) fail();}
  else if(rule.type || !(rule.$ref||rule.anyOf||rule.oneOf||rule.allOf||Object.hasOwn(rule,'const')||rule.enum)) fail();
  if(rule===root && root['x-slowmatch-label-forbidden-pattern']) {
    const forbidden=new RegExp(root['x-slowmatch-label-forbidden-pattern']||legacySchema['x-slowmatch-label-forbidden-pattern'],'iu');
    const labels=[value.alias,value.city,...(value.areas||[]),...(value.options||[]).flatMap(option=>[option.place_name,option.address_or_area,option.planning_area])].filter(v=>typeof v==='string');
    for(const label of labels) if(forbidden.test(label)) fail();
    if(root===schema) summaryExpiry(value.expires_at);
  }
  return value;
}
export const validateStored=value=>validate(value,value?.schema_version==='1.0'?legacySchema:schema);
export const summaryMode=value=>value.schema_version==='1.0'?'dating':value.mode;
export function summaryExpiry(value) {
  const parts=typeof value==='string'?/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(?:Z|\+00:00)$/u.exec(value):null;
  if(!parts||!Number.isFinite(Date.parse(value)))throw new ServiceError('utc_timestamp_required');
  const [year,month,day,hour,minute,second]=parts.slice(1).map(Number);
  const days=[31,year%4===0&&(year%100!==0||year%400===0)?29:28,31,30,31,30,31,31,30,31,30,31];
  if(year<1||month<1||month>12||day<1||day>days[month-1]||hour>23||minute>59||second>59)throw new ServiceError('utc_timestamp_required');
  return Date.parse(value);
}
export const summaryExpired=(value,at=new Date())=>value.schema_version==='2.0'&&summaryExpiry(value.expires_at)<=at.getTime();
export function canonical(value) {
  if(Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
  if(value && typeof value==='object') return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  return JSON.stringify(value);
}
export async function digest(value) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(value))))].map(b=>b.toString(16).padStart(2,'0')).join('');
}
const normalize=v=>v.normalize('NFKC').trim().toLocaleLowerCase('en');
const regionAllows=(a,b)=>(a.areas.length?a.areas:[a.city]).map(normalize).includes(normalize(b.city));
export function reciprocal(a,b,at=new Date()) {
  const mode=summaryMode(a);
  const common=mode===summaryMode(b) && !summaryExpired(a,at) && !summaryExpired(b,at) && a.discoverable && b.discoverable && a.visibility==='participants' && b.visibility==='participants'
    && regionAllows(a,b) && regionAllows(b,a)
    && a.accepted_age_bands.includes(b.age_band) && b.accepted_age_bands.includes(a.age_band);
  if(!common) return false;
  if(mode==='friendship') return a.accepted_friendship_intents.includes(b.friendship_intent) && b.accepted_friendship_intents.includes(a.friendship_intent)
    && a.accepted_frequencies.includes(b.interaction_frequency) && b.accepted_frequencies.includes(a.interaction_frequency)
    && a.interests.some(v=>b.interests.includes(v)) && a.activity_styles.some(v=>b.activity_styles.includes(v));
  return mode==='dating' && a.accepted_goals.includes(b.relationship_goal) && b.accepted_goals.includes(a.relationship_goal);
}
export function explain(a,b) {
  const shared={}; const differences={};
  const mode=summaryMode(a);
  const keys=mode==='friendship'?['values','communication_preferences','interests','activity_styles','boundaries']:['values','life_directions','communication_preferences','interests'];
  for(const key of keys) {
    shared[key]=a[key].filter(v=>b[key].includes(v));
    differences[key]={you:a[key].filter(v=>!b[key].includes(v)),them:b[key].filter(v=>!a[key].includes(v))};
  }
  const theirs=new Set([...b.values,...(b.life_directions||[]),...b.communication_preferences,...b.interests]);
  const yours=new Set([...a.values,...(a.life_directions||[]),...a.communication_preferences,...a.interests]);
  const conflicts=mode==='dating' && ((a.life_directions.includes('build_family') && b.life_directions.includes('childfree')) || (b.life_directions.includes('build_family') && a.life_directions.includes('childfree')));
  return {basis:'shared_summaries_only',mode,hard_conditions:mode==='friendship'?'reciprocal_city_age_intent_frequency_activity_pass':'reciprocal_city_age_goal_pass',shared,differences,
    preferences_met:{you:a.preferences.filter(v=>theirs.has(v)),them:b.preferences.filter(v=>yours.has(v))},
    potential_conflicts:conflicts?['family_direction_needs_discussion']:[],
    unknowns:['identity_not_verified','self_reports_not_independently_verified','private_profiles_not_compared'],
    caveat:'Preliminary discussion aid, not a compatibility score or safety guarantee. / 初步交流参考，不是兼容评分或安全保证。'};
}
