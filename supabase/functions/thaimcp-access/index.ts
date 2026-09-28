// Yerel araştırma yapmaz. Yalnız erişim/yönetim; olay metni kabul edilmez.
const origins = new Set(['https://turk-hukuk-ai-mcp.netlify.app','http://127.0.0.1:8765','http://localhost:8765']);
const url = Deno.env.get('SUPABASE_URL')!;
const secrets = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') || '{}');
const publishes = JSON.parse(Deno.env.get('SUPABASE_PUBLISHABLE_KEYS') || '{}');
const secret = (Object.values(secrets)[0] as string) || Deno.env.get('THAIMCP_SECRET_KEY');
const publishable = (Object.values(publishes)[0] as string) || Deno.env.get('THAIMCP_PUBLISHABLE_KEY');
export async function hashKey(key:string) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(key)))).map(v=>v.toString(16).padStart(2,'0')).join('');
}
export function generateKey() {
  const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';let key='';
  while(key.length<12){for(const b of crypto.getRandomValues(new Uint8Array(24))){if(b<248&&key.length<12)key+=alphabet[b%62];}}
  return key;
}
Deno.serve(async(req:Request)=>{
  const origin=req.headers.get('origin');
  const headers:Record<string,string>={'Content-Type':'application/json','Cache-Control':'no-store','Vary':'Origin'};
  if(origin&&origins.has(origin))headers['Access-Control-Allow-Origin']=origin;
  headers['Access-Control-Allow-Headers']='authorization, apikey, content-type';headers['Access-Control-Allow-Methods']='POST, OPTIONS';
  const reply=(status:number,body:unknown)=>new Response(JSON.stringify(body),{status,headers});
  if(origin&&!origins.has(origin))return reply(403,{error:'Origin reddedildi.'});
  if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
  if(req.method!=='POST')return reply(405,{error:'POST gerekli.'});
  if(!secret||!publishable)return reply(503,{error:'Erişim hizmeti yapılandırılmadı.'});
  try{
    const bodyText=await req.text();if(bodyText.length>2048)return reply(413,{error:'İstek çok büyük.'});
    const b=JSON.parse(bodyText);if(b.text||b.incident)return reply(400,{error:'Olay metni bu servise gönderilemez.'});
    const action=b.action;const admin=['list','create','rotate','toggle','revoke'].includes(action);
    if(!admin&&!['verify','consume'].includes(action))return reply(400,{error:'Geçersiz işlem.'});
    let actor=null;
    if(admin){
      const authorization=req.headers.get('authorization')||'';
      if(!authorization.startsWith('Bearer '))return reply(401,{error:'Yönetici oturumu gerekli.'});
      const auth=await fetch(url+'/auth/v1/user',{headers:{apikey:publishable,Authorization:authorization},signal:AbortSignal.timeout(8000)});
      if(!auth.ok)return reply(401,{error:'Yönetici oturumu geçersiz.'});actor=(await auth.json()).id;
    }
    // Proxy platformunca iletilen IP'nin yalnız hash'i kısa süreli sayaçta tutulur.
    const client=await hashKey(req.headers.get('x-forwarded-for')?.split(',')[0]?.trim()||'unknown');
    let plain='';
    if(action==='create'||action==='rotate')plain=generateKey();
    else if(!admin){
      if(typeof b.key!=='string'||!/^[A-Za-z0-9]{12}$/.test(b.key)){
        // Biçimsiz denemeler de aynı DB rate limiter'dan geçer.
        b.key='invalid';
      }
    }
    const payload={p_action:action,p_actor:actor,p_id:b.id||null,p_hash:plain?await hashKey(plain):!admin?await hashKey(b.key):'',p_prefix:plain.slice(0,3),p_label:String(b.label||'').slice(0,128),p_active:b.active!==false,p_expires:b.expires_at||null,p_client:client};
    const response=await fetch(url+'/rest/v1/rpc/thaimcp_access',{method:'POST',headers:{apikey:secret,'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(10000)});
    if(!response.ok){if(response.status===409)return reply(409,{error:'Anahtar çakışması; yeniden oluşturun.'});return reply(503,{error:'Erişim veritabanına ulaşılamadı.'});}
    const data=await response.json();
    if(data.error)return reply(data.error==='rate_limit'?429:data.error==='forbidden'?403:400,{error:data.error});
    return reply(200,plain?{...data,key:plain}:data);
  }catch{return reply(503,{error:'Erişim hizmeti isteği tamamlanamadı.'});}
});
