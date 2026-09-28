from dataclasses import dataclass,field,asdict
import hashlib,re
from urllib.parse import urlparse
from datetime import datetime,timezone
from .planning import normalize,similarity

ALLOWED={'emsal.uyap.gov.tr','karararama.danistay.gov.tr','kararlarbilgibankasi.anayasa.gov.tr','mevzuat.adalet.gov.tr','mevzuat.gov.tr','www.mevzuat.gov.tr','bedesten.adalet.gov.tr'}

@dataclass
class Evidence:
    id:str
    kind:str
    title:str
    url:str
    text:str
    metadata:dict=field(default_factory=dict)
    score:float=0
    verified:bool=False
    digest:str=''
    fetched_at:str=''

    def verify(self):
        u=urlparse(self.url)
        self.verified=bool(self.id and len(self.text.strip())>=40 and u.scheme=='https' and u.hostname in ALLOWED and not self.metadata.get('error'))
        self.digest=hashlib.sha256(self.text.encode()).hexdigest()
        self.fetched_at=datetime.now(timezone.utc).isoformat()
        return self.verified

def deduplicate(items):
    seen=set();result=[]
    for e in items:
        key=(e.kind,e.id)
        if key not in seen: seen.add(key);result.append(e)
    return result

def rank(items,analysis):
    """Hafif konu/alt konu/sorun/kavram/madde/mahkeme eşleşmesi; açıklanabilir."""
    fields=[('konu',analysis.hukuki_konu,2),('alt_konu',analysis.alt_konu,3),('hukuki_sorun',analysis.hukuki_sorun,4),('dava_turu',analysis.dava_turu,2)]
    for e in items:
        body=normalize(e.title+' '+e.text)
        parts={}
        for label,text,weight in fields:
            parts[label]=round(weight*similarity(text,body),3)
        parts['kavram']=round(sum(similarity(k,body) for k in analysis.anahtar_kavramlar),3)
        parts['mevzuat']=sum(bool(re.search(r'\b'+re.escape(l.mevzuat_no)+r'\b',body)) for l in analysis.ilgili_mevzuat if l.mevzuat_no)
        parts['madde']=sum(bool(re.search(r'(?:madde\s*'+str(n)+r'\b|\b'+str(n)+r'\s*\.?\s*(?:inci|uncu|nci)?\s*madde)',body)) or str(e.metadata.get('madde_no'))==str(n) for l in analysis.ilgili_mevzuat for n in l.maddeler)
        parts['sorgu']=round(max((similarity(q,body) for q in e.metadata.get('arama_sorgulari',[])),default=0),3)
        parts['baslik_kunye']=round(max((similarity(k,e.title) for k in analysis.anahtar_kavramlar),default=0),3)
        parts['tam_metin']=round(max((similarity(k,e.text) for k in analysis.anahtar_kavramlar),default=0)*2,3)
        problem=normalize(analysis.hukuki_sorun+' '+analysis.hukuki_konu+' '+analysis.alt_konu)
        court=normalize(str(e.metadata.get('mahkeme') or ''))
        parts['mahkeme_daire']=.5 if court and (court in problem or any(w in problem and w in court for w in ['yargıtay','danıştay','anayasa'])) else 0
        parts['daire']=.25 if court and re.search(r'\b\d+\.?\s*(?:hukuk|ceza|daire)',court) else 0
        parts['tarih']=0
        date=str(e.metadata.get('karar_tarihi') or '')
        for fmt in ['%d.%m.%Y','%Y-%m-%d','%d/%m/%Y']:
            try:
                year=datetime.strptime(date,fmt).year
                parts['tarih']=round(.2*max(0,min(1,(year-2000)/(datetime.now().year-2000))),3)
                break
            except ValueError: pass
        e.score=round(sum(parts.values()),3)
        e.metadata['alaka_bilesenleri']=parts
    return sorted(items,key=lambda e:e.score,reverse=True)

def accepted_claims(data,items):
    """Modelin iddiası yalnızca kaynakta birebir bulunan alıntıysa kabul edilir."""
    lookup={e.id:e for e in items if e.verified}
    claims=[]
    for claim in data.get('bulgular',[])[:8]:
        e=lookup.get(str(claim.get('kaynak_id','')))
        quote=str(claim.get('alinti','')).strip()
        if e and 40<=len(quote)<=900 and quote in e.text:
            claims.append({'kaynak_id':e.id,'alinti':quote,'baslik':e.title})
    return claims

def source_passages(items,analysis):
    """Model alıntısı doğrulanamazsa metinden birebir pasaj; serbest iddia yok."""
    result=[]
    for e in items:
        if not e.verified: continue
        segments=list(re.finditer(r'[^\n.!?]{40,450}(?:[.!?]|$)',e.text))
        if not segments: continue
        scored=[(sum(normalize(k) in normalize(m.group()) for k in analysis.anahtar_kavramlar),m.group().strip()) for m in segments]
        score,passage=max(scored,key=lambda pair:pair[0])
        if score and passage in e.text:
            result.append({'kaynak_id':e.id,'alinti':passage,'baslik':e.title,'secim':'kaynak pasajı — otomatik metin eşleşmesi'})
    return result[:4]

def related_articles(items):
    relations=[]
    laws=[e for e in items if e.kind=='mevzuat' and e.verified]
    for e in items:
        if e.kind!='ictihat' or not e.verified: continue
        for law in laws:
            no=str(law.metadata.get('kanun_no',''));article=str(law.metadata.get('madde_no',''))
            if no and article and re.search(r'\b'+re.escape(no)+r'\b',e.text) and re.search(r'(?:madde\s*'+re.escape(article)+r'\b|\b'+re.escape(article)+r'\s*\.?(?:inci|uncu|üncü|ıncı)?\s*madde)',e.text,re.I):
                relations.append({'karar_id':e.id,'madde_id':law.id,'durum':'Metinde kanun ve madde atfı bulundu; anlam incelemesi gerekir.'})
    return relations
