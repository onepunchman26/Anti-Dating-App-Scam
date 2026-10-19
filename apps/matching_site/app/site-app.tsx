'use client';
import {useEffect,useState,useRef} from 'react';
import {Compass,CalendarDays,UserRound,ArrowUpRight,ArrowRight,HeartHandshake,MessageCircle,ShieldCheck} from 'lucide-react';
import {useLanguage} from './language';
import SiteReminder from './site-reminder';
import ServiceStatus from './service-status';
import MatchingClient from './matching-client';
import OnboardingClient from './onboarding-client';
import {onboardingText} from '../lib/onboarding.mjs';
export type View='start'|'discover'|'plans'|'profile'|'help';
const INSTALL='https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/INSTALL_WITH_CHATGPT.md';
const CREDITS='https://github.com/onepunchman26/Anti-Dating-App-Scam/blob/main/docs/39_open_source_credits.md';
const steps=[{Icon:MessageCircle,key:'stepOne'},{Icon:ShieldCheck,key:'stepTwo'},{Icon:HeartHandshake,key:'stepThree'}];
export default function SiteApp({signedIn,accountHref}:{signedIn:boolean;accountHref:string}){
 const {t,locale,setLocale}=useLanguage();
 const [view,setView]=useState<View>('start');
 const lastView=useRef<View>('start');
 useEffect(()=>{if(lastView.current!==view){document.getElementById('main')?.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});lastView.current=view;}},[view]);
 useEffect(()=>{const read=()=>{const hash=location.hash.slice(1);if(['start','discover','plans','profile','help'].includes(hash))setView(hash as View);else if(!hash)setView('start');};read();window.addEventListener('hashchange',read);return()=>window.removeEventListener('hashchange',read);},[]);
 const navigate=(next:View)=>{setView(next);location.hash=next;};
 return <>
 <a className="skip-link" href="#main">{t('skip')}</a>
 <header className="top">
  <a href={signedIn?'#discover':'/'} className="brand" aria-label="AI-SlowMatch"><span className="brand-icon" aria-hidden="true"><HeartHandshake size={22}/></span><span>slowmatch<span className="brand-dot">.</span></span></a>
  {signedIn&&<nav className="main-nav" aria-label={t('navigation')}><a href="#start" aria-current={view==='start'?'page':undefined}><MessageCircle size={18} aria-hidden="true"/>{onboardingText(locale,'start')}</a>{([['discover',Compass],['plans',CalendarDays],['profile',UserRound]] as const).map(([key,Icon])=><a key={key} href={'#'+key} aria-current={view===key?'page':undefined}><Icon size={18} aria-hidden="true"/>{t(key)}</a>)}</nav>}
  <div className="top-tools"><a href="#help" onClick={()=>setView('help')} aria-current={view==='help'?'page':undefined}>{t('help')}</a><label className="language-picker"><span className="sr-only">{t('language')}</span><select value={locale} onChange={e=>setLocale(e.target.value as 'en'|'zh-CN')}><option value="en">English</option><option value="zh-CN">中文</option></select></label><a className="account-link" href={accountHref} target="_top">{t(signedIn?'signOut':'signIn')}</a></div>
 </header>
 <main id="main" tabIndex={-1}>
 <div hidden={view!=='start'}><OnboardingClient navigate={navigate}/></div>
 {signedIn?<MatchingClient view={view} navigate={navigate}/>:<div hidden={view==='help'||view==='start'}>
  <section className="hero"><p className="eyebrow">{t('eyebrow')}</p><h1>{t('heroTitle')}</h1><p className="hero-intro">{t('heroIntro')}</p><div className="actions"><a className="button" href={INSTALL} target="_blank" rel="noreferrer">{t('start')}<ArrowUpRight size={18} aria-hidden="true"/></a><a className="text-link" href="#how-it-works">{t('how')}<ArrowRight size={18} aria-hidden="true"/></a></div><span className="pilot">{t('pilot')}</span></section>
  <section id="how-it-works" className="how-grid" aria-label={t('how')}>{steps.map(({Icon,key},i)=><article key={key}><span className="how-number">0{i+1}</span><Icon size={26} aria-hidden="true"/><h2>{t(key)}</h2><p>{t(key+'Body')}</p></article>)}</section>
  <SiteReminder/>
 </div>}
 <section hidden={view!=='help'} className="help-page"><div className="page-heading"><p className="eyebrow">AI-SLOWMATCH</p><h1>{t('help')}</h1><p>{t('installBody')}</p></div><div className="panel"><h2>{t('start')}</h2><p>{t('accessNote')}</p><a className="button" href={INSTALL} target="_blank" rel="noreferrer">{t('install')}<ArrowUpRight size={18} aria-hidden="true"/></a></div><div className="boundary"><section><ShieldCheck size={24} aria-hidden="true"/><h2>{t('privateTitle')}</h2><p>{t('privateBody')}</p></section><section><UserRound size={24} aria-hidden="true"/><h2>{t('sharedTitle')}</h2><p>{t('sharedBody')}</p></section></div>{signedIn&&<ServiceStatus/>}<p className="muted">{t('withdrawalNote')}</p></section>
 </main>
 <footer><span className="footer-brand">AI-SlowMatch</span><p>{t('footer')}</p><a href={CREDITS} target="_blank" rel="noreferrer">{t('credits')}</a></footer>
 </>;
}
