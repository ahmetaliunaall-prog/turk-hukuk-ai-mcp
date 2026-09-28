"""Public erişim anahtarı Edge Function'da doğrulanır; fail closed."""
import json,re,hashlib,secrets,string,time,threading,urllib.request,urllib.error
from pathlib import Path

def generate_key():return ''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(12))
def hash_key(key):return hashlib.sha256(key.encode()).hexdigest()
def valid_format(key):return isinstance(key,str) and re.fullmatch(r'[A-Za-z0-9]{12}',key) is not None

class AccessError(Exception):
    def __init__(self,message,status=401):super().__init__(message);self.status=status

class RateLimiter:
    def __init__(self,limit=20,window=60):self.limit=limit;self.window=window;self.rows={};self.lock=threading.Lock()
    def allow(self,scope):
        now=time.monotonic()
        with self.lock:
            self.rows={k:v for k,v in self.rows.items() if v[0]>now}
            end,count=self.rows.get(scope,(now+self.window,0));count+=1;self.rows[scope]=(end,count)
            return count<=self.limit

LIMITER=RateLimiter()
def settings():
    p=Path(__file__).resolve().parents[1]/'config/access.json'
    if not p.exists():p=p.with_name('access.public.json')
    if not p.exists():raise AccessError('Erişim hizmeti henüz bağlanmadı.',503)
    d=json.loads(p.read_text(encoding='utf-8'))
    url=d.get('supabase_url','');key=d.get('publishable_key','')
    if not re.fullmatch(r'https://[a-z0-9]+\.supabase\.co',url) or not key.startswith('sb_publishable_'):raise AccessError('Erişim hizmeti ayarları geçersiz.',503)
    return d

def validate_access(key,client='local',consume=True):
    if not LIMITER.allow(client):raise AccessError('Çok fazla erişim denemesi. Bir dakika bekleyin.',429)
    if not valid_format(key):raise AccessError('Sistemi kullanmak için geçerli erişim anahtarı gereklidir.')
    d=settings();body=json.dumps({'action':'consume' if consume else 'verify','key':key}).encode()
    req=urllib.request.Request(d['supabase_url']+'/functions/v1/thaimcp-access',data=body,headers={'apikey':d['publishable_key'],'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=12) as r:data=json.load(r)
    except urllib.error.HTTPError as ex:
        raise AccessError('Erişim deneme sınırı aşıldı.' if ex.code==429 else 'Erişim hizmeti isteği reddetti.',429 if ex.code==429 else 503) from None
    except Exception:raise AccessError('Erişim hizmetine ulaşılamadı.',503) from None
    if data.get('valid') is not True:raise AccessError('Erişim anahtarı geçersiz, iptal edilmiş veya süresi dolmuş.')
    return True
