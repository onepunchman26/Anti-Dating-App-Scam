// Coarse names only. No GPS, address lookup, inferred residence or radius claims.
const aliases={多伦多:'toronto',多倫多:'toronto',温哥华:'vancouver',溫哥華:'vancouver',蒙特利尔:'montreal',蒙特利爾:'montreal',渥太华:'ottawa',渥太華:'ottawa',纽约:'new york',紐約:'new york',北京:'beijing',上海:'shanghai',深圳:'shenzhen',广州:'guangzhou',廣州:'guangzhou',伦敦:'london',倫敦:'london',香港:'hong kong'};
export function normalizePlace(value){const key=value.normalize('NFKC').normalize('NFD').replace(/\p{M}/gu,'').trim().toLocaleLowerCase('en').replace(/\s+/g,' ');return aliases[key]||key;}
export function discoveryFilter(value={}){
 if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!['regions','age_bands','interests'].includes(k)))throw Error('invalid_discovery_filter');
 const result={regions:[],age_bands:[],interests:[]};
 const allowed={age_bands:['18-24','25-34','35-44','45-54','55-64','65+'],interests:['reading','music','art','outdoors','cooking','games','travel','sport','learning','volunteering']};
 for(const key of Object.keys(result)){const list=value[key]??[];if(!Array.isArray(list)||list.length>(key==='regions'?5:key==='interests'?8:6)||new Set(list).size!==list.length||list.some(x=>typeof x!=='string'||x.length<2||x.length>60||(!allowed[key]&&!/^[A-Za-z\u00C0-\u024F\u3400-\u9FFF][A-Za-z\u00C0-\u024F\u3400-\u9FFF ’.,-]*$/.test(x))||(allowed[key]&&!allowed[key].includes(x))))throw Error('invalid_discovery_filter');result[key]=list;}
 return result;
}
export function acceptsFilter(summary,filter){return (!filter.regions.length||filter.regions.map(normalizePlace).includes(normalizePlace(summary.city)))&&(!filter.age_bands.length||filter.age_bands.includes(summary.age_band))&&(!filter.interests.length||filter.interests.some(v=>summary.interests.includes(v)));}
export const discoveryMessages={
 title:['Choose area, age and interests','选择地区、年龄和兴趣'],
 region:['Where should they be based? One city/area per line','希望对方在哪个地区？每行一个城市／地区'],
 locationHint:['Exact coarse city/area names, with selected Chinese/English aliases. These filters run on the server before the result limit. This is not a kilometre radius or GPS search. Your reciprocal published limits still apply.','按粗略城市／地区名称筛选，支持部分中英文别名。筛选在服务端结果截断前执行，不是公里半径或GPS搜索，仍遵守双方发布的条件。'],
 ages:['Acceptable age groups (blank: use my published limits)','接受的年龄段（不选则使用已发布条件）'],
 interests:['Interests to explore together (optional)','希望一起探索的兴趣（可选）'],
 rule:['Location and mutual conditions checked · AI analysis not yet run','地区及双方条件已核对 · 尚未运行AI分析'],
 ai:['Prepare private AI review','准备私人AI分析'],
 bundle:['Copy approved candidate information','复制获准共享的候选资料'],
 bundleHint:['Paste this bundle into “Private candidate review” on your local conversation page. Only shared summaries are copied. There, you choose whether to include your own confirmed private statements. Nothing is returned to the Site.','将资料粘贴到本机对话页面的“私人候选分析”。这里只复制获准共享的摘要；在本机另行选择是否加入本人的已确认私人陈述。分析不回传网站。'],
 open:['Open private conversation','打开本机私人对话'],copied:['Copied. Continue on your local page.','已复制，请到本机页面继续。'],
 empty:['No eligible people in this search. A private pilot with only one account cannot produce a real match. Change your search or invite a person you know; no sample person is presented as a real user.','本次查询没有符合条件的人。仅一位账号的私有测试无法产生真实匹配。可以修改查询或邀请认识的人；不会用示例人物冒充真实用户。'],
 prompt:['AI can compare approved information and identify useful questions. It cannot know another person’s private profile or verify their honesty.','AI可比较获准资料并提出需要了解的问题，不能读取对方私人档案或证明其诚实程度。'],
};
export const discoveryText=(locale,key)=>discoveryMessages[key]?.[locale==='zh-CN'?1:0]||key;
