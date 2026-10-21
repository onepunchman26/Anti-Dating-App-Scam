import React from 'react';
import {createRoot} from 'react-dom/client';
import {LanguageProvider,useLanguage} from '../app/language';
import OnboardingClient from '../app/onboarding-client';
import {setupText} from '../lib/setup-copy.mjs';
import '../app/globals.css';
function LocalApp(){const {locale,setLocale}=useLanguage();return <><header className="top"><strong>slowmatch.</strong><label>Language / 语言<select value={locale} onChange={e=>setLocale(e.target.value as 'en'|'zh-CN')}><option value="en">English</option><option value="zh-CN">中文</option></select></label><a href="https://slowmatch-private-pilot.fizzydeer7.chatgpt.site/#discover" target="_blank" rel="noreferrer">{setupText(locale,'service')}</a></header><main><OnboardingClient localMode navigate={view=>{window.open('https://slowmatch-private-pilot.fizzydeer7.chatgpt.site/#'+view,'_blank','noopener,noreferrer');}}/></main></>;}
const saved=document.cookie.match(/(?:^|; )slowmatch-language=(en|zh-CN)/)?.[1];
createRoot(document.getElementById('root')!).render(<LanguageProvider initialLocale={saved==='en'?'en':'zh-CN'}><LocalApp/></LanguageProvider>);
