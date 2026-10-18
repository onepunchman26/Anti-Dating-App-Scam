import {headers} from 'next/headers';
import {resolveLanguage} from '../lib/i18n.mjs';
import type {Locale} from './language';
export async function requestLanguage():Promise<Locale>{
 const h=await headers();return resolveLanguage(h.get('cookie')||'',h.get('accept-language')||'') as Locale;
}
