from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json,os,asyncio,secrets,threading
import queue
from .ollama import request,MODEL
from legal_mcp.orchestrator import research
from legal_mcp.access import validate_access,AccessError

ROOT=Path(__file__).resolve().parents[1]
TOKEN=secrets.token_urlsafe(32)
LOCK=threading.Lock()
ALLOWED_ORIGINS={'http://127.0.0.1:8765','http://localhost:8765'}
cfg=ROOT/'config/local.json'
if cfg.exists():
    value=json.loads(cfg.read_text(encoding='utf-8')).get('netlify_origin')
    if value and urlparse(value).scheme=='https' and urlparse(value).hostname.endswith('.netlify.app'): ALLOWED_ORIGINS.add(value.rstrip('/'))

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # Müvekkil verisi/log tutulmaz.
    def valid_host(self): return self.headers.get('Host') in ('127.0.0.1:8765','localhost:8765')
    def headers_out(self,code,ctype='application/json'):
        self.send_response(code);self.send_header('Content-Type',ctype+'; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        origin=self.headers.get('Origin')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin',origin);self.send_header('Vary','Origin')
            self.send_header('Access-Control-Allow-Headers','Content-Type, X-Local-Token, X-Access-Key')
            self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
            if self.headers.get('Access-Control-Request-Private-Network')=='true':
                self.send_header('Access-Control-Allow-Private-Network','true')
        self.end_headers()
    def json(self,code,data):
        self.headers_out(code);self.wfile.write(json.dumps(data,ensure_ascii=False).encode())
    def do_OPTIONS(self):
        if not self.valid_host() or self.headers.get('Origin') not in ALLOWED_ORIGINS: return self.json(403,{'error':'Origin reddedildi'})
        self.headers_out(204)
    def do_GET(self):
        if not self.valid_host(): return self.json(403,{'error':'Host reddedildi'})
        if self.path=='/api/status':
            if self.headers.get('Origin') and self.headers.get('Origin') not in ALLOWED_ORIGINS: return self.json(403,{'error':'Origin reddedildi'})
            try:
                models=[m['name'] for m in request('/api/tags',timeout=3)['models']]
                return self.json(200,{'ollama':True,'model':MODEL,'ready':MODEL in models})
            except Exception: return self.json(200,{'ollama':False,'model':MODEL,'ready':False})
        if self.path=='/session.js':
            # Token yalnızca aynı yerel sayfaya verilir; dış sayfaya otomatik verilmez.
            if self.headers.get('Origin') or self.headers.get('Sec-Fetch-Site') not in (None,'same-origin'):
                return self.json(403,{'error':'Yerel oturum gerekli'})
            self.headers_out(200,'application/javascript');return self.wfile.write(('window.LOCAL_TOKEN='+json.dumps(TOKEN)+';').encode())
        name=self.path.split('?')[0].lstrip('/') or 'index.html'
        if name not in ('index.html','style.css','app.js','favicon.svg','config.js','admin.html','admin.js'): return self.json(404,{'error':'Bulunamadı'})
        types={'html':'text/html','css':'text/css','js':'application/javascript','svg':'image/svg+xml'}
        self.headers_out(200,types[name.split('.')[-1]]);self.wfile.write((ROOT/'frontend'/name).read_bytes())
    def do_POST(self):
        origin=self.headers.get('Origin')
        if not self.valid_host() or origin not in ALLOWED_ORIGINS or not secrets.compare_digest(self.headers.get('X-Local-Token',''),TOKEN):
            return self.json(403,{'error':'Yerel bağlantı kodu veya origin geçersiz.'})
        if self.path not in ('/api/research','/api/research/stream','/api/key/verify'): return self.json(404,{'error':'Bulunamadı'})
        try:
            validate_access(self.headers.get('X-Access-Key',''),self.client_address[0],consume=self.path!='/api/key/verify')
            if self.path=='/api/key/verify':return self.json(200,{'valid':True})
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=24000: return self.json(413,{'error':'En fazla 24 KB olay anlatımı kullanın.'})
            data=json.loads(self.rfile.read(size));text=data.get('text','')
            if not isinstance(text,str) or not 15<=len(text)<=6000: return self.json(400,{'error':'Soruyu 15–6000 karakter arasında yazın.'})
            limit=int(data.get('limit',10));page=int(data.get('page',1))
            if limit not in (10,20) or not 1<=page<=10 or data.get('court','adli') not in ('adli','idari','anayasa'): return self.json(400,{'error':'Geçersiz araştırma sınırı.'})
            if data.get('mode','research') not in ('research','petition'): return self.json(400,{'error':'Geçersiz araştırma türü.'})
            if not LOCK.acquire(blocking=False): return self.json(409,{'error':'Bir araştırma sürüyor. Tamamlanmasını bekleyin.'})
            streamed=False
            try:
                if self.path=='/api/research/stream':
                    events=queue.Queue()
                    def job():
                        try:
                            result=asyncio.run(research(text,limit,page,data.get('mode','research'),data.get('court','adli'),progress=lambda e:events.put(('progress',e))))
                            events.put(('result',result))
                        except Exception:events.put(('error',{'error':'Araştırma tamamlanamadı. Yerel bağlantıyı kontrol edin.'}))
                        finally:LOCK.release()
                    threading.Thread(target=job,daemon=True).start();streamed=True
                    self.headers_out(200,'application/x-ndjson')
                    while True:
                        kind,event=events.get()
                        try:self.wfile.write((json.dumps({'type':kind,'data':event},ensure_ascii=False)+'\n').encode());self.wfile.flush()
                        except (BrokenPipeError,ConnectionResetError):return
                        if kind in ('result','error'):break
                    return
                result=asyncio.run(research(text,limit,page,data.get('mode','research'),data.get('court','adli')))
            finally:
                if not streamed:LOCK.release()
            return self.json(200,result)
        except AccessError as ex:return self.json(ex.status,{'error':str(ex),'valid':False})
        except Exception as ex: return self.json(502,{'error':'Araştırma tamamlanamadı: '+type(ex).__name__+'. Yerel bağlantıyı kontrol edin.'})

def main():
    print('Türk Hukuk AI: http://127.0.0.1:8765',flush=True)
    print('Netlify için bu oturumun bağlantı kodu: '+TOKEN,flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()

if __name__=='__main__': main()
