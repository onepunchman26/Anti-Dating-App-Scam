import type {Metadata} from 'next';
import {requestLanguage} from './request-language';
import {LanguageProvider} from './language';
import {text} from '../lib/i18n.mjs';
import './globals.css';
export async function generateMetadata():Promise<Metadata>{
 const locale=await requestLanguage();
 return {title:text(locale,'title'),description:text(locale,'description'),icons:{icon:'/favicon.svg',shortcut:'/favicon.svg'}};
}
export default async function RootLayout({children}:{children:React.ReactNode}){
 const locale=await requestLanguage();
 return <html lang={locale}><body><LanguageProvider initialLocale={locale}>{children}</LanguageProvider></body></html>;
}
