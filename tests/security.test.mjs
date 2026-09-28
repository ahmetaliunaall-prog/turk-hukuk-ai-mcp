import {readFile} from 'node:fs/promises';
import {stripTypeScriptTypes} from 'node:module';
import assert from 'node:assert/strict';
let handler;
globalThis.Deno={env:{get:k=>({SUPABASE_URL:'https://test.supabase.co',SUPABASE_SECRET_KEYS:'{"default":"sb_secret_test"}',SUPABASE_PUBLISHABLE_KEYS:'{"default":"sb_publishable_test"}'})[k]},serve:fn=>{handler=fn}};
const source=await readFile(new URL('../supabase/functions/thaimcp-access/index.ts',import.meta.url),'utf8');
const mod=await import('data:text/javascript;base64,'+Buffer.from(stripTypeScriptTypes(source)).toString('base64'));
const keys=new Set(Array.from({length:1000},()=>mod.generateKey()));
assert.equal(keys.size,1000);for(const key of keys){assert.match(key,/^[A-Za-z0-9]{12}$/);assert.match(await mod.hashKey(key),/^[a-f0-9]{64}$/)}
const request=(body,headers={})=>new Request('https://test/functions/v1/thaimcp-access',{method:'POST',headers:{'Content-Type':'application/json',...headers},body:JSON.stringify(body)});
let rpc=0;
globalThis.fetch=async(url,options)=>{
  if(url.endsWith('/auth/v1/user'))return Response.json({id:'admin-user'},{status:options.headers.Authorization==='Bearer valid-admin'?200:401});
  rpc++;const b=JSON.parse(options.body);
  assert.ok(!options.headers.Authorization);assert.equal(options.headers.apikey,'sb_secret_test');
  if(b.p_action==='list')return Response.json({keys:[]});
  if(b.p_action==='create'){assert.match(b.p_hash,/^[0-9a-f]{64}$/);assert.equal(b.p_prefix.length,3);return Response.json({id:'new-id'})}
  return Response.json({valid:false});
};
assert.equal((await handler(request({action:'list'}))).status,401);assert.equal(rpc,0);
assert.equal((await handler(request({action:'list'},{Authorization:'Bearer invalid'}))).status,401);assert.equal(rpc,0);
assert.equal((await handler(request({action:'verify',key:'wrong'}))).status,200);
assert.equal((await handler(request({action:'verify',key:'wrong'},{Origin:'https://evil.com'}))).status,403);
assert.equal((await handler(request({action:'verify',key:'wrong',text:'private incident'}))).status,400);
const created=await handler(request({action:'create',label:'test'},{Authorization:'Bearer valid-admin'}));assert.equal(created.status,200);
const d=await created.json();assert.match(d.key,/^[A-Za-z0-9]{12}$/);assert.equal(d.key_hash,undefined);
assert.deepEqual(await (await handler(request({action:'list'},{Authorization:'Bearer valid-admin'}))).json(),{keys:[]});
console.log('PASS: Edge TypeScript parse, 1000 secure 12-character keys, hashes, admin JWT rejection, origin, incident rejection, one-time key response, hash-free listing.');
