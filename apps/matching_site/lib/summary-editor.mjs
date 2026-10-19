import {validate} from './summary.mjs';
export const editorMessages={
title:['Create your shared summary','填写共享摘要'],body:['Choose only what other eligible participants may see. Private conversations and profile statements are never copied into this form. No choices are preselected.','仅填写允许其他符合条件的参与者看到的内容。私人会话与档案陈述不会复制到此表单，也不预设你的答案。'],preview:['Preview this summary','预览这份摘要'],optional:['Optional','可选'],required:['Required','必填'],regions:['Cities I am willing to meet in (one per line; blank means my city only)','愿意见面的城市（每行一个；留空表示仅限本人城市）'],geo:['Both people must accept the other’s city. Use matching city names; this is city-level matching, not GPS or a distance measurement.','双方必须接受对方所在城市，请使用一致的城市名称。这是城市级匹配，不是 GPS 或距离测量。'],enable:['Allow eligible participants to discover this summary after I publish it','发布后允许符合条件的参与者发现这份摘要'],expiry:['Summary expiry date (YYYY-MM-DD, UTC)','摘要到期日期（YYYY-MM-DD，UTC）'],invalid:['Complete required choices and review city names, expiry and selection limits.','请补齐必填选项，并检查城市名称、到期日期及选择数量限制。'],accepted_goals:['Relationship goals I accept','可接受的关系目标'],accepted_age_bands:['Age groups I accept','可接受的年龄段'],age_band:['My age group','本人年龄段'],alias:['Display name','展示昵称'],city:['My city','本人城市'],relationship_goal:['My relationship goal','本人的关系目标'],friendship_intent:['My friendship intention','本人的交友意向'],accepted_friendship_intents:['Friendship intentions I accept','可接受的交友意向'],interaction_frequency:['My preferred frequency','本人偏好的相处频率'],accepted_frequencies:['Frequencies I accept','可接受的相处频率'],life_directions:['Life directions','人生方向'],communication_preferences:['Communication preferences','沟通偏好'],values:['Values','价值观'],interests:['Interests','兴趣'],preferences:['Preferences','偏好'],activity_styles:['Activity styles','活动形式'],boundaries:['Boundaries','边界']};
export const editorText=(locale,key)=>editorMessages[key]?.[locale==='zh-CN'?1:0]||key;
// Construct a separate object from explicit allowlisted fields; never take a
// private-profile input or spread an imported object into the outbound payload.
export function buildSummary(fields,properties,{mode,id,version,expiry,discoverable}){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(expiry)||new Date(expiry+'T23:59:59Z').toISOString().slice(0,10)!==expiry)throw Error('invalid_expiry');
 const summary={schema_version:'2.0',mode,summary_id:id,version,expires_at:new Date(expiry+'T23:59:59Z').toISOString(),visibility:'participants',discoverable};
 for(const [name,definition] of Object.entries(properties)){
  if(['schema_version','mode','summary_id','version','expires_at','visibility','discoverable'].includes(name))continue;
  summary[name]=name==='areas'?(fields[name]||'').split('\n').map(s=>s.trim()).filter(Boolean):definition.type==='array'?(fields[name]||[]):fields[name]||'';
 }
 return validate(summary);
}
