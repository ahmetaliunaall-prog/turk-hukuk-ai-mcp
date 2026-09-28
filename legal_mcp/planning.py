"""Kişisiz hukuk terimleriyle arama ailesi; öneriler kaynak kanıtı değildir."""
import re
from difflib import SequenceMatcher
from .privacy import public_query
from local_ai.ollama import Analysis,LawQuery

def normalize(text):
    return re.sub(r'\s+',' ',str(text).translate(str.maketrans('ıİşŞğĞüÜöÖçÇ','iissgguuoocc')).lower()).strip()

def similarity(needle,haystack):
    a=re.findall(r'[a-z0-9]+',normalize(needle));b=set(re.findall(r'[a-z0-9]+',normalize(haystack)))
    if not a or not b:return 0.0
    def match(w):
        if w in b:return 1.0
        if len(w)<4:return 0
        candidates=[v for v in b if v[:2]==w[:2]]
        if any(v.startswith(w) or w.startswith(v) for v in candidates):return .85
        return max((SequenceMatcher(None,w,v).ratio() for v in candidates if abs(len(w)-len(v))<=2),default=0)
    return sum(s if s>=.78 else 0 for s in map(match,a))/len(a)

FAMILIES=[
    (['ise iade','performans','fesih'],['işe iade','geçersiz fesih','objektif performans kriterleri','savunma fesih','fesih geçersizliği'],['performans','savunma','objektif','fesih','işe iade'],'İş hukuku','adli',LawQuery(mevzuat_no='4857',maddeler=[18,19,20])),
    (['kira','tahliye'],['kira tahliye','tahliye taahhüdü','kira bedeli','temerrüt tahliye'],['kira','tahliye','temerrüt'],'Kira uyuşmazlığı','adli',LawQuery(mevzuat_adi='Türk Borçlar Kanunu')),
    (['bosanma','nafaka','velayet'],['boşanma','nafaka','velayet','kusur boşanma'],['boşanma','nafaka','velayet','kusur'],'Aile hukuku','adli',LawQuery(mevzuat_adi='Türk Medenî Kanunu')),
    (['idari','memur','vergi','iptal'],['idari işlem iptal','hukuka aykırılık','idari dava','vergi cezası'],['idari işlem','iptal','hukuka aykırılık'],'İdari uyuşmazlık','idari',LawQuery(mevzuat_adi='İdari Yargılama Usulü Kanunu')),
    (['bireysel basvuru','anayasa','adil yargilanma'],['adil yargılanma','bireysel başvuru','hak ihlali','gerekçeli karar'],['adil yargılanma','hak ihlali','gerekçeli karar'],'Temel haklar','anayasa',LawQuery(mevzuat_adi='Anayasa')),
]
VOCAB=['tazminat','haksız fiil','sözleşme','zamanaşımı','alacak','icra','itiraz','borç','ceza','delil','savunma','mülkiyet','işçilik','ücret','iş kazası','süre','yetki','görev','dava','temerrüt']

def fallback(text):
    clean=normalize(text)
    family=next((f for f in FAMILIES if any(t in clean for t in f[0])),None)
    if family:
        _,queries,concepts,topic,_,law=family
        return Analysis(dava_turu=queries[0],hukuki_konu=topic,alt_konu=' / '.join(concepts[:3]),hukuki_sorun=' / '.join(concepts[:5]),anahtar_kavramlar=concepts,ilgili_mevzuat=[law],aranacak_icihat_kriterleri=queries[:5])
    # Yalnız izinli hukuk sözlüğü: kişi isimleri ve olay cümlesi dışarı çıkmaz.
    words=[w for w in VOCAB if normalize(w) in clean][:8]
    words=words or ['dava','delil']
    queries=list(dict.fromkeys([' '.join(words[:2])]+words))[:5]
    return Analysis(dava_turu='Hukuki araştırma',hukuki_konu=words[0],alt_konu=' / '.join(words[:3]),hukuki_sorun=' / '.join(words),anahtar_kavramlar=words,ilgili_mevzuat=[LawQuery(mevzuat_adi=words[0])],aranacak_icihat_kriterleri=queries)

def safe_terms(values):
    allowed=[q for f in FAMILIES for q in f[1]+f[2]]+VOCAB
    result=[]
    for value in values:
        n=normalize(value)
        # Model özel isim veya olay metni gönderemez; onaylı terimlerle kesişim.
        for term in allowed:
            if normalize(term)==n and term not in result:result.append(public_query(term))
    return result

def queries(plan):
    values=safe_terms(plan.aranacak_icihat_kriterleri+plan.anahtar_kavramlar)
    return list(dict.fromkeys(values))[:5] or ['dava','delil']

def alternate_court(plan,current):
    n=normalize(plan.hukuki_konu+' '+plan.hukuki_sorun)
    preferred='idari' if any(x in n for x in ['idari','vergi','memur']) else 'anayasa' if any(x in n for x in ['temel hak','adil yargilanma','hak ihlali']) else 'adli'
    return preferred if preferred!=current else ('anayasa' if current=='idari' else 'idari' if current=='anayasa' else 'anayasa')
