import sys
from pathlib import Path
import asyncio,httpx
from urllib.parse import quote
from .privacy import public_query
from .transport import CASE_HTTP,law_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/ictihat'))
sys.path.insert(0,str(ROOT/'vendor/mevzuat'))
from turk_hukuku_ictihat import uyap, danistay, anayasa
from mevzuat_client import MevzuatApiClient
from mevzuat_models import MevzuatSearchRequest

SOURCES = {'adli':uyap,'idari':danistay,'anayasa':anayasa}
# Yalnız HTTP taşıması enjekte edilir; vendor arama/parse mantığı aynıdır.
for source in SOURCES.values(): source.httpx=CASE_HTTP

async def ictihat_ara(ifade:str,mahkeme:str='adli',adet:int=10,sayfa:int=1)->dict:
    query=public_query(ifade)
    try:return await asyncio.to_thread(SOURCES[mahkeme].ara,query,adet=max(1,min(adet,20)),sayfa=max(1,min(sayfa,10)))
    except httpx.HTTPStatusError as ex:return {'error':'Resmî kaynak HTTP '+str(ex.response.status_code),'sonuclar':[]}

async def karar_getir(karar_id:str,mahkeme:str='adli')->dict:
    if not karar_id or len(karar_id)>200:
        raise ValueError('Geçersiz kaynak kimliği')
    try:return await asyncio.to_thread(SOURCES[mahkeme].karar,karar_id)
    except httpx.HTTPStatusError as ex:return {'error':'Resmî kaynak HTTP '+str(ex.response.status_code),'metin':''}

async def search_mevzuat(mevzuat_adi:str='',mevzuat_no:str='',page_number:int=1,page_size:int=10,phrase:str='')->dict:
    c=law_client(MevzuatApiClient)
    result=await c.search_documents(MevzuatSearchRequest(mevzuat_adi=public_query(mevzuat_adi) or None,mevzuat_no=public_query(mevzuat_no) or None,phrase=public_query(phrase) or None,page_number=max(1,min(10,page_number)),page_size=min(20,max(1,page_size))))
    if result.error_message:raise RuntimeError(result.error_message)
    return result.model_dump(mode='json')

async def get_mevzuat_article_tree(mevzuat_id:str)->list:
    c=law_client(MevzuatApiClient)
    return [n.model_dump(mode='json') for n in await c.get_article_tree(mevzuat_id)]

async def get_mevzuat_article_content(mevzuat_id:str,madde_id:str)->dict:
    c=law_client(MevzuatApiClient)
    r=await c.get_article_content(madde_id,mevzuat_id)
    if r.error_message: raise RuntimeError(r.error_message)
    return r.model_dump(mode='json')

TOOLS={f.__name__:f for f in [ictihat_ara,karar_getir,search_mevzuat,get_mevzuat_article_tree,get_mevzuat_article_content]}
