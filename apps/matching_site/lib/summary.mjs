// Generated JSON schema is copied from the Python core by the source sync check.
import schema from './shareable-profile.schema.json' with { type: 'json' };
export { schema };
export class ServiceError extends Error {
  constructor(code, status=400) { super(code); this.status=status; }
}
export function validate(value, rule=schema) {
  const fail=()=>{ throw new ServiceError('invalid_summary'); };
  if(rule.anyOf) {
    if(!rule.anyOf.some(r=>{try {validate(value,r);return true;} catch{return false;}})) fail();
    return value;
  }
  if(rule.const!==undefined && value!==rule.const) fail();
  if(rule.enum && !rule.enum.includes(value)) fail();
  if(rule.type==='object') {
    if(!value || Array.isArray(value) || typeof value!=='object') fail();
    if(Object.keys(value).some(k=>!Object.hasOwn(rule.properties,k))) fail();
    if((rule.required||[]).some(k=>!Object.hasOwn(value,k))) fail();
    for(const [key,item] of Object.entries(value)) validate(item,rule.properties[key]);
  } else if(rule.type==='array') {
    if(!Array.isArray(value) || value.length<(rule.minItems||0) || value.length>(rule.maxItems??100)) fail();
    if(rule.uniqueItems && new Set(value.map(v=>JSON.stringify(v))).size!==value.length) fail();
    value.forEach(v=>validate(v,rule.items));
  } else if(rule.type==='string') {
    if(typeof value!=='string' || [...value].length<(rule.minLength||0) || [...value].length>(rule.maxLength??2000)) fail();
    if(rule.pattern && !new RegExp(rule.pattern,'u').test(value)) fail();
  } else if(rule.type==='boolean') { if(typeof value!=='boolean') fail(); }
  else if(rule.type==='integer') {if(!Number.isSafeInteger(value) || value<(rule.minimum??0) || value>(rule.maximum??Number.MAX_SAFE_INTEGER)) fail();}
  else fail();
  if(rule===schema) {
    const forbidden=new RegExp(schema['x-slowmatch-label-forbidden-pattern'],'iu');
    for(const label of [value.alias,value.city,...value.areas]) if(forbidden.test(label)) fail();
  }
  return value;
}
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
export function reciprocal(a,b) {
  return a.discoverable && b.discoverable && a.visibility==='participants' && b.visibility==='participants'
    && regionAllows(a,b) && regionAllows(b,a)
    && a.accepted_age_bands.includes(b.age_band) && b.accepted_age_bands.includes(a.age_band)
    && a.accepted_goals.includes(b.relationship_goal) && b.accepted_goals.includes(a.relationship_goal);
}
export function explain(a,b) {
  const shared={}; const differences={};
  for(const key of ['values','life_directions','communication_preferences','interests']) {
    shared[key]=a[key].filter(v=>b[key].includes(v));
    differences[key]={you:a[key].filter(v=>!b[key].includes(v)),them:b[key].filter(v=>!a[key].includes(v))};
  }
  const theirs=new Set([...b.values,...b.life_directions,...b.communication_preferences,...b.interests]);
  const yours=new Set([...a.values,...a.life_directions,...a.communication_preferences,...a.interests]);
  const conflicts=(a.life_directions.includes('build_family') && b.life_directions.includes('childfree')) || (b.life_directions.includes('build_family') && a.life_directions.includes('childfree'));
  return {basis:'shared_summaries_only',hard_conditions:'reciprocal_city_age_goal_pass',shared,differences,
    preferences_met:{you:a.preferences.filter(v=>theirs.has(v)),them:b.preferences.filter(v=>yours.has(v))},
    potential_conflicts:conflicts?['family_direction_needs_discussion']:[],
    unknowns:['identity_not_verified','self_reports_not_independently_verified','private_profiles_not_compared'],
    caveat:'Preliminary discussion aid, not a compatibility score or safety guarantee. / 初步交流参考，不是兼容评分或安全保证。'};
}
