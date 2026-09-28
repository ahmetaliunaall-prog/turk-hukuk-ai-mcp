import asyncio,json,urllib.request
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

async def chat(system,user,schema=None):
    payload={'model':MODEL,'stream':False,'think':False,'keep_alive':'2m','messages':[{'role':'system','content':system},{'role':'user','content':user}], 'options':{'num_ctx':4096,'num_predict':850,'temperature':0,'num_thread':2}}
    if schema: payload['format']=schema
    result=await asyncio.to_thread(request,'/api/chat',payload)
    return result['message']['content']

async def analyze(text):
    prompt='Türk hukuku araştırma planı oluştur. Olaydaki özel isimleri ASLA arama ifadelerine koyma. Yalnızca genel hukuki kavramları kullan. En fazla 3 farklı kısa içtihat sorgusu ve 2 mevzuat öner. Kanun ve maddeler araştırılacak öneridir, doğrulanmış kaynak değildir. Bilinmeyeni eksik_bilgiler alanına yaz. /no_think'
    data=await chat(prompt,text,Analysis.model_json_schema())
    return Analysis.model_validate_json(data)
