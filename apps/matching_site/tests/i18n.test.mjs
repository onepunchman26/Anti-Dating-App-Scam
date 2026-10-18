import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {messages,text,resolveLanguage,errorKey} from '../lib/i18n.mjs';
import {labels,label} from '../lib/labels.mjs';
test('all UI messages and enum labels have complete separate translations and matching placeholders',()=>{
 for(const [key,pair] of Object.entries({...messages,...labels})){
  assert.equal(pair.length,2,key);assert.ok(pair.every(v=>typeof v==='string'&&v.trim()),key);
  assert.doesNotMatch(pair[0],/[\u4e00-\u9fff]/,key);assert.match(pair[1],/[\u4e00-\u9fff]/,key);
  assert.deepEqual(pair[0].match(/\{\w+\}/g)||[],pair[1].match(/\{\w+\}/g)||[],key);
 }
 assert.equal(text('zh-CN','resultCount',{count:3}),'显示 3 份资料');
 assert.equal(label('unknown_internal_code','zh-CN'),'未分享');
 assert.equal(errorKey('raw server details are private'),'errorGeneric');
});
test('saved preference wins; supported browser preference honors quality; invalid preferences fall back safely',()=>{
 assert.equal(resolveLanguage('slowmatch-language=zh-CN','en-US'),'zh-CN');
 assert.equal(resolveLanguage('slowmatch-language=en','zh-CN'),'en');
 assert.equal(resolveLanguage('slowmatch-language=bad','fr;q=1,zh;q=0.8,en;q=0.5'),'zh-CN');
 assert.equal(resolveLanguage('','zh;q=0,en;q=0.4'),'en');
 assert.equal(resolveLanguage('','fr,zh-Hans;q=0.7'),'zh-CN');
 assert.equal(resolveLanguage('','de-DE'),'en');
});
test('components reference existing resource keys and contain no mixed-language copy',async()=>{
 for(const file of (await readdir(new URL('../app/',import.meta.url))).filter(f=>f.endsWith('.tsx'))){
  const source=await readFile(new URL('../app/'+file,import.meta.url),'utf8');
  for(const [,key] of source.matchAll(/\bt\(['"]([A-Za-z_]+)['"]/g))assert.ok(Object.hasOwn(messages,key),file+': '+key);
  assert.doesNotMatch(source,/[A-Za-z][^\n<>]* \/ [\u4e00-\u9fff]/,file);
 }
});
