'use client';
import {useState} from 'react';
import {useLanguage} from './language';
type Status={version:string;protocol:string;scope:string;access:string;read:string};
export default function ServiceStatus(){
 const {t}=useLanguage();
 const [status,setStatus]=useState<Status|null>(null),[busy,setBusy]=useState(false),[failed,setFailed]=useState(false);
 async function check(){
  setBusy(true);setFailed(false);setStatus(null);
  try{
   const response=await fetch('/api/matching',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'slowmatch_channel_check',arguments:{write:false,client_protocol:'1.0'}})});
   const raw:unknown=await response.json();if(!response.ok||!raw||typeof raw!=='object')throw Error('unavailable');
   const body=raw as Record<string,unknown>,scope=body.data_scope as Record<string,unknown>|undefined;
   if(body.authenticated!==true||typeof body.service_version!=='string'||typeof body.service_protocol_version!=='string'||typeof body.database_read!=='string'||!scope||typeof scope.kind!=='string'||typeof scope.access!=='string')throw Error('unavailable');
   setStatus({version:body.service_version,protocol:body.service_protocol_version,scope:scope.kind,access:scope.access,read:body.database_read});
  }catch{setFailed(true);}finally{setBusy(false);}
 }
 return <section className="panel"><h2>{t('serviceCheck')}</h2><p>{t('serviceCheckBody')}</p><button onClick={check} disabled={busy}>{t(busy?'checking':'checkConnection')}</button><div aria-live="polite">{failed&&<p className="error">{t('checkFailed')}</p>}{status&&<><p className="status-badge">{t('connected')}</p><p>{t(status.read==='passed'?'databaseOk':'databaseUnknown')} · {t(status.scope==='controlled_test'?'testScope':'productionScope')}</p><p>{t('desktopUnchecked')}</p><details><summary>{t('diagnostics')}</summary><p>{t('serviceVersion')}: {status.version} · {t('protocol')}: {status.protocol}</p><p>{t(status.access==='enabled'?'accessEnabled':'accessRestricted')}</p></details></>}</div></section>;
}
