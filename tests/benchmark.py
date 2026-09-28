"""Aynı süreçte soğuk/sıcak kamu kaynağı önbelleğini ölçer; olay metni kaydetmez."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from legal_mcp.orchestrator import research
async def main():
    rows=[]
    for name in ['cold','warm']:
        r=await research('İşveren objektif olmayan performans kriterleriyle işçiyi çıkardı. İşe iade ve savunma açısından hangi koşullar araştırılmalı?',mode='petition')
        rows.append({'run':name,**r['metrics'],'errors':r['errors'],'claims':len(r['claims']),'petition':bool(r['petition'])})
        print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
    Path('tests/benchmark-latest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())
