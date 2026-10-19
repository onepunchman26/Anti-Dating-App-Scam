// Local synthetic browser QA only; excluded from every hosted source/package.
import {createServer,request as forward} from 'node:http';
import {fixture} from './helpers.mjs';
if(process.env.SLOWMATCH_UI_QA!=='1')throw Error('Explicit QA flag required');
const f=await fixture(),servers=[],calls=[];
for(const [i,owner] of ['synthetic-circle-A','synthetic-circle-B','synthetic-circle-C'].entries()){
 const port=5174+i,origin='http://127.0.0.1:'+port;
 const server=createServer(async(req,res)=>{
  if(req.headers.host!=='127.0.0.1:'+port){res.writeHead(403);res.end();return;}
  if(req.url==='/__qa/calls'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(calls));return;}
  if(req.url==='/api/matching'){
   if(req.method!=='POST'||req.headers.origin!==origin||!req.headers.cookie?.split(';').some(v=>v.trim()==='__sites_local_auth=1')){res.writeHead(403);res.end(JSON.stringify({error:'sign_in_required'}));return;}
   try{let body='';for await(const part of req){body+=part;if(body.length>16000)throw Error('input_limit');}const input=JSON.parse(body);calls.push({actor:i,operation:input.arguments?.request?.action||input.name});const result=await f.call(input.name,input.arguments,owner);res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(result));}
   catch(error){res.writeHead(400,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify({error:error.message}));}return;
  }
  if(!req.url?.startsWith('/')||req.url.startsWith('//')){res.writeHead(400);res.end();return;}
  const headers={...req.headers,host:'127.0.0.1:5173'};if(headers.origin===origin)headers.origin='http://127.0.0.1:5173';
  const proxy=forward({host:'127.0.0.1',port:5173,path:req.url,method:req.method,headers},upstream=>{res.writeHead(upstream.statusCode||502,upstream.headers);upstream.pipe(res);});
  proxy.on('error',()=>{res.writeHead(502);res.end('Local preview unavailable');});req.pipe(proxy);
 });
 server.listen(port,'127.0.0.1',()=>console.log('Synthetic circle '+(i+1)+': '+origin));servers.push(server);
}
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,async()=>{for(const s of servers)s.close();await f.dispose();process.exit(0);});
