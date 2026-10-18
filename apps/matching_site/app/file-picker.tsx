'use client';
import {useRef,useState} from 'react';
import {Upload} from 'lucide-react';
import {useLanguage} from './language';
export default function FilePicker({title,disabled,onPick}:{title:string;disabled:boolean;onPick:(file:File|undefined)=>void}){
  const {t}=useLanguage();
  const input=useRef<HTMLInputElement>(null);
  const [name,setName]=useState('');
  return <div className="file"><button type="button" className="quiet" disabled={disabled} onClick={()=>input.current?.click()}><Upload size={16} aria-hidden="true"/>{title}</button><span className="file-name">{name||t('noFile')}</span><input ref={input} type="file" accept=".json,application/json" hidden aria-hidden="true" tabIndex={-1} onChange={e=>{const file=e.target.files?.[0];setName(file?.name||'');onPick(file);}}/></div>;
}
