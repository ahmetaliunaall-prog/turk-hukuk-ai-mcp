import asyncio,json,urllib.request,httpx
from pydantic import BaseModel,Field

URL='http://127.0.0.1:11434'
MODEL='qwen3:1.7b'

class LawQuery(BaseModel):
    mevzuat_adi:str=Field(default='',max_length=120)
    mevzuat_no:str=Field(default='',max_length=12)
    maddeler:list[int]=Field(default_factory=list,max_length=5)

class Analysis(BaseModel):
    dava_turu:str=Field(max_length=120)
    hukuki_konu:str=Field(max_length=120)
    alt_konu:str=Field(max_length=120)
    hukuki_sorun:str=Field(max_length=400)
    anahtar_kavramlar:list[str]=Field(max_length=10)
    ilgili_mevzuat:list[LawQuery]=Field(max_length=3)
    aranacak_icihat_kriterleri:list[str]=Field(max_length=5)
    eksik_bilgiler:list[str]=Field(default_factory=list,max_length=5)

def request(path,body=None,timeout=180):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(URL+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)

async def chat(system,user,schema=None,max_tokens=120,timeout=8):
    payload={'model':MODEL,'stream':True,'think':False,'keep_alive':0,'messages':[{'role':'system','content':system},{'role':'user','content':user}], 'options':{'num_ctx':2048,'num_predict':max_tokens,'temperature':0,'num_thread':2}}
    if schema: payload['format']=schema
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout,connect=2)) as client:
        async with asyncio.timeout(timeout):
            chunks=[]
            async with client.stream('POST',URL+'/api/chat',json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        row=json.loads(line)
                        if row.get('error'):raise RuntimeError('Yerel model isteği başarısız')
                        chunks.append(row.get('message',{}).get('content',''))
            return ''.join(chunks)

async def analyze(text):
    from legal_mcp.planning import fallback,safe_terms
    plan=fallback(text)
    schema={'type':'object','properties':{'kavramlar':{'type':'array','maxItems':4,'items':{'type':'string'}}},'required':['kavramlar']}
    data=json.loads(await chat('En fazla dört kısa Türkçe hukuk kavramı çıkar. İsim, numara, hüküm yazma. /no_think',text[:1800],schema,max_tokens=64,timeout=8))
    additions=safe_terms(data.get('kavramlar',[]))
    plan.anahtar_kavramlar=list(dict.fromkeys(plan.anahtar_kavramlar+additions))[:10]
    return plan
