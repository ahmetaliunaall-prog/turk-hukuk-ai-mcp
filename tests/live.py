"""Canlı testler: başarısızlığı atlama veya başarılı olarak etiketleme yok."""
import asyncio,json,sys,time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from local_ai.ollama import request,chat,analyze
from legal_mcp.client import connect,call
from legal_mcp.orchestrator import research

async def main():
    results=[]
    async def check(name,fn):
        start=time.monotonic()
        try:
            result=await fn()
            if result is False: raise AssertionError('Beklenen canlı veri yok')
            row={'name':name,'status':'PASS','seconds':round(time.monotonic()-start,2)}
        except Exception as ex: row={'name':name,'status':'FAIL','error':type(ex).__name__+': '+str(ex)[:250],'seconds':round(time.monotonic()-start,2)}
        results.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    async def tags(): return any(m['name']=='qwen3:1.7b' for m in (await asyncio.to_thread(request,'/api/tags'))['models'])
    async def model(): return bool(await chat('Tek kelime Türkçe cevap ver. /no_think','Hazır mısın?',max_tokens=8,timeout=45))
    await check('Ollama bağlantısı',tags);await check('Qwen 3 1.7B yanıtı',model)
    async with connect() as s:
        hits={};laws={};tree=[]
        async def cases():
            nonlocal hits
            hits=await call(s,'ictihat_ara',{'ifade':'performans','adet':3});return bool(hits.get('sonuclar'))
        async def decision():
            if not hits.get('sonuclar'): return False
            r=await call(s,'karar_getir',{'karar_id':hits['sonuclar'][0]['id']});return len(r.get('metin',''))>40
        async def legislation():
            nonlocal laws
            laws=await call(s,'search_mevzuat',{'mevzuat_no':'4857','page_size':3});return bool(laws.get('documents'))
        async def articles():
            nonlocal tree
            if not laws.get('documents'): return False
            tree=await call(s,'get_mevzuat_article_tree',{'mevzuat_id':laws['documents'][0]['mevzuat_id']});return bool(tree)
        async def content():
            if not tree: return False
            from legal_mcp.orchestrator import flatten
            n=next((n for n in flatten(tree) if n.get('madde_no')==19),None)
            if not n: return False
            r=await call(s,'get_mevzuat_article_content',{'mevzuat_id':laws['documents'][0]['mevzuat_id'],'madde_id':n['madde_id']});return len(r.get('markdown_content',''))>40
        await check('İçtihat arama',cases);await check('Karar getirme',decision);await check('Mevzuat arama',legislation);await check('Madde ağacı',articles);await check('Madde getirme',content)
    async def combined():
        r=await research('İşveren objektif olmayan performans kriterleriyle işçiyi çıkardı. İşe iade ve savunma açısından hangi koşullar araştırılmalı?',mode='petition')
        Path('tests/research-live.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
        return all(any(e['kind']==k and e['verified'] for e in r['sources']) for k in ['mevzuat','ictihat']) and bool(r['claims']) and bool(r['petition'])
    await check('Süre sınırlı Qwen desteği, MCP, birleşik araştırma ve dilekçe',combined)
    Path('tests/live-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if all(r['status']=='PASS' for r in results) else 1

if __name__=='__main__': raise SystemExit(asyncio.run(main()))
