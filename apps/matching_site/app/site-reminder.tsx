'use client';
import {useLanguage} from './language';
export default function SiteReminder({compact=true}:{compact?:boolean}){
 const {t}=useLanguage();
 return <aside className={'reminder '+(compact?'compact':'')} aria-label={t('reminderTitle')}><span className="reminder-mark" aria-hidden="true">i</span><div>
 {compact?<><p>{t('reminderShort')}</p><details><summary>{t('reminderTitle')}</summary><p>{t('reminderFull')}</p></details></>:<><h3>{t('reminderTitle')}</h3><p>{t('reminderFull')}</p></>}
 </div></aside>;
}
