'use client';
import {createContext,useContext,useEffect,useState,useCallback,type ReactNode} from 'react';
import {text,LANGUAGE_COOKIE} from '../lib/i18n.mjs';
import {label as enumLabel} from '../lib/labels.mjs';
export type Locale='en'|'zh-CN';
type Language={locale:Locale;setLocale:(locale:Locale)=>void;t:(key:string,values?:Record<string,string|number>)=>string;label:(value:string|undefined)=>string;date:(value:string)=>string};
const Context=createContext<Language|null>(null);
export function LanguageProvider({initialLocale,children}:{initialLocale:Locale;children:ReactNode}){
 const [locale,updateLocale]=useState(initialLocale);
 const setLocale=useCallback((next:Locale)=>{
  updateLocale(next);
  // Persist only the language. Storage denial leaves this session usable.
  try{document.cookie=LANGUAGE_COOKIE+'='+next+'; Path=/; Max-Age=31536000; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');}catch{/* session still works */}
 },[]);
 useEffect(()=>{document.documentElement.lang=locale;document.title=text(locale,'title');},[locale]);
 const t=(key:string,values:Record<string,string|number>={})=>text(locale,key,values);
 const label=(value:string|undefined)=>enumLabel(value,locale);
 const date=(value:string)=>Number.isFinite(Date.parse(value))?new Intl.DateTimeFormat(locale,{dateStyle:'medium',timeStyle:'short'}).format(new Date(value)):t('notShared');
 return <Context.Provider value={{locale,setLocale,t,label,date}}>{children}</Context.Provider>;
}
export function useLanguage(){const language=useContext(Context);if(!language)throw Error('LanguageProvider required');return language;}
